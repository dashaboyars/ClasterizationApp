from unittest.mock import patch, MagicMock
import numpy as np
import pytest
from PIL import Image
from services.clasifier_service import ENTClassifier


def test_constructor_loads_onnx(temp_db, temp_onnx_file):
    with patch('onnxruntime.InferenceSession') as mock_inference:
        classifier = ENTClassifier(db=temp_db, project_root="", model_path=temp_onnx_file)
        mock_inference.assert_called_once_with(
            temp_onnx_file,
            providers=['CUDAExecutionProvider', 'CPUExecutionProvider']
        )
        assert classifier.ort_session is not None
        assert classifier.LABELMAP_RU == ['Ухо', 'Гортань', 'Нос', 'Глотка', 'Не в кадре']


def test_predict_normal(temp_db, temp_onnx_file, mock_ort_session, tmp_path):
    img_path = tmp_path / "test.jpg"
    img = Image.new('RGB', (224, 224), color='red')
    img.save(img_path)
    with patch('onnxruntime.InferenceSession', return_value=mock_ort_session):
        classifier = ENTClassifier(db=temp_db, project_root="", model_path=temp_onnx_file)
        label, confidence = classifier.predict(str(img_path))
        assert label in classifier.LABELMAP_RU
        assert 0 <= confidence <= 1


def test_predict_no_session(temp_db):
    with patch.object(ENTClassifier, 'load_onnx') as mock_load:
        classifier = ENTClassifier(db=temp_db, project_root="", model_path=None)
        classifier.ort_session = None
        with pytest.raises(RuntimeError):
            classifier.predict("dummy.jpg")


def test_predict_batch_success(temp_db, mock_ort_session, tmp_path):
    # Создаём два временных изображения
    img1 = tmp_path / "a.jpg"
    img2 = tmp_path / "b.jpg"
    Image.new('RGB', (224, 224), color='red').save(img1)
    Image.new('RGB', (224, 224), color='blue').save(img2)

    class MockImage:
        def __init__(self, idx, path):
            self.id = idx
            self.filepath = path

    images = [MockImage(1, str(img1)), MockImage(2, str(img2))]
    dataset = MagicMock()
    dataset.id = 123
    dataset.classification_groups = []
    model_id = 42
    progress_cb = MagicMock()
    cancel_check = MagicMock(return_value=False)

    with patch('onnxruntime.InferenceSession', return_value=mock_ort_session):
        classifier = ENTClassifier(db=temp_db, project_root="", model_path="dummy.onnx")
        with patch('services.clasifier_service.ClassificationSessionRepository') as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.create_session.return_value = "new_session_obj"
            mock_repo_class.return_value = mock_repo
            result = classifier.predict_batch(images, dataset, model_id, progress_cb, cancel_check)

    predictions, new_session, returned_images, returned_dataset = result
    assert len(predictions) == 2
    for pred, conf in predictions:
        assert pred == "Нос"        # логиты дают максимум на индексе 2 -> "Нос"
        assert conf > 0             # уверенность положительна
    assert returned_images == images
    assert returned_dataset is dataset
    mock_repo.create_session.assert_called_once_with(
        "Сессия 1", model_id, dataset.id, predictions, images
    )


def test_predict_batch_cancel_during_processing(temp_db, mock_ort_session, tmp_path):
    class MockImage:
        def __init__(self, idx):
            self.id = idx
            self.filepath = str(tmp_path / f"{idx}.jpg")
    # Создаём два временных изображения
    for i in [1, 2]:
        img_path = tmp_path / f"{i}.jpg"
        Image.new('RGB', (224, 224), color='red').save(img_path)
    images = [MockImage(1), MockImage(2)]
    dataset = MagicMock()
    dataset.id = 123
    progress_cb = MagicMock()
    cancel_check = MagicMock(side_effect=[False, True])

    with patch('onnxruntime.InferenceSession', return_value=mock_ort_session):
        classifier = ENTClassifier(db=temp_db, project_root="", model_path="dummy.onnx")
        result = classifier.predict_batch(images, dataset, 1, progress_cb, cancel_check)
    assert result is None


def test_predict_batch_empty_image_list(temp_db, mock_ort_session):
    images = []
    dataset = MagicMock()
    dataset.id = 123
    dataset.classification_groups = []
    progress_cb = MagicMock()
    cancel_check = MagicMock()

    with patch('onnxruntime.InferenceSession', return_value=mock_ort_session):
        classifier = ENTClassifier(db=temp_db, project_root="", model_path="dummy.onnx")
        with patch('services.clasifier_service.ClassificationSessionRepository') as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.create_session.return_value = "new_session_obj"
            mock_repo_class.return_value = mock_repo
            result = classifier.predict_batch(images, dataset, 1, progress_cb, cancel_check)

    predictions, new_session, returned_images, returned_dataset = result
    assert predictions == []
    assert returned_images == []
    assert returned_dataset is dataset
    mock_repo.create_session.assert_called_once()
