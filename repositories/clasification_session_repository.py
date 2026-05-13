import json

from models.clasification_session import ClasificationSession
from repositories.image_repository import ImageRepository


class ClassificationSessionRepository:
    def __init__(self, conn):
        self.conn = conn

    def change_image_label(self, dataset_id, session_id, image_id, new_label):
        if new_label == 'Другое':
            new_label = 'Не в кадре'
        cursor = self.conn.cursor()
        cursor.execute("""SELECT id FROM images_datasets 
                        WHERE image_id = ? AND dataset_id = ?""",
                       (image_id, dataset_id))
        row = cursor.fetchone()
        if not row:
            return False
        image_in_dataset_id = row['id']

        cursor.execute("""UPDATE classification_results
                        SET label = ?, confidence = 0, is_manual = 1
                        WHERE image_in_dataset_id = ? AND classification_session_id = ?""",
                       (new_label, image_in_dataset_id, session_id))
        self.conn.commit()


    def rename_session(self, new_name, id):
        cursor = self.conn.cursor()
        cursor.execute("""UPDATE classification_sessions
                        SET name = ? 
                        WHERE id = ?""",
                       (new_name, id))
        self.conn.commit()

    def delete_session(self, ids):
        placeholders = ','.join('?' * len(ids))
        query = f"DELETE FROM classification_sessions WHERE id IN ({placeholders})"
        cursor = self.conn.cursor()
        cursor.execute(query, ids)
        self.conn.commit()

    def create_session(self, name, model_version_id, dataset_id, images_labels=None, images=None):
        cursor = self.conn.cursor()

        cursor.execute("""INSERT INTO classification_sessions (dataset_id, model_version_id, name)
                            VALUES (?, ?, ?)""",
                       (dataset_id, model_version_id, name))
        self.conn.commit()

        new_session = self.get_session_by_name(name, dataset_id)

        #добавляем изображения с метками
        if images_labels is not None:
            self.add_labeled_images(images, new_session.id, images_labels, dataset_id)

        return new_session

    def get_session_labels(self, session_id):
        cursor = self.conn.cursor()
        cursor.execute("""SELECT label 
                        FROM classification_results
                        WHERE classification_session_id = ?""",
                       (session_id,))
        rows = cursor.fetchall()
        if rows is None:
            return None
        labels = [row['label'] for row in rows]
        return set(labels)


    def delete_group(self, label, session_id):
        cursor = self.conn.cursor()
        cursor.execute("""DELETE FROM classification_results
                        WHERE classification_session_id = ? AND label = ?""",
                       (session_id, label))
        self.conn.commit()


    def add_labeled_images(self, images, session_id, images_labels, dataset_id):
        cursor = self.conn.cursor()
        image_repo = ImageRepository(self.conn)
        img_ids = [img.id for img in images]
        img_in_dataset_ids = image_repo.get_imageDataset_Pair_Ids(img_ids, dataset_id)

        for i in range (len(images)):
            img_in_dts_id = img_in_dataset_ids[i]
            label = images_labels[i][0]
            confidence = images_labels[i][1]

            cursor.execute("""INSERT INTO classification_results 
                                (classification_session_id, image_in_dataset_id, label, confidence)
                                VALUES (?, ?, ?, ?)""",
                           (session_id, img_in_dts_id, label, confidence))
        self.conn.commit()


    def get_session_by_name(self, name, dataset_id):
        cursor = self.conn.cursor()
        cursor.execute("""SELECT * FROM classification_sessions
                        WHERE name = ? AND dataset_id = ?""",
                       (name, dataset_id))
        row = cursor.fetchone()
        if row is None:
            return None

        return ClasificationSession.from_row(row)


    def get_sessions_by_datasetId(self, dataset_id):
        cursor = self.conn.cursor()
        cursor.execute("""SELECT * FROM classification_sessions
                        WHERE dataset_id = ?""",
                       (dataset_id,))
        rows = cursor.fetchall()
        if not rows:
            return None
        sessions = []
        for row in rows:
            sessions.append(ClasificationSession.from_row(row))
        return sessions
