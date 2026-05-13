import copy
import json

from PyQt6.QtWidgets import QApplication

from models.clasification_session import ClasificationSession
from models.cluster import Cluster
from models.dataset import Dataset
from models.image import Image
from models.session import Session
from repositories.anomaly_repositoty import AnomalyGroupRepository
from repositories.clasification_session_repository import ClassificationSessionRepository
from repositories.cluster_repository import ClusterRepository
from repositories.dataset_repository import DatasetRepository
from repositories.image_repository import ImageRepository
from repositories.modelVersion_repository import ModelVersionRepository
from repositories.session_repository import SessionRepository
from repositories.tag_repository import TagRepository
from services.drag_drop_service import DragDropService
from services.qualityAnalyse_service import QualityAnalyseService
from ui.interaction_subsystem.feedback_manager import FeedbackManager





class ObjectsManager:
    @staticmethod
    def load_data_fromDB(mainWindow):
        #загрузка датасетов
        dataset_repo = DatasetRepository(mainWindow.main_conn)
        users_datasets = dataset_repo.get_datasets_by_user(mainWindow.current_user.id)
        if users_datasets is not None:
            mainWindow.datasets_list = users_datasets

        #загрузка изображений и сессий
        image_repo = ImageRepository(mainWindow.main_conn)
        session_repo = SessionRepository(mainWindow.main_conn)
        cluster_repo = ClusterRepository(mainWindow.main_conn)
        tag_repo = TagRepository(mainWindow.main_conn)
        anomalyGroup_repo = AnomalyGroupRepository(mainWindow.main_conn)
        classification_session_repo = ClassificationSessionRepository(mainWindow.main_conn)

        # загрузка данных о модели
        modelVersion_repo = ModelVersionRepository(mainWindow.main_conn, mainWindow.project_root)
        mainWindow.models_data = modelVersion_repo.load_all_versions()

        for dataset in mainWindow.datasets_list:
            #изображения
            images_in_dataset = image_repo.get_images_by_dataset(dataset.id)
            for img in images_in_dataset:
                img.tags_list = tag_repo.get_tags_by_image(img.id, dataset.id)
            if images_in_dataset is not None:
                dataset.images_list = images_in_dataset
            #сессии
            sessions_on_dataset = session_repo.get_sessions_by_dataset(dataset.id)
            if sessions_on_dataset is not None:
                dataset.sessions_list = sessions_on_dataset
                dataset.sessions_count = len(sessions_on_dataset)
            #кластеры и аномалии для каждой сессии
            for session in sessions_on_dataset:
                clusters_in_session = cluster_repo.get_clusters_by_session(session.id)
                if clusters_in_session is not None:
                    # изображения в каждом кластере
                    for cluster in clusters_in_session:
                        images_in_cluster = image_repo.get_images_by_cluster(cluster.id, dataset.id)
                        found_images = []
                        for img in images_in_cluster:
                            img_in_dataset = ObjectsManager.find_image_by_id(dataset, img.id)
                            found_images.append(img_in_dataset)
                        if found_images is not None:
                            cluster.images_list = found_images
                            cluster.count_images = len(found_images)
                    session.clusters_list = clusters_in_session
                anomalyGroup_in_session = anomalyGroup_repo.get_anomalyGroup_by_session(session.id)
                if anomalyGroup_in_session is not None:
                    images_in_anomalyGroup = image_repo.get_images_by_anomalyGroup(anomalyGroup_in_session.id, dataset.id)
                    found_images = []
                    for img in images_in_anomalyGroup:
                        img_in_dataset = ObjectsManager.find_image_by_id(dataset, img.id)
                        found_images.append(img_in_dataset)
                    if found_images is not None:
                        anomalyGroup_in_session.images_list = found_images
                    session.anomaly_group = anomalyGroup_in_session

            #сессии классификации НС
            classification_sessions = classification_session_repo.get_sessions_by_datasetId(dataset.id)
            if classification_sessions is not None:
                #Заполняем группы сессии НС
                for cl_session in classification_sessions:
                    labels = classification_session_repo.get_session_labels(cl_session.id)
                    #labels = []
                    #for model in mainWindow.models_data:
                        #if cl_session.model_id == model.id:
                            #labels = model.label_map
                    if labels:
                        cl_session.create_images_labels_dict(labels)
                    items = image_repo.get_images_by_classification_session(cl_session.id)
                    for item in items:
                        img_in_dataset = ObjectsManager.find_image_by_id(dataset, item['image_id'])
                        if img_in_dataset is not None:
                            cl_session.images_labels[item['label']].append([img_in_dataset, item['confidence']])
                dataset.classification_groups = classification_sessions
        return

    @staticmethod
    def create_dataset(mainWindow, name, user_id):
        existing_names = [dt.name for dt in mainWindow.datasets_list]
        if name in existing_names:
            FeedbackManager.DatasetAlreadyExists(mainWindow)
            return
        new_dataset = Dataset(name, None, user_id)
        dataset_repo = DatasetRepository(mainWindow.main_conn)
        saved_dataset = dataset_repo.create_dataset(name, None, user_id)

        mainWindow.datasets_list.append(saved_dataset)
        mainWindow.update_ui()
        mainWindow.tree_model.add_dataset(new_dataset)

    @staticmethod
    def change_imageCluster(mainWindow, source_cluster, target_cluster, image_id, dataset):
        image = ObjectsManager.find_image_by_id(dataset, image_id)
        if image in target_cluster.images_list:
            FeedbackManager.ImageExists_Warning(mainWindow, image.filename)
            return False

        target_cluster.images_list.append(image)
        source_cluster.images_list.remove(image)
        source_cluster.count_images -= 1
        target_cluster.count_images += 1

        image_repo = ImageRepository(mainWindow.main_conn)
        image_repo.change_cluster(image, source_cluster, target_cluster)

        mainWindow.update_ui()
        return True

    @staticmethod
    def moveImage_fromCluster_toAnomalies(mainWindow, source_cluster, target_group, image_id, dataset):
        image = ObjectsManager.find_image_by_id(dataset, image_id)
        if image in target_group.images_list:
            FeedbackManager.ImageExists_Warning(mainWindow, image.filename)
            return False

        target_group.images_list.append(image)
        source_cluster.images_list.remove(image)
        source_cluster.count_images -= 1

        image_repo = ImageRepository(mainWindow.main_conn)
        image_repo.moveImages_fromCluster_toAnomalies(image, source_cluster, target_group)

        mainWindow.update_ui()
        return True

    @staticmethod
    def moveImages_between_labelGroups(mainWindow, source_group_label, target_group_label, session, image_id):
        source = session.images_labels[source_group_label]
        if target_group_label == 'Другое':
            target = session.images_labels['Не в кадре']
        else:
            target = session.images_labels[target_group_label]
        dataset = ObjectsManager.find_dataset_by_id(mainWindow, session.dataset_id)
        image = ObjectsManager.find_image_by_id(dataset, image_id)

        target.append([image, 0])
        for item in source:
            if item[0] == image:
                source.remove(item)
                break

        classification_session_repo = ClassificationSessionRepository(mainWindow.main_conn)
        classification_session_repo.change_image_label(dataset.id, session.id, image_id, target_group_label)

        mainWindow.update_ui()
        return True


    @staticmethod
    def moveImage_fromAnomalies_toCluster(mainWindow, source_group, target_cluster, image_id, dataset):
        image = ObjectsManager.find_image_by_id(dataset, image_id)
        if image in target_cluster.images_list:
            FeedbackManager.ImageExists_Warning(mainWindow, image.filename)
            return False

        target_cluster.images_list.append(image)
        source_group.images_list.remove(image)
        target_cluster.count_images += 1

        image_repo = ImageRepository(mainWindow.main_conn)
        image_repo.moveImage_fromAnomalies_toCluster(image, source_group, target_cluster)

        mainWindow.update_ui()
        return True

    @staticmethod
    def show_only_clusterized_datasets(mainWindow):
        datasets = [dt for dt in mainWindow.datasets_list if len(dt.sessions_list) > 0]
        mainWindow.show_datasets(datasets)

    @staticmethod
    def show_sessions_with_algorythm(mainWindow, algorythm):
        sessions = [sn for sn in mainWindow.currentDataset.sessions_list if sn.algorythm == algorythm]
        mainWindow.show_sessions(mainWindow.currentDataset, sessions)

    @staticmethod
    def show_only_tagged_images(mainWindow):
        if mainWindow.currentMode == "images_in_dataset":
            images = [img for img in mainWindow.currentDataset.images_list if len(img.tags_list) > 0]
            mainWindow.open_dataset(mainWindow.currentDataset, images)
        elif mainWindow.currentMode == "images_in_cluster":
            images = [img for img in mainWindow.currentCluster.images_list if len(img.tags_list) > 0]
            mainWindow.open_cluster(mainWindow.currentCluster, images)
        elif mainWindow.currentMode == "anomalies":
            images = [img for img in mainWindow.currentAnomalies.images_list if len(img.tags_list) > 0]
            mainWindow.open_anomalyGroup(mainWindow.currentAnomalies, images)
        elif mainWindow.currentMode == "images_in_classificationSession":
            images = [img[0] for img in mainWindow.currentClassifSession.images_labels[mainWindow.currentGroupLabel]
                      if len(img[0].tags_list) > 0]
            mainWindow.on_classificationGroup_double_clicked(mainWindow.currentClassifSession,
                                                             images, mainWindow.currentGroupLabel)
    @staticmethod
    def show_only_noTags_images(mainWindow):
        if mainWindow.currentMode == "images_in_dataset":
            images = [img for img in mainWindow.currentDataset.images_list if len(img.tags_list) == 0]
            mainWindow.open_dataset(mainWindow.currentDataset, images)
        elif mainWindow.currentMode == "images_in_cluster":
            images = [img for img in mainWindow.currentCluster.images_list if len(img.tags_list) == 0]
            mainWindow.open_cluster(mainWindow.currentCluster, images)
        elif mainWindow.currentMode == "anomalies":
            images = [img for img in mainWindow.currentAnomalies.images_list if len(img.tags_list) == 0]
            mainWindow.open_anomalyGroup(mainWindow.currentAnomalies, images)
        elif mainWindow.currentMode == "images_in_classificationSession":
            images = [img[0] for img in mainWindow.currentClassifSession.images_labels[mainWindow.currentGroupLabel]
                      if len(img[0].tags_list) == 0]
            mainWindow.on_classificationGroup_double_clicked(mainWindow.currentClassifSession,
                                                             images, mainWindow.currentGroupLabel)


    @staticmethod
    def show_only_withStatus(mainWindow, status):
        if mainWindow.currentMode == "images_in_dataset":
            images = [img for img in mainWindow.currentDataset.images_list if img.status == status]
            mainWindow.open_dataset(mainWindow.currentDataset, images)
        elif mainWindow.currentMode == "images_in_cluster":
            images = [img for img in mainWindow.currentCluster.images_list if img.status == status]
            mainWindow.open_cluster(mainWindow.currentCluster, images)
        elif mainWindow.currentMode == "anomalies":
            images = [img for img in mainWindow.currentAnomalies.images_list if img.status == status]
            mainWindow.open_anomalyGroup(mainWindow.currentAnomalies, images)
        elif mainWindow.currentMode == "images_in_classificationSession":
            images = [img[0] for img in mainWindow.currentClassifSession.images_labels[mainWindow.currentGroupLabel]
                      if img[0].status == status]
            mainWindow.on_classificationGroup_double_clicked(mainWindow.currentClassifSession,
                                                             images, mainWindow.currentGroupLabel)


    @staticmethod
    def show_all(mainWindow):
        if mainWindow.currentMode == 'datasets':
            mainWindow.show_datasets(mainWindow.datasets_list)
        elif mainWindow.currentMode == 'images_in_dataset':
            mainWindow.open_dataset(mainWindow.currentDataset, mainWindow.currentDataset.images_list)
        elif mainWindow.currentMode == "sessions_on_dataset":
            mainWindow.show_sessions(mainWindow.currentDataset, mainWindow.currentDataset.sessions_list)
        elif mainWindow.currentMode == "images_in_cluster":
            mainWindow.open_cluster(mainWindow.currentCluster, mainWindow.currentCluster.images_list)
        elif mainWindow.currentMode == "anomalies":
            mainWindow.open_anomalyGroup(mainWindow.currentAnomalies, mainWindow.currentAnomalies.images_list)
        elif mainWindow.currentMode == "clusters":
            mainWindow.open_session(mainWindow.currentSession, mainWindow.currentSession.clusters_list)
        elif mainWindow.currentMode == "images_in_classificationSession":
            label = mainWindow.currentGroupLabel
            images = [img[0] for img in mainWindow.currentClassifSession.images_labels[label]]
            mainWindow.on_classificationGroup_double_clicked(mainWindow.currentClassifSession,
                                                             images,
                                                             mainWindow.currentGroupLabel)
        elif mainWindow.currentMode == "classification_sessions":
            mainWindow.show_classification_sessions(mainWindow.currentDataset,
                                                    mainWindow.currentDataset.classification_groups)

    @staticmethod
    def sort_datasets_by_imageAmount(datasets, mainWindow):
        datasets.sort(key=lambda ds: len(ds.images_list), reverse=True)
        mainWindow.show_datasets(datasets)

    @staticmethod
    def sort_labeledGroups_by_imageAmount(session, mainWindow):
        group_names = [gr for gr in session.images_labels]
        groups = [gr for gr in session.images_labels.values()]
        paired = sorted(zip(group_names, groups), key=lambda x: len(x[1]), reverse=True)
        group_names_sorted, groups_sorted = zip(*paired) if paired else ([], [])

        group_names_sorted = list(group_names_sorted)
        groups_sorted = list(groups_sorted)
        mainWindow.on_classification_session_double_clicked(session, groups_sorted, names=group_names_sorted)

    @staticmethod
    def sort_sessions_by_clustersAmount(sessions, mainWindow):
        sessions.sort(key=lambda sn: len(sn.clusters_list), reverse=True)
        mainWindow.show_sessions(mainWindow.currentDataset, sessions)

    @staticmethod
    def sort_clusters_by_imageAmount(clusters, mainWindow):
        clusters.sort(key=lambda cl: len(cl.images_list), reverse=True)
        mainWindow.open_session(mainWindow.currentSession, clusters)

    @staticmethod
    def sort_datasets_by_sessionAmount(datasets, mainWindow):
        datasets.sort(key=lambda ds: len(ds.sessions_list), reverse=True)
        mainWindow.show_datasets(datasets)
    @staticmethod
    def sort_sessions_by_name(sessions, mainWindow):
        sessions.sort(key=lambda sn: sn.name)
        mainWindow.show_sessions(mainWindow.currentDataset, sessions)

    @staticmethod
    def sort_classificationSessions_by_name(sessions, mainWindow):
        sessions.sort(key=lambda sn:sn.name)
        mainWindow.show_classification_sessions(mainWindow.currentDataset, sessions)

    @staticmethod
    def sort_classificationSessions_by_date(sessions, mainWindow):
        sessions.sort(key=lambda sn:sn.created_at, reverse=True)
        mainWindow.show_classification_sessions(mainWindow.currentDataset, sessions)

    @staticmethod
    def sort_clusters_by_name(clusters, mainWindow):
        clusters.sort(key=lambda cl: cl.name)
        mainWindow.open_session(mainWindow.currentSession, clusters)

    @staticmethod
    def sort_datasets_by_name(datasets, mainWindow):
        datasets.sort(key=lambda ds: ds.name)
        mainWindow.show_datasets(datasets)

    @staticmethod
    def sort_images_by_name(images, mainWindow, parent):
        images.sort(key=lambda img: img.filename)
        if parent == "dataset":
            mainWindow.open_dataset(mainWindow.currentDataset, images)
        elif parent == "cluster":
            mainWindow.open_cluster(mainWindow.currentCluster, images)
        elif parent == "anomaliesGroup":
            mainWindow.open_anomalyGroup(mainWindow.currentAnomalies, images)
        elif parent == "labeled_group":
            mainWindow.on_classificationGroup_double_clicked(mainWindow.currentClassifSession,
                                                             images,
                                                             mainWindow.currentGroupLabel)


    @staticmethod
    def sort_sessions_by_creationTime(sessions, mainWindow):
        sessions.sort(key=lambda sn: sn.created_at, reverse=True)
        mainWindow.show_sessions(mainWindow.currentDataset, sessions)

    @staticmethod
    def sort_images_by_uploadTime(images, mainWindow, parent):
        images.sort(key=lambda img: img.uploaded_at, reverse=True)
        if parent == "dataset":
            mainWindow.open_dataset(mainWindow.currentDataset, images)
        elif parent == "cluster":
            mainWindow.open_cluster(mainWindow.currentCluster, images)
        elif parent == "anomaliesGroup":
            mainWindow.open_anomalyGroup(mainWindow.currentAnomalies, images)
        elif parent == "labeled_group":
            mainWindow.on_classificationGroup_double_clicked(mainWindow.currentClassifSession,
                                                             images,
                                                             mainWindow.currentGroupLabel)

    @staticmethod
    def sort_datasets_by_creationTime(datasets, mainWindow):
        datasets.sort(key=lambda ds: ds.created_at, reverse=True)
        mainWindow.show_datasets(datasets)

    @staticmethod
    def get_cluster_params(cluster, session, mainWindow):
        #расчет параметров
        qualityAnalyse_service = QualityAnalyseService(mainWindow.db)
        params = qualityAnalyse_service.get_claster_qualityParams(cluster, session)

        #сохранение в БД
        cluster_repo = ClusterRepository(mainWindow.main_conn)
        cluster_repo.save_params(params, cluster.id)

        return params

    @staticmethod
    def get_session_params(session, mainWindow):
        #расчет параметров
        qualityAnalyse_service = QualityAnalyseService(mainWindow.db)
        params = qualityAnalyse_service.get_session_qualityParams(session)

        #сохранение в БД
        session_repo = SessionRepository(mainWindow.main_conn)
        session_repo.save_quality_params(params, session.id)

        return params



    @staticmethod
    def get_embeddings_clusterLabels(clusters_list, anomaly_group=None):
        embeddings = []
        labels = []

        for cluster in clusters_list:
            cluster_embeddings = [img.embedding for img in cluster.images_list]
            embeddings = embeddings + cluster_embeddings
            cluster_labels = [cluster.name] * len(cluster.images_list)
            labels = labels + cluster_labels

        if anomaly_group:
            group_embeddings = [img.embedding for img in anomaly_group.images_list]
            embeddings = embeddings + group_embeddings
            anomaly_labels = ["Аномалии"] * len(group_embeddings)
            labels = labels + anomaly_labels

        return embeddings, labels

    @staticmethod
    def get_clusters_sizes(clusters_list, anomaly_group=None):
        cluster_size = {}
        for cluster in clusters_list:
            cluster_size[cluster.name] = len(cluster.images_list)

        if anomaly_group:
            cluster_size["Аномалии"] = len(anomaly_group.images_list)
        return cluster_size

    @staticmethod
    def delete_sessions(mainWindow, sessions):
        #удаляем из БД
        session_repo = SessionRepository(mainWindow.main_conn)
        session_repo.delete_sessions([session.id for session in sessions])
        #удаляем из ui
        dataset = ObjectsManager.find_dataset_by_id(mainWindow, sessions[0].dataset_id)
        dataset.remove_sessions(sessions.copy())
        if mainWindow.currentSession in sessions:
            mainWindow.currentSession = None
        mainWindow.tree_model.delete_sessions(sessions, dataset)

    @staticmethod
    def add_tags_toImages(mainWindow, images):
        tag = FeedbackManager.get_tag(mainWindow)
        if tag:
            #СОХРАНЕНИЕ В БД
            #создание или поиск тега
            tag_repo = TagRepository(mainWindow.main_conn)
            created_tag = tag_repo.create_tag(tag)

            #ищем id всех пар изображение-датасет, к которым надо присвоить тег
            image_repo = ImageRepository(mainWindow.main_conn)
            images_ids = [img.id for img in images]
            pair_ids = image_repo.get_imageDataset_Pair_Ids(images_ids, mainWindow.currentDataset.id)

            #присваиваем тег изображениям в выбранном датасете
            tag_repo.set_tag_toImages(created_tag.id, pair_ids)

            #СОХРАНЕНИЕ В UI
            for img in images:
                img.tags_list.append(created_tag)
                created_tag.images_list.append(img)

            mainWindow.update_ui()


    @staticmethod
    def copy_images(mainWindow, images):
        mime_data = DragDropService.create_mimeData_fromImages(images, mainWindow.currentDataset.id)
        #Копирование в буфер обмена
        QApplication.clipboard().setMimeData(mime_data)
        mainWindow.images_copied = True
        mainWindow.dataset_copied = False

    @staticmethod
    def copy_dataset(mainWindow, dataset):
        mime_data = dataset.create_mimeData()
        QApplication.clipboard().setMimeData(mime_data)
        mainWindow.dataset_copied = True
        mainWindow.images_copied = False

    @staticmethod
    def paste_dataset(mainWindow):
        if mainWindow.currentMode == 'datasets' and mainWindow.dataset_copied:
            mime_data = QApplication.clipboard().mimeData()
            dataset_data_bytes = mime_data.data(Dataset.DATASET_MIME_TYPE)
            dataset_data = json.loads(dataset_data_bytes.data().decode())

            #создание копии датасета
            dataset_item = ObjectsManager.find_dataset_by_id(mainWindow, dataset_data['dataset_id'])
            dataset_repo = DatasetRepository(mainWindow.main_conn)
            new_dataset = None
            #подбор нового имени копии
            if len(dataset_item.name) >=5 and "копия" in dataset_item.name:
                digits = "1234567890"
                i = -1
                while dataset_item.name[i] in digits:
                    i-=1
                i+=1
                if i!=0:
                    count_copies = int(dataset_item.name[i:]) + 1
                    new_name = f"{dataset_item.name[:i]}{count_copies}"
                else:
                    new_name = dataset_item.name
            else:
                new_name = f"{dataset_item.name}-копия"
            count = 2
            while new_dataset is None:
                new_dataset = dataset_repo.create_dataset(f"{new_name}{count}",
                                                          dataset_item.file_path,
                                                          dataset_item.user_id, dataset_item.images_list)
                count += 1

            mainWindow.datasets_list.append(new_dataset)
            mainWindow.update_ui()
            mainWindow.tree_model.add_dataset(new_dataset)
        else:
            FeedbackManager.UnsupportedDirectory_Warning(mainWindow)

    @staticmethod
    def delete_dataset(mainWindow, dataset):
        #удаление из БД
        dataset_repo = DatasetRepository(mainWindow.main_conn)
        dataset_repo.delete(dataset.id)
        #удаление из ui
        mainWindow.datasets_list.remove(dataset)
        mainWindow.update_ui()
        mainWindow.tree_model.delete_dataset(dataset)

    @staticmethod
    def delete_anomalyGroup(mainWindow, session, anomalyGroup):
        #удаление из БД
        anomalyGroup_repo =AnomalyGroupRepository(mainWindow.main_conn)
        anomalyGroup_repo.delete_group(session.anomaly_group.id)
        #удаление из ui
        session.anomaly_group = None
        if mainWindow.currentAnomalies == session.anomaly_group:
            mainWindow.currentAnomalies = None
            mainWindow.prev_page()
        mainWindow.update_ui()
        dataset = ObjectsManager.find_dataset_by_id(mainWindow, session.dataset_id)
        mainWindow.tree_model.delete_anomalyGroup(session, dataset)


    @staticmethod
    def delete_classificationGroup(mainWindow, session, group_name):
        #удаление из БД
        classifSession_repo = ClassificationSessionRepository(mainWindow.main_conn)
        classifSession_repo.delete_group(group_name, session.id)
        #удаление из ui
        session.images_labels[group_name] = None
        del session.images_labels[group_name]
        if mainWindow.currentGroupLabel == group_name and mainWindow.currentClassifSession == session:
            mainWindow.prev_page()
            mainWindow.currentGroupLabel = None
        dataset = ObjectsManager.find_dataset_by_id(mainWindow, session.dataset_id)
        mainWindow.tree_model.delete_classificationGroup(session, group_name, dataset)
        mainWindow.update_ui()


    @staticmethod
    def delete_cluster(mainWindow, cluster, session=None):
        #удаление из БД
        cluster_repo = ClusterRepository(mainWindow.main_conn)
        cluster_repo.delete_cluster(cluster.id)
        #удаление из ui
        if not session:
            session = mainWindow.currentSession
        session.clusters_list.remove(cluster)
        if mainWindow.currentCluster == cluster:
            mainWindow.currentCluster = None

        session = ObjectsManager.find_session_by_id(mainWindow, cluster.session_id)
        dataset = ObjectsManager.find_dataset_by_id(mainWindow, session.dataset_id)
        mainWindow.update_ui()
        #mainWindow.open_session(session, session.clusters_list, True)
        mainWindow.tree_model.delete_cluster(cluster, session, dataset)


    @staticmethod
    def find_dataset_by_id(mainWindow, dataset_id):
        for dataset in mainWindow.datasets_list:
            if dataset.id == dataset_id:
                return dataset
        return None

    @staticmethod
    def add_imageCopy_to_dataset(parent, dataset, image_info):
        old_dataset = ObjectsManager.find_dataset_by_id(parent, image_info['dataset_id'])
        img_item = ObjectsManager.find_image_by_id(old_dataset, image_info['image_id'])

        #сохраняем изменения в БД
        #формируем имя для изобржения
        #проверка есть ли изображение в целевом датасете
        image_exists = ObjectsManager.find_image_by_id(dataset, img_item.id)
        if not image_exists:
            dataset_repo = DatasetRepository(parent.main_conn)
            dataset_repo.add_existing_image(img_item, dataset.id)
            new_image = copy.deepcopy(img_item)
            new_image.status = "uploaded"
        else:
            image_repo = ImageRepository(parent.main_conn)
            image_name = f"{img_item.filename}-копия"
            new_image = image_repo.create_image(image_name, img_item.filepath, img_item.format,
                                    dataset.id, img_item.embedding, img_item.quality_params)

        # добавляем изображение в целевой датасет
        new_image.dataset_id = dataset.id
        new_image.tags_list = []
        dataset.images_list.append(new_image)

        parent.tree_model.add_images(dataset, [new_image])



    @staticmethod
    def rename_item(item, mainWindow, dataset=None):
        new_name = FeedbackManager.get_new_name(item)
        if new_name:
            if type(item) == Image:
                old_name = item.filename
                item.filename = new_name
                image_repo = ImageRepository(mainWindow.main_conn)
                image_repo.change_name(item, new_name)
                mainWindow.tree_model.rename_image(dataset, new_name, old_name)
            elif type(item) == Dataset:
                old_name = item.name
                item.name = new_name
                dataset_repo = DatasetRepository(mainWindow.main_conn)
                dataset_repo.change_name(new_name, item)
                mainWindow.tree_model.rename_dataset(new_name, old_name)
            elif type(item) == Session:
                old_name = item.name
                item.name = new_name
                session_repo = SessionRepository(mainWindow.main_conn)
                session_repo.change_name(new_name, item.id)

                dataset = ObjectsManager.find_dataset_by_id(mainWindow, item.dataset_id)
                mainWindow.tree_model.rename_session(dataset, new_name, old_name)
            elif type(item) == Cluster:
                old_name = item.name
                item.name = new_name
                cluster_repo = ClusterRepository(mainWindow.main_conn)
                cluster_repo.rename_cluster(new_name, item.id)

                session = ObjectsManager.find_session_by_id(mainWindow, item.session_id)
                dataset = ObjectsManager.find_dataset_by_id(mainWindow, session.dataset_id)
                mainWindow.tree_model.rename_cluster(dataset, session, new_name, old_name)

            elif type(item) == ClasificationSession:
                old_name = item.name
                item.name = new_name
                classification_session_repo = ClassificationSessionRepository(mainWindow.main_conn)
                classification_session_repo.rename_session(new_name, item.id)

                dataset = ObjectsManager.find_dataset_by_id(mainWindow, item.dataset_id)
                mainWindow.tree_model.rename_classification_session(item, dataset, new_name, old_name)

        mainWindow.update_ui()


    @staticmethod
    def delete_classificationSessions(mainWindow, sessions):
        if len(sessions) > 0:
            #Удаление из БД
            ids = [sn.id for sn in sessions]
            classification_session_repo = ClassificationSessionRepository(mainWindow.main_conn)
            classification_session_repo.delete_session(ids)

            #Удаление из ui
            dataset = ObjectsManager.find_dataset_by_id(mainWindow, sessions[0].dataset_id)

            new_list = [sn for sn in sessions if sn.id not in ids]
            dataset.classification_groups = new_list
            if mainWindow.currentClassifSession in sessions:
                mainWindow.currentClassifSession = None

            mainWindow.tree_model.delete_classification_sessions(sessions, dataset)
            mainWindow.update_ui()



    @staticmethod
    def find_dataset_from_tree(mainWindow, dataset_name):
        for dataset in mainWindow.datasets_list:
            if dataset.name == dataset_name:
                return dataset
        return None

    @staticmethod
    def find_image_by_id(dataset, image_id):
        for img in dataset.images_list:
            if img.id == image_id:
                return img
        return None
    @staticmethod
    def find_session_by_id(mainWindow, session_id):
        for dataset in mainWindow.datasets_list:
            for session in dataset.sessions_list:
                if session_id == session.id:
                    return session
        return None

    @staticmethod
    def find_session_from_tree(dataset, session_name):
        for session in dataset.sessions_list:
            if session.name == session_name:
                return session
        return None

    @staticmethod
    def find_classificationSession_by_name(dataset, name):
        for session in dataset.classification_groups:
            if session.name == name:
                return session
        return None

    @staticmethod
    def find_cluster_from_tree(session, cluster_name):
        for cluster in session.clusters_list:
            if cluster_name == cluster.name:
                return cluster
        return None

    @staticmethod
    def find_image_by_name(dataset, name):
        name = name.strip()
        for img in dataset.images_list:
            if img.filename == name:
                return img

    @staticmethod
    def set_status_deleted(images):
        for img in images:
            img.status = "deleted"

    @staticmethod
    def update_imagesStatus(mainWindow, images, dataset_id):
        image_repo = ImageRepository(mainWindow.main_conn)
        image_repo.update_status(images, dataset_id)




