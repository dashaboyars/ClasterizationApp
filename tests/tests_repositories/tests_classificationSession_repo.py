import numpy as np


def test_create_session(dataset_repo, classifSession_repo, modelVersion_repo):
    dataset = dataset_repo.create_dataset("ChangeCluster", "/path", 1)
    model = modelVersion_repo.save_new_version("path1", ["label1", "label2"], "test_model")
    classif_session = classifSession_repo.create_session("ClassifSession", model.id, dataset.id)
    assert classif_session is not None
    assert classif_session.name == "ClassifSession"
    assert classif_session.model_id == model.id
    assert classif_session.dataset_id == dataset.id

def test_get_sessions_by_dataset(dataset_repo, classifSession_repo, modelVersion_repo):
    dataset = dataset_repo.create_dataset("Dataset1", "/path", 1)
    dataset2 = dataset_repo.create_dataset("Dataset2", "/path", 1)
    model = modelVersion_repo.save_new_version("path1", ["label1", "label2"], "test_model")
    first_classif_session = classifSession_repo.create_session("ClassifSession", model.id, dataset.id)
    second_classif_session = classifSession_repo.create_session("ClassifSession2", model.id, dataset.id)
    third_classif_session = classifSession_repo.create_session("ClassifSession3", model.id, dataset2.id)

    sessions = classifSession_repo.get_sessions_by_datasetId(dataset.id)
    assert len(sessions) == 2
    assert sessions[0].id == first_classif_session.id
    assert sessions[1].id == second_classif_session.id

def test_get_session_by_name(dataset_repo, classifSession_repo, modelVersion_repo):
    dataset = dataset_repo.create_dataset("Dataset1", "/path", 1)
    model = modelVersion_repo.save_new_version("path1", ["label1", "label2"], "test_model")
    classif_session = classifSession_repo.create_session("ClassifSession", model.id, dataset.id)

    found_session = classifSession_repo.get_session_by_name("ClassifSession", dataset.id)
    assert found_session is not None
    assert found_session.id == classif_session.id

def test_delete_session(dataset_repo, classifSession_repo, modelVersion_repo):
    dataset = dataset_repo.create_dataset("Dataset1", "/path", 1)
    model = modelVersion_repo.save_new_version("path1", ["label1", "label2"], "test_model")
    classif_session = classifSession_repo.create_session("ClassifSession", model.id, dataset.id)
    classifSession_repo.delete_session([classif_session.id])

    found_sessions = classifSession_repo.get_sessions_by_datasetId(dataset.id)

    assert found_sessions is None

def test_rename_session(dataset_repo, classifSession_repo, modelVersion_repo):
    dataset = dataset_repo.create_dataset("Dataset1", "/path", 1)
    model = modelVersion_repo.save_new_version("path1", ["label1", "label2"], "test_model")
    classif_session = classifSession_repo.create_session("ClassifSession", model.id, dataset.id)
    classifSession_repo.rename_session("NewName", classif_session.id)

    found_session = classifSession_repo.get_session_by_name("NewName", dataset.id)

    assert found_session is not None
    assert found_session.id == classif_session.id
    assert found_session.name == "NewName"

def test_add_labeled_images(classifSession_repo, modelVersion_repo, dataset_repo, image_repo):
    dataset = dataset_repo.create_dataset("Dataset1", "/path", 1)
    model = modelVersion_repo.save_new_version("path1", ["label1", "label2"], "test_model")
    classif_session = classifSession_repo.create_session("ClassifSession", model.id, dataset.id)
    embedding = np.zeros(1280, dtype=np.float32)
    img1 = image_repo.create_image("img1.jpg", "/path", "jpg", dataset.id, embedding, None)
    img2 = image_repo.create_image("img2.jpg", "/path", "jpg", dataset.id, embedding, None)
    images_labels = [["label1", 0.9], ["label2", 0.91]]
    classifSession_repo.add_labeled_images([img1, img2], classif_session.id, images_labels, dataset.id)
    res = image_repo.get_images_by_classification_session(classif_session.id)
    assert len(res) == 2
    assert res[0]['image_id'] == img1.id
    assert res[0]['label'] == 'label1'
    assert res[0]['confidence'] == 0.9
    assert res[1]['image_id'] == img2.id
    assert res[1]['label'] == 'label2'
    assert res[1]['confidence'] == 0.91

def test_change_image_label(image_repo, dataset_repo, classifSession_repo, modelVersion_repo):
    dataset = dataset_repo.create_dataset("Dataset1", "/path", 1)
    model = modelVersion_repo.save_new_version("path1", ["label1", "label2"], "test_model")
    classif_session = classifSession_repo.create_session("ClassifSession", model.id, dataset.id)
    embedding = np.zeros(1280, dtype=np.float32)
    img1 = image_repo.create_image("img1.jpg", "/path", "jpg", dataset.id, embedding, None)
    images_labels = [["label1", 0.9]]
    classifSession_repo.add_labeled_images([img1], classif_session.id, images_labels, dataset.id)

    classifSession_repo.change_image_label(dataset.id, classif_session.id, img1.id, "changed")
    res = image_repo.get_images_by_classification_session(classif_session.id)
    assert len(res) == 1
    assert res[0]['image_id'] == img1.id
    assert res[0]['label'] == 'changed'
    assert res[0]['confidence'] == 0.0