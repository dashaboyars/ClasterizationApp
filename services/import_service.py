import os

from PyQt6.QtWidgets import *

from models.dataset import Dataset
from models.image import Image
from services.qualityAnalyse_service import QualityAnalyseService


class ImportService:
    def __init__(self, db, embedding_calculator, qualityAnalyse_service):
        self.db = db
        self.embedding_calculator = embedding_calculator
        self.qualityAnalyse_service = qualityAnalyse_service

    def import_image(self, dataset, files, progress_callback=None, cancel_check=None):
        # начальный прогресс
        if progress_callback:
            progress_callback(5, "Подготовка...")
        if cancel_check and cancel_check():
            return None

        added_count = 0
        total_images = len(files)
        added_images = []
        for file_path in files:
            filename = os.path.basename(file_path)
            normalised = os.path.normpath(file_path)
            # обновление прогресса
            if cancel_check and cancel_check():
                return None
            if progress_callback:
                percent = 5 + int((added_count + 1) / total_images * 75)
                progress_callback(percent, f"Обработка: {filename}")

            format = os.path.splitext(filename)[1].lower()
            vector_data = self.embedding_calculator.get_embedding(normalised)
            quality_characteristics = self.qualityAnalyse_service.get_quality_char(normalised)

            #сначала создаем только модель (в приложении)
            new_image = Image(filename, normalised, format, vector_data, quality_characteristics, dataset.id)
            added_images.append(new_image)
            added_count += 1

        #сохраняем все в БД
        added_images = self.saveImages_inDB(added_images, dataset, progress_callback)

        return [added_count, dataset], added_images

    def saveImages_inDB(self, images, dataset, progress_callback=None, cur_conn=None):
        from repositories.image_repository import ImageRepository
        # создаем новое соединение
        if cur_conn:
            conn = cur_conn
        else:
            conn = self.db.connect()
        image_repo = ImageRepository(conn)

        total = len(images)
        added_count = 0
        added_images = []
        for img in images:
            new_image = image_repo.create_image(img.filename, img.filepath, img.format, dataset.id,
                                                    img.embedding, img.quality_params)
            added_images.append(new_image)
            dataset.images_list.append(new_image)

            # обновление прогресса
            if progress_callback:
                percent = 80 + int((added_count + 1) / total * 20)
                progress_callback(percent, f"Cохранение: {img.filename}\n(Отмена операции невозможна)")

        conn.commit()
        # прогресс при завершении
        if progress_callback:
            progress_callback(100, "Завершено!")
        if not cur_conn:
            conn.close()

        return added_images

    def saveDataset_inDB(self, dataset, images_list, progress_callback=None):
        from repositories.dataset_repository import DatasetRepository
        # СОЗДАЕМ НОВОЕ соединение в этом потоке
        conn = self.db.connect()
        dataset_repo = DatasetRepository(conn)

        new_dataset = dataset_repo.create_dataset(dataset.name, dataset.file_path, dataset.user_id)
        self.saveImages_inDB(images_list, new_dataset, progress_callback, conn)

        conn.commit()
        conn.close()

        return new_dataset

    def import_dataset(self, folder_path, dataset_name, current_user_id, image_files, progress_callback=None, cancel_check=None):
        #начальный прогресс
        if progress_callback:
            progress_callback(5, "Подготовка...")

        if cancel_check and cancel_check():
            return None

        if progress_callback:
            progress_callback(10, "Создание датасета...")
        # создание модели датасета (в приложении)
        new_dataset = Dataset(dataset_name, folder_path, current_user_id)

        # создание моделей изображений (в приложении)
        added_count = 0
        total_images = len(image_files)
        added_images = []
        for filename in image_files:
            #обновление прогресса
            if cancel_check and cancel_check():
                return None
            if progress_callback:
                percent = 10 + int((added_count + 1) / total_images * 70)
                progress_callback(percent, f"Обработка: {filename}")

            filePath = os.path.join(folder_path, filename)
            normalised = os.path.normpath(filePath)
            format = os.path.splitext(filename)[1].lower()
            vector_data = self.embedding_calculator.get_embedding(filePath)
            quality_characteristics = self.qualityAnalyse_service.get_quality_char(filePath)

            new_image = Image(filename, normalised, format, vector_data, quality_characteristics)
            added_images.append(new_image)
            added_count += 1

        saved_dataset = self.saveDataset_inDB(new_dataset, added_images, progress_callback)

        return saved_dataset


