from unittest.mock import MagicMock

import numpy as np

from models.image import Image


def test_saveImages_inDB_with_external_connection(image_repo, import_service, dataset_repo):
    # Создаём датасет
    dataset = dataset_repo.create_dataset("Test", "/path", 1)
    quality = {
        'file_size': 1024,
        'resolution_width': 1920,
        'resolution_height': 1080,
        'colors_amount': 16777216,
        'sharpness': 0.5,
        'noise_level': 0.1,
        'contrast': 0.8,
    }
    # Создаём временные объекты Image (без id)
    img1 = Image("a.jpg", "/a.jpg", "jpg", np.zeros(1280), quality, dataset.id)
    img2 = Image("b.jpg", "/b.jpg", "jpg", np.zeros(1280), quality, dataset.id)
    # Сохраняем через saveImages_inDB с внешним соединением
    conn = import_service.db.connect()
    saved = import_service.saveImages_inDB([img1, img2], dataset, cur_conn=conn)
    assert len(saved) == 2
    assert all(img.id is not None for img in saved)
    # Проверяем, что изображения появились в БД
    images_in_db = image_repo.get_images_by_dataset(dataset.id)
    assert len(images_in_db) == 2
    conn.close()

def test_import_dataset_empty_folder(import_service, tmp_path):
    folder = tmp_path / "empty"
    folder.mkdir()
    result = import_service.import_dataset(str(folder), "EmptyDS", 1, [])
    assert result is not None
    assert len(result.images_list) == 0

def test_import_dataset_cancel_after_creation(import_service, tmp_path):
    folder = tmp_path / "dataset"
    folder.mkdir()
    img1 = folder / "1.jpg"
    img1.write_bytes(b"fake")
    image_files = ["1.jpg"]
    cancel_check = MagicMock(side_effect=[False, True])
    result = import_service.import_dataset(str(folder), "CancelDS", 1,
                                           image_files, cancel_check=cancel_check)
    assert result is None
    from repositories.dataset_repository import DatasetRepository
    dataset_repo = DatasetRepository(import_service.db.connect())
    saved_ds = dataset_repo.get_dataset_by_name("CancelDS", 1)
    assert saved_ds is None

def test_import_dataset_success(import_service, tmp_path):
    # Создаём временную папку с изображениями
    folder = tmp_path / "dataset"
    folder.mkdir()
    img1 = folder / "1.jpg"
    img2 = folder / "2.png"
    img1.write_bytes(b"fake image data")
    img2.write_bytes(b"fake image data")
    image_files = ["1.jpg", "2.png"]
    dataset = import_service.import_dataset(str(folder), "NewDataset", 1, image_files)
    assert dataset is not None
    assert dataset.name == "NewDataset"
    assert dataset.user_id == 1
    assert len(dataset.images_list) == 2
    # Проверяем, что датасет сохранился в БД
    from repositories.dataset_repository import DatasetRepository
    from repositories.image_repository import ImageRepository
    dataset_repo = DatasetRepository(import_service.db.connect())
    saved_ds = dataset_repo.get_dataset_by_name("NewDataset", 1)
    assert saved_ds is not None
    image_repo = ImageRepository(import_service.db.connect())
    images = image_repo.get_images_by_dataset(saved_ds.id)
    assert len(images) == 2

def test_import_image_success(image_repo, import_service, dataset_repo):
    # Создаём датасет в БД
    dataset = dataset_repo.create_dataset("TestDS", "/path", 1)
    files = [r"C:\test\img1.jpg", r"C:\test\img2.jpg"]
    # Мокаем get_embedding для каждого вызова (можно оставить как есть, он замокан)
    result, added_images = import_service.import_image(dataset, files)
    assert result[0] == 2  # добавлено 2 изображения
    assert result[1] == dataset
    assert len(added_images) == 2
    assert all(isinstance(img, Image) for img in added_images)
    # Проверяем, что изображения действительно сохранились в БД
    images_in_db = image_repo.get_images_by_dataset(dataset.id)
    assert len(images_in_db) == 2

def test_import_image_cancel_before_start(import_service, dataset_repo):
    dataset = dataset_repo.create_dataset("TestDS", "/path", 1)
    files = ["a.jpg", "b.jpg"]
    # Определяем cancel_check, возвращающий True сразу
    cancel_check = lambda: True
    result = import_service.import_image(dataset, files, cancel_check=cancel_check)
    assert result is None

def test_import_image_cancel_during_processing(image_repo, import_service, dataset_repo):
    dataset = dataset_repo.create_dataset("TestDS", "/path", 1)
    files = ["a.jpg", "b.jpg"]
    # Мок для cancel_check: первый раз False, потом True
    calls = [False, True]

    def cancel_check():
        return calls.pop(0) if calls else False

    result = import_service.import_image(dataset, files, cancel_check=cancel_check)
    # Операция должна быть прервана, результат None
    assert result is None
    # Проверяем, что ни одно изображение не было сохранено
    images_in_db = image_repo.get_images_by_dataset(dataset.id)
    assert len(images_in_db) == 0