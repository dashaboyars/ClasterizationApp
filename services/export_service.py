import os
import shutil


class ExportService:
    def __init__(self, db):
        self.db = db

    def export_dataset(self, dataset, directory, progress_callback, cancel_check):
        if progress_callback:
            progress_callback(5, "Создание корневых папок... (Отмена невозможна)")
        if cancel_check and cancel_check():
            return None

        count_session, count_images = 0, 0

        #корневая папка-датасет
        root_dir = os.path.join(directory, self.safe_filename(dataset.name))
        os.makedirs(root_dir, exist_ok=True)

        #папка для всех изображений
        images_dir = os.path.join(root_dir, "images")
        os.makedirs(images_dir, exist_ok=True)

        # Папка для сессий
        sessions_dir = os.path.join(root_dir, "clasterization_sessions")
        os.makedirs(sessions_dir, exist_ok=True)

        #Папка для сессий классификации НС
        classif_sessions_dir = os.path.join(root_dir, "neural_model_classification_sessions")
        os.makedirs(classif_sessions_dir, exist_ok=True)

        #добавляем все АКТИВНЫЕ изображения в папку images
        active_images = dataset.get_activeImages()
        total_images = len(active_images)

        for idx, img in enumerate(active_images):
            if progress_callback:
                progress_callback(5 + int((idx + 1)/total_images * 10),
                                  f"Копирование изображений: {img.filename}")
            source = img.filepath
            if not os.path.exists(source):
                #добавить предупреждение
                continue
            destination = os.path.join(images_dir, f"{img.id}_{self.safe_filename(img.filename)}")
            shutil.copy2(source, destination)
            count_images += 1

        total_sessions = len(dataset.sessions_list)

        #добавляем сессии
        for idx, session in enumerate(dataset.sessions_list):
            session_dir = os.path.join(sessions_dir, self.safe_filename(session.name))
            os.makedirs(session_dir, exist_ok=True)

            #сохранение папок-кластеров
            for cluster in session.clusters_list:
                cluster_dir = os.path.join(session_dir, self.safe_filename(cluster.name))
                os.makedirs(cluster_dir, exist_ok=True)
                #сохранение изображений кластера
                for img in cluster.images_list:
                    src = img.filepath
                    if not os.path.exists(src):
                        continue
                    dst = os.path.join(cluster_dir, f"{img.id}_{self.safe_filename(img.filename)}")
                    if not os.path.exists(dst):  # избегаем дублей в пределах кластера
                        shutil.copy2(src, dst)
            #сохранение группы-аномалии
            if session.anomaly_group:
                group_dir = os.path.join(session_dir, self.safe_filename(session.anomaly_group.name))
                os.makedirs(group_dir, exist_ok=True)
                for img in session.anomaly_group.images_list:
                    src = img.filepath
                    if not os.path.exists(src):
                        continue
                    dst = os.path.join(group_dir, f"{img.id}_{self.safe_filename(img.filename)}")
                    if not os.path.exists(dst):
                        shutil.copy2(src, dst)
            count_session += 1

            if progress_callback:
                progress_callback(25 + int((idx + 1)/total_sessions * 60),
                                  f"Экспорт сессий кластеризации: {session.name}")

        total_sessions = len(dataset.classification_groups)
        #добавляем сессии классификации НС
        for idx, session in enumerate(dataset.classification_groups):
            session_dir = os.path.join(classif_sessions_dir, self.safe_filename(session.name))
            os.makedirs(session_dir, exist_ok=True)

            #сохранение папок-групп
            for label in session.images_labels.keys():
                group_dir = os.path.join(session_dir, self.safe_filename(label))
                os.makedirs(group_dir, exist_ok=True)
                for item in session.images_labels[label]:
                    img = item[0]
                    src = img.filepath
                    if not os.path.exists(src):
                        continue
                    dst = os.path.join(group_dir, f"{img.id}_{self.safe_filename(img.filename)}")
                    if not os.path.exists(dst):  # избегаем дублей
                        shutil.copy2(src, dst)

            if progress_callback:
                progress_callback(85 + int((idx + 1)/total_sessions * 14),
                                  f"Экспорт сессий клаассификации НС: {session.name}")

        if progress_callback:
            progress_callback(100, "Завершено!")

        return dataset.name, count_session, count_images





    @staticmethod
    def safe_filename(name):
        """Заменяет недопустимые символы в имени файла"""
        return "".join(c for c in name if c.isalnum() or c in (' ', '.', '_', '-')).rstrip()


