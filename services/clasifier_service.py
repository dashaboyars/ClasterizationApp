

import onnx
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms, models
import onnxruntime as ort
import numpy as np
from PIL import Image
from typing import List, Tuple, Optional

from repositories.clasification_session_repository import ClassificationSessionRepository
from repositories.modelVersion_repository import ModelVersionRepository


class ImageDataset(Dataset):
    def __init__(self, images_paths, labels, transform=None):
        self.images_paths = images_paths
        self.labels = labels
        self.transform = transform

    def __len__(self):
        return len(self.images_paths)

    def __getitem__(self, idx):
        img = Image.open(self.images_paths[idx]).convert('RGB')
        if self.transform:
            img = self.transform(img)
        return img, self.labels[idx]

class ENTClassifier:
    MEAN = [0.485, 0.456, 0.406]
    STD = [0.229, 0.224, 0.225]
    INPUT_SIZE = 224

    def __init__(self,
                 db, project_root,
                 model_path: Optional[str] = None,  # путь к .onnx для инференса
                 device: Optional[str] = None,
                 backbone: str = 'mobilenet_v2',
                 num_classes=None,
                 labelmap_ru = None):

        self.project_root = project_root
        self.device = torch.device(device or ('cuda' if torch.cuda.is_available() else 'cpu'))
        self.ort_session = None
        self.db = db

        self.LABELMAP_RU = labelmap_ru if labelmap_ru else ['Ухо', 'Гортань', 'Нос', 'Глотка', 'Не в кадре']
        self.NUM_CLASSES = num_classes if num_classes else 5

        # Инициализация модели ТОЛЬКО если будем обучать
        self.torch_model = None

        # Для инференса загружаем ONNX-сессию
        self.load_onnx(model_path)

    def load_onnx(self, onnx_path):
        #ЗАГРУЗКА ONNX ДЛЯ ИНФЕРЕНСА через ONNX RUNTIME
        providers = ['CUDAExecutionProvider', 'CPUExecutionProvider']
        self.ort_session = ort.InferenceSession(onnx_path, providers=providers)
        print(f"ONNX loaded: {onnx_path}")

    #ИНФЕРЕНС
    def predict(self, image_path: str) -> Tuple[str, float]:
        #возврат: (русская метка, уверенность от 0 до 1)
        if self.ort_session is None:
            raise RuntimeError("ONNX session not loaded. Call load_onnx() or export_to_onnx() first.")

        # Preprocess
        img = Image.open(image_path).convert('RGB').resize((self.INPUT_SIZE, self.INPUT_SIZE))
        img_np = np.array(img).astype(np.float32) / 255.0
        for c in range(3):
            img_np[:, :, c] = (img_np[:, :, c] - self.MEAN[c]) / self.STD[c]
        input_tensor = np.transpose(img_np, (2, 0, 1))[np.newaxis, ...].astype(np.float32)

        # Inference
        ort_input = {self.ort_session.get_inputs()[0].name: input_tensor}
        output = self.ort_session.run(None, ort_input)[0]
        probs = torch.nn.functional.softmax(torch.tensor(output), dim=1).numpy()[0]

        pred_idx = int(np.argmax(probs))
        return self.LABELMAP_RU[pred_idx], float(probs[pred_idx])

    #ПАКЕТНЫЙ ИНФЕРЕНС
    def predict_batch(self, images, dataset, model_id, progress_callback, cancel_check):
        """Предсказание для списка изображений"""
        predictions = []
        count = 0
        image_paths = [img.filepath for img in images]
        for img in images:
            if img.filepath == None:
                print(img.id)
                print(img.filename)

        total_count = len(image_paths)
        for p in image_paths:
            predictions.append(self.predict(p))
            if progress_callback:
                progress_callback(int((count + 1)/total_count * 85),
                                  f"Разработка предсказания: {(count + 1)}/{total_count}")
            if cancel_check and cancel_check():
                return None
            count += 1

        #сохранение результатов
        if progress_callback:
            progress_callback(90,
                              f"Сохранение результатов...\nОтмена операции невозможна.")

        conn = self.db.connect()

        #получаем id версии модели
        newSession_name = f"Сессия {len(dataset.classification_groups) + 1}"

        classification_session_repo = ClassificationSessionRepository(conn)
        new_session = classification_session_repo.create_session(newSession_name, model_id, dataset.id,
                                                   predictions, images)

        conn.close()

        if progress_callback:
            progress_callback(100, "Завершено")

        return predictions, new_session, images, dataset
