import tempfile

import pytest
import os
from unittest.mock import MagicMock, patch, call
from services.export_service import ExportService


@pytest.fixture
def mock_image():
    img = MagicMock()
    img.id = 1
    img.filename = "test.jpg"
    img.filepath = "/src/test.jpg"
    return img


@pytest.fixture
def mock_dataset(mock_image):
    dataset = MagicMock()
    dataset.name = "TestDataset"
    dataset.get_activeImages.return_value = [mock_image]
    dataset.sessions_list = []
    dataset.classification_groups = []
    return dataset


@pytest.fixture
def mock_cluster(mock_image):
    cluster = MagicMock()
    cluster.name = "Cluster1"
    cluster.images_list = [mock_image]
    return cluster

@pytest.fixture
def mock_anomalyGroup(mock_image):
    anomaly_group = MagicMock()
    anomaly_group.name = "Anomalies"
    anomaly_group.images_list = [mock_image]
    return anomaly_group


@pytest.fixture
def mock_session(mock_cluster):
    session = MagicMock()
    session.name = "Session1"
    session.clusters_list = [mock_cluster]
    session.anomaly_group = None
    return session

def test_safe_filename():
    assert ExportService.safe_filename("test:name?*") == "testname"
    assert ExportService.safe_filename("valid name.txt") == "valid name.txt"
    assert ExportService.safe_filename("") == ""

def test_export_dataset_basic(export_service, mock_dataset, tmp_path):
    import tempfile
    import os
    export_dir = tmp_path / "export"
    export_dir.mkdir()
    directory = str(export_dir)

    # Создаём реальный временный файл
    fd, fake_path = tempfile.mkstemp(suffix='.jpg')
    os.close(fd)
    with open(fake_path, 'wb') as f:
        f.write(b'fake image data')

    mock_image = mock_dataset.get_activeImages.return_value[0]
    mock_image.filepath = fake_path
    mock_image.id = 1
    mock_image.filename = "test.jpg"

    progress_cb = MagicMock()
    cancel_check = MagicMock(return_value=False)
    result = export_service.export_dataset(mock_dataset, directory, progress_cb, cancel_check)

    assert result[0] == "TestDataset"
    assert result[2] == 1  # должно скопироваться 1 изображение
    root = export_dir / "TestDataset"
    assert root.exists()
    images_dir = root / "images"
    assert images_dir.exists()
    assert len(list(images_dir.glob("*.jpg"))) == 1

    os.unlink(fake_path)

def test_export_dataset_with_session(export_service, mock_dataset, mock_session, tmp_path):
    import tempfile
    import os
    export_dir = tmp_path / "export"
    export_dir.mkdir()
    directory = str(export_dir)

    # Создаём реальный файл для изображения
    fd, fake_path = tempfile.mkstemp(suffix='.jpg')
    os.close(fd)
    with open(fake_path, 'wb') as f:
        f.write(b'fake image data')

    # Настраиваем мок изображения
    mock_image = mock_dataset.get_activeImages.return_value[0]
    mock_image.filepath = fake_path
    mock_image.id = 1
    mock_image.filename = "test.jpg"

    # Настраиваем мок кластера
    mock_cluster = mock_session.clusters_list[0]
    mock_cluster.images_list = [mock_image]
    mock_cluster.name = "Cluster1"

    mock_dataset.sessions_list = [mock_session]

    progress_cb = MagicMock()
    cancel_check = MagicMock(return_value=False)
    export_service.export_dataset(mock_dataset, directory, progress_cb, cancel_check)

    root = export_dir / "TestDataset"
    sessions_dir = root / "clasterization_sessions" / "Session1"
    cluster_dir = sessions_dir / "Cluster1"
    assert cluster_dir.exists()
    assert len(list(cluster_dir.glob("*.jpg"))) == 1

    # Удаляем временный файл
    os.unlink(fake_path)

def test_export_dataset_with_anomalyGroup(export_service, mock_dataset, mock_session, mock_anomalyGroup, tmp_path):
    import tempfile
    import os
    export_dir = tmp_path / "export"
    export_dir.mkdir()
    directory = str(export_dir)

    # Создаём реальный файл для изображения
    fd, fake_path = tempfile.mkstemp(suffix='.jpg')
    os.close(fd)
    with open(fake_path, 'wb') as f:
        f.write(b'fake image data')

    # Настраиваем мок изображения
    mock_image = mock_dataset.get_activeImages.return_value[0]
    mock_image.filepath = fake_path
    mock_image.id = 1
    mock_image.filename = "test.jpg"

    # Настраиваем мок кластера
    mock_cluster = mock_session.clusters_list[0]
    mock_cluster.images_list = [mock_image]
    mock_cluster.name = "Cluster1"

    #настраиваем мок группы аномалий
    mock_anomalyGroup.images_list = [mock_image]
    mock_anomalyGroup.name = "anomalies"
    mock_session.anomaly_group = mock_anomalyGroup

    mock_dataset.sessions_list = [mock_session]

    progress_cb = MagicMock()
    cancel_check = MagicMock(return_value=False)
    export_service.export_dataset(mock_dataset, directory, progress_cb, cancel_check)

    root = export_dir / "TestDataset"
    sessions_dir = root / "clasterization_sessions" / "Session1"
    cluster_dir = sessions_dir / "Cluster1"
    assert cluster_dir.exists()
    assert len(list(cluster_dir.glob("*.jpg"))) == 1

    # Удаляем временный файл
    os.unlink(fake_path)

def test_export_dataset_with_classification(export_service, mock_dataset, tmp_path):
    import os
    export_dir = tmp_path / "export"
    export_dir.mkdir()
    directory = str(export_dir)

    # Создаём реальный временный файл
    fd, fake_path = tempfile.mkstemp(suffix='.jpg')
    os.close(fd)
    with open(fake_path, 'wb') as f:
        f.write(b'fake image data')

    mock_image = mock_dataset.get_activeImages.return_value[0]
    mock_image.filepath = fake_path
    mock_image.id = 1
    mock_image.filename = "test.jpg"

    classif_session = MagicMock()
    classif_session.name = "ClassifSession"
    classif_session.images_labels = {"Ear": [(mock_image, 0.95)]}
    mock_dataset.classification_groups = [classif_session]

    progress_cb = MagicMock()
    cancel_check = MagicMock(return_value=False)
    export_service.export_dataset(mock_dataset, directory, progress_cb, cancel_check)

    root = export_dir / "TestDataset"
    classif_dir = root / "neural_model_classification_sessions" / "ClassifSession"
    ear_dir = classif_dir / "Ear"
    assert ear_dir.exists()
    assert len(list(ear_dir.glob("*.jpg"))) == 1

    # Очистка
    os.unlink(fake_path)

def test_export_dataset_cancel_during_preparation(export_service, mock_dataset, tmp_path):
    export_dir = tmp_path / "export"
    export_dir.mkdir()
    directory = str(export_dir)
    cancel_check = MagicMock(return_value=True)
    progress_cb = MagicMock()

    result = export_service.export_dataset(mock_dataset, directory, progress_cb, cancel_check)
    assert result is None
    assert not (export_dir / "TestDataset").exists()

def test_export_dataset_skip_nonexistent_source(export_service, mock_dataset, tmp_path):
    export_dir = tmp_path / "export"
    export_dir.mkdir()
    directory = str(export_dir)
    # Извлекаем изображение из списка
    img = mock_dataset.get_activeImages.return_value[0]
    img.filepath = "/nonexistent.jpg"
    with patch('os.path.exists', return_value=False):
        progress_cb = MagicMock()
        cancel_check = MagicMock(return_value=False)
        result = export_service.export_dataset(mock_dataset, directory, progress_cb, cancel_check)
        assert result[2] == 0
        root = export_dir / "TestDataset"
        images_dir = root / "images"
        # Папка images должна существовать, но без файлов
        assert images_dir.exists()
        assert len(list(images_dir.iterdir())) == 0