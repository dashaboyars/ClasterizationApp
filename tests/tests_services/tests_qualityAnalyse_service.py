import os
import tempfile
from unittest.mock import MagicMock, patch

import cv2
import numpy as np
import pytest

from models.cluster import Cluster
from PIL import Image as PILImage
from models.image import Image
from models.session import Session

@pytest.fixture
def sample_embedding():
    return np.random.randn(128).astype(np.float32)

@pytest.fixture
def mock_image(sample_embedding):
    img = MagicMock(spec=Image)
    img.id = 1
    img.filename = "test.jpg"
    img.embedding = sample_embedding
    img.quality_params = {
        'file_size': 150.0,
        'resolution_width': 1920,
        'resolution_height': 1080,
        'colors_amount': 16777216,
        'sharpness': 500.0,
        'noise_level': 0.05,
        'contrast': 0.7
    }
    img.status = "uploaded"
    return img

@pytest.fixture
def mock_cluster(mock_image):
    cluster = MagicMock(spec=Cluster)
    cluster.id = 1
    cluster.name = "Cluster1"
    cluster.images_list = [mock_image, mock_image]  # два одинаковых для простоты
    return cluster

@pytest.fixture
def mock_session(mock_cluster):
    session = MagicMock(spec=Session)
    session.id = 1
    session.name = "TestSession"
    session.clusters_list = [mock_cluster]
    return session

def test_get_session_qualityParams_with_one_cluster(quality_service, mock_session):
    mock_session.clusters_list = []  # нет кластеров
    result = quality_service.get_session_qualityParams(mock_session)
    assert result == {"silhouette": None, "chi": None, "dbi": None}

def test_get_session_qualityParams_normal(quality_service, mock_session):
    # Подготавливаем данные: создадим два кластера с разными эмбеддингами
    emb1 = np.random.randn(10, 50)
    emb2 = np.random.randn(10, 50) + 5
    cluster1 = MagicMock()
    cluster1.id = 1
    cluster1.images_list = [MagicMock(embedding=e) for e in emb1]
    cluster2 = MagicMock()
    cluster2.id = 2
    cluster2.images_list = [MagicMock(embedding=e) for e in emb2]
    mock_session.clusters_list = [cluster1, cluster2]
    # Мокаем внутренние методы, чтобы не вычислять реальные метрики (они будут вызваны)
    with patch.object(quality_service, 'get_session_silhouette', return_value=0.5):
        with patch.object(quality_service, 'get_chi_index', return_value=100.0):
            with patch.object(quality_service, 'get_dbi_index', return_value=0.8):
                res = quality_service.get_session_qualityParams(mock_session)
                assert res['silhouette'] == 0.5
                assert res['chi'] == 100.0
                assert res['dbi'] == 0.8

def test_get_dbi_index_one_cluster(quality_service, mock_session):
    mock_session.clusters_list = [MagicMock()]
    result = quality_service.get_dbi_index(mock_session)
    assert result is None

def test_get_dbi_index_normal(quality_service, mock_session):
    # Создадим два кластера с разными эмбеддингами
    emb1 = np.random.randn(5, 10)
    emb2 = np.random.randn(5, 10) + 2
    cluster1 = MagicMock()
    cluster1.id = 1
    cluster1.images_list = [MagicMock(embedding=e) for e in emb1]
    cluster2 = MagicMock()
    cluster2.id = 2
    cluster2.images_list = [MagicMock(embedding=e) for e in emb2]
    mock_session.clusters_list = [cluster1, cluster2]
    dbi = quality_service.get_dbi_index(mock_session)
    assert isinstance(dbi, float)
    assert dbi >= 0

def test_get_chi_index_one_cluster(quality_service, mock_session):
    mock_session.clusters_list = [MagicMock()]
    result = quality_service.get_chi_index(mock_session)
    assert result is None

def test_get_chi_index_normal(quality_service, mock_session):
    emb1 = np.random.randn(5, 5)  # 5 точек, размерность 5
    emb2 = np.random.randn(5, 5) + 3
    cluster1 = MagicMock()
    cluster1.id = 1
    cluster1.images_list = [MagicMock(embedding=e) for e in emb1]
    cluster2 = MagicMock()
    cluster2.id = 2
    cluster2.images_list = [MagicMock(embedding=e) for e in emb2]
    mock_session = MagicMock()
    mock_session.clusters_list = [cluster1, cluster2]
    chi = quality_service.get_chi_index(mock_session)
    assert isinstance(chi, float)
    assert chi > 0

def test_get_session_silhouette_one_cluster(quality_service, mock_session):
    mock_session.clusters_list = [MagicMock()]
    assert quality_service.get_session_silhouette(mock_session) is None

def test_get_session_silhouette_normal(quality_service, mock_session):
    with patch.object(quality_service, 'count_point_silhouettes', return_value=(np.array([0.2, 0.3, 0.4]), None)):
        result = quality_service.get_session_silhouette(mock_session)
        assert result == pytest.approx(0.3)

def test_get_claster_qualityParams(quality_service, mock_cluster, mock_session):
    with patch.object(quality_service, 'count_cluster_silhouette', return_value=0.6):
        with patch.object(quality_service, 'count_cluster_cohesion', return_value=1.2):
            with patch.object(quality_service, 'count_cluster_separation', return_value=2.5):
                with patch.object(quality_service, 'count_cluster_density', return_value=0.8):
                    with patch.object(quality_service, 'get_cluster_radius', return_value=3.0):
                        res = quality_service.get_claster_qualityParams(mock_cluster, mock_session)
                        assert res['size'] == len(mock_cluster.images_list)
                        assert res['silhouette'] == 0.6
                        assert res['cohesion'] == 1.2
                        assert res['separation'] == 2.5
                        assert res['density'] == 0.8
                        assert res['radius'] == 3.0

def test_count_cluster_silhouette(quality_service, mock_cluster, mock_session):
    # Мокаем count_point_silhouettes
    sil_values = np.array([0.1, 0.2, 0.3, 0.4])
    labels = [1, 1, 2, 2]  # два кластера, первый кластер (id=1) имеет индексы 0,1
    mock_cluster.id = 1
    with patch.object(quality_service, 'count_point_silhouettes', return_value=(sil_values, labels)):
        result = quality_service.count_cluster_silhouette(mock_cluster, mock_session)
        expected = np.mean([0.1, 0.2])
        assert result == expected

def test_count_cluster_cohesion(quality_service, mock_cluster):
    emb = np.array([[0, 0], [1, 1], [2, 2]])
    mock_cluster.images_list = [MagicMock(embedding=e) for e in emb]
    expected_cohesion = np.mean([np.linalg.norm(e - np.mean(emb, axis=0)) for e in emb])
    result = quality_service.count_cluster_cohesion(mock_cluster)
    assert result == pytest.approx(expected_cohesion)

def test_count_cluster_separation(quality_service, mock_session):
    class DummyImage:
        def __init__(self, emb):
            self.embedding = emb

    class DummyCluster:
        def __init__(self, cid, centroid):
            self.id = cid
            self.images_list = [DummyImage(centroid)]

    cluster1 = DummyCluster(1, np.array([0.0, 0.0]))
    cluster2 = DummyCluster(2, np.array([5.0, 5.0]))
    mock_session.clusters_list = [cluster1, cluster2]

    separation = quality_service.count_cluster_separation(cluster1, mock_session)
    expected = np.linalg.norm(np.array([5.0, 5.0]) - np.array([0.0, 0.0]))
    assert separation == pytest.approx(expected, rel=1e-6)

def test_count_cluster_density(quality_service):
    result = quality_service.count_cluster_density(2.0)
    assert result == 1.0 / (2.0 + 1e-12)
    assert isinstance(result, float)

def test_get_cluster_radius(quality_service, mock_cluster):
    emb = np.array([[0, 0], [1, 1], [2, 2]])
    mock_cluster.images_list = [MagicMock(embedding=e) for e in emb]
    centroid = np.mean(emb, axis=0)
    expected_radius = np.max(np.linalg.norm(emb - centroid, axis=1))
    result = quality_service.get_cluster_radius(mock_cluster)
    assert result == expected_radius




def test_count_point_silhouettes_one_cluster(quality_service, mock_session):
    mock_session.clusters_list = [MagicMock()]
    result, labels = quality_service.count_point_silhouettes(mock_session)
    assert result is None
    assert labels is None

def test_count_point_silhouettes_normal(quality_service, mock_session):
    emb1 = np.random.randn(3, 5)
    emb2 = np.random.randn(3, 5) + 2
    cluster1 = MagicMock()
    cluster1.id = 1
    cluster1.images_list = [MagicMock(embedding=e) for e in emb1]
    cluster2 = MagicMock()
    cluster2.id = 2
    cluster2.images_list = [MagicMock(embedding=e) for e in emb2]
    mock_session.clusters_list = [cluster1, cluster2]
    # Просто вызываем, проверяем, что возвращаются не None
    sil_vals, labels = quality_service.count_point_silhouettes(mock_session)
    assert sil_vals is not None
    assert labels is not None
    assert len(sil_vals) == len(labels) == 6

@pytest.fixture
def temp_image():
    # Создаём временное изображение для тестов
    fd, path = tempfile.mkstemp(suffix='.jpg')
    os.close(fd)
    img = PILImage.new('RGB', (100, 100), color='red')
    img.save(path)
    yield path
    os.unlink(path)

@pytest.fixture
def quality_char_fixture(quality_service, temp_image):
    # Реальный вызов get_quality_char на временном изображении
    return quality_service.get_quality_char(temp_image)

def test_get_medium_noiseLevel(quality_service, mock_image):
    images = [mock_image, mock_image]
    # Установим разные noise_level
    mock_image.quality_params['noise_level'] = 0.1
    mock_image2 = MagicMock()
    mock_image2.quality_params = {'noise_level': 0.3}
    result = quality_service.get_medium_noiseLevel([mock_image, mock_image2])
    assert result == 0.2

def test_check_quality_all_good(quality_service, mock_image):
    # Все параметры в норме
    params = {
        'min_size': 100, 'max_size': 200,
        'min_resolution': 1000,
        'min_colors': 1000000,
        'min_sharpness': 100,
        'max_noise': 0.1,
        'min_contrast': 0.5
    }
    mock_image.quality_params['file_size'] = 150
    mock_image.quality_params['resolution_width'] = 1920
    mock_image.quality_params['resolution_height'] = 1080
    mock_image.quality_params['colors_amount'] = 16777216
    mock_image.quality_params['sharpness'] = 500
    mock_image.quality_params['noise_level'] = 0.05
    mock_image.quality_params['contrast'] = 0.7
    bad = quality_service.check_quality([mock_image], params)
    assert bad == {}
    assert mock_image.status == "quality_passed"

def test_check_quality_bad(quality_service, mock_image):
    params = {
        'min_size': 200, 'max_size': 1000,
        'min_resolution': 2000,
        'min_colors': 20000000,
        'min_sharpness': 1000,
        'max_noise': 0.02,
        'min_contrast': 0.9
    }
    mock_image.quality_params['file_size'] = 150
    mock_image.quality_params['resolution_width'] = 1920
    mock_image.quality_params['resolution_height'] = 1080
    mock_image.quality_params['colors_amount'] = 16777216
    mock_image.quality_params['sharpness'] = 500
    mock_image.quality_params['noise_level'] = 0.05
    mock_image.quality_params['contrast'] = 0.7
    bad = quality_service.check_quality([mock_image], params)
    assert len(bad) == 1
    assert mock_image.filename in bad
    assert isinstance(bad[mock_image.filename], list)
    assert mock_image.status == "quality_failed"

def test_get_quality_char_basic(quality_service, temp_image):
    # Проверяем, что метод возвращает словарь с нужными ключами и значениями
    result = quality_service.get_quality_char(temp_image)
    expected_keys = {'file_size', 'resolution_width', 'resolution_height', 'colors_amount', 'sharpness',
                     'noise_level', 'contrast'}
    assert set(result.keys()) == expected_keys
    assert isinstance(result['file_size'], float)
    assert result['resolution_width'] > 0
    assert result['resolution_height'] > 0
    assert result['colors_amount'] > 0
    assert result['sharpness'] >= 0
    assert result['noise_level'] >= 0
    assert 0 <= result['contrast'] <= 1  # контраст нормализован

@patch('os.path.getsize')
def test_get_fileSize(mock_getsize, quality_service):
    mock_getsize.return_value = 2048  # bytes
    result = quality_service.get_fileSize("dummy.jpg")
    assert result == 2.0  # KB

def test_get_resolution(quality_service, temp_image):
    pil_img = PILImage.open(temp_image)
    w, h = quality_service.get_resolution(pil_img)
    assert w == 100
    assert h == 100

def test_get_colors(quality_service, temp_image):
    pil_img = PILImage.open(temp_image)
    colors = quality_service.get_colors(pil_img)
    assert colors == 1  # красное изображение, всего один цвет

def test_get_sharpness(quality_service, temp_image):
    img_cv = cv2.imread(temp_image)
    sharpness = quality_service.get_sharpness(img_cv)
    assert isinstance(sharpness, float)
    assert sharpness >= 0

def test_get_noise(quality_service, temp_image):
    img_cv = cv2.imread(temp_image)
    noise = quality_service.get_noise(img_cv)
    assert isinstance(noise, float)
    assert not np.isnan(noise)
    assert noise >= 0

def test_get_contrast(quality_service, temp_image):
    img_cv = cv2.imread(temp_image)
    contrast = quality_service.get_contrast(img_cv)
    assert isinstance(contrast, float)
    assert 0 <= contrast <= 1

def test_quality_char_error_handling(quality_service):
    # Несуществующий путь
    with pytest.raises(FileNotFoundError):
        quality_service.get_quality_char("non_existent.jpg")