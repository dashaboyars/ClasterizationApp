import numpy as np


def test_get_embedding(embedding_calculator):
    file_path = r"C:\Users\ADMIN\Desktop\Тестовый датасет ЛОР\0459f78e9185487f9d384d5542b2ca19.jpg"
    embedding = embedding_calculator.get_embedding(file_path)

    assert embedding is not None
    assert isinstance(embedding, np.ndarray)
    assert embedding.dtype == np.float32
    assert embedding.shape == (1280,)
    assert not np.all(embedding == 0)

def test_get_embedding_pathNotExists(embedding_calculator):
    embedding = embedding_calculator.get_embedding("not_exists")
    assert embedding is None

def test_get_embedding_batch(embedding_calculator):
    file_path1 = r"C:\Users\ADMIN\Desktop\Тестовый датасет ЛОР\0459f78e9185487f9d384d5542b2ca19.jpg"
    file_path2 = r"C:\Users\ADMIN\Desktop\Тестовый датасет ЛОР\0037dc8a133e4f4da3e7d595ffee02bd.png"
    embeddings = embedding_calculator.get_embedding_batch([file_path1, file_path2])

    assert embeddings[0] is not None
    assert isinstance(embeddings[0], np.ndarray)
    assert embeddings[0].dtype == np.float32
    assert embeddings[0].shape == (1280,)
    assert not np.all(embeddings[0] == 0)

    assert embeddings[1] is not None
    assert isinstance(embeddings[1], np.ndarray)
    assert embeddings[1].dtype == np.float32
    assert embeddings[1].shape == (1280,)
    assert not np.all(embeddings[1] == 0)

def test_get_embedding_batch_onePathNotExists(embedding_calculator):
    file_path1 = r"C:\Users\ADMIN\Desktop\Тестовый датасет ЛОР\0459f78e9185487f9d384d5542b2ca19.jpg"
    file_path2 = r"no_exists"
    embeddings = embedding_calculator.get_embedding_batch([file_path1, file_path2])

    assert embeddings[0] is not None
    assert isinstance(embeddings[0], np.ndarray)
    assert embeddings[0].dtype == np.float32
    assert embeddings[0].shape == (1280,)
    assert not np.all(embeddings[0] == 0)

    assert embeddings[1] is not None
    assert embeddings[1].shape == (1280,)
    assert embeddings[1].dtype == np.float32


