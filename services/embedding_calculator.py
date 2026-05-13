import numpy as np
import tensorflow as tf
from tensorflow.keras.applications import EfficientNetB0, EfficientNetB1, EfficientNetB2, EfficientNetB3, EfficientNetB4, EfficientNetB5, EfficientNetB6, EfficientNetB7
from tensorflow.keras.applications.efficientnet import preprocess_input
from tensorflow.keras.preprocessing import image
import os

#класс для извлечения эмбеддингов изображений с использованием EfficientNet
class EmbeddingCalculator:
    def __init__(self, variant='B0', input_size=None):
        self.variant = variant
        #стандартные размеры (в пикселях) для разных версий EfficientNet
        self.input_sizes = {
            'B0': 224, 'B1': 240, 'B2': 260, 'B3': 300,
            'B4': 380, 'B5': 456, 'B6': 528, 'B7': 600
        }
        self.input_size = input_size or self.input_sizes.get(variant, 224)

        #загружаем модель
        self.model = self.load_model()
        print(f"✅ EfficientNet-{variant} загружена, размер входа: {self.input_size}")

    #метод для загрузки модели
    def load_model(self):
        model_map = {
            'B0': EfficientNetB0,
            'B1': EfficientNetB1,
            'B2': EfficientNetB2,
            'B3': EfficientNetB3,
            'B4': EfficientNetB4,
            'B5': EfficientNetB5,
            'B6': EfficientNetB6,
            'B7': EfficientNetB7
        }

        if self.variant not in model_map:
            raise ValueError(f"Неизвестный вариант: {self.variant}. Доступны: {list(model_map.keys())}")
        #устанавливаем выбранный класс модели
        model_class = model_map[self.variant]

        model = model_class(
            weights='imagenet',
            include_top=False,
            pooling='avg',  # avg для усреднения значений
            input_shape=(self.input_size, self.input_size, 3)
        )
        return model

    #метод для извлечения эмбеддинга одного изображения
    def get_embedding(self, img_path):
        try:
            # Открытие изображение по пути, преобразование размера
            img = image.load_img(img_path, target_size=(self.input_size, self.input_size))
            #преобразование изображения в массив размера input_size, где каждый элемент
            x = image.img_to_array(img)
            #добавляет в начало batch dimension (количество изображений)
            x = np.expand_dims(x, axis=0)
            #нормализация пикселей для корректной работы модели
            x = preprocess_input(x)
            #Прогон через нейросеть
            embedding = self.model.predict(x, verbose=0)
            #преобразование в одномерный массив, приведение к float
            return embedding.flatten().astype(np.float32)

        except Exception as e:
            print(f"Ошибка при обработке {img_path}: {e}")
            return None

    # метод для вычисления эмбеддингов из множества изображений (пакетная обработка)
    def get_embedding_batch(self, img_paths, batch_size=16):
        #по умолчанию размера пакета = 16 изображения
        embeddings = []

        for i in range(0, len(img_paths), batch_size):
            batch_paths = img_paths[i:i + batch_size]
            batch_images = []
            valid_indices = []

            for j, path in enumerate(batch_paths):
                try:
                    img = image.load_img(path, target_size=(self.input_size, self.input_size))
                    x = image.img_to_array(img)
                    batch_images.append(x)
                    valid_indices.append(i + j)
                except Exception as e:
                    print(f"⚠️ Пропускаем {path}: {e}")
                    # Добавляем нулевой вектор для сохранения порядка
                    batch_images.append(np.zeros((self.input_size, self.input_size, 3)))

            if batch_images:
                x = np.array(batch_images)
                x = preprocess_input(x)
                batch_embeddings = self.model.predict(x, verbose=0)
                embeddings.extend(batch_embeddings)

        #возврат двумерной матрицы, где каждая строка - эмбеддинг одного изображения
        return np.array(embeddings)

#добавить методы для работы с эмбеддингами