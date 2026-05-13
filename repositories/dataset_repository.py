import sqlite3

from models.dataset import Dataset
from repositories.image_repository import ImageRepository


class DatasetRepository:
    def __init__(self, conn):
        self.conn = conn

    def add_existing_image(self, image, dataset_id):
        cursor = self.conn.cursor()
        cursor.execute("""INSERT INTO images_datasets (image_id, dataset_id, image_status)
                        VALUES (?, ?, ?)""",
                       (image.id, dataset_id, "uploaded"))
        self.conn.commit()

    def delete(self, dataset_id):
        cursor = self.conn.cursor()
        image_repo = ImageRepository(self.conn)
        #поиск изображений в удаляемом датасете
        img_toDelete_ids = image_repo.get_imageIds_by_dataset(dataset_id)

        #удаление из таблицы изображения-датасеты
        #self.delete_images_from_dataset(dataset_id)

        #удаление из таблицы Датасеты
        cursor.execute("DELETE FROM datasets WHERE id = ?",
                       (dataset_id,))
        self.conn.commit()

        #удаление изображений находящихся только в удаляемом датасете
        image_repo.delete_noExist_images(img_toDelete_ids)

    def delete_images_from_dataset(self, dataset_id):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM images_datasets WHERE dataset_id = ?",
                       (dataset_id,))
        self.conn.commit()

    def change_name(self, new_name, item):
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE datasets SET name = ? WHERE id = ?",
            (new_name, item.id)
        )
        self.conn.commit()

    def get_datasets_by_user(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM datasets WHERE user_id = ?;",
            (user_id,)
        )
        rows = cursor.fetchall()

        if rows is None:
            return None

        datasets = []
        for row in rows:
            loaded_dataset = Dataset.from_row(row)
            datasets.append(loaded_dataset)

        return datasets


    def create_dataset(self, name, file_path, user_id, images=None):
        cursor = self.conn.cursor()

        #проверяем существование датасета с таким именем
        exists = self.get_dataset_by_name(name, user_id)
        if exists:
            return None

        #создаем датасет
        cursor.execute(
            """INSERT INTO datasets (name, file_path, user_id)
                VALUES (?, ?, ?)""",
            (name, file_path, user_id)
        )
        self.conn.commit()
        new_dataset = self.get_dataset_by_name(name, user_id)

        if images and len(images) > 0:
            active_images = [img for img in images if img.status != "deleted"]
            for img in active_images:
                self.add_existing_image(img, new_dataset.id)

            new_dataset.add_existing_images(active_images)

        return new_dataset


    def get_dataset_by_name(self, name, user_id):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM datasets WHERE name = ? AND user_id = ?;",
            (name, user_id)
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return Dataset.from_row(row)

    def get_dataset_by_id(self, id):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM datasets WHERE id = ?;",
            (id,)
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return Dataset.from_row(row)


