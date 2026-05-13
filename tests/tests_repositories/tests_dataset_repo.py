import numpy as np
import pytest
from models.dataset import Dataset


def test_create_dataset(dataset_repo):
    dataset = dataset_repo.create_dataset("TestDataset", "/path", user_id=1)
    assert dataset is not None
    assert dataset.name == "TestDataset"
    assert dataset.file_path == "/path"
    assert dataset.user_id == 1

    # Повторное создание с тем же именем должно вернуть None
    duplicate = dataset_repo.create_dataset("TestDataset", "/other", user_id=1)
    assert duplicate is None

def test_create_dataset_withImages(image_repo, dataset_repo):
    # Создаём изображение
    embedding = np.zeros(1280, dtype=np.float32)
    dataset = dataset_repo.create_dataset("TestDataset", "/path", user_id=1)
    img = image_repo.create_image("test.jpg", "/test.jpg", "jpg", dataset.id, embedding, None)

    #создаем копию датасета с изображением
    dataset_copy = dataset_repo.create_dataset("TestDataset_Copy", "/path", user_id=1, images=[img])
    images_found = image_repo.get_images_by_dataset(dataset_copy.id)
    assert dataset_copy is not None
    assert dataset_copy.name == "TestDataset_Copy"
    assert dataset_copy.file_path == "/path"
    assert dataset_copy.user_id == 1
    assert len(dataset_copy.images_list) == 1
    assert images_found is not None
    assert len(images_found) == 1
    assert images_found[0].id  == img.id

    # Повторное создание с тем же именем должно вернуть None
    duplicate = dataset_repo.create_dataset("TestDataset", "/other", user_id=1)
    assert duplicate is None

def test_get_dataset_by_id(dataset_repo):
    dataset = dataset_repo.create_dataset("GetById", "/path", 1)
    fetched = dataset_repo.get_dataset_by_id(dataset.id)
    assert fetched is not None
    assert fetched.name == "GetById"
    assert fetched.id == dataset.id

    assert dataset_repo.get_dataset_by_id(9999) is None

def test_get_dataset_by_name(dataset_repo):
    dataset = dataset_repo.create_dataset("UniqueName", "/path", 1)
    fetched = dataset_repo.get_dataset_by_name("UniqueName", 1)
    assert fetched is not None
    assert fetched.id == dataset.id

    # Несуществующее имя
    assert dataset_repo.get_dataset_by_name("NoSuch", 1) is None

def test_get_datasets_by_user(dataset_repo):
    # Создаём два датасета для пользователя 1
    ds1 = dataset_repo.create_dataset("User1_DS1", "/p1", 1)
    ds2 = dataset_repo.create_dataset("User1_DS2", "/p2", 1)
    datasets = dataset_repo.get_datasets_by_user(1)
    assert len(datasets) >= 2
    ids = [ds.id for ds in datasets]
    assert ds1.id in ids
    assert ds2.id in ids

def test_get_datasets_by_user_noDatasets(dataset_repo):
    datasets = dataset_repo.get_datasets_by_user(1)
    assert len(datasets) == 0

def test_change_name(dataset_repo):
    dataset = dataset_repo.create_dataset("OldName", "/path", 1)
    dataset_repo.change_name("NewName", dataset)
    updated = dataset_repo.get_dataset_by_id(dataset.id)
    assert updated.name == "NewName"

def test_add_existing_image(dataset_repo, image_repo):
    # Создаём датасет
    dataset = dataset_repo.create_dataset("ForImage", "/path", 1)
    dataset_other = dataset_repo.create_dataset("Other", "/path", 1)
    # Создаём изображение
    embedding = np.zeros(1280, dtype=np.float32)
    img = image_repo.create_image("test.jpg", "/test.jpg", "jpg", dataset_other.id, embedding, None)
    #добавляем созданное изображения в датасет
    dataset_repo.add_existing_image(img, dataset.id)
    # Проверяем, что связь появилась
    images_in_ds = image_repo.get_images_by_dataset(dataset.id)
    for img in images_in_ds:
        print(img.id)
        print(img.filename)
    assert len(images_in_ds) == 1
    assert images_in_ds[0].id == img.id

def test_delete_images_from_dataset(dataset_repo, image_repo):
    dataset = dataset_repo.create_dataset("DelImages", "/path", 1)
    embedding = np.zeros(1280, dtype=np.float32)
    img1 = image_repo.create_image("img1.jpg", "/p1", "jpg", dataset.id, embedding, None)
    img2 = image_repo.create_image("img2.jpg", "/p2", "jpg", dataset.id, embedding, None)
    assert image_repo.get_image_by_id(img1.id) is not None
    assert image_repo.get_image_by_id(img2.id) is not None
    images = image_repo.get_images_by_dataset(dataset.id)
    assert len(images) == 2
    # Удаляем связи
    dataset_repo.delete_images_from_dataset(dataset.id)
    images = image_repo.get_images_by_dataset(dataset.id)
    assert len(images) == 0
    assert image_repo.get_image_by_id(img1.id) is None
    assert image_repo.get_image_by_id(img2.id) is None

def test_delete_dataset(dataset_repo, image_repo):
    # Создаём датасет с изображениями
    dataset = dataset_repo.create_dataset("ToDelete", "/path", 1)
    embedding = np.zeros(1280, dtype=np.float32)
    img1 = image_repo.create_image("del1.jpg", "/d1", "jpg", dataset.id, embedding, None)
    img2 = image_repo.create_image("del2.jpg", "/d2", "jpg", dataset.id, embedding, None)
    # Удаляем датасет
    dataset_repo.delete(dataset.id)
    # Сам датасет не должен находиться
    assert dataset_repo.get_dataset_by_id(dataset.id) is None
    # Связи изображений должны быть удалены
    assert len(image_repo.get_images_by_dataset(dataset.id)) == 0
    # Изображения, которые были только в этом датасете, должны быть удалены физически
    assert image_repo.get_image_by_id(img1.id) is None
    assert image_repo.get_image_by_id(img2.id) is None