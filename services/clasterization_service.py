import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import pairwise_distances
from sklearn.preprocessing import normalize
import kmars
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler

from services.qualityAnalyse_service import QualityAnalyseService


class ClusterizationService:
    def __init__(self, db):
        self.db = db

    def clusterize_DBSCAN(self, session_name, dataset, params, progress_callback=None, cancel_check=None):
        # начальный прогресс
        if progress_callback:
            progress_callback(5, "Подготовка...")
        if cancel_check and cancel_check():
            return None

        # получаем эмбеддинги
        embeddings = np.array([img.embedding for img in dataset.images_list if img.status != "deleted"])

        #получаем все выбранные параметры
        eps = params['eps']
        min_samples = params['min_samples']
        similarity_method = params['similarity_method']

        if similarity_method == "Косинусное расстояние (Cosine Similarity)":
            metric = 'cosine'
        elif similarity_method == "Манхэттенское расстояние (Manhattan/L1)":
            metric = 'manhattan'
        elif similarity_method == "Чебышева расстояние (Chebyshev)":
            metric = 'chebyshev'
        else:
            metric = 'euclidean'

        if metric == 'cosine':
            # нормализация эмбеддингов для косинусного расстояния
            embeddings = normalize(embeddings, norm='l2')
        else:
            #Стандартизация
            scaler = StandardScaler()
            embeddings = scaler.fit_transform(embeddings)

        # обновление прогресса
        if progress_callback:
            progress_callback(15, "Обучение модели...(Отмена невозможна)")

        dbscan = DBSCAN(
            eps=eps,
            min_samples=min_samples,
            metric=metric,
            n_jobs=-1
        )
        labels = dbscan.fit_predict(embeddings)

        if progress_callback:
            progress_callback(50, "Сохранение результатов... (Отмена невозможна)")

        conn = self.db.connect()
        # Cохранение результатов без возможности отмены операции
        new_session = self.SaveResults_DBSCAN(conn, params, session_name, dataset, labels, progress_callback)

        conn.commit()
        conn.close()

        # обновление прогресса
        if progress_callback:
            progress_callback(100, "Завершено")

        return new_session, dataset

    def SaveResults_DBSCAN(self, conn, params, session_name, dataset, labels, progress_callback):
        from repositories.session_repository import SessionRepository
        from repositories.cluster_repository import ClusterRepository
        from repositories.anomaly_repositoty import AnomalyGroupRepository

        # создание новой сессии
        session_repo = SessionRepository(conn)
        new_session = session_repo.create_session(session_name, params, dataset.id)

        clusters = [None] * (max(labels) + 1)
        anomalyGroup = None
        cluster_repo = ClusterRepository(conn)
        anomalyGroup_repo = AnomalyGroupRepository(conn)
        image_index = 0
        total_images = len(labels)
        active_images = [img for img in dataset.images_list if img.status != "deleted"]

        for index in labels:
            # обновление прогресса
            if progress_callback:
                percent = 50 + int((image_index + 1) / total_images * 45)
                progress_callback(percent, "Сохранение результатов... (Отмена операции невозможна)")

            if index == -1:
                if anomalyGroup is None:
                    anomalyGroup = anomalyGroup_repo.create_group("Аномалии", new_session.id)
                image_id = active_images[image_index].id
                #добавление изображения в группу аномалий в БД
                anomalyGroup_repo.add_image_to_group(image_id, anomalyGroup.id)
                #добавление в список
                anomalyGroup.images_list.append(active_images[image_index])
            else:
                if clusters[index] == None:
                    new_cluster = cluster_repo.create_cluster(f"Кластер_{index + 1}", new_session.id)
                    clusters[index] = new_cluster
                #добавление изображения в кластер в БД
                image_id = active_images[image_index].id
                cluster_repo.add_image_to_cluster(image_id, clusters[index].id, 0)
                # добавляем изображение в модель кластера
                clusters[index].images_list.append(active_images[image_index])
                clusters[index].count_images += 1
                active_images[image_index].clusters_list.append(clusters[index])
                # добавляем имя кластера в список кластеров изображения для отображения
                active_images[image_index].clusters_list.append(clusters[index].name)
            image_index += 1

        # добавляем в сессию список кластеров
        new_session.clusters_list = clusters
        new_session.anomaly_group = anomalyGroup
        dataset.sessions_list.append(new_session)
        dataset.sessions_count += 1

        return new_session



    def clusterize_KMeans(self, session_name, dataset, params, progress_callback=None, cancel_check=None):
        # начальный прогресс
        if progress_callback:
            progress_callback(5, "Подготовка...")
        if cancel_check and cancel_check():
            return None

        # получаем эмбеддинги
        embeddings = np.array([img.embedding for img in dataset.images_list if img.status != "deleted"])

        #получаем все выбранные параметры
        k = params['k']
        max_iter = params['max_iterations']
        tol = params['tol']
        similarity_method = params['similarity_method']
        init_method = self.get_initMethod(params['initialization_method'], similarity_method, embeddings, k)

        # обновление прогресса
        if progress_callback:
            progress_callback(10, "Нормализация эмбеддингов...")
        if cancel_check and cancel_check():
            return None

        #нормализуем эмбеддинги
        #при нормализации эмбеддингов эвклидово расстояние даст такой же результат как и косинусное
        if similarity_method == "Косинусное расстояние (Cosine Similarity)":
            #приведение к единичной длине
            embeddings = normalize(embeddings, norm='l2')
        elif similarity_method == "Евклидово расстояние (Euclidean)":
            # Стандартизация
            scaler = StandardScaler()
            embeddings = scaler.fit_transform(embeddings)


        # обновление прогресса
        if progress_callback:
            progress_callback(15, "Обучение модели...(Отмена операции невозможна)")

        if similarity_method ==  "Манхэттенское расстояние (Manhattan/L1)":
            kmeans = kmars.KMeans(
                n_clusters=k,
                init=init_method,  # Только k-means++ поддерживается
                max_iter=max_iter,
                tol=tol,
                random_state=42,
                dist='manhattan'
            )
            kmeans.fit(embeddings)
            labels = kmeans.labels_
        else:
            # Создаем и обучаем модель K-Means
            kmeans = KMeans(
                n_clusters=k,
                init=init_method,
                max_iter=max_iter,
                tol=tol,
                random_state=42,  # для воспроизводимости
                n_init=10  # количество запусков с разными инициализациями
            )
            # Обучаем на наших данных (группировка по кластерам)
            labels = kmeans.fit_predict(embeddings)

        # обновление прогресса
        if progress_callback:
            progress_callback(50, "Сохранение результатов... (Отмена операции невозможна)")

        conn = self.db.connect()
        #Cохранение результатов без возможности отмены операции
        new_session = self.SaveResults(conn, params, session_name, dataset, labels, progress_callback)

        conn.commit()
        conn.close()

        # обновление прогресса
        if progress_callback:
            progress_callback(100, "Завершено")

        return new_session, dataset

    def random_init(self, embeddings, k_param):
        n_samples = embeddings.shape[0]
        random_indices = np.random.choice(n_samples, size=k_param, replace=False)
        initial_centroids = embeddings[random_indices]

        return initial_centroids

    def furthest_points_init(self, embeddings, k_param):
        #первая точка задается случайным образом
        n_points = embeddings.shape[0]
        centroids_idx = [np.random.randint(n_points)]
        #ищем максимально удаленную точку от первой
        dist_to_centroids = pairwise_distances(embeddings,
                                               embeddings[centroids_idx].reshape(1, -1)).flatten()
        next_idx = np.argmax(dist_to_centroids)
        centroids_idx.append(next_idx)
        #оставшиеся точки добавляем итеративно
        for _ in range(2, k_param):
            dist_to_centroids = pairwise_distances(embeddings, embeddings[centroids_idx]).min(axis=1)
            next_idx = np.argmax(dist_to_centroids)
            centroids_idx.append(next_idx)
        return embeddings[centroids_idx]

    def first_kPoints_init(self, embeddings, k_param):
        centroids_idx = [ind for ind in range(k_param)]
        return embeddings[centroids_idx]


    def SaveResults(self, conn, params, session_name, dataset, labels, progress_callback):
        from repositories.session_repository import SessionRepository
        from repositories.cluster_repository import ClusterRepository
        # создание новой сессии
        session_repo = SessionRepository(conn)
        new_session = session_repo.create_session(session_name, params, dataset.id)

        clusters = [None] * params['k']
        cluster_repo = ClusterRepository(conn)
        image_index = 0
        total_images = len(labels)
        active_images = [img for img in dataset.images_list if img.status != "deleted"]

        for index in labels:
            #обновление прогресса
            if progress_callback:
                percent = 50 + int((image_index + 1) / total_images * 45)
                progress_callback(percent, "Сохранение результатов... (Отмена операции невозможна)")

            if clusters[index] == None:
                new_cluster = cluster_repo.create_cluster(f"Кластер_{index + 1}", new_session.id)
                clusters[index] = new_cluster
            #добавление изображения в кластер в БД
            #image_id = dataset.images_list[image_index].id
            image_id = active_images[image_index].id
            cluster_repo.add_image_to_cluster(image_id, clusters[index].id, 0)
            #добавляем изображение в модель кластера
            clusters[index].images_list.append(active_images[image_index])
            clusters[index].count_images += 1
            active_images[image_index].clusters_list.append(clusters[index])
            #добавляем имя кластера в список кластеров изображения для отображения
            active_images[image_index].clusters_list.append(clusters[index].name)

            image_index += 1

        #добавляем в сессию список кластеров
        qualityAnalyse_service = QualityAnalyseService(self.db)

        new_session.clusters_list = clusters
        for clus in new_session.clusters_list:
            clus.silhouette = qualityAnalyse_service.count_cluster_silhouette(clus, new_session)
            cluster_repo.save_silhouette(clus.silhouette, clus.id)

        dataset.sessions_list.append(new_session)
        dataset.sessions_count += 1

        return new_session

    def get_initMethod(self, param, similarity_method, embeddings, k):
        if param == "K-Means++":
            if similarity_method == "Манхэттенское расстояние (Manhattan/L1)":
                return "kmeans++"
            else:
                return 'k-means++'
        elif param == "Случайный выбор":
            if similarity_method == "Манхэттенское расстояние (Manhattan/L1)":
                return self.random_init(embeddings, k)
            else:
                return 'random'
        elif param == "Furthest (самые удаленные точки)":
            return self.furthest_points_init(embeddings, k)
        elif param == "First K (первые k точек)":
            return self.first_kPoints_init(embeddings, k)


    #поиск оптимального k методом локтя
    def get_optimal_k(self, images, progress_callback=None, cancel_check=None):
        # начальный прогресс
        if progress_callback:
            progress_callback(5, "Подготовка...")
        if cancel_check and cancel_check():
            return None

        inertias = []
        embeddings = [img.embedding for img in images]
        #для каждого k проверяем инерцию - метрика качества
        #(сумма квадратов расстояний от точек до центров их кластеров)
        max_value = min(int(len(images)/2), 20)
        for k in range (2, max_value):
            # обновление прогресса
            if cancel_check and cancel_check():
                return None
            if progress_callback:
                percent = 5 + int(k / max_value * 90)
                progress_callback(percent, f"Проверка значений...")

            kmeans = KMeans(n_clusters=k, random_state=42)
            kmeans.fit(embeddings)
            inertias.append(kmeans.inertia_)

        # обновление прогресса
        if cancel_check and cancel_check():
            return None
        if progress_callback:
            percent = 95
            progress_callback(percent, f"Находим оптимальное значение...")
        #находим точку перегиба
        elbow_point = self.find_elbow_point(inertias)
        if progress_callback:
            percent = 100
            progress_callback(percent, f"Находим оптимальное значение...")
        return elbow_point

    def get_optimal_minSamples_Esp(self, images, metric, progress_callback, cancel_check):
        min_samples = self.get_optimal_minSamples(images, progress_callback, cancel_check)
        embeddings = np.array([img.embedding for img in images])
        eps = self.get_optimal_eps(embeddings, min_samples, progress_callback, cancel_check, metric)

        return [min_samples, eps]


    def get_optimal_eps(self, embeddings, min_samples, progress_callback, cancel_check, metric):
        from sklearn.neighbors import NearestNeighbors
        import numpy as np

        # обновление прогресса
        if cancel_check and cancel_check():
            return None
        if progress_callback:
            percent = 50
            progress_callback(percent, f"Расчет оптимального радиуса поиска соседей...")

        #нормализация эмбеддингов
        if metric == 'cosine':
            embeddings = normalize(embeddings, norm='l2')
        else:
            #Стандартизация
            scaler = StandardScaler()
            embeddings = scaler.fit_transform(embeddings)

        # Строим k-distance график
        neighbors = NearestNeighbors(n_neighbors=min_samples, metric=metric)#, metric='euclidean')
        neighbors_fit = neighbors.fit(embeddings)

        # обновление прогресса
        if cancel_check and cancel_check():
            return None
        if progress_callback:
            percent = 70
            progress_callback(percent, f"Расчет расстояний...")

        distances, indices = neighbors_fit.kneighbors(embeddings)
        k_distances = np.sort(distances[:, min_samples - 1])

        # обновление прогресса
        if cancel_check and cancel_check():
            return None
        if progress_callback:
            percent = 95
            progress_callback(percent, f"Выбор значения...")

        n = len(k_distances)
        # Нормализуем расстояния и координаты в [0, 1]
        k_dist_norm = (k_distances - k_distances[0]) / (k_distances[-1] - k_distances[0] + 1e-8)
        x = np.linspace(0, 1, n)

        # Ищем точку, максимально удалённую от диагонали (y = x)
        max_dist = 0
        elbow_idx = 0
        for i in range(1, n - 1):
            dist = abs(k_dist_norm[i] - x[i]) / np.sqrt(2)
            if dist > max_dist:
                max_dist = dist
                elbow_idx = i

        eps = k_distances[elbow_idx]
        # Ограничиваем eps разумными пределами
        #eps = max(eps, 0.05)  # минимум 0.05
        #eps = min(eps, 1.0)  # максимум 1.0 (для нормализованных данных)

        # обновление прогресса
        if cancel_check and cancel_check():
            return None
        if progress_callback:
            percent = 100
            progress_callback(percent, f"Завершено...")
        print(f"eps = {eps:.4f}, elbow_idx = {elbow_idx}, max_dist = {max_dist:.4f}")

        return eps


    def get_optimal_minSamples(self, images, progress_callback, cancel_check):
        from services.qualityAnalyse_service import QualityAnalyseService

        # обновление прогресса
        if cancel_check and cancel_check():
            return None
        if progress_callback:
            percent = 5
            progress_callback(percent, f"Оценка min_samples относительно количества...")
        #оцениваем относительно кол-ва изображений в датасете
        count = len(images)
        if count < 100:
            min_sample = 3
        elif count < 1000:
            min_sample = 5
        elif count < 5000:
            min_sample = 8
        else:
            min_sample = 10

        # обновление прогресса
        if cancel_check and cancel_check():
            return None
        if progress_callback:
            percent = 35
            progress_callback(percent, f"Оценка min_samples относительно зашумленности данных...")

        #оцениваем относительно зашумленности данных
        qualityAnalyse_service = QualityAnalyseService(self.db)
        medium_noise = qualityAnalyse_service.get_medium_noiseLevel(images)
        if medium_noise < 0.05:
            return min_sample
        elif medium_noise < 0.1:
            return round(min_sample + min_sample * 0.2)
        elif medium_noise < 0.15:
            return round(min_sample + min_sample * 0.4)
        elif medium_noise < 0.2:
            return round(min_sample + min_sample * 0.6)
        elif medium_noise < 0.25:
            return round(min_sample + min_sample * 0.8)
        else:
            return min_sample * 2

    def find_elbow_point(self, inertias):
        n = len(inertias)

        # Нормализуем инерции
        inertias_norm = np.array(inertias)
        inertias_norm = (inertias_norm - inertias_norm[0]) / (inertias_norm[-1] - inertias_norm[0] + 1e-8)

        # Строим линию от первой до последней точки
        x = np.linspace(0, 1, n)

        # Ищем точку с максимальным расстоянием до линии
        max_dist = 0
        elbow_idx = 0

        for i in range(1, n - 1):
            # Расстояние от точки до прямой
            point = (x[i], inertias_norm[i])

            # Расстояние до линии y = 1 - x
            dist = abs(point[1] - (1 - point[0])) / np.sqrt(2)

            if dist > max_dist:
                max_dist = dist
                elbow_idx = i

        # +2 потому что inertias начинается с k=2
        return elbow_idx + 2


