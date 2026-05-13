import numpy as np

from models.image import Image


class ImageRepository:
    def __init__(self, conn):
        self.conn = conn

    def get_imageStatus(self, image_id, dataset_id):
        cursor = self.conn.cursor()
        cursor.execute("""SELECT imd.image_status
            FROM images_datasets imd
            WHERE imd.image_id = ? AND imd.dataset_id = ?""",
            (image_id, dataset_id))
        row = cursor.fetchone()
        if row:
            return row['image_status']
        return None


    def update_status(self, images, dataset_id):
        cursor = self.conn.cursor()
        for img in images:
            cursor.execute("""UPDATE images_datasets SET image_status = ? 
            WHERE image_id = ? AND dataset_id = ?""",
                           (img.status, img.id, dataset_id))
        self.conn.commit()

    def change_cluster(self, image, old_cluster, target_cluster):
        cursor = self.conn.cursor()
        cursor.execute("""
                UPDATE images_clusters
                SET cluster_id = ?, manual = 1, connect_time = CURRENT_TIMESTAMP
                WHERE image_id = ? AND cluster_id = ?""",
                (target_cluster.id, image.id, old_cluster.id))
        self.conn.commit()

    def moveImages_fromCluster_toAnomalies(self, image, old_cluster, target_group):
        cursor = self.conn.cursor()
        cursor.execute("""
                DELETE FROM images_clusters
                WHERE image_id = ? AND cluster_id = ?""",
                (image.id, old_cluster.id))
        self.conn.commit()

        cursor.execute("""
                INSERT INTO images_anomalies (image_id, anomaliesGroup_id)
                VALUES (?, ?)""",
                (image.id, target_group.id))
        self.conn.commit()

    def moveImage_fromAnomalies_toCluster(self, image, old_group, target_cluster):
        cursor = self.conn.cursor()
        cursor.execute("""
                DELETE FROM images_anomalies
                WHERE image_id = ? AND anomaliesGroup_id = ?""",
                (image.id, old_group.id))
        self.conn.commit()

        cursor.execute("""
                INSERT INTO images_clusters (image_id, cluster_id, manual)
                VALUES (?, ?, 1)""",
                (image.id, target_cluster.id))
        self.conn.commit()

    def change_dataset(self, image, old_dataset, target_dataset):
        from repositories.dataset_repository import DatasetRepository

        cursor = self.conn.cursor()
        #у текущей записи статус ставим deleted
        self.update_status([image], old_dataset.id)
        #self.conn.commit()

        #добавляем новую запись
        dataset_repo = DatasetRepository(self.conn)
        dataset_repo.add_existing_image(image, target_dataset.id)

    def change_name(self, image, new_name):
        cursor = self.conn.cursor()
        cursor.execute("""
                        UPDATE images
                        SET file_name = ?
                        WHERE id = ?""",
                       (new_name, image.id))
        self.conn.commit()

    def get_images_by_anomalyGroup(self, anomalyGroup_id, dataset_id):
        cursor = self.conn.cursor()
        cursor.execute(
            """SELECT i.*, imd.image_status, imd.upload_time
            FROM images i
            JOIN images_anomalies ia ON i.id = ia.image_id
            JOIN images_datasets imd ON i.id = imd.image_id
            WHERE ia.anomaliesGroup_id = ? AND imd.dataset_id = ?""",
            (anomalyGroup_id, dataset_id)
        )
        rows = cursor.fetchall()
        if rows is None:
            return None

        images = []
        for row in rows:
            loaded_image = Image.from_row(row)
            # приводим эмбеддинг к numpy array
            embedding = np.frombuffer(loaded_image.embedding, dtype=np.float32)
            loaded_image.embedding = embedding

            images.append(loaded_image)
        return images


    def get_images_by_cluster(self, cluster_id, dataset_id):
        cursor = self.conn.cursor()
        cursor.execute(
            """SELECT i.*, imd.image_status, imd.upload_time
            FROM images i
            JOIN images_clusters ic ON i.id = ic.image_id
            JOIN images_datasets imd ON i.id = imd.image_id
            WHERE ic.cluster_id = ? AND imd.dataset_id = ?""",
            (cluster_id, dataset_id)
        )
        rows = cursor.fetchall()
        if rows is None:
            return None

        images = []
        for row in rows:
            loaded_image = Image.from_row(row)
            # приводим эмбеддинг к numpy array
            embedding = np.frombuffer(loaded_image.embedding, dtype=np.float32)
            loaded_image.embedding = embedding

            images.append(loaded_image)
        return images

    def delete_noExist_images(self, img_toDelete_ids):
        cursor = self.conn.cursor()
        placeholders = ','.join('?' * len(img_toDelete_ids))

        query = f"SELECT image_id FROM images_datasets WHERE image_id IN ({placeholders})"
        cursor.execute(query, img_toDelete_ids)
        existing_ids = {row['image_id'] for row in cursor.fetchall()}
        # Изображения, которые есть хотя бы в одном датасете, не удаляем
        to_delete = [id for id in img_toDelete_ids if id not in existing_ids]
        if not to_delete:
            return
        placeholders = ','.join('?' * len(to_delete))
        query = f"DELETE FROM images WHERE id in ({placeholders})"
        cursor.execute(query, to_delete)
        self.conn.commit()

    def get_images_by_classification_session(self, classif_session_id):
        cursor = self.conn.cursor()
        cursor.execute(
            """SELECT i.id, cr.label, cr.confidence
            FROM images i
            JOIN images_datasets imd ON i.id = imd.image_id
            JOIN classification_results cr ON cr.image_in_dataset_id = imd.id
            WHERE classification_session_id = ?""",
            (classif_session_id,))
        rows = cursor.fetchall()
        if rows is None:
            return None

        res = []
        for row in rows:
            item = {'image_id': row['id'],
                    'label': row['label'],
                    'confidence': row['confidence']}
            res.append(item)
        return res


    def get_images_by_dataset(self, dataset_id):
        cursor = self.conn.cursor()
        cursor.execute(
            """SELECT i.*, imd.image_status, imd.upload_time, imd.dataset_id, imd.dataset_id
            FROM images i
            JOIN images_datasets imd ON i.id = imd.image_id
            WHERE imd.dataset_id = ?
            """,
            (dataset_id, )
        )
        rows = cursor.fetchall()
        if rows is None:
            return None

        images = []
        for row in rows:
            loaded_image = Image.from_row(row)
            #приводим эмбеддинг к numpy array
            embedding = np.frombuffer(loaded_image.embedding, dtype=np.float32)
            loaded_image.embedding = embedding

            images.append(loaded_image)

        return images

    def get_imageDataset_Pair_Ids(self, images_ids, dataset_id):
        cursor = self.conn.cursor()
        placeholders = ','.join('?' * len(images_ids))
        query = f"SELECT id FROM images_datasets WHERE dataset_id = ? AND image_id IN ({placeholders})"
        params = [dataset_id] + images_ids
        cursor.execute(query, params)
        rows = cursor.fetchall()

        pair_ids = []
        for row in rows:
            pair_ids.append(row['id'])

        return pair_ids

    def get_imageIds_by_dataset(self, dataset_id):
        cursor = self.conn.cursor()
        img_ids = []
        cursor.execute("SELECT image_id FROM images_datasets WHERE dataset_id = ?",
                       (dataset_id,))
        rows = cursor.fetchall()
        for row in rows:
            img_ids.append(row['image_id'])

        return img_ids

    def create_image(self, file_name, file_path, format, dataset_id, vector_data=None, quality=None):
        cursor = self.conn.cursor()

        # проверяем существование изображения с таким именем в датасете
        exists = self.get_imageInDataset_by_name(file_name, dataset_id)
        if exists:
            name = f"{file_name} - копия"
        else:
            name = file_name

        #создаем изображение
        # Конвертируем numpy массив в BLOB
        embedding_blob = vector_data.astype(np.float32).tobytes()

        if quality is None:
            cursor.execute(
                """INSERT INTO images (file_name, file_path, format, vector_data)
                     VALUES (?, ?, ?, ?)""",
                (name, file_path, format, embedding_blob)
            )
        else:
            cursor.execute(
                """INSERT INTO images (file_name, file_path, format, vector_data, file_size,
                 resolution_width, resolution_height, colors_amount, sharpness, noise_level,
                 contrast)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (name, file_path, format, embedding_blob, quality['file_size'],
                 quality['resolution_width'], quality['resolution_height'], quality['colors_amount'],
                 quality['sharpness'], quality['noise_level'], quality['contrast'])
            )
        new_id = cursor.lastrowid
        self.conn.commit()

        #добавляем свзяь между изображением и датасетом
        cursor.execute(
            """INSERT INTO images_datasets (image_id, dataset_id)
                VALUES (?, ?)""",
            (new_id, dataset_id)
        )
        new_image = self.get_image_by_id(new_id)
        self.conn.commit()

        return new_image

    def get_imageInDataset_by_name(self, name, dataset_id):
        cursor = self.conn.cursor()
        cursor.execute(
            """SELECT i.*, imd.image_status, imd.upload_time
            FROM images i
            JOIN images_datasets imd ON i.id = imd.image_id
            WHERE i.file_name = ? AND imd.dataset_id = ? AND imd.image_status <> 'deleted'
            """,
            (name, dataset_id)
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return Image.from_row(row)




    def get_image_by_id(self, id):
        cursor = self.conn.cursor()
        cursor.execute(
            """SELECT i.*, imd.image_status, imd.upload_time
            FROM images i
            JOIN images_datasets imd ON i.id = imd.image_id
            WHERE i.id = ? AND imd.image_status <> 'deleted'
            """,
            (id,)
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return Image.from_row(row)