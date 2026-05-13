from unittest.mock import MagicMock

import numpy as np
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
from database import DatabaseConnection
from services.qualityAnalyse_service import QualityAnalyseService
import shutil

import pytest
import sqlite3
import tempfile
from pathlib import Path

@pytest.fixture
def temp_db():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    original_db_path = os.path.join(project_root, 'database', 'DBClasterizationApp.db')
    #создание временного файла базы данных
    temp_db_fd, temp_db_path = tempfile.mkstemp(suffix='.db')
    os.close(temp_db_fd) #закрытие дескриптора
    #Копирование содержимого базы данных во временный файл
    shutil.copy2(original_db_path, temp_db_path)
    yield DatabaseConnection(temp_db_path)
    try:
        os.unlink(temp_db_path)
    except PermissionError:
        pass

@pytest.fixture
def db_conn(temp_db):
    from database import DatabaseConnection
    db = DatabaseConnection(temp_db)
    conn = temp_db.connect()
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    yield conn
    conn.close()


@pytest.fixture
def user_repo(db_conn):
    from repositories.user_repository import UserRepository
    return UserRepository(db_conn)

#создание тестового пользователя
@pytest.fixture(autouse=True)
def ensure_test_user(db_conn):
    cursor = db_conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (id, username, email, password_hash) VALUES (1, 'test', 'test@example.com', 'hash')")
    db_conn.commit()

@pytest.fixture
def tag_repo(db_conn):
    from repositories.tag_repository import TagRepository
    return TagRepository(db_conn)

@pytest.fixture
def session_repo(db_conn):
    from repositories.session_repository import SessionRepository
    return SessionRepository(db_conn)

@pytest.fixture
def modelVersion_repo(db_conn):
    from repositories.modelVersion_repository import ModelVersionRepository
    return ModelVersionRepository(db_conn)

@pytest.fixture
def image_repo(db_conn):
    from repositories.image_repository import ImageRepository
    return ImageRepository(db_conn)

@pytest.fixture
def dataset_repo(db_conn):
    from repositories.dataset_repository import DatasetRepository
    return DatasetRepository(db_conn)

@pytest.fixture
def cluster_repo(db_conn):
    from repositories.cluster_repository import ClusterRepository
    return ClusterRepository(db_conn)

@pytest.fixture
def classifSession_repo(db_conn):
    from repositories.clasification_session_repository import ClassificationSessionRepository
    return ClassificationSessionRepository(db_conn)

@pytest.fixture
def anomalyGroup_repo(db_conn):
    from repositories.anomaly_repositoty import AnomalyGroupRepository
    return AnomalyGroupRepository(db_conn)

@pytest.fixture
def systemUser_service(db_conn):
    from services.system_user_service import SystemUserService
    return SystemUserService(db_conn)

@pytest.fixture
def quality_analyse_service(temp_db):
    from services.qualityAnalyse_service import QualityAnalyseService
    return QualityAnalyseService(temp_db)

@pytest.fixture
def embedding_calculator():
    from services.embedding_calculator import EmbeddingCalculator
    return EmbeddingCalculator()

@pytest.fixture
def mock_embedding_calculator():
    #Мок для EmbeddingCalculator, возвращающий фиксированный эмбеддинг
    mock = MagicMock()
    mock.get_embedding.return_value = np.random.randn(1280).astype(np.float32)
    return mock

@pytest.fixture
def mock_quality_service():
    #Мок для QualityAnalyseService, возвращающий фиксированные характеристики
    mock = MagicMock()
    mock.get_quality_char.return_value = {
        'file_size': 1024,
        'resolution_width': 1920,
        'resolution_height': 1080,
        'colors_amount': 16777216,
        'sharpness': 0.5,
        'noise_level': 0.1,
        'contrast': 0.8,
    }
    return mock

@pytest.fixture
def import_service(temp_db, mock_embedding_calculator, mock_quality_service):
    from services.import_service import ImportService
    return ImportService(temp_db, mock_embedding_calculator, mock_quality_service)

# Фикстура для создания мок-изображения с эмбеддингом
@pytest.fixture
def mock_image():
    class MockImage:
        def __init__(self, idx, embedding):
            self.id = idx
            self.embedding = embedding
            self.status = "active"
            self.filename = f"img_{idx}.jpg"
            self.clusters_list = []
        def __repr__(self):
            return f"MockImage(id={self.id})"
    return MockImage

@pytest.fixture
def mock_dataset(mock_image):
    class MockDataset:
        def __init__(self, images):
            self.images_list = images
            self.sessions_list = []
            self.sessions_count = 0
            self.id = 1
            self.name = "TestDataset"
        def get_activeImages(self):
            return [img for img in self.images_list if img.status != "deleted"]
    return MockDataset

@pytest.fixture
def duplicate_detector(temp_db):
    from services.duplicate_detector import DuplicateDetector
    return DuplicateDetector(temp_db)

@pytest.fixture
def cluster_service(temp_db):
    from services.clasterization_service import ClusterizationService
    return ClusterizationService(temp_db)

# Вспомогательная функция для создания тестовых эмбеддингов
def create_embeddings(n_samples=10, n_features=5, random_state=42):
    np.random.seed(random_state)
    return np.random.randn(n_samples, n_features).astype(np.float32)

@pytest.fixture
def mock_ort_session():
    #Мок для сессии ONNX Runtime
    session = MagicMock()
    session.get_inputs.return_value = [MagicMock(name='input')]
    # Возвращаем логиты
    session.run.return_value = [np.array([[0.1, 0.2, 0.6, 0.05, 0.05]], dtype=np.float32)]
    return session


@pytest.fixture
def temp_onnx_file(tmp_path):
    onnx_file = tmp_path / "test_model.onnx"
    onnx_file.touch()
    return str(onnx_file)

@pytest.fixture
def quality_service(temp_db):
    return QualityAnalyseService(temp_db)

@pytest.fixture
def export_service(temp_db):
    from services.export_service import ExportService
    return ExportService(temp_db)




