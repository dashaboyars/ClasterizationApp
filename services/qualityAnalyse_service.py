import os

import cv2
import numpy as np
from sklearn.metrics import silhouette_samples, calinski_harabasz_score, davies_bouldin_score
from PIL import Image #для расчета разрешения
from joblib.parallel import method
from skimage.restoration import estimate_sigma

class QualityAnalyseService:
    def __init__(self, db):
        self.db = db

    #АНАЛИЗ КАЧЕСТВА СЕССИЙ
    def get_session_qualityParams(self, session):
        #силуэт
        silhouette = self.get_session_silhouette(session)
        #chi-index
        chi = self.get_chi_index(session)
        #dbi-index
        dbi = self.get_dbi_index(session)

        return {
            "silhouette": silhouette,
            "chi": chi,
            "dbi": dbi
        }

    def get_dbi_index(self, session):
        if len(session.clusters_list) <= 1:
            return None
        emb_matrix = []
        labels = []
        for clus in session.clusters_list:
            for img in clus.images_list:
                emb_matrix.append(img.embedding)
                labels.append(clus.id)
        dbi = davies_bouldin_score(np.array(emb_matrix), labels)
        return dbi




    def get_chi_index(self, session):
        if len(session.clusters_list) <= 1:
            return None
        emb_matrix = []
        labels = []
        for clus in session.clusters_list:
            for img in clus.images_list:
                emb_matrix.append(img.embedding)
                labels.append(clus.id)
        chi = calinski_harabasz_score(np.array(emb_matrix), labels)
        return chi

    def get_session_silhouette(self, session):
        silhouette_values, labels = self.count_point_silhouettes(session)
        if silhouette_values is None:
            return None
        return float(np.mean(silhouette_values))


    #АНАЛИЗ КАЧЕСТВА КЛАСТЕРОВ
    def get_claster_qualityParams(self, cluster, session):
        #размер
        size = len(cluster.images_list)
        #силуэт
        silhouette = self.count_cluster_silhouette(cluster, session)
        #компактность
        cohesion = self.count_cluster_cohesion(cluster)
        #разделяемость
        separation = self.count_cluster_separation(cluster, session)
        #плотность
        density = self.count_cluster_density(cohesion)
        #радиус
        radius = self.get_cluster_radius(cluster)

        return{
            'size': size,
            'silhouette': silhouette,
            'cohesion': cohesion,
            'separation': separation,
            'density': density,
            'radius': radius
        }

    def get_cluster_radius(self, cluster):
        emb_matrix = np.array([img.embedding for img in cluster.images_list])
        centroid = np.mean(emb_matrix, axis=0)
        distances = np.linalg.norm(emb_matrix - centroid, axis=1)
        return float(np.max(distances))

    def count_cluster_density(self, cohesion):
        return float(1.0/(cohesion + 1e-12))


    def count_cluster_separation(self, cluster, session):
        other_centroids = []
        own_centroid = 0
        #расчет центроидов
        for clus in session.clusters_list:
            emb_matrix = np.array([img.embedding for img in clus.images_list])
            centroid = np.mean(emb_matrix, axis=0)
            if clus.id != cluster.id:
                other_centroids.append(centroid)
            else:
                own_centroid = centroid

        #расчет расстояний
        other_centroids = np.array(other_centroids)
        if other_centroids.ndim == 1:
            # Если только один центроид, он должен быть 2D
            other_centroids = other_centroids.reshape(1, -1)
        distances = np.linalg.norm(other_centroids - own_centroid, axis=1)
        return float(np.mean(distances))


    def count_cluster_cohesion(self, cluster):
        emb_matrix = np.array([img.embedding for img in cluster.images_list])
        centroid = np.mean(emb_matrix)
        #вычисление расстояния от каждой точки до центроида
        distances = np.linalg.norm(emb_matrix - centroid, axis=1)
        #среднее расстояние - компактность
        return float(np.mean(distances))


    def count_cluster_silhouette(self, cluster, session):
        silhouette_values, labels = self.count_point_silhouettes(session)
        if silhouette_values is None:
            return None

        mask = (np.array(labels) == cluster.id)
        cluster_silhouette = silhouette_values[mask]
        return float(np.average(cluster_silhouette))

    def count_point_silhouettes(self, session):
        if len(session.clusters_list) <= 1:
            return None, None

        emb_matrix = []
        labels = []
        # получаем матрицу эмбеддингов и метку кластера для каждого из них
        for clus in session.clusters_list:
            for img in clus.images_list:
                emb_matrix.append(img.embedding)
                labels.append(clus.id)
        # вычисляем силуэт
        silhouette_values = silhouette_samples(emb_matrix, labels, metric='euclidean')

        return silhouette_values, labels




    #АНАЛИЗ КАЧЕСТВА ИЗОБРАЖЕНИЙ
    def get_medium_noiseLevel(self, images):
        noise_level = 0
        count = 0
        for img in images:
            if img.quality_params['noise_level']:
                noise_level += img.quality_params['noise_level']
                count += 1

        return noise_level / count

    def check_quality(self, images, params):
        for img in images:
            if img.quality_params['noise_level'] == None:
                print(img.id)
                print(img.filename)

        bad_quality = {}
        good_quality = []
        for img in images:
            bad_sides = []
            if img.quality_params['file_size'] < params['min_size']:
                bad_sides.append('low size')
            elif img.quality_params['file_size'] > params['max_size']:
                bad_sides.append('high size')
            if min(img.quality_params['resolution_width'],
                   img.quality_params['resolution_height']) < params['min_resolution']:
                bad_sides.append('low resolution')
            if img.quality_params['colors_amount'] < params['min_colors']:
                bad_sides.append('low colors amount')
            if img.quality_params['sharpness'] < params['min_sharpness']:
                bad_sides.append('low sharpness')
            if img.quality_params['noise_level'] > params['max_noise']:
                bad_sides.append('high noise level')
            if img.quality_params['contrast'] < params['min_contrast']:
                bad_sides.append('low contrast')

            if len(bad_sides) > 0:
                img.status = "quality_failed"
                bad_quality[img.filename] = bad_sides
            else:
                img.status = "quality_passed"
                good_quality.append(img.filename)

        return bad_quality



    def get_quality_char(self, img_path):
        # Пробуем через PIL сначала (для кириллицы)
        pil_img = Image.open(img_path)

        # Конвертируем в RGB для единообразия
        if pil_img.mode != 'RGB':
            pil_img = pil_img.convert('RGB')

        # Сохраняем для OpenCV (конвертируем PIL в OpenCV формат)
        img_cv = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

        # вычисляем все характеристики
        size = self.get_fileSize(img_path)
        resolution_width, resolution_height = self.get_resolution(pil_img)
        colors = self.get_colors(pil_img)
        sharpness = self.get_sharpness(img_cv)
        noise = self.get_noise(img_cv)
        contrast = self.get_contrast(img_cv)
        print("метод get_quality_char")
        print(f"DEBUG: colors = {colors}, тип = {type(colors)}")
        return {
            "file_size": size,
            "resolution_width": resolution_width,
            "resolution_height": resolution_height,
            "colors_amount": colors,
            "sharpness": sharpness,
            "noise_level": noise,
            "contrast": contrast
        }


    def get_fileSize(self, image):
        size_kb = os.path.getsize(image) / 1024
        return size_kb

    def get_resolution(self, image):
        return image.size

    def get_colors(self, image):
        colors = image.getcolors(maxcolors=1000)
        if colors:
            return len(colors)
        else:
            return 256


    def get_sharpness(self, image):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return cv2.Laplacian(gray, cv2.CV_64F).var()

    def get_noise(self, image):
        img_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        img_norm = img_rgb.astype(np.float32) / 255.0
        sigma_est = estimate_sigma(
            img_norm,
            channel_axis=-1,
            average_sigmas=True
        )
        if np.isnan(sigma_est):
            return 0.0
        return sigma_est

    def get_contrast(self, image):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        img_norm = gray.astype(np.float32) / 255.0
        return float(np.std(img_norm))

