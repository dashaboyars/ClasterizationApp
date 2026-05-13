from unittest.mock import patch, MagicMock

import numpy as np

from tests.conftest import create_embeddings


def test_clusterize_kmeans_basic(cluster_service, mock_dataset, mock_image):
    # Создаём датасет с 10 изображениями
    embeddings = create_embeddings(10, 5)
    images = [mock_image(i, embeddings[i]) for i in range(10)]
    dataset = mock_dataset(images)
    params = {
        'k': 3,
        'max_iterations': 300,
        'tol': 1e-4,
        'similarity_method': "Евклидово расстояние (Euclidean)",
        'initialization_method': "K-Means++"
    }
    session_name = "TestKMeans"
    with patch.object(cluster_service, 'SaveResults', return_value=MagicMock()) as mock_save:
        result = cluster_service.clusterize_KMeans(session_name, dataset, params,
                                                   progress_callback=None, cancel_check=None)
        assert result is not None
        mock_save.assert_called_once()
        args, kwargs = mock_save.call_args
        conn, passed_params, passed_name, passed_dataset, labels, cb = args
        assert passed_name == session_name
        assert passed_dataset is dataset
        assert len(labels) == 10


def test_clusterize_kmeans_cosine(cluster_service, mock_dataset, mock_image):
    embeddings = create_embeddings(10, 5)
    images = [mock_image(i, embeddings[i]) for i in range(10)]
    dataset = mock_dataset(images)
    params = {
        'k': 3,
        'max_iterations': 300,
        'tol': 1e-4,
        'similarity_method': "Косинусное расстояние (Cosine Similarity)",
        'initialization_method': "K-Means++"
    }
    with patch.object(cluster_service, 'SaveResults') as mock_save:
        cluster_service.clusterize_KMeans("TestCosine", dataset, params)
        mock_save.assert_called_once()


def test_clusterize_kmeans_manhattan(cluster_service, mock_dataset, mock_image):
    embeddings = create_embeddings(10, 5)
    images = [mock_image(i, embeddings[i]) for i in range(10)]
    dataset = mock_dataset(images)
    params = {
        'k': 3,
        'max_iterations': 300,
        'tol': 1e-4,
        'similarity_method': "Манхэттенское расстояние (Manhattan/L1)",
        'initialization_method': "K-Means++"
    }
    with patch('kmars.KMeans') as mock_kmars:
        mock_kmars.return_value.fit.return_value.labels_ = np.array([0, 0, 1, 1, 2, 2, 0, 1, 2, 0])
        with patch.object(cluster_service, 'SaveResults') as mock_save:
            cluster_service.clusterize_KMeans("TestManhattan", dataset, params)
            mock_kmars.assert_called_once()
            mock_save.assert_called_once()


def test_clusterize_kmeans_cancel(cluster_service, mock_dataset, mock_image):
    embeddings = create_embeddings(10, 5)
    images = [mock_image(i, embeddings[i]) for i in range(10)]
    dataset = mock_dataset(images)
    params = {
        'k': 3,
        'max_iterations': 300,
        'tol': 1e-4,
        'similarity_method': "Евклидово расстояние (Euclidean)",
        'initialization_method': "K-Means++"
    }
    cancel_check = lambda: True  # отмена при первой же проверке
    result = cluster_service.clusterize_KMeans("TestCancel", dataset, params,
                                               progress_callback=None, cancel_check=cancel_check)
    assert result is None


# ---------- Тесты для DBSCAN ----------
def test_clusterize_dbscan_basic(cluster_service, mock_dataset, mock_image):
    embeddings = create_embeddings(20, 5)
    images = [mock_image(i, embeddings[i]) for i in range(20)]
    dataset = mock_dataset(images)
    params = {
        'eps': 0.5,
        'min_samples': 3,
        'similarity_method': "Евклидово расстояние (Euclidean)"
    }
    session_name = "TestDBSCAN"
    with patch.object(cluster_service, 'SaveResults_DBSCAN', return_value=MagicMock()) as mock_save:
        result = cluster_service.clusterize_DBSCAN(session_name, dataset, params,
                                                   progress_callback=None, cancel_check=None)
        assert result is not None
        mock_save.assert_called_once()

def test_clusterize_dbscan_manhattan(cluster_service, mock_dataset, mock_image):
    embeddings = create_embeddings(20, 5)
    images = [mock_image(i, embeddings[i]) for i in range(20)]
    dataset = mock_dataset(images)
    params = {
        'eps': 0.5,
        'min_samples': 3,
        'similarity_method': "Манхэттенское расстояние (Manhattan/L1)"
    }
    session_name = "TestDBSCAN"
    with patch.object(cluster_service, 'SaveResults_DBSCAN', return_value=MagicMock()) as mock_save:
        result = cluster_service.clusterize_DBSCAN(session_name, dataset, params,
                                                   progress_callback=None, cancel_check=None)
        assert result is not None
        mock_save.assert_called_once()

def test_clusterize_dbscan_chebyshev(cluster_service, mock_dataset, mock_image):
    embeddings = create_embeddings(20, 5)
    images = [mock_image(i, embeddings[i]) for i in range(20)]
    dataset = mock_dataset(images)
    params = {
        'eps': 0.5,
        'min_samples': 3,
        'similarity_method': "Чебышева расстояние (Chebyshev)"
    }
    session_name = "TestDBSCAN"
    with patch.object(cluster_service, 'SaveResults_DBSCAN', return_value=MagicMock()) as mock_save:
        result = cluster_service.clusterize_DBSCAN(session_name, dataset, params,
                                                   progress_callback=None, cancel_check=None)
        assert result is not None
        mock_save.assert_called_once()

def test_clusterize_dbscan_cosine(cluster_service, mock_dataset, mock_image):
    embeddings = create_embeddings(20, 5)
    images = [mock_image(i, embeddings[i]) for i in range(20)]
    dataset = mock_dataset(images)
    params = {
        'eps': 0.5,
        'min_samples': 3,
        'similarity_method': "Косинусное расстояние (Cosine Similarity)"
    }
    with patch.object(cluster_service, 'SaveResults_DBSCAN') as mock_save:
        cluster_service.clusterize_DBSCAN("TestDBSCANCosine", dataset, params)
        mock_save.assert_called_once()


def test_clusterize_dbscan_cancel(cluster_service, mock_dataset, mock_image):
    embeddings = create_embeddings(20, 5)
    images = [mock_image(i, embeddings[i]) for i in range(20)]
    dataset = mock_dataset(images)
    params = {
        'eps': 0.5,
        'min_samples': 3,
        'similarity_method': "Евклидово расстояние (Euclidean)"
    }
    cancel_check = lambda: True
    result = cluster_service.clusterize_DBSCAN("TestCancel", dataset, params,
                                               progress_callback=None, cancel_check=cancel_check)
    assert result is None


# ---------- Тесты для методов инициализации ----------
def test_random_init(cluster_service):
    embeddings = create_embeddings(50, 10)
    k = 5
    centroids = cluster_service.random_init(embeddings, k)
    assert centroids.shape == (k, 10)
    # Проверяем, что все центроиды являются разными точками из набора
    for i in range(k):
        assert any(np.array_equal(centroids[i], embeddings[j]) for j in range(len(embeddings)))


def test_furthest_points_init(cluster_service):
    embeddings = create_embeddings(30, 5)
    k = 4
    centroids = cluster_service.furthest_points_init(embeddings, k)
    assert centroids.shape == (k, 5)
    # Проверка на то, что индексы уникальны (простая)
    indices = [np.where((embeddings == c).all(axis=1))[0][0] for c in centroids]
    assert len(set(indices)) == k


def test_first_kPoints_init(cluster_service):
    embeddings = create_embeddings(10, 3)
    k = 5
    centroids = cluster_service.first_kPoints_init(embeddings, k)
    assert centroids.shape == (k, 3)
    # Должны совпадать с первыми k точками
    np.testing.assert_array_equal(centroids, embeddings[:k])


# ---------- Тесты для get_initMethod ----------
def test_get_initMethod_kmeanspp(cluster_service):
    embeddings = create_embeddings(10, 2)
    # Для евклидовой метрики
    result = cluster_service.get_initMethod("K-Means++", "Евклидово расстояние (Euclidean)", embeddings, 3)
    assert result == 'k-means++'
    # Для манхэттенской
    result_man = cluster_service.get_initMethod("K-Means++", "Манхэттенское расстояние (Manhattan/L1)", embeddings, 3)
    assert result_man == "kmeans++"


def test_get_initMethod_random(cluster_service):
    with patch.object(cluster_service, 'random_init', return_value=MagicMock()) as mock_rand:
        cluster_service.get_initMethod("Случайный выбор", "Манхэттенское расстояние (Manhattan/L1)", None, 3)
        mock_rand.assert_called_once()
    result = cluster_service.get_initMethod("Случайный выбор", "Евклидово расстояние (Euclidean)", None, 3)
    assert result == 'random'


def test_get_initMethod_furthest(cluster_service):
    with patch.object(cluster_service, 'furthest_points_init', return_value=MagicMock()) as mock_fur:
        cluster_service.get_initMethod("Furthest (самые удаленные точки)", "any", None, 3)
        mock_fur.assert_called_once()


def test_get_initMethod_firstK(cluster_service):
    with patch.object(cluster_service, 'first_kPoints_init', return_value=MagicMock()) as mock_first:
        cluster_service.get_initMethod("First K (первые k точек)", "any", None, 3)
        mock_first.assert_called_once()

def test_save_results_kmeans(cluster_service, temp_db, mock_dataset, mock_image):
    conn = temp_db.connect()
    # Создаём датасет через репозиторий
    from repositories.dataset_repository import DatasetRepository
    ds_repo = DatasetRepository(conn)
    dataset = ds_repo.create_dataset("TestSave", "/path", 1)
    # Создаём изображения и сохраняем их (через ImageRepository)
    from repositories.image_repository import ImageRepository
    img_repo = ImageRepository(conn)
    embeddings = create_embeddings(5, 10)
    images = []
    for i, emb in enumerate(embeddings):
        img = img_repo.create_image(f"img_{i}.jpg", f"/path/img_{i}.jpg", "jpg", dataset.id, emb, None)
        images.append(img)
    dataset.images_list = images
    # Параметры
    params = {'algorythm': "K-Means",
              'k': 2}
    labels = np.array([0, 0, 0, 1, 1])
    # Вызываем SaveResults
    new_session = cluster_service.SaveResults(conn, params, "TestSession", dataset, labels, None)
    assert new_session is not None
    assert len(new_session.clusters_list) == 2
    # Проверяем, что кластеры имеют правильное количество изображений
    sizes = [len(c.images_list) for c in new_session.clusters_list]
    assert sum(sizes) == 5
    # Закрываем соединение
    conn.close()


def test_save_results_dbscan(cluster_service, temp_db, mock_dataset, mock_image):
    # Аналогично, но для DBSCAN с группой аномалий.
    conn = temp_db.connect()
    from repositories.dataset_repository import DatasetRepository
    ds_repo = DatasetRepository(conn)
    dataset = ds_repo.create_dataset("TestDBSCAN", "/path", 1)
    from repositories.image_repository import ImageRepository
    img_repo = ImageRepository(conn)
    embeddings = create_embeddings(6, 10)
    images = []
    for i, emb in enumerate(embeddings):
        img = img_repo.create_image(f"img_{i}.jpg", f"/path/img_{i}.jpg", "jpg", dataset.id, emb, None)
        images.append(img)
    dataset.images_list = images
    # Метки DBSCAN: -1 для шума, 0,1 для кластеров
    labels = np.array([-1, 0, 0, 1, 1, -1])
    params = {'algorythm': "DBSCAN",'eps': 0.5, 'min_samples': 2}
    new_session = cluster_service.SaveResults_DBSCAN(conn, params, "TestDBSCAN", dataset, labels, None)
    assert new_session is not None
    # Кластеров должно быть два (0 и 1)
    clusters = [c for c in new_session.clusters_list if c is not None]
    assert len(clusters) == 2
    # Группа аномалий не None
    assert new_session.anomaly_group is not None
    # Проверяем количество изображений в аномалиях
    assert len(new_session.anomaly_group.images_list) == 2  # два -1
    conn.close()


# ---------- Тесты для get_optimal_k ----------
def test_get_optimal_k(cluster_service, mock_image):
    np.random.seed(42)
    c1 = np.random.randn(30, 2) + [0, 0]
    c2 = np.random.randn(30, 2) + [5, 5]
    c3 = np.random.randn(30, 2) + [10, 0]
    embeddings = np.vstack([c1, c2, c3])
    images = [mock_image(i, embeddings[i]) for i in range(len(embeddings))]
    opt_k = cluster_service.get_optimal_k(images)
    # Допустим, что метод должен возвращать значение от 2 до 20 и не None
    assert opt_k is not None
    assert 2 <= opt_k <= 20


def test_get_optimal_k_cancel(cluster_service, mock_image):
    embeddings = create_embeddings(10, 2)
    images = [mock_image(i, embeddings[i]) for i in range(10)]
    cancel_check = lambda: True
    result = cluster_service.get_optimal_k(images, cancel_check=cancel_check)
    assert result is None


def test_get_optimal_k_progress_callback(cluster_service, mock_image):
    embeddings = create_embeddings(10, 2)
    images = [mock_image(i, embeddings[i]) for i in range(10)]
    calls = []

    def progress(percent, status):
        calls.append((percent, status))

    with patch('sklearn.cluster.KMeans') as mock_kmeans:
        mock_kmeans.return_value.inertia_ = 100
        cluster_service.get_optimal_k(images, progress_callback=progress)
        assert len(calls) > 0


# ---------- Тесты для get_optimal_minSamples_Esp и get_optimal_eps ----------
def test_get_optimal_eps(cluster_service, mock_image):
    # Создаём данные, где k-distance график имеет перегиб
    np.random.seed(42)
    embeddings = np.random.randn(200, 10)
    images = [mock_image(i, embeddings[i]) for i in range(200)]
    min_samples = 10
    metric = 'euclidean'
    eps = cluster_service.get_optimal_eps(embeddings, min_samples, None, None, metric)
    assert isinstance(eps, float)
    assert 0 < eps < 10

def test_get_optimal_eps_cosine(cluster_service, mock_image):
    # Создаём данные, где k-distance график имеет перегиб
    np.random.seed(42)
    embeddings = np.random.randn(200, 10)
    images = [mock_image(i, embeddings[i]) for i in range(200)]
    min_samples = 10
    metric = 'cosine'
    eps = cluster_service.get_optimal_eps(embeddings, min_samples, None, None, metric)
    assert isinstance(eps, float)
    assert 0 < eps < 10

def test_get_optimal_eps_cancel(cluster_service, mock_image):
    embeddings = create_embeddings(50, 3)
    cancel_check = lambda: True
    eps = cluster_service.get_optimal_eps(embeddings, 5, None, cancel_check, 'euclidean')
    assert eps is None


def test_get_optimal_minSamples_estimation(cluster_service, mock_image):
    # Мокаем get_medium_noiseLevel
    from services.qualityAnalyse_service import QualityAnalyseService
    with patch.object(QualityAnalyseService, 'get_medium_noiseLevel', return_value=0.07):
        embeddings = create_embeddings(200, 10)
        images = [mock_image(i, embeddings[i]) for i in range(200)]
        min_sample = cluster_service.get_optimal_minSamples(images, None, None)
        assert min_sample == 6


def test_get_optimal_minSamples_Esp(cluster_service, mock_image):
    embeddings = create_embeddings(100, 5)
    images = [mock_image(i, embeddings[i]) for i in range(100)]
    # Замокаем get_optimal_minSamples и get_optimal_eps
    with patch.object(cluster_service, 'get_optimal_minSamples', return_value=5) as mock_min:
        with patch.object(cluster_service, 'get_optimal_eps', return_value=0.3) as mock_eps:
            result = cluster_service.get_optimal_minSamples_Esp(images, 'euclidean', None, None)
            assert result == [5, 0.3]
            mock_min.assert_called_once()
            mock_eps.assert_called_once()


# ---------- Тесты для прогресса и отмены в DBSCAN / K‑Means ----------
def test_progress_callback_called(cluster_service, mock_dataset, mock_image):
    embeddings = create_embeddings(10, 5)
    images = [mock_image(i, embeddings[i]) for i in range(10)]
    dataset = mock_dataset(images)
    params = {'k': 2, 'max_iterations': 300, 'tol': 1e-4,
              'similarity_method': "Евклидово расстояние (Euclidean)",
              'initialization_method': "K-Means++"}
    progress_calls = []

    def progress(percent, status):
        progress_calls.append((percent, status))

    with patch.object(cluster_service, 'SaveResults'):
        cluster_service.clusterize_KMeans("TestProgress", dataset, params, progress_callback=progress)
        assert len(progress_calls) > 0
        assert progress_calls[0][0] == 5
        assert progress_calls[-1][0] == 100