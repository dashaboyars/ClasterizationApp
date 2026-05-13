import json
import shutil
import struct

import onnx

from models.session import Session
from ui.dialogs.modelName_dialog import ModelNameDialog
from ui.dialogs.modelParams_dialog import ModelParamsDialog

print(struct.calcsize("P") * 8)

import onnxruntime
print(onnxruntime.__version__)
import tempfile
import os
from datetime import datetime

from repositories.modelVersion_repository import ModelVersionRepository
from services.clasifier_service import ENTClassifier

# Создаём папку для временных файлов прямо в корне проекта
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CUSTOM_TEMP = os.path.join(PROJECT_ROOT, 'temp_for_onnx2torch2')
os.makedirs(CUSTOM_TEMP, exist_ok=True)
tempfile.tempdir = CUSTOM_TEMP

# Дополнительно: явно указываем переменную окружения для TMPDIR
os.environ['TMPDIR'] = CUSTOM_TEMP
os.environ['TEMP'] = CUSTOM_TEMP
os.environ['TMP'] = CUSTOM_TEMP

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import *
from PyQt6 import uic

from models.dataset import Dataset
from services.clasterization_service import ClusterizationService
from services.drag_drop_service import DragDropService
from services.duplicate_detector import DuplicateDetector
from services.embedding_calculator import EmbeddingCalculator
from services.export_service import ExportService
from services.qualityAnalyse_service import QualityAnalyseService
from ui.dialogs.duplicates_dialog import DuplicatesDialog
from ui.dialogs.qualityAnalyse_results_dialog import QualityAnalyseResultsDialog
from ui.dialogs.quality_params_dialog import QualityParamsDialog
from ui.interaction_subsystem.feedback_manager import FeedbackManager
from ui.interaction_subsystem.menu_manager import MenuManager
from ui.interaction_subsystem.objects_manager import ObjectsManager
from ui.visualization_subsystem.charts_visualization.DistributionWidget import DistributionWidget
from ui.visualization_subsystem.dataset_viewer import WidgetViewer
from ui.visualization_subsystem.image_viewer_new import ImageViewer
from ui.visualization_subsystem.tree_model import TreeModel
from services.import_service import ImportService
from ui.dialogs.select_dataset_dialog import SelectDatasetDialog
from workers.import_thread import BackgroundThread


class MainWindow(QMainWindow):
    def __init__(self, db, user):
        super().__init__()
        uic.loadUi('gui/main_window.ui', self)

        self.stackedWidget = self.findChild(QStackedWidget, "stackedWidget")
        self.fullScreen_scrollArea = self.stackedWidget.findChild(QScrollArea, "fullScreen_scrollArea")
        self.partial_scrollArea = self.stackedWidget.findChild(QScrollArea, "partial_scrollArea")
        self.visualization_frame = self.stackedWidget.findChild(QFrame, "visualization_frame")

        # Устанавливаем первую страницу
        self.stackedWidget.setCurrentIndex(1)

        #Потоки
        self.threads = {}
        self.progress_bars = {}  # словарь для хранения прогресс-баров
        self.operation_counter = 0

        # Сохраняем зависимости
        self.db = db
        self.main_conn = db.connect()
        self.current_user = user

        # Сервисы
        self.embedding_calculator = EmbeddingCalculator('B0')
        self.quality_analyse_service = QualityAnalyseService(self.db)
        self.import_service = ImportService(self.db, self.embedding_calculator, self.quality_analyse_service)
        self.export_service = ExportService(self.db)
        self.duplicate_detector = DuplicateDetector(self.db)
        self.clusterization_service = ClusterizationService(self.db)
        self.modelClasify_service = None

        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.project_root = os.path.dirname(current_dir)  # .../ (корень)

        #загрузка данных из БД
        self.datasets_list = []
        self.models_data = []
        self.load_data()

        # Настраиваем интерфейс
        self.currentMode = ""
        self.currentDataset = None
        self.currentSession = None
        self.currentCluster = None
        self.currentAnomalies = None
        self.currentClassifSession=None
        self.currentGroupLabel = None
        self.tree_view = None
        self.tree_model = None
        self.search_line = self.findChild(QLineEdit, "search_line")
        self.currentPath_lineEdit = self.findChild(QLineEdit, "currentPath_lineEdit")
        self.searchKey_comboBox = self.findChild(QComboBox, "comboBox")
        self.search_line.returnPressed.connect(self.on_search_return_pressed)

        self.opened_windows = []

        self.currentMode_changed.connect(self.on_currentMode_changed)

        self.images_copied = False
        self.dataset_copied = False
        self.setup_ui()
        print(f"👋 Добро пожаловать, {user.username}!")

    currentMode_changed = pyqtSignal()

    def load_new_model(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите ONNX модель", "", "ONNX Files (*.onnx)"
        )

        if not file_path:
            return

        model_name_dialog = ModelNameDialog(self)
        if model_name_dialog.exec() == QDialog.DialogCode.Accepted:
            name = model_name_dialog.name
            if name:
                # загрузка модели из файла
                dest_folder = os.path.join(self.project_root, 'clasify_models')
                os.makedirs(dest_folder, exist_ok=True)
                dest_path = os.path.join(dest_folder, os.path.basename(file_path))
                shutil.copy2(file_path, dest_path)

                # считываем метки из файла и загружаем в БД
                onnx_model = onnx.load(dest_path)
                meta = {p.key: p.value for p in onnx_model.metadata_props}
                labels = meta.get('labelmap_ru', "Unknown")
                labels_str = json.loads(labels)

                modelVersion_repo = ModelVersionRepository(self.main_conn)
                new_model = modelVersion_repo.save_new_version(dest_path, labels_str, name)
                self.models_data.append(new_model)

    def get_active_model(self):
        for mv in self.models_data:
            if mv.is_active:
                return mv

    def create_dataset(self):
        name = FeedbackManager.get_new_name(self)
        if name:
            ObjectsManager.create_dataset(self, name, self.current_user.id)

    def on_currentMode_changed(self):
        #обновление comboBox для поиска
        self.update_searchKey_comboBox()
        #обновление меню сортировки
        MenuManager.setup_menu(self)
        #Изменение текущего пути
        self.set_currentPath()

        #изменение текущей страницы в stackedWidget
        if self.currentMode == "clusters" or self.currentMode == "images_in_cluster":
            self.stackedWidget.setCurrentIndex(0)
            if self.currentMode == "clusters":
                cluster_sizes = ObjectsManager.get_clusters_sizes(self.currentSession.clusters_list,
                                                                  self.currentSession.anomaly_group)
                embeddings, labels = ObjectsManager.get_embeddings_clusterLabels(self.currentSession.clusters_list,
                                                                                 self.currentSession.anomaly_group)
            else:
                cluster_sizes = ObjectsManager.get_clusters_sizes([self.currentCluster])
                embeddings, labels = ObjectsManager.get_embeddings_clusterLabels([self.currentCluster])
            if self.currentMode == "clusters":
                self.distr_widget.update_pie_chart(cluster_sizes)
            self.distr_widget.update_embedding_map(embeddings, labels)
        else:
            self.stackedWidget.setCurrentIndex(1)

    def set_currentPath(self):
        text = ""
        if not self.currentDataset:
            text = "Датасеты/"
        elif self.currentCluster:
            text = self.currentDataset.name + "/" + self.currentSession.name + "/" + self.currentCluster.name + "/"
        elif self.currentAnomalies:
            text = self.currentDataset.name + "/" + self.currentSession.name + "/" + self.currentAnomalies.name + "/"
        elif self.currentSession:
            text = self.currentDataset.name + "/" + self.currentSession.name + "/"
        elif self.currentGroupLabel:
            text = self.currentDataset.name + "/" + self.currentClassifSession.name + "/" + self.currentGroupLabel
        elif self.currentClassifSession:
            text = self.currentDataset.name + "/" + self.currentClassifSession.name + "/"
        elif self.currentDataset:
            text = self.currentDataset.name + "/"

        self.currentPath_lineEdit.setText(text)



    def update_searchKey_comboBox(self):
        currentMode = self.searchKey_comboBox.currentText()
        self.searchKey_comboBox.clear()

        self.searchKey_comboBox.addItem("поиск по названию")
        if len(self.currentMode) >= 6 and self.currentMode[:6] == "images":
            self.searchKey_comboBox.addItem("поиск по тегам")
            if currentMode == "поиск по тегам":
                self.searchKey_comboBox.setCurrentIndex(1)


    def on_search_return_pressed(self):
        search_text = self.search_line.text().strip()
        if search_text == "":
            self.update_ui()
            return

        if self.searchKey_comboBox.currentText() == "поиск по названию":
            if self.currentMode == "datasets":
                self.search_in_datasets(search_text)
            elif self.currentMode == "sessions_on_dataset":
                self.search_in_sessions(search_text)
            elif self.currentMode == "clusters":
                self.search_in_clusters(search_text)
            elif self.currentMode == "images_in_dataset":
                self.search_in_datasetImages_byName(search_text)
            elif self.currentMode == "images_in_cluster":
                self.search_in_clusterImages_byName(search_text)
            elif self.currentMode == "classification_sessions":
                self.search_in_classificationSessions(search_text)
            elif self.currentMode == "labeled_groups":
                self.search_in_labeledGroups(search_text)
            elif self.currentMode == "images_in_classificationSession":
                self.search_in_images_ofClassificationSession_byName(search_text)
        elif self.searchKey_comboBox.currentText() == "поиск по тегам":
            if self.currentMode == "images_in_dataset":
                self.search_in_datasetImages_byTags(search_text)
            elif self.currentMode == "images_in_cluster":
                self.search_in_clusterImages_byTags(search_text)
            elif self.currentMode == "images_in_classificationSession":
                self.search_in_images_ofClassificationSession_byTags(search_text)

    def search_in_images_ofClassificationSession_byTags(self, search_text):
        items = []
        currentGroup = self.currentClassifSession.images_labels[self.currentGroupLabel]

        for item in currentGroup:
            img = item[0]
            for tag in img.tags_list:
                if search_text in tag.name:
                    items.append(item)
                    break


        self.on_classificationGroup_double_clicked(self.currentClassifSession, items,
                                                   self.currentGroupLabel,
                                                   search_text, "tags")

    def search_in_images_ofClassificationSession_byName(self, search_text):
        items = []
        currentGroup = self.currentClassifSession.images_labels[self.currentGroupLabel]

        for item in currentGroup:
            if search_text in item[0].filename:
                items.append(item)

        self.on_classificationGroup_double_clicked(self.currentClassifSession, items,
                                                   self.currentGroupLabel,
                                                   search_text, "name")

    def search_in_labeledGroups(self, search_text):
        groups_found = []
        if search_text in 'Ухо':
            groups_found.append(self.currentClassifSession.images_labels['Ухо'])
        if search_text in 'Нос':
            groups_found.append(self.currentClassifSession.images_labels['Нос'])
        if search_text in 'Глотка':
            groups_found.append(self.currentClassifSession.images_labels['Глотка'])
        if search_text in 'Гортань':
            groups_found.append(self.currentClassifSession.images_labels['Гортань'])
        if search_text in 'Не в кадре':
            groups_found.append(self.currentClassifSession.images_labels['Не в кадре'])
        self.on_classification_session_double_clicked(self.currentClassifSession, groups_found, search_text)

    def search_in_classificationSessions(self, search_text):
        sessions_found = []
        for sn in self.currentDataset.classification_groups:
            if search_text in sn.name:
                sessions_found.append(sn)
        self.show_classification_sessions(self.currentDataset, sessions_found, search_text)

    def search_in_clusterImages_byTags(self, search_text):
        images_found = []
        for img in self.currentCluster.images_list:
            for tag in img.tags_list:
                if search_text in tag.name:
                    images_found.append(img)
                    break
        self.open_cluster(self.currentCluster, images_found, False, search_text, "tags")

    def search_in_datasetImages_byTags(self, search_text):
        images_found = []
        for img in self.currentDataset.images_list:
            for tag in img.tags_list:
                if search_text in tag.name:
                    images_found.append(img)
                    break
        self.open_dataset(self.currentDataset, images_found, search_text, "tags")

    def search_in_clusterImages_byName(self, search_text):
        images_found = []
        for img in self.currentCluster.images_list:
            if search_text in img.filename:
                images_found.append(img)
        self.open_cluster(self.currentCluster, images_found, False, search_text, "name")

    def search_in_datasetImages_byName(self, search_text):
        images_found = []
        for img in self.currentDataset.images_list:
            if search_text in img.filename:
                images_found.append(img)
        self.open_dataset(self.currentDataset, images_found, search_text, "name")


    def search_in_clusters(self, search_text):
        clusters_found = []
        for cluster in self.currentSession.clusters_list:
            if search_text in cluster.name:
                clusters_found.append(cluster)
        self.open_session(self.currentSession, clusters_found, False, search_text)


    def search_in_sessions(self, search_text):
        sessions_found = []
        for session in self.currentDataset.sessions_list:
            if search_text in session.name:
                sessions_found.append(session)
        self.show_sessions(self.currentDataset, sessions_found, search_text)


    def search_in_datasets(self, search_text):
        datasets_found = []
        for dataset in self.datasets_list:
            if search_text in dataset.name:
                datasets_found.append(dataset)
        self.show_datasets(datasets_found, search_text)

    def sort_by_imageAmount(self):
        if self.currentMode == 'datasets':
            ObjectsManager.sort_datasets_by_imageAmount(self.datasets_list, self)
        elif self.currentMode == "clusters":
            ObjectsManager.sort_clusters_by_imageAmount(self.currentSession.clusters_list, self)
        elif self.currentMode == "labeled_groups":
            ObjectsManager.sort_labeledGroups_by_imageAmount(self.currentClassifSession, self)

    def sort_by_sessionsAmount(self):
        ObjectsManager.sort_datasets_by_sessionAmount(self.datasets_list, self)

    def sort_by_clustersAmount(self):
        ObjectsManager.sort_sessions_by_clustersAmount(self.currentDataset.sessions_list, self)

    def sort_by_name(self):
        if self.currentMode == 'datasets':
            ObjectsManager.sort_datasets_by_name(self.datasets_list, self)
        elif self.currentMode == 'images_in_dataset':
            ObjectsManager.sort_images_by_name(self.currentDataset.images_list, self, "dataset")
        elif self.currentMode == "sessions_on_dataset":
            ObjectsManager.sort_sessions_by_name(self.currentDataset.sessions_list, self)
        elif self.currentMode == "clusters":
            ObjectsManager.sort_clusters_by_name(self.currentSession.clusters_list, self)
        elif self.currentMode == "images_in_cluster":
            ObjectsManager.sort_images_by_name(self.currentCluster.images_list, self, "cluster")
        elif self.currentMode == "anomalies":
            ObjectsManager.sort_images_by_name(self.currentAnomalies.images_list, self, "anomaliesGroup")
        elif self.currentMode == "images_in_classificationSession":
            label = self.currentGroupLabel
            images = [img[0] for img in self.currentClassifSession.images_labels[label]]
            ObjectsManager.sort_images_by_name(images, self, "labeled_group")
        elif self.currentMode == "classification_sessions":
            ObjectsManager.sort_classificationSessions_by_name(self.currentDataset.classification_groups, self)

    def sort_by_date(self):
        if self.currentMode == 'datasets':
            ObjectsManager.sort_datasets_by_creationTime(self.datasets_list, self)
        elif self.currentMode == 'images_in_dataset':
            ObjectsManager.sort_images_by_uploadTime(self.currentDataset.images_list, self, "dataset")
        elif self.currentMode == "sessions_on_dataset":
            ObjectsManager.sort_sessions_by_creationTime(self.currentDataset.sessions_list, self)
        elif self.currentMode == "images_in_cluster":
            ObjectsManager.sort_images_by_uploadTime(self.currentCluster.images_list, self, "cluster")
        elif self.currentMode == "anomalies":
            ObjectsManager.sort_images_by_uploadTime(self.currentAnomalies.images_list, self, "anomalies")
        elif self.currentMode == "images_in_classificationSession":
            label = self.currentGroupLabel
            images = [img[0] for img in self.currentClassifSession.images_labels[label]]
            ObjectsManager.sort_images_by_uploadTime(images, self, "labeled_group")
        elif self.currentMode == "classification_sessions":
            ObjectsManager.sort_classificationSessions_by_date(self.currentDataset.classification_groups, self)

    def load_data(self):
        ObjectsManager.load_data_fromDB(self)

    def show_modelLOR_data(self):
        modelParams_dialog = ModelParamsDialog(self)
        modelParams_dialog.exec()

    def neural_network_clasify(self):
        active_model = self.get_active_model()

        if not active_model:
            return
        try:
            self.modelClasify_service = ENTClassifier(db=self.db, project_root=self.project_root,
                                                      model_path=active_model.onnx_path,
                                                      num_classes=len(active_model.label_map),
                                                      labelmap_ru=active_model.label_map)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить модель: {e}")
            return

        #выбор датасета для классификации
        selected_dataset = FeedbackManager.get_selected_dataset(self)
        if selected_dataset:
            #image_paths = [img.filepath for img in selected_dataset.images_list]
            progress_id = FeedbackManager.ShowProgress_OnNeuralNetworkClassification(self)
            def neural_network_clasification_task(progress_callback, cancel_check):
                return self.modelClasify_service.predict_batch(selected_dataset.get_activeImages(), selected_dataset,
                                                               active_model.id,
                                                               progress_callback, cancel_check)

            self.Start_Thread(neural_network_clasification_task, "classification", progress_id)

    def on_neuralNetwork_clasification_finished(self, result, progress_id):
        self.progress_bars[progress_id].close()
        del self.progress_bars[progress_id]
        del self.threads[progress_id]

        predictions, session, images, dataset= result
        #active_model = self.get_active_model()
        labels = set([label[0] for label in predictions])
        session.create_images_labels_dict(labels)

        for i in range (len(images)):
            label = predictions[i][0]
            confidence = predictions[i][1]
            img_confidence = [images[i], confidence]

            session.images_labels[label].append(img_confidence)

        dataset.classification_groups.append(session)
        self.tree_model.add_classification_session(session, dataset)
        self.update_ui()

    def change_active_model(self, name):
        set_active = False
        found_last = False
        for mv in self.models_data:
            if mv.is_active:
                if mv.name == name:
                    return
                mv.is_active = False
                found_last = True
            if mv.name == name:
                mv.is_active = True
                set_active = True
            if set_active and found_last:
                break


    def Start_Thread(self, background_task, operationType=None, progress_id=None, params_dialog=None):
        # Создаем поток
        thread = BackgroundThread(background_task)
        # Сохраняем в словарь
        self.threads[progress_id] = thread

        thread.progress.connect(
            lambda value, status: self.on_task_progress(value, status, progress_id)
        )
        if operationType == "import":
            thread.finished.connect(
                lambda result: self.on_import_finished(result, progress_id)
            )
        elif operationType == "duplicates_search":
            thread.finished.connect(
                lambda result: self.on_duplicateSearch_finished(result, progress_id)
            )
        elif operationType == "countK":
            thread.finished.connect(
                lambda result: params_dialog.on_countK_finished(result, progress_id)
            )
        elif operationType == "count_minSamples_esp":
            thread.finished.connect(
                lambda result: params_dialog.on_countEspMinSamples_finished(result, progress_id)
            )
        elif operationType == "clasterization":
            thread.finished.connect(
                lambda result: self.on_clasterization_finished(result, progress_id)
            )
        elif operationType == "tsne":
            thread.finished.connect(
                lambda result: self.distr_widget.on_tsneTask_finished(result, progress_id)
            )
        elif operationType == "export":
            thread.finished.connect(
                lambda result: self.on_exportDataset_finished(result, progress_id)
            )
        elif operationType == "classification":
            thread.finished.connect(
                lambda result: self.on_neuralNetwork_clasification_finished(result, progress_id)
            )

        thread.error.connect(
            lambda error: self.on_task_error(error, progress_id)
        )
        if progress_id in self.progress_bars:
            self.progress_bars[progress_id].canceled.connect(thread.cancel)
        thread.start()

    def on_clasterization_finished(self, result, progress_id):
        self.progress_bars[progress_id].close()
        del self.progress_bars[progress_id]
        del self.threads[progress_id]

        new_session, dataset = result

        self.tree_model.add_session(new_session, dataset)

        self.update_ui()

    def clasterize(self):
        selected_dataset = FeedbackManager.get_selected_dataset(self)
        if selected_dataset:
            params = FeedbackManager.get_clusterization_params(self, selected_dataset.images_list)
            if params:
                # получение названия сессии
                session_name = FeedbackManager.get_session_name(self, selected_dataset)
                if session_name:
                    if params['algorythm'] == "K-Means":
                        #запуск в фоновом потоке
                        progress_id = FeedbackManager.ShowProgress_OnClasterization(self, selected_dataset.name)
                        def clasterization_task(progress_callback, cancel_check):
                            return self.clusterization_service.clusterize_KMeans(
                                session_name, selected_dataset, params, progress_callback, cancel_check
                            )
                        self.Start_Thread(clasterization_task, "clasterization",  progress_id)
                    elif params['algorythm'] == "DBSCAN":
                        progress_id = FeedbackManager.ShowProgress_OnClasterization(self, selected_dataset.name)
                        def clasterization_task(progress_callback, cancel_check):
                            return self.clusterization_service.clusterize_DBSCAN(
                                session_name, selected_dataset, params, progress_callback, cancel_check
                            )
                        self.Start_Thread(clasterization_task, "clasterization", progress_id)




    def on_duplicateSearch_finished(self, result, progress_id):
        self.progress_bars[progress_id].close()
        del self.progress_bars[progress_id]
        del self.threads[progress_id]

        duplicate_groups, dataset = result[0], result[1]
        to_delete = FeedbackManager.get_toDelete_list(self, duplicate_groups)
        if to_delete and len(to_delete) > 0:
            ObjectsManager.set_status_deleted(to_delete)
            ObjectsManager.update_imagesStatus(self, to_delete, dataset.id)
            dataset.remove_images(to_delete)
            self.update_ui()

    def find_duplicates(self):
        selected_dataset = FeedbackManager.get_selected_dataset(self)
        if selected_dataset:
            similarity_level = FeedbackManager.get_similarity_level(self)
            if similarity_level:
                #запускаем в фоновом потоке
                progress_id = FeedbackManager.ShowProgress_OnDuplicates(self)
                def duplicate_task(progress_callback, cancel_check):
                    return self.duplicate_detector.find_duplicates(selected_dataset, progress_callback, cancel_check,  similarity_level)
                self.Start_Thread(duplicate_task, "duplicates_search", progress_id)


    def analyse_quality(self):
        selected_dataset = FeedbackManager.get_selected_dataset(self)
        if selected_dataset:
            qualityParams_dialog = QualityParamsDialog(self)
            qualityParams_dialog.show()
            if qualityParams_dialog.exec() == QDialog.DialogCode.Accepted:
                params = qualityParams_dialog.values
                badQuality_images = self.quality_analyse_service.check_quality(selected_dataset.get_activeImages(), params)
                #открываем диалог результата
                qualityAnalyse_result_dialog = QualityAnalyseResultsDialog(self)
                qualityAnalyse_result_dialog.set_results(selected_dataset.get_activeImages(), badQuality_images)
                qualityAnalyse_result_dialog.show()

                #если пользователь выбрал "Продолжить с прошедшими" то убираем остальные,
                #можно сделать не полное удаление
                to_delete = []
                if qualityAnalyse_result_dialog.exec() == QDialog.DialogCode.Accepted:
                    #присвоим низкокачественным изображениям статус deleted
                    to_delete = [img for img in selected_dataset.images_list if img.status == "quality_failed"]
                    ObjectsManager.set_status_deleted(to_delete)
                    selected_dataset.remove_images(to_delete)

                #обновляем статус всех изображений датасета в БД
                ObjectsManager.update_imagesStatus(self, selected_dataset.images_list + to_delete, selected_dataset.id)
            self.update_ui()


    def import_image(self):
        #выбор датасета для импорта
        if len(self.datasets_list) == 0:
            FeedbackManager.NoDatasets_Warning(self)
            return

        selectDataset_dialog = SelectDatasetDialog(self.datasets_list, self)
        selectDataset_dialog.show()
        #если пользователь нажал ОК
        if selectDataset_dialog.exec() == QDialog.DialogCode.Accepted:
            selected = selectDataset_dialog.get_selected_dataset()
            # открытие диалога выбора изображения
            files = FeedbackManager.Open_ImageSelect_Dialog(self)

            #создаем фоновую операцию
            progress_id = FeedbackManager.ShowProgress(self, "images")

            def import_task(progress_callback, cancel_check):
                return self.import_service.import_image(selected, files, progress_callback,
                                                        cancel_check)

            self.Start_Thread(import_task, "import", progress_id)


    def update_ui(self):
        #self.display_tree()
        if self.currentMode == "datasets":
            self.show_datasets(self.datasets_list)
        elif self.currentMode == "images_in_dataset":
            self.open_dataset(self.currentDataset, self.currentDataset.images_list)
        elif self.currentMode == "sessions_on_dataset":
            self.show_sessions(self.currentDataset, self.currentDataset.sessions_list)
        elif self.currentMode == "clusters":
            self.open_session(self.currentSession, self.currentSession.clusters_list)
        elif self.currentMode == "images_in_cluster":
            if self.currentSession == None:
                self.show_datasets(self.datasets_list)
            elif self.currentCluster == None:
                self.open_session(self.currentSession, self.currentSession.clusters_list)
            else:
                self.open_cluster(self.currentCluster, self.currentCluster.images_list)
        elif self.currentMode == "anomalies":
            self.open_anomalyGroup(self.currentAnomalies, self.currentAnomalies.images_list)
        elif self.currentMode == "images_in_classificationSession":
            imgs = self.currentClassifSession.images_labels[self.currentGroupLabel]
            self.on_classificationGroup_double_clicked(self.currentClassifSession, imgs, self.currentGroupLabel)
        elif self.currentMode == "classification_sessions":
            self.show_classification_sessions(self.currentDataset, self.currentDataset.classification_groups)
        elif self.currentMode == "labeled_groups":
            groups = [gr for gr in self.currentClassifSession.images_labels.values() if gr is not None]
            self.on_classification_session_double_clicked(self.currentClassifSession, groups)


    def export_datasets(self):
        dataset = FeedbackManager.get_selected_dataset(self)
        if not dataset:
            return

        directory = FeedbackManager.get_existing_directory(self)
        if not directory:
            return

        progress_id = FeedbackManager.ShowProgress_OnExportDataset(self)
        def export_task(progress_callback, cancel_check):
            return self.export_service.export_dataset(dataset,
                                                      directory,
                                                      progress_callback,
                                                      cancel_check)
        self.Start_Thread(export_task, "export", progress_id)

    def on_exportDataset_finished(self, result, progress_id):
        self.progress_bars[progress_id].close()
        del self.progress_bars[progress_id]
        del self.threads[progress_id]

        dataset_name, sessions_count, images_count = result
        FeedbackManager.DatasetExported_Message(self, dataset_name, sessions_count, images_count)

    def import_dataset(self):
        # открытие диалога выбора папки
        folder_path = FeedbackManager.Open_FolderSelect_Dialog(self)
        if not folder_path:  # пользователь отменил выбор
            return
        # Получаем имя папки
        dataset_name = os.path.basename(folder_path)

        #проверяем существование датасета с таким именем
        for dataset in self.datasets_list:
            if dataset.name == dataset_name:
                FeedbackManager.DatasetAlreadyExists(self)
                return

        #Проверка на наличие изображений
        image_files = [f for f in os.listdir(folder_path)
                       if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))]
        if not image_files:
            FeedbackManager.NoImagesInFolder_Warning(self)
            return

        reply = FeedbackManager.DatasetCreation_Answer(self, dataset_name, len(image_files))
        if reply != QMessageBox.StandardButton.Yes:
            return

        progress_id = FeedbackManager.ShowProgress(self,"dataset")

        def import_task(progress_callback, cancel_check):
            return self.import_service.import_dataset(
                folder_path,
                dataset_name,
                self.current_user.id,
                image_files,
                progress_callback,
                cancel_check
            )

        self.Start_Thread(import_task, "import", progress_id)

    def on_task_progress(self, value, status, progress_id):
        self.progress_bars[progress_id].setValue(value)
        self.progress_bars[progress_id].setLabelText(status)


    def on_import_finished(self, result, progress_id):
        self.progress_bars[progress_id].close()
        del self.progress_bars[progress_id]
        del self.threads[progress_id]

        if type(result) is Dataset:
            new_dataset = result
            self.datasets_list.append(new_dataset)
            if self.currentMode == "datasets":
                FeedbackManager.DatasetCreated_Message(self, new_dataset.name, len(new_dataset.images_list))
                if len(self.datasets_list) == 1:
                    MenuManager.setup_menu(self)
            self.tree_model.add_dataset(new_dataset)
        else:
            arr, images = result
            FeedbackManager.ImagesAdded_Message(self, arr[1].name, arr[0])
            self.tree_model.add_images(arr[1], images)
        self.update_ui()

    def on_task_error(self, error_msg, progress_id):
        QMessageBox.critical(self, "Ошибка", error_msg)
        self.progress_bars[progress_id].close()
        del self.progress_bars[progress_id]
        del self.threads[progress_id]


    def setup_ui(self):
        #настройка меню
        MenuManager.setup_menu(self)
        #настройка кнопки "Назад"
        MenuManager.setup_backButton(self)
        self.setup_tree()
        #настройка отображения графиков
        self.distr_widget = DistributionWidget(self, self.visualization_frame)
        layout = QVBoxLayout(self.visualization_frame)
        layout.addWidget(self.distr_widget)
        #настройка отображения датасетов
        self.show_datasets(self.datasets_list)
        pass


    def setup_tree(self):
        # настройка отображения дерева
        self.tree_view = self.findChild(QTreeView, "treeView")
        # Настраиваем дерево
        self.tree_view.setHeaderHidden(False)  # показываем заголовок
        self.tree_view.setAnimated(True)  # анимация при разворачивании

        DragDropService.setup_target(self)

        # Двойной клик на элемент дерева
        self.tree_view.doubleClicked.connect(self.on_tree_item_double_clicked)
        self.tree_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree_view.customContextMenuRequested.connect(self.show_treeItem_context_menu)

        # отображаем дерево
        self.display_tree()

    def show_treeItem_context_menu(self, position):
        index = self.tree_view.indexAt(position)

        if not index.isValid():
            return

        item = index.internalPointer()

        global_pos = self.tree_view.viewport().mapToGlobal(position)
        MenuManager.show_tree_contextMenu(self, item, global_pos)


    def on_tree_item_double_clicked(self, index):
        item = index.internalPointer()
        data = item.data(0)

        if data.startswith("📁"):  # Датасет
            dataset = ObjectsManager.find_dataset_from_tree(self, data[2:])
            self.open_dataset(dataset, dataset.images_list)
        elif data.startswith("🖼️ Изображения"):
            parent = item.parent()
            dataset = ObjectsManager.find_dataset_from_tree(self, parent.data(0)[2:])
            self.open_dataset(dataset, dataset.images_list)
        elif data.startswith("🖼️"):
            dataset_item = item.parent().parent()
            dataset = ObjectsManager.find_dataset_from_tree(self, dataset_item.data(0)[2:])
            image = ObjectsManager.find_image_by_name(dataset, data[2:])
            self.on_image_double_clicked(image)
        elif data.startswith("📊"):
            parent = item.parent()
            dataset = ObjectsManager.find_dataset_from_tree(self, parent.data(0)[2:])
            self.show_sessions(dataset, dataset.sessions_list)
        elif data.startswith("📈"):
            parent_root = item.parent()
            parent_dataset = parent_root.parent()
            dataset = ObjectsManager.find_dataset_from_tree(self, parent_dataset.data(0)[2:])
            session = ObjectsManager.find_session_from_tree(dataset, data[2:])
            self.on_session_double_clicked(session)
        elif data.startswith("🗂️ Кластеры"):
            parent_session = item.parent()
            parent_dataset = parent_session.parent().parent()
            dataset = ObjectsManager.find_dataset_from_tree(self, parent_dataset.data(0)[2:])
            session = ObjectsManager.find_session_from_tree(dataset, parent_session.data(0)[2:])
            self.on_session_double_clicked(session)
        elif data.startswith("⚠️"):
            parent_session = item.parent()
            parent_sessions_root = parent_session.parent()
            parent_dataset = parent_sessions_root.parent()
            dataset = ObjectsManager.find_dataset_from_tree(self, parent_dataset.data(0)[2:])
            session = ObjectsManager.find_session_from_tree(dataset, parent_session.data(0)[2:])
            self.on_anomalyGroup_double_clicked(session.anomaly_group)
        elif data.startswith("🎯"):
            parent_root = item.parent()
            parent_session = parent_root.parent()
            parent_sessions_root = parent_session.parent()
            parent_dataset = parent_sessions_root.parent()
            dataset = ObjectsManager.find_dataset_from_tree(self, parent_dataset.data(0)[2:])
            session = ObjectsManager.find_session_from_tree(dataset, parent_session.data(0)[2:])
            cluster = ObjectsManager.find_cluster_from_tree(session, data[2:])
            self.on_cluster_double_clicked(cluster)
        elif data.startswith("🧠"):
            parent_dataset = item.parent()
            dataset = ObjectsManager.find_dataset_from_tree(self, parent_dataset.data(0)[2:])
            self.show_classification_sessions(dataset, dataset.classification_groups)
        elif data.startswith("📋"):
            parent_dataset = item.parent().parent()
            dataset = ObjectsManager.find_dataset_from_tree(self, parent_dataset.data(0)[2:])
            classif_session = dataset.find_classificationSession_byName(data[2:])
            groups = [gr for gr in classif_session.images_labels.values()]
            self.on_classification_session_double_clicked(classif_session, groups)
        elif data.startswith("🏷️"):
            group_name = item.data(0)[2:]
            parent_classif_session = item.parent()
            parent_dataset = parent_classif_session.parent().parent()
            dataset = ObjectsManager.find_dataset_from_tree(self, parent_dataset.data(0)[2:])
            classif_session = dataset.find_classificationSession_byName(parent_classif_session.data(0)[2:])
            if 'Другое' in group_name:
                images = [img for img in classif_session.images_labels['Не в кадре']]
            else:
                images = [img for img in classif_session.images_labels[group_name.strip()]]
            self.on_classificationGroup_double_clicked(classif_session, images, group_name)

    def on_classification_session_double_clicked(self, classification_session, groups, search_query=None, names=None):
        self.currentMode = "labeled_groups"
        self.currentDataset = ObjectsManager.find_dataset_by_id(self, classification_session.dataset_id)
        self.currentSession = None
        self.currentCluster = None
        self.currentAnomalies = None
        self.currentGroupLabel = None
        self.currentClassifSession = classification_session
        self.currentMode_changed.emit()
        self.search_line.setPlaceholderText(f"Поиск в: {classification_session.name}")

        if names:
            names_param = names
        else:
            names_param = [key for key in classification_session.images_labels.keys()]
        WidgetViewer.display(self, self.fullScreen_scrollArea, groups, "labeled_group",
                             search_query, session=classification_session,
                             names=names_param)

    def show_classification_sessions(self, dataset: object, sessions: object, search_query: object = None) -> object:
        self.currentMode = "classification_sessions"
        self.currentDataset = dataset
        self.currentSession = None
        self.currentCluster = None
        self.currentAnomalies = None
        self.currentClassifSession = None
        self.currentGroupLabel = None
        self.currentMode_changed.emit()
        self.search_line.setPlaceholderText(f"Поиск в: Сессии классификации НС")
        WidgetViewer.display(self, self.fullScreen_scrollArea, sessions, "classification_session", search_query)

    def on_classificationGroup_double_clicked(self, classification_session, images, group_name, search_text=None, search_mode=None):
        if 'Ухо' in group_name:
            name = 'Ухо'
        elif 'Нос' in group_name:
            name = 'Нос'
        elif 'Глотка' in group_name:
            name = 'Глотка'
        elif 'Гортань' in group_name:
            name = 'Гортань'
        elif 'Другое' in group_name or 'Не в кадре' in group_name:
            name = 'Не в кадре'
        else:
            name = group_name.strip()
        label_group = classification_session.images_labels[name]
        #отображение изображений сессии кластеризации НС
        self.currentMode = "images_in_classificationSession"

        self.currentDataset = ObjectsManager.find_dataset_by_id(self, classification_session.dataset_id)
        self.currentSession = None
        self.currentCluster = None
        self.currentAnomalies = None
        self.currentClassifSession = classification_session
        self.currentGroupLabel = name
        self.currentMode_changed.emit()
        self.search_line.setPlaceholderText(f"Поиск в: {classification_session.name}")
        ImageViewer.display(self, self.fullScreen_scrollArea, images, self.currentDataset, search_text, search_mode)



    def prev_page(self):
        if (self.currentMode == "images_in_dataset" or
                self.currentMode == "sessions_on_dataset" or
                self.currentMode == "classification_sessions"):
            self.show_datasets(self.datasets_list)
            self.currentDataset = None
        if self.currentMode == "clusters":
            self.show_sessions(self.currentDataset, self.currentDataset.sessions_list)
        if self.currentMode == "images_in_cluster" or self.currentMode == "anomalies":
            self.open_session(self.currentSession, self.currentSession.clusters_list, True)
        if self.currentMode == "labeled_groups":
            self.show_classification_sessions(self.currentDataset, self.currentDataset.classification_groups)
        if self.currentMode == "images_in_classificationSession":
            groups = [gr for gr in self.currentClassifSession.images_labels.values()]
            self.on_classification_session_double_clicked(self.currentClassifSession, groups)


    def show_datasets(self, datasets, search_query=None):
        self.currentMode = "datasets"

        self.currentDataset = None
        self.currentSession = None
        self.currentCluster = None
        self.currentAnomalies = None
        self.currentClassifSession = None
        self.currentGroupLabel = None
        self.currentMode_changed.emit()
        self.search_line.setPlaceholderText("Поиск в: Датасеты")
        WidgetViewer.display(self, self.fullScreen_scrollArea, datasets, "dataset", search_query)


    def on_dataset_double_clicked(self, dataset):
        self.open_dataset(dataset, dataset.images_list)

    def on_session_double_clicked(self, session):
        self.open_session(session, session.clusters_list, True)

    def open_session(self, session, clusters_list, redraw_map = False,search_query=None):
        self.currentMode = "clusters"

        self.currentSession = session
        self.currentDataset = ObjectsManager.find_dataset_by_id(self, session.dataset_id)
        self.currentCluster = None
        self.currentAnomalies = None
        self.currentClassifSession = None
        self.currentGroupLabel = None
        self.search_line.setPlaceholderText(f"Поиск в: {session.name}")

        self.stackedWidget.setCurrentIndex(0)
        if redraw_map:
            self.currentMode_changed.emit()
        WidgetViewer.display(self, self.partial_scrollArea, clusters_list, "cluster", search_query, session.anomaly_group)

    def on_anomalyGroup_double_clicked(self, anomalyGroup):
        self.open_anomalyGroup(anomalyGroup, anomalyGroup.images_list)

    def open_anomalyGroup(self, anomalyGroup, images_list, search_query=None, search_mode=None):
        self.currentMode = "anomalies"

        self.currentSession = ObjectsManager.find_session_by_id(self, anomalyGroup.session_id)
        self.currentDataset = ObjectsManager.find_dataset_by_id(self, self.currentSession.dataset_id)
        self.currentCluster = None
        self.currentAnomalies = anomalyGroup
        self.currentGroupLabel = None
        self.currentClassifSession = None
        self.search_line.setPlaceholderText(f"Поиск в: {anomalyGroup.name}")
        self.stackedWidget.setCurrentIndex(1)
        if not search_query:
            self.currentMode_changed.emit()
        ImageViewer.display(self, self.fullScreen_scrollArea, images_list, self.currentDataset, search_query, search_mode)

    def on_cluster_double_clicked(self, cluster):
        self.open_cluster(cluster, cluster.images_list, True)

    def open_cluster(self, cluster, images_list, redraw_map = False, search_query=None, search_mode=None):
        self.currentMode = "images_in_cluster"

        self.currentSession = ObjectsManager.find_session_by_id(self, cluster.session_id)
        self.currentDataset = ObjectsManager.find_dataset_by_id(self, self.currentSession.dataset_id)
        self.currentCluster = cluster
        self.currentAnomalies = None
        self.currentClassifSession = None
        self.currentGroupLabel = None
        self.search_line.setPlaceholderText(f"Поиск в: {cluster.name}")

        self.stackedWidget.setCurrentIndex(0)
        if redraw_map:
            self.currentMode_changed.emit()
        ImageViewer.display(self, self.partial_scrollArea, images_list, self.currentDataset, search_query, search_mode)

    def on_image_double_clicked(self, image):
        image.open_file()

    def open_dataset(self, dataset, images_list, search_query=None, search_mode=None):
        self.currentMode = "images_in_dataset"

        self.currentDataset = dataset
        self.currentSession = None
        self.currentCluster = None
        self.currentAnomalies = None
        self.currentClassifSession = None
        self.currentGroupLabel = None
        self.currentMode_changed.emit()
        self.search_line.setPlaceholderText(f"Поиск в: {dataset.name}")

        active_images = [img for img in images_list if img.status != "deleted"]
        ImageViewer.display(self, self.fullScreen_scrollArea, active_images, dataset.id, search_query, search_mode)

    def show_sessions(self, dataset, sessions_list, search_query=None):
        self.currentMode = "sessions_on_dataset"

        self.currentDataset = dataset
        self.currentSession = None
        self.currentCluster = None
        self.currentAnomalies = None
        self.currentClassifSession = None
        self.currentGroupLabel = None
        self.currentMode_changed.emit()
        self.search_line.setPlaceholderText("Поиск в: Сессии")
        WidgetViewer.display(self, self.fullScreen_scrollArea, sessions_list, "session", search_query)

    def display_tree(self):
        if self.tree_view:
            # Создаем модель с данными
            self.tree_model = TreeModel(self.datasets_list, self)
            # Устанавливаем модель в tree view
            self.tree_view.setModel(self.tree_model)



    def closeEvent(self, event):
        if len(self.threads) > 0:
            reply = QMessageBox.question(
                self,
                "Подтверждение закрытия",
                "Выполняются фоновые операции. Закрыть приложение?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                # Отменяем все потоки
                for progress_id, thread in self.threads.items():
                    thread.cancel()
                self.main_conn.close()
                event.accept()
            else:
                event.ignore()
        else:
            self.main_conn.commit()
            self.main_conn.close()
            event.accept()