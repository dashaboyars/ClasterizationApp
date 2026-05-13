import numpy as np


def test_create_group(dataset_repo, session_repo, anomalyGroup_repo):
    dataset = dataset_repo.create_dataset("Dataset1", "/path", 1)
    session = session_repo.create_session("TestSession",
                                          {"algorythm": "DBSCAN", "eps": 0.5},
                                          dataset.id)
    anomalyGroup = anomalyGroup_repo.create_group("Anomalies", session.id)
    assert anomalyGroup is not None
    assert anomalyGroup.name == "Anomalies"
    assert anomalyGroup.session_id == session.id

def test_get_group_by_name(dataset_repo, session_repo, anomalyGroup_repo):
    dataset = dataset_repo.create_dataset("Dataset1", "/path", 1)
    session = session_repo.create_session("TestSession",
                                          {"algorythm": "DBSCAN", "eps": 0.5},
                                          dataset.id)
    anomalyGroup_repo.create_group("Anomalies", session.id)
    found_group = anomalyGroup_repo.get_group_by_name("Anomalies", session.id)

    assert found_group is not None
    assert found_group.session_id == session.id

def test_add_image_to_group(dataset_repo, session_repo, anomalyGroup_repo, image_repo):
    dataset = dataset_repo.create_dataset("Dataset1", "/path", 1)
    session = session_repo.create_session("TestSession",
                                          {"algorythm": "DBSCAN", "eps": 0.5},
                                          dataset.id)
    anomalyGroup = anomalyGroup_repo.create_group("Anomalies", session.id)
    embedding = np.zeros(1280, dtype=np.float32)
    img = image_repo.create_image("old.jpg", "/path", "jpg", dataset.id, embedding, None)
    anomalyGroup_repo.add_image_to_group(img.id, anomalyGroup.id)
    images = image_repo.get_images_by_anomalyGroup(anomalyGroup.id, dataset.id)

    assert images is not None
    assert len(images) == 1
    assert images[0].id == img.id

def test_get_anomalyGroup_by_session(dataset_repo, session_repo, anomalyGroup_repo, image_repo):
    dataset = dataset_repo.create_dataset("Dataset1", "/path", 1)
    session = session_repo.create_session("TestSession",
                                          {"algorythm": "DBSCAN", "eps": 0.5},
                                          dataset.id)
    anomalyGroup = anomalyGroup_repo.create_group("Anomalies", session.id)
    found_group = anomalyGroup_repo.get_anomalyGroup_by_session(session.id)

    assert found_group is not None
    assert found_group.id == anomalyGroup.id