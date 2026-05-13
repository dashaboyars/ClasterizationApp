import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

class DuplicateDetector:
    def __init__(self, db):
        self.db = db
        self.dataset = None

    def find_duplicates(self, dataset, progress_callback, cancel_check, threshold = 0.95):
        # начальный прогресс
        if progress_callback:
            progress_callback(5, "Подготовка...")
        if cancel_check and cancel_check():
            return None
        self.dataset = dataset
        images = dataset.get_activeImages()

        if len(images) == 0:
            return [[], dataset]

        embeddings = [img.embedding for img in images]

        #вычисление матрицы косинусной близости
        similarity_matrix = cosine_similarity(embeddings)

        #находим дубликаты
        n = len(embeddings)
        graph = {i: [] for i in range (n)}

        # обновление прогресса
        if cancel_check and cancel_check():
            return None
        if progress_callback:
            progress_callback(10, "Построение связей...")

        #строим граф
        steps = n * (n-1) / 2
        current_steps = 0
        for i in range (n - 1):
            for j in range (i + 1, n):
                if similarity_matrix[i][j] >= threshold:
                    graph[i].append(j)
                    graph[j].append(i)
                current_steps += 1
                if cancel_check and cancel_check():
                    return None
                if progress_callback:
                    percent = int((10 + (current_steps / steps * 90))/2)
                    progress_callback(percent, f"Построение связей...")


        visited = set()
        duplicate_groups = []
        #находим все компоненты связности
        for i in range (n):
            if cancel_check and cancel_check():
                return None
            if progress_callback:
                percent = 50 + int((i + 1) / n * 50)
                progress_callback(percent, f"Ищем похожие...")

            if i in visited:
                continue
            visited.add(i)
            queue = [i]
            group = []

            while queue:
                 elem = queue.pop(0)
                 group.append(images[elem])

                 for neighbour in graph[elem]:
                     if neighbour not in visited:
                         queue.append(neighbour)
                         visited.add(neighbour)
            if len(group) > 1:
                duplicate_groups.append(group)

        if progress_callback:
            progress_callback(100, "Завершено!")

        return [duplicate_groups, dataset]







