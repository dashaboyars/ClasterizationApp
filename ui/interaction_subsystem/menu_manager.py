from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QMainWindow, QMessageBox, QToolButton, QStackedWidget, QMenu, QPushButton
from PyQt6 import uic
from services.import_service import ImportService
from ui.interaction_subsystem.feedback_manager import FeedbackManager
from ui.interaction_subsystem.objects_manager import ObjectsManager


class MenuManager:
    @staticmethod
    def show_tree_contextMenu(mainWindow, item, position):
        item_data = item.data(0)

        if item_data.startswith("📁"):  # Датасет
            dataset = ObjectsManager.find_dataset_from_tree(mainWindow, item_data[2:])
            MenuManager.show_dataset_contextMenu(mainWindow, dataset, position)
        elif item_data.startswith("📈"):
            parent_root = item.parent()
            parent_dataset = parent_root.parent()
            dataset = ObjectsManager.find_dataset_from_tree(mainWindow, parent_dataset.data(0)[2:])
            session = ObjectsManager.find_session_from_tree(dataset, item_data[2:])
            MenuManager.show_session_contextMenu(mainWindow, session, position)
        elif item_data.startswith("🖼️ Изображения"):
            parent_dataset = item.parent()
            dataset = ObjectsManager.find_dataset_from_tree(mainWindow, parent_dataset.data(0)[2:])
            MenuManager.show_imagesRoot_contextMenu(mainWindow, dataset, position)
        elif item_data.startswith("📊"):
            parent_dataset = item.parent()
            dataset = ObjectsManager.find_dataset_from_tree(mainWindow, parent_dataset.data(0)[2:])
            MenuManager.show_sessionsRoot_contextMenu(mainWindow, dataset, position)
        elif item_data.startswith(f"🗂️ Кластеры"):
            parent_session = item.parent()
            parent_root = parent_session.parent()
            parent_dataset = parent_root.parent()
            dataset = ObjectsManager.find_dataset_from_tree(mainWindow, parent_dataset.data(0)[2:])
            session = ObjectsManager.find_session_from_tree(dataset, parent_session.item_data[2:])
            MenuManager.show_clustersRoot_contextMenu(mainWindow, session, position)
        elif item_data.startswith("⚠️"):
            parent_session = item.parent()
            parent_sessions_root = parent_session.parent()
            parent_dataset = parent_sessions_root.parent()
            dataset = ObjectsManager.find_dataset_from_tree(mainWindow, parent_dataset.data(0)[2:])
            session = ObjectsManager.find_session_from_tree(dataset, parent_session.item_data[2:])
            MenuManager.show_anomalyGroup_contextMenu(mainWindow, session, session.anomaly_group, position)
        elif item_data.startswith("🎯"):
            parent_root = item.parent()
            parent_session = parent_root.parent()
            parent_sessions_root = parent_session.parent()
            parent_dataset = parent_sessions_root.parent()
            dataset = ObjectsManager.find_dataset_from_tree(mainWindow, parent_dataset.data(0)[2:])
            session = ObjectsManager.find_session_from_tree(dataset, parent_session.item_data[2:])
            cluster = ObjectsManager.find_cluster_from_tree(session, item_data[2:])
            MenuManager.show_cluster_contextMenu(mainWindow, session, cluster, position)
        elif item_data.startswith("📋"):
            dataset_parent = item.parent().parent()
            dataset = ObjectsManager.find_dataset_from_tree(mainWindow, dataset_parent.data(0)[2:])
            session = dataset.find_classificationSession_byName(item_data[2:])
            MenuManager.show_classificationSession_contextMenu(mainWindow, session, position)
        elif item_data.startswith("🧠"):
            dataset_parent = item.parent()
            dataset = ObjectsManager.find_dataset_from_tree(mainWindow, dataset_parent.data(0)[2:])
            MenuManager.show_classificationSession_root_contextMenu(mainWindow, dataset, position)
        elif item_data.startswith("🏷️"):
            session_parent = item.parent()
            sessions_root = session_parent.parent()
            dataset_parent = sessions_root.parent()
            dataset = ObjectsManager.find_dataset_from_tree(mainWindow, dataset_parent.data(0)[2:])
            session = ObjectsManager.find_classificationSession_by_name(dataset, session_parent.data(0)[2:].strip())
            MenuManager.show_labeledGroup_contextMenu(mainWindow, session, item_data[2:].strip(), position)

    @staticmethod
    def show_classificationSession_root_contextMenu(mainWindow, dataset, position):
        menu = QMenu()
        open_action = QAction("Открыть")
        open_action.triggered.connect(lambda: mainWindow.show_classification_sessions(dataset, dataset.classification_groups))
        menu.addAction(open_action)

        menu.addSeparator()

        delete_action = QAction("Удалить все сессии классификации НС")
        delete_action.triggered.connect(lambda: ObjectsManager.delete_classificationSessions(mainWindow,
                                                                                    dataset.classification_groups))
        menu.addAction(delete_action)

        menu.exec(position)




    @staticmethod
    def show_clustersRoot_contextMenu(mainWindow, session, position):
        menu = QMenu()

        open_action = QAction("Открыть")
        open_action.triggered.connect(lambda: mainWindow.open_session(session, session.clusters_list))
        menu.addAction(open_action)

        delete_action = QAction("Удалить все кластеры сессии")
        delete_action.triggered.connect(lambda: ObjectsManager.delete_sessions(mainWindow,
                                                                               [session]))
        delete_action.triggered.connect(mainWindow.update_ui)

        menu.addAction(delete_action)

        menu.exec(position)

    @staticmethod
    def show_sessionsRoot_contextMenu(mainWindow, dataset, position):
        menu = QMenu()

        open_action = QAction("Открыть")
        open_action.triggered.connect(lambda: mainWindow.show_sessions(dataset, dataset.sessions_list))
        menu.addAction(open_action)

        menu.addSeparator()

        delete_action = QAction("Удалить все сессии")
        if mainWindow.currentSession in dataset.sessions_list:
            delete_action.triggered.connect(mainWindow.prev_page)
        delete_action.triggered.connect(lambda: ObjectsManager.delete_sessions(mainWindow,
                                                                       dataset.sessions_list.copy()))
        delete_action.triggered.connect(mainWindow.update_ui)

        menu.addAction(delete_action)

        menu.exec(position)

    @staticmethod
    def show_imagesRoot_contextMenu(mainWindow, dataset, position):
        menu = QMenu()

        open_action = QAction("Открыть")
        open_action.triggered.connect(lambda: mainWindow.open_dataset(dataset, dataset.images_list))
        menu.addAction(open_action)

        menu.addSeparator()

        delete_action = QAction("Удалить все изображения")
        delete_action.triggered.connect(lambda: ObjectsManager.set_status_deleted(dataset.images_list))
        delete_action.triggered.connect(
            lambda: ObjectsManager.update_imagesStatus(mainWindow, dataset.images_list, dataset.id))
        delete_action.triggered.connect(lambda: dataset.remove_images(dataset.images_list.copy()))
        delete_action.triggered.connect(mainWindow.update_ui)
        menu.addAction(delete_action)

        #delete_action.triggered.connect(mainWindow.prev_page)
        menu.addAction(delete_action)
        menu.exec(position)

    @staticmethod
    def show_anomalyGroup_contextMenu(mainWindow, session, anomalyGroup, position):
        menu = QMenu()

        open_action = QAction("Открыть")
        open_action.triggered.connect(lambda: mainWindow.open_anomalyGroup(anomalyGroup, anomalyGroup.images_list))
        menu.addAction(open_action)

        menu.addSeparator()
        delete_action = QAction("Удалить")
        delete_action.triggered.connect(lambda: ObjectsManager.delete_anomalyGroup(mainWindow,
                                                                                   session, anomalyGroup))
        menu.addAction(delete_action)
        menu.exec(position)

    @staticmethod
    def show_cluster_contextMenu(mainWindow, session, cluster, position):
        menu = QMenu()

        open_action = QAction("Открыть")
        open_action.triggered.connect(lambda: mainWindow.open_cluster(cluster, cluster.images_list))
        menu.addAction(open_action)

        rename_action = QAction("Переименовать")
        rename_action.triggered.connect(lambda: ObjectsManager.rename_item(cluster,
                                                                            mainWindow))
        menu.addAction(rename_action)

        # ОБЯЗАТЕЛЬНО ДОБАВИТЬ ОТОБРАЖЕНИЕ СВОЙСТВ
        menu.addSeparator()
        showParams_action = QAction("Свойства")
        showParams_action.triggered.connect(lambda: FeedbackManager.show_cluster_params(cluster, mainWindow))
        menu.addAction(showParams_action)
        menu.addSeparator()

        delete_action = QAction("Удалить")
        delete_action.triggered.connect(lambda: ObjectsManager.delete_cluster(mainWindow,
                                                                              cluster, session))
        delete_action.triggered.connect(mainWindow.prev_page)
        menu.addAction(delete_action)

        menu.exec(position)

    @staticmethod
    def show_labeledGroup_contextMenu(mainWindow, session, group_name, position):
        menu = QMenu()
        open_action = QAction("Открыть")
        images = [item[0] for item in session.images_labels[group_name]]
        open_action.triggered.connect(
            lambda: mainWindow.on_classificationGroup_double_clicked(session, images, group_name))
        menu.addAction(open_action)

        menu.addSeparator()

        delete_action = QAction("Удалить")
        delete_action.triggered.connect(
            lambda: ObjectsManager.delete_classificationGroup(mainWindow, session, group_name))
        menu.addAction(delete_action)

        menu.exec(position)


    @staticmethod
    def show_classificationSession_contextMenu(mainWindow, session, position):
        menu = QMenu()
        open_action = QAction("Открыть")
        groups = [gr for gr in session.images_labels.values()]
        open_action.triggered.connect(lambda: mainWindow.on_classification_session_double_clicked(session,
                                                                                                  groups))
        menu.addAction(open_action)

        rename_action = QAction("Переименовать")
        rename_action.triggered.connect(lambda: ObjectsManager.rename_item(session,
                                                                           mainWindow))
        menu.addAction(rename_action)

        menu.addSeparator()

        delete_action = QAction("Удалить")
        delete_action.triggered.connect(lambda: ObjectsManager.delete_classificationSessions(mainWindow,
                                                                               [session]))
        delete_action.triggered.connect(mainWindow.update_ui)
        if mainWindow.currentSession == session:
            delete_action.triggered.connect(mainWindow.prev_page)

        menu.addAction(delete_action)

        menu.exec(position)




    @staticmethod
    def show_session_contextMenu(mainWindow, session, position):
        menu = QMenu()

        open_action = QAction("Открыть")
        open_action.triggered.connect(lambda: mainWindow.open_session(session, session.clusters_list))
        menu.addAction(open_action)

        rename_action = QAction("Переименовать")
        rename_action.triggered.connect(lambda: ObjectsManager.rename_item(session,
                                                                               mainWindow))
        menu.addAction(rename_action)

        #ОБЯЗАТЕЛЬНО ДОБАВИТЬ ОТОБРАЖЕНИЕ СВОЙСТВ
        menu.addSeparator()

        showParams_action = QAction("Свойства")
        showParams_action.triggered.connect(lambda: FeedbackManager.show_session_params(session,
                                                                                        mainWindow))
        menu.addAction(showParams_action)

        menu.addSeparator()

        delete_action = QAction("Удалить")
        delete_action.triggered.connect(lambda: ObjectsManager.delete_sessions(mainWindow,
                                                                              [session]))
        delete_action.triggered.connect(mainWindow.update_ui)
        if mainWindow.currentSession == session:
            delete_action.triggered.connect(mainWindow.prev_page)

        menu.addAction(delete_action)

        menu.exec(position)


    @staticmethod
    def show_dataset_contextMenu(mainWindow, dataset, position):
        menu = QMenu()
        open_action = QAction("Открыть")
        open_action.triggered.connect(lambda: mainWindow.open_dataset(dataset, dataset.images_list))
        menu.addAction(open_action)

        rename_action = QAction("Переименовать")
        rename_action.triggered.connect(lambda: ObjectsManager.rename_item(dataset,
                                                                               mainWindow))
        menu.addAction(rename_action)

        #МОЖНО ДОБАВИТЬ ОТОБРАЖЕНИЕ СВОЙСТВ
        menu.addSeparator()

        delete_action = QAction("Удалить")
        delete_action.triggered.connect(lambda: ObjectsManager.delete_dataset(mainWindow, dataset))
        delete_action.triggered.connect(mainWindow.prev_page)
        menu.addAction(delete_action)

        menu.exec(position)




    @staticmethod
    def show_image_contextMenu(image_list_widget, images, position, dataset):
        menu = QMenu(image_list_widget)

        if (len(images) == 1):
            #открыть
            open_action = QAction("Открыть", image_list_widget)
            open_action.triggered.connect(images[0].open_file)
            menu.addAction(open_action)

            #переименование
            rename_action = QAction("Переименовать", image_list_widget)
            rename_action.triggered.connect(lambda: ObjectsManager.rename_item(images[0],
                                                                               image_list_widget.parent,
                                                                               dataset))
            menu.addAction(rename_action)

            menu.addSeparator()

        # копирование
        copy_action = QAction("Копировать", image_list_widget)
        copy_action.triggered.connect(lambda: ObjectsManager.copy_images(image_list_widget.parent, images))
        menu.addAction(copy_action)

        # вставка
        paste_action = QAction("Вставить", image_list_widget)
        paste_action.triggered.connect(image_list_widget.paste_images)
        menu.addAction(paste_action)

        if image_list_widget.parent.images_copied:
            paste_action.setEnabled(True)
        else:
            paste_action.setEnabled(False)

        menu.addSeparator()

        #присвоение тега
        addTag_action = QAction("Добавить тег", image_list_widget)
        addTag_action.triggered.connect(lambda: ObjectsManager.add_tags_toImages(image_list_widget.parent, images))
        menu.addAction(addTag_action)

        menu.addSeparator()

        # удаление
        delete_action = QAction("Удалить элементы", image_list_widget)
        delete_action.triggered.connect(lambda: ObjectsManager.set_status_deleted(images))
        delete_action.triggered.connect(lambda: ObjectsManager.update_imagesStatus(image_list_widget.parent, images, dataset.id))
        delete_action.triggered.connect(lambda: dataset.remove_images(images))
        delete_action.triggered.connect(image_list_widget.parent.update_ui)
        delete_action.triggered.connect(lambda: image_list_widget.parent.tree_model.delete_images_from_dataset(dataset, images))
        menu.addAction(delete_action)
        menu.exec(image_list_widget.viewport().mapToGlobal(position))

    @staticmethod
    def setup_menu(mainWindow):
        MenuManager.setup_importButton(mainWindow)
        MenuManager.setup_instruments(mainWindow)
        MenuManager.setup_modelsButton(mainWindow)
        MenuManager.setup_sortButton(mainWindow)
        MenuManager.setup_createDataset_button(mainWindow)

    @staticmethod
    def setup_createDataset_button(mainWindow):
        mainWindow.createDataset_button = mainWindow.findChild(QToolButton, "createDataset_button")
        if mainWindow.createDataset_button:
            try:
                mainWindow.createDataset_button.clicked.disconnect(mainWindow.create_dataset)
            except TypeError:
                pass
            mainWindow.createDataset_button.clicked.connect(mainWindow.create_dataset)


    @staticmethod
    def setup_sortButton(mainWindow):
        #кнопка сортировки в меню
        mainWindow.btn_sort = mainWindow.findChild(QToolButton, "sort_button")
        if mainWindow.btn_sort:
            menu = QMenu(mainWindow)
            #СОРТИРОВКА
            #сортировка по имени - для любых объектов
            if mainWindow.currentMode != "labeled_groups":
                action_nameSort = QAction("Сортировка по имени", mainWindow)
                action_nameSort.triggered.connect(mainWindow.sort_by_name)
                menu.addAction(action_nameSort)

            if mainWindow.currentMode != "clusters" and mainWindow.currentMode != "labeled_groups":
                #сортировка по дате создания - для всего кроме кластеров
                action_dateSort = QAction("Сортировка по дате создания/загрузки", mainWindow)
                action_dateSort.triggered.connect(mainWindow.sort_by_date)
                menu.addAction(action_dateSort)

            if (mainWindow.currentMode == "datasets" or mainWindow.currentMode == "clusters" or
                mainWindow.currentMode == "labeled_groups"):
                #сортировка по кол-ву изображений для датасетов и кластеров
                action_imageAmount_sort = QAction("Сортировка по количеству изображений", mainWindow)
                action_imageAmount_sort.triggered.connect(mainWindow.sort_by_imageAmount)
                menu.addAction(action_imageAmount_sort)

            if mainWindow.currentMode == "datasets":
                #по кол-ву сессий для датасетов
                action_sessionAmount_sort = QAction("Сортировка по количеству сессий", mainWindow)
                action_sessionAmount_sort.triggered.connect(mainWindow.sort_by_sessionsAmount)
                menu.addAction(action_sessionAmount_sort)

            if mainWindow.currentMode == "sessions_on_dataset":
                #по кол-ву кластеров для сессий
                action_clusterAmount_sort = QAction("Сортировка по количеству кластеров", mainWindow)
                action_clusterAmount_sort.triggered.connect(mainWindow.sort_by_clustersAmount)
                menu.addAction(action_clusterAmount_sort)

            menu.addSeparator()

            #ФИЛЬТРЫ
            if mainWindow.currentMode == "datasets":
                action_onlyClusterized = QAction("Только кластеризованные", mainWindow)
                action_onlyClusterized.triggered.connect(lambda: ObjectsManager.show_only_clusterized_datasets(mainWindow))
                menu.addAction(action_onlyClusterized)
            if (mainWindow.currentMode == "images_in_dataset" or mainWindow.currentMode == "images_in_cluster"
                    or mainWindow.currentMode == "anomalies" or mainWindow.currentMode == "images_in_classificationSession"):
                action_onlyQualityPassed = QAction("Только качественные", mainWindow)
                action_onlyQualityPassed.triggered.connect(lambda: ObjectsManager.show_only_withStatus(mainWindow, "quality_passed"))
                menu.addAction(action_onlyQualityPassed)

                action_onlyQualityFailed = QAction("Только некачественные", mainWindow)
                action_onlyQualityFailed.triggered.connect(lambda: ObjectsManager.show_only_withStatus(mainWindow, "quality_failed"))
                menu.addAction(action_onlyQualityFailed)

                action_NoQualityTested = QAction("Только с непроверенным качеством", mainWindow)
                action_NoQualityTested.triggered.connect(lambda: ObjectsManager.show_only_withStatus(mainWindow, "uploaded"))
                menu.addAction(action_NoQualityTested)

                action_noTags = QAction("Только без тегов", mainWindow)
                action_noTags.triggered.connect(lambda: ObjectsManager.show_only_noTags_images(mainWindow))
                menu.addAction(action_noTags)

                action_withTags = QAction("Только с тегами", mainWindow)
                action_withTags.triggered.connect(lambda: ObjectsManager.show_only_tagged_images(mainWindow))
                menu.addAction(action_withTags)
            if mainWindow.currentMode == "sessions_on_dataset":
                action_onlyKMeans = QAction("Только K-Means", mainWindow)
                action_onlyKMeans.triggered.connect(lambda: ObjectsManager.show_sessions_with_algorythm(mainWindow, 'K-Means'))
                menu.addAction(action_onlyKMeans)
                action_onlyDBSCAN = QAction("Только DBSCAN", mainWindow)
                action_onlyDBSCAN.triggered.connect(lambda: ObjectsManager.show_sessions_with_algorythm(mainWindow, 'DBSCAN'))
                menu.addAction(action_onlyDBSCAN)

            if mainWindow.currentMode != "clusters" and mainWindow.currentMode != "labeled_groups":
                menu.addSeparator()
                #отмена всех фильтров
                action_cancelFilters = QAction("Снять фильтры", mainWindow)
                action_cancelFilters.triggered.connect(lambda: ObjectsManager.show_all(mainWindow))
                menu.addAction(action_cancelFilters)


            mainWindow.btn_sort.setMenu(menu)




    @staticmethod
    def setup_modelsButton(mainWindow):
        #кнопка экспорта в меню
        mainWindow.models_btn = mainWindow.findChild(QToolButton, "models_button")
        if mainWindow.models_btn:
            menu = QMenu(mainWindow)
            #Загруженные модели
            action_choose_model = QAction("Выбрать модель...", mainWindow)
            action_choose_model.triggered.connect(mainWindow.show_modelLOR_data)
            menu.addAction(action_choose_model)

            #Добавить модель
            action_import_model = QAction("Загрузить классификационную модель", mainWindow)
            action_import_model.triggered.connect(mainWindow.load_new_model)
            menu.addAction(action_import_model)

            mainWindow.models_btn.setMenu(menu)


    @staticmethod
    def setup_importButton(mainWindow):
        # кнопка иморта в меню
        mainWindow.btn_load = mainWindow.findChild(QToolButton, "file_button")
        if mainWindow.btn_load:
            menu = QMenu(mainWindow)
            action_importImage = QAction("Импорт изображения", mainWindow)

            if len(mainWindow.datasets_list) == 0:
                action_importImage.setEnabled(False)

            action_importDataset = QAction("Импорт датасета", mainWindow)

            menu.addAction(action_importImage)
            menu.addAction(action_importDataset)

            menu.addSeparator()

            # экспорт датасетов (можно выбрать несколько)
            action_dataset_export = QAction("Экспорт датасета", mainWindow)
            if len(mainWindow.datasets_list) == 0:
                action_dataset_export.setEnabled(False)
            action_dataset_export.triggered.connect(mainWindow.export_datasets)
            menu.addAction(action_dataset_export)

            mainWindow.btn_load.setMenu(menu)
            action_importImage.triggered.connect(mainWindow.import_image)
            action_importDataset.triggered.connect(mainWindow.import_dataset)

    @staticmethod
    def setup_backButton(mainWindow):
        back_button = mainWindow.findChild(QPushButton, "back_button")
        back_button.clicked.connect(mainWindow.prev_page)

    @staticmethod
    def setup_instruments(mainWindow):
        #настройка кнопки "Инструменты" в меню
        mainWindow.btn_instruments = mainWindow.findChild(QToolButton, "instruments_button")
        if mainWindow.btn_instruments:
            menu = QMenu(mainWindow)

            #функция "Анализ качества изображений"
            action_analyseQuality = QAction("Анализ качества изображений", mainWindow)
            if len(mainWindow.datasets_list) == 0:
                action_analyseQuality.setEnabled(False)
            menu.addAction(action_analyseQuality)

            #функция "Поиск дубликатов"
            action_duplicateSearch = QAction("Поиск дубликатов", mainWindow)
            if len(mainWindow.datasets_list) == 0:
                action_duplicateSearch.setEnabled(False)
            menu.addAction(action_duplicateSearch)

            #функция кластеризация
            action_clasterization = QAction("Кластеризация", mainWindow)
            if len(mainWindow.datasets_list) == 0:
                action_clasterization.setEnabled(False)
            menu.addAction(action_clasterization)

            menu.addSeparator()

            #функция классификация НС
            action_neuralNetwork_classification = QAction("Классификация НС", mainWindow)
            if len(mainWindow.datasets_list) == 0:
                action_neuralNetwork_classification.setEnabled(False)
            menu.addAction(action_neuralNetwork_classification)
            action_neuralNetwork_classification.triggered.connect(mainWindow.neural_network_clasify)


            mainWindow.btn_instruments.setMenu(menu)
            action_analyseQuality.triggered.connect(mainWindow.analyse_quality)
            action_duplicateSearch.triggered.connect(mainWindow.find_duplicates)
            action_clasterization.triggered.connect(mainWindow.clasterize)











