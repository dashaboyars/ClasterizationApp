import numpy as np
import pytest
from models.image import Image

def test_create_image(image_repo, dataset_repo):
    dataset = dataset_repo.create_dataset("TestDataset", "/path", user_id=1)
    embedding = np.zeros(1280, dtype=np.float32)
    image = image_repo.create_image("TestImage", "/TestImage",
                                    ".jpg", dataset.id, embedding)
    image_in_db = image_repo.get_image_by_id(image.id)
    assert image is not None
    assert (image_in_db.id == image.id and image_in_db.filename == image.filename
            and image_in_db.filepath == image.filepath and image_in_db.format == image.format
            and np.array_equal(image_in_db.embedding, image.embedding))


def test_get_image_by_id(dataset_repo, image_repo):
    dataset = dataset_repo.create_dataset("GetById", "/path", 1)
    embedding = np.zeros(1280, dtype=np.float32)
    img = image_repo.create_image("test.jpg", "/path", "jpg", dataset.id, embedding, None)
    fetched = image_repo.get_image_by_id(img.id)
    assert fetched is not None
    assert fetched.id == img.id
    assert fetched.filename == img.filename
    np.testing.assert_array_equal(fetched.embedding, embedding)

def test_get_imageInDataset_by_name(dataset_repo, image_repo):
    dataset = dataset_repo.create_dataset("NameTest", "/path", 1)
    embedding = np.zeros(1280, dtype=np.float32)
    img = image_repo.create_image("unique.jpg", "/path", "jpg", dataset.id, embedding, None)
    # ищем по имени
    found = image_repo.get_imageInDataset_by_name("unique.jpg", dataset.id)
    assert found is not None
    assert found.id == img.id
    # несуществующее имя
    not_found = image_repo.get_imageInDataset_by_name("no.jpg", dataset.id)
    assert not_found is None

def test_get_images_by_dataset(dataset_repo, image_repo):
    dataset = dataset_repo.create_dataset("ListImages", "/path", 1)
    embedding = np.zeros(1280, dtype=np.float32)
    img1 = image_repo.create_image("a.jpg", "/a", "jpg", dataset.id, embedding, None)
    img2 = image_repo.create_image("b.jpg", "/b", "jpg", dataset.id, embedding, None)
    images = image_repo.get_images_by_dataset(dataset.id)
    assert len(images) == 2
    ids = [img.id for img in images]
    assert img1.id in ids
    assert img2.id in ids

def test_get_imageIds_by_dataset(dataset_repo, image_repo):
    dataset = dataset_repo.create_dataset("GetIds", "/path", 1)
    embedding = np.zeros(1280, dtype=np.float32)
    img1 = image_repo.create_image("a.jpg", "/a", "jpg", dataset.id, embedding, None)
    img2 = image_repo.create_image("b.jpg", "/b", "jpg", dataset.id, embedding, None)
    ids = image_repo.get_imageIds_by_dataset(dataset.id)
    assert len(ids) == 2
    assert img1.id in ids
    assert img2.id in ids

def test_get_imageDataset_Pair_Ids(dataset_repo, image_repo):
    dataset = dataset_repo.create_dataset("PairIds", "/path", 1)
    embedding = np.zeros(1280, dtype=np.float32)
    img1 = image_repo.create_image("a.jpg", "/a", "jpg", dataset.id, embedding, None)
    img2 = image_repo.create_image("b.jpg", "/b", "jpg", dataset.id, embedding, None)
    pair_ids = image_repo.get_imageDataset_Pair_Ids([img1.id, img2.id], dataset.id)
    assert len(pair_ids) == 2
    # проверяем, что это id из таблицы images_datasets
    cursor = dataset_repo.conn.cursor()
    cursor.execute("SELECT id FROM images_datasets WHERE dataset_id = ?", (dataset.id,))
    db_ids = [row[0] for row in cursor.fetchall()]
    assert set(pair_ids) == set(db_ids)

def test_update_status(dataset_repo, image_repo):
    dataset = dataset_repo.create_dataset("UpdateStatus", "/path", 1)
    embedding = np.zeros(1280, dtype=np.float32)
    img = image_repo.create_image("status.jpg", "/path", "jpg", dataset.id, embedding, None)
    assert image_repo.get_imageStatus(img.id, dataset.id) == "uploaded"   # статус по умолчанию
    img.status = "deleted"
    image_repo.update_status([img], dataset.id)
    assert image_repo.get_imageStatus(img.id, dataset.id) == "deleted"

def test_change_name(dataset_repo, image_repo):
    dataset = dataset_repo.create_dataset("Rename", "/path", 1)
    embedding = np.zeros(1280, dtype=np.float32)
    img = image_repo.create_image("old.jpg", "/path", "jpg", dataset.id, embedding, None)
    image_repo.change_name(img, "new.jpg")
    updated = image_repo.get_image_by_id(img.id)
    assert updated.filename == "new.jpg"

def test_change_cluster(dataset_repo, image_repo, session_repo, cluster_repo):
    # создаём датасет
    dataset = dataset_repo.create_dataset("ChangeCluster", "/path", 1)
    # сессия кластеризации
    session = session_repo.create_session("TestSession",
                                          {"algorythm": "DBSCAN", "eps": 0.5},
                                          dataset.id)
    # два кластера
    cluster1 = cluster_repo.create_cluster("Cluster1", session.id)
    cluster2 = cluster_repo.create_cluster("Cluster2", session.id)
    # изображение
    embedding = np.zeros(1280, dtype=np.float32)
    img = image_repo.create_image("img.jpg", "/path", "jpg", dataset.id, embedding, None)
    # привязываем к cluster1 (прямой запрос для теста)
    cursor = dataset_repo.conn.cursor()
    cursor.execute("INSERT INTO images_clusters (image_id, cluster_id, manual) VALUES (?, ?, 0)", (img.id, cluster1.id))
    dataset_repo.conn.commit()
    # переносим в cluster2
    image_repo.change_cluster(img, cluster1, cluster2)
    # проверяем, что связь обновилась
    cursor.execute("SELECT cluster_id, manual FROM images_clusters WHERE image_id = ?", (img.id,))
    row = cursor.fetchone()
    assert row[0] == cluster2.id
    assert row[1] == 1   # manual = 1

def test_moveImages_fromCluster_toAnomalies(dataset_repo, image_repo, session_repo, cluster_repo, anomalyGroup_repo):
    dataset = dataset_repo.create_dataset("ClusterToAnomaly", "/path", 1)
    session = session_repo.create_session("TestSession",
                                          {"algorythm": "DBSCAN","eps": 0.5},
                                          dataset.id)
    cluster = cluster_repo.create_cluster("Cluster", session.id)
    anomaly_group = anomalyGroup_repo.create_group("Anomalies", session.id)
    embedding = np.zeros(1280, dtype=np.float32)
    img = image_repo.create_image("img.jpg", "/path", "jpg", dataset.id, embedding, None)
    cursor = dataset_repo.conn.cursor()
    cursor.execute("INSERT INTO images_clusters (image_id, cluster_id, manual) VALUES (?, ?, 0)",
                   (img.id, cluster.id))
    dataset_repo.conn.commit()
    # перемещаем в аномалии
    image_repo.moveImages_fromCluster_toAnomalies(img, cluster, anomaly_group)
    # проверяем, что cluster_link удалена, anomaly_link добавлена
    cursor.execute("SELECT 1 FROM images_clusters WHERE image_id = ?", (img.id,))
    assert cursor.fetchone() is None
    cursor.execute("SELECT 1 FROM images_anomalies WHERE image_id = ? AND anomaliesGroup_id = ?", (img.id, anomaly_group.id))
    assert cursor.fetchone() is not None

def test_moveImage_fromAnomalies_toCluster(dataset_repo, image_repo, session_repo, cluster_repo, anomalyGroup_repo):
    dataset = dataset_repo.create_dataset("AnomalyToCluster", "/path", 1)
    session = session_repo.create_session("TestSession",
                                          {"algorythm": "DBSCAN","eps": 0.5},
                                          dataset.id)
    cluster = cluster_repo.create_cluster("Cluster", session.id)
    anomaly_group = anomalyGroup_repo.create_group("Anomalies", session.id)
    embedding = np.zeros(1280, dtype=np.float32)
    img = image_repo.create_image("img.jpg", "/path", "jpg", dataset.id, embedding, None)
    cursor = dataset_repo.conn.cursor()
    cursor.execute("INSERT INTO images_anomalies (image_id, anomaliesGroup_id) VALUES (?, ?)", (img.id, anomaly_group.id))
    dataset_repo.conn.commit()
    # перемещаем в кластер
    image_repo.moveImage_fromAnomalies_toCluster(img, anomaly_group, cluster)
    cursor.execute("SELECT 1 FROM images_anomalies WHERE image_id = ?", (img.id,))
    assert cursor.fetchone() is None
    cursor.execute("SELECT 1 FROM images_clusters WHERE image_id = ? AND cluster_id = ?", (img.id, cluster.id))
    assert cursor.fetchone() is not None

def test_change_dataset(dataset_repo, image_repo):
    # создаём два датасета
    dataset1 = dataset_repo.create_dataset("Source", "/path", 1)
    dataset2 = dataset_repo.create_dataset("Target", "/path", 1)
    embedding = np.zeros(1280, dtype=np.float32)
    img = image_repo.create_image("img.jpg", "/path", "jpg", dataset1.id, embedding, None)
    # меняем датасет
    img.status = "deleted"
    image_repo.change_dataset(img, dataset1, dataset2)
    # проверяем, что связь с dataset1 удалена (статус deleted)
    assert image_repo.get_imageStatus(img.id, dataset1.id) == "deleted"
    # проверяем, что связь с dataset2 создана
    images_in_ds2 = image_repo.get_images_by_dataset(dataset2.id)
    assert len(images_in_ds2) == 1
    assert images_in_ds2[0].id == img.id

def test_get_images_by_cluster(dataset_repo, image_repo, session_repo, cluster_repo):
    dataset = dataset_repo.create_dataset("GetByCluster", "/path", 1)
    session = session_repo.create_session("TestSession",
                                          {"algorythm": "DBSCAN",
                                           "eps": 0.5},
                                          dataset.id)
    cluster = cluster_repo.create_cluster("Cluster", session.id)
    embedding = np.zeros(1280, dtype=np.float32)
    img1 = image_repo.create_image("img1.jpg", "/p1", "jpg", dataset.id, embedding, None)
    img2 = image_repo.create_image("img2.jpg", "/p2", "jpg", dataset.id, embedding, None)
    cursor = dataset_repo.conn.cursor()
    cursor.executemany("INSERT INTO images_clusters (image_id, cluster_id, manual) VALUES (?, ?, 0)",
                       [(img1.id, cluster.id), (img2.id, cluster.id)])
    dataset_repo.conn.commit()
    images = image_repo.get_images_by_cluster(cluster.id, dataset.id)
    assert len(images) == 2
    ids = [img.id for img in images]
    assert img1.id in ids
    assert img2.id in ids

def test_get_images_by_anomalyGroup(dataset_repo, image_repo, session_repo, anomalyGroup_repo):
    dataset = dataset_repo.create_dataset("GetByAnomaly", "/path", 1)
    session = session_repo.create_session("TestSession",
                                          {"algorythm": "DBSCAN", "eps": 0.5},
                                          dataset.id)
    anomaly_group = anomalyGroup_repo.create_group("Anomalies", session.id)
    embedding = np.zeros(1280, dtype=np.float32)
    img1 = image_repo.create_image("img1.jpg", "/p1", "jpg", dataset.id, embedding, None)
    img2 = image_repo.create_image("img2.jpg", "/p2", "jpg", dataset.id, embedding, None)
    cursor = dataset_repo.conn.cursor()
    cursor.executemany("INSERT INTO images_anomalies (image_id, anomaliesGroup_id) VALUES (?, ?)", [(img1.id, anomaly_group.id), (img2.id, anomaly_group.id)])
    dataset_repo.conn.commit()
    images = image_repo.get_images_by_anomalyGroup(anomaly_group.id, dataset.id)
    assert len(images) == 2

def test_delete_noExist_images(dataset_repo, image_repo):
    dataset = dataset_repo.create_dataset("DeleteNoExist", "/path", 1)
    embedding = np.zeros(1280, dtype=np.float32)
    img1 = image_repo.create_image("keep.jpg", "/k", "jpg", dataset.id, embedding, None)
    img2 = image_repo.create_image("delete.jpg", "/d", "jpg", dataset.id, embedding, None)
    dataset2 = dataset_repo.create_dataset("Another", "/path", 1)
    #image_repo.add_existing_image(img1, dataset2.id)
    from repositories.dataset_repository import DatasetRepository
    ds_repo = DatasetRepository(dataset_repo.conn)
    ds_repo.add_existing_image(img1, dataset2.id)
    img2.status = "deleted"
    image_repo.update_status([img2], dataset.id)
    # Теперь передаём список ID на удаление
    to_delete = [img1.id, img2.id]
    image_repo.delete_noExist_images(to_delete)
    # img2 должен быть удалён
    assert image_repo.get_image_by_id(img2.id) is None
    # img1 не должен быть удалён (так как есть в dataset2)
    assert image_repo.get_image_by_id(img1.id) is not None

def test_get_images_by_classification_session(dataset_repo, image_repo, classifSession_repo, modelVersion_repo):
    dataset = dataset_repo.create_dataset("ClassifImages", "/path", 1)
    embedding = np.zeros(1280, dtype=np.float32)
    img = image_repo.create_image("img.jpg", "/p", "jpg", dataset.id, embedding, None)
    # создаём сессию классификации
    model_version = modelVersion_repo.save_new_version("path", ["label"], "newVersion")
    session = classifSession_repo.create_session("TestClassif", model_version_id=model_version.id, dataset_id=dataset.id, images_labels=[], images=[])
    # создаём запись в classification_results для этого изображения
    cursor = dataset_repo.conn.cursor()
    # сначала нужно получить image_in_dataset_id
    cursor.execute("SELECT id FROM images_datasets WHERE image_id = ? AND dataset_id = ?", (img.id, dataset.id))
    imd_id = cursor.fetchone()[0]
    cursor.execute("INSERT INTO classification_results (classification_session_id, image_in_dataset_id, label, confidence, is_manual) VALUES (?, ?, 'Ear', 0.9, 0)", (session.id, imd_id))
    dataset_repo.conn.commit()
    # метод get_images_by_classification_session возвращает список словарей
    res = image_repo.get_images_by_classification_session(session.id)
    assert len(res) == 1
    assert res[0]['image_id'] == img.id
    assert res[0]['label'] == 'Ear'
    assert res[0]['confidence'] == 0.9



