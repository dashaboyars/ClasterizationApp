from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QProgressDialog, QMessageBox, QFileDialog, QDialog

from ui.dialogs.changeName_dialog import ChangeNameDialog
from ui.dialogs.cluster_params_dialog import ClusterParamsDialog
from ui.dialogs.duplicates_dialog import DuplicatesDialog
from ui.dialogs.selectSession_dialog import SelectSessionDialog
from ui.dialogs.select_dataset_dialog import SelectDatasetDialog
from ui.dialogs.sessionName_dialog import SessionNameDialog
from ui.dialogs.session_quality_dialog import SessionQualityDialog
from ui.dialogs.similarityLevel_dialog import SimilarityLevelDialog
from ui.dialogs.clusterization_params_dialog import ClusterizationParamsDialog



class FeedbackManager():

    @staticmethod
    def show_image_params(image):
        return


    @staticmethod
    def get_tag(mainWindow):
        from ui.dialogs.tagInput_dialog import TagInputDialog
        tagInput_dialog = TagInputDialog(mainWindow)
        if tagInput_dialog.exec() == QDialog.DialogCode.Accepted:
            return tagInput_dialog.tag_name
        return None


    @staticmethod
    def get_new_name(mainWindow, item=None):
        changeName_dialog = ChangeNameDialog(item)
        correct = True
        if changeName_dialog.exec() == QDialog.DialogCode.Accepted:
            return changeName_dialog.name
        return None

    @staticmethod
    def show_cluster_params(cluster, mainWindow):
        clusterParams_dialog = ClusterParamsDialog(cluster, mainWindow)
        clusterParams_dialog.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        mainWindow.opened_windows.append(clusterParams_dialog)
        clusterParams_dialog.show()

    @staticmethod
    def show_session_params(session, mainWindow):
        sessionParams_dialog = SessionQualityDialog(session, mainWindow)
        sessionParams_dialog.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        mainWindow.opened_windows.append(sessionParams_dialog)
        sessionParams_dialog.show()

    @staticmethod
    def get_clusterization_params(mainWindow, images_list):
        clusterization_params_dialog = ClusterizationParamsDialog(images_list, mainWindow)
        if clusterization_params_dialog.exec() == QDialog.DialogCode.Accepted:
            return clusterization_params_dialog.params
        return None

    @staticmethod
    def get_session_name(mainWindow, dataset):
        existing_names = [sn.name for sn in dataset.sessions_list]
        while True:
            sessionName_dialog = SessionNameDialog(dataset.id, mainWindow)
            if sessionName_dialog.exec() == QDialog.DialogCode.Accepted:
                if sessionName_dialog.name in existing_names:
                    FeedbackManager.SessionAlreadyExists(mainWindow)
                else:
                    return sessionName_dialog.name
            else:
                return None

    @staticmethod
    def get_existing_directory(mainWindow):
        directory = QFileDialog.getExistingDirectory(
            mainWindow,  # родительское окно
            "Выберите папку для экспорта датасета",
            "",  # начальная директория (пусто — последняя использованная)
            QFileDialog.Option.ShowDirsOnly
        )
        if not directory:
            return None
        return directory

    @staticmethod
    def get_selected_session(mainWindow, train_mode=None):
        selectSession_dialog = SelectSessionDialog(mainWindow.datasets_list, train_mode, mainWindow)
        selectSession_dialog.show()
        if selectSession_dialog.exec() == QDialog.DialogCode.Accepted:
            return selectSession_dialog.selected_session, selectSession_dialog.selected_dataset
        return None


    @staticmethod
    def get_selected_dataset(mainWindow):
        selectDataset_dialog = SelectDatasetDialog(mainWindow.datasets_list, mainWindow)
        selectDataset_dialog.show()
        if selectDataset_dialog.exec() == QDialog.DialogCode.Accepted:
            return selectDataset_dialog.get_selected_dataset()
        return None

    @staticmethod
    def get_toDelete_list(mainWindow, duplicate_groups):
        duplicate_dialog = DuplicatesDialog(duplicate_groups, mainWindow)
        duplicate_dialog.setWindowModality(Qt.WindowModality.NonModal)
        if duplicate_dialog.exec() == QDialog.DialogCode.Accepted:
            return duplicate_dialog.to_delete
        return None

    @staticmethod
    def get_similarity_level(mainWindow):
        similarityLevel_dialog = SimilarityLevelDialog(mainWindow)
        similarityLevel_dialog.show()
        if similarityLevel_dialog.exec() == QDialog.DialogCode.Accepted:
            return similarityLevel_dialog.similarityPercent/100
        return None

    @staticmethod
    def AllImagesSimilar_Warning(mainWindow):
        QMessageBox.warning(
            mainWindow,
            "Не удалось построить карту эмбеддингов",
            "Все изображения кластера идентичны! Карту построить не удалось!"
        )

    @staticmethod
    def UnavailableModel_Warning(mainWindow, current_mode=None):
        if current_mode not in ["ear", "nose", "larynx", "pharynx"]:
            msg = "Данная модель может быть использована только для обучения на распознавание органов или их классификации"
        if current_mode == "ear":
            msg = "Данная модель может быть использована только для обучения на распознавание патологий уха или их классификации"
        if current_mode == "nose":
            msg = "Данная модель может быть использована только для обучения на распознавание патологий носа или их классификации"
        if current_mode == "larynx":
            msg = "Данная модель может быть использована только для обучения на распознавание патологий гортани или их классификации"
        if current_mode == "pharynx":
            msg = "Данная модель может быть использована только для обучения на распознавание патологий глотки или их классификации"
        QMessageBox.warning(
            mainWindow,
            "Версия модели недоступна для использования",
            msg
        )

    @staticmethod
    def NoImages_Warning(mainWindow):
        QMessageBox.warning(
            mainWindow,
            "Не удалось построить карту эмбеддингов",
            "Изображения отсутствуют! Карту построить не удалось!"
        )

    @staticmethod
    def ImageExists_Warning(mainWindow, name):
        QMessageBox.warning(
            mainWindow,
            f"Ошибка переноса изображения: {name}",
            "Изображение уже находится в целевом кластере! Добавить дубликат невозможно!"
        )

    @staticmethod
    def UnsupportedDirectory_Warning(mainWindow):
        QMessageBox.warning(
            mainWindow,
            "Некорректная директория",
            "Нельзя добавить изображения в данную директорию!"
        )
    @staticmethod
    def DatasetCreated_Message(mainWindow, dataset_name, count_images):
        QMessageBox.information(
            mainWindow,
            "Успех",
            f"Датасет '{dataset_name}' создан!\n"
            f"Добавлено изображений: {count_images}"
        )
    @staticmethod
    def ImagesAdded_Message(mainWindow, dataset_name, count_images):
        QMessageBox.information(
            mainWindow,
            "Успех",
            f"Добавлено изображений: {count_images}\nДатасет: {dataset_name}"
        )

    @staticmethod
    def DatasetExported_Message(mainWindow, dataset_name, sessions_count, images_count):
        QMessageBox.information(
            mainWindow,
            "Успешный экспорт",
            f"Датасет: {dataset_name}\nСессий: {sessions_count}\Изображений: {images_count}"
        )

    @staticmethod
    def WrongTagInput(parent, error_text):
        QMessageBox.warning(
            parent,
            "Некорректный ввод",
            error_text
        )

    @staticmethod
    def SessionAlreadyExists(mainWindow):
        QMessageBox.warning(
            mainWindow,
            "Ошибка создания сессии",
            "Сессия с таким именем уже существует!"
        )

    @staticmethod
    def DatasetAlreadyExists(mainWindow):
        QMessageBox.warning(
            mainWindow,
            "Ошибка создания датасета",
            "Датасет с таким именем уже существует!"
        )
    @staticmethod
    def DatasetCreation_Answer(mainWindow, dataset_name, images_count):
        reply = QMessageBox.question(
            mainWindow,
            "Подтверждение",
            f"Создать датасет '{dataset_name}'?\n"
            f"Найдено изображений: {images_count}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        return reply
    @staticmethod
    def NoDatasets_Warning(mainWindow):
        QMessageBox.warning(
            mainWindow,
            "Нет датасетов",
            "Нет созданных датасетов!"
        )

    @staticmethod
    def EmptyDataset_Warning(mainWindow):
        QMessageBox.warning(
            mainWindow,
            "Пустой датасет",
            "В датасете нет изображений.\nДобавьте изображения в датасет!"
        )
    @staticmethod
    def NoImagesInFolder_Warning(mainWindow):
        QMessageBox.warning(
            mainWindow,
            "Нет изображений",
            f"В папке не найдено изображений!"
        )

    @staticmethod
    def WrongName_Warning(mainWindow):
        QMessageBox.warning(
            mainWindow,
            "Некорректный ввод",
            f"Введите имя загружаемой модели!"
        )

    @staticmethod
    def Open_FolderSelect_Dialog(mainWindow):
        folder_path = QFileDialog.getExistingDirectory(
            mainWindow,
            "Выберите папку с изображениями",
            "",  # стартовая директория
            QFileDialog.Option.ShowDirsOnly
        )
        return folder_path
    @staticmethod
    def Open_ImageSelect_Dialog(mainWindow):
        files, selected_filter = QFileDialog.getOpenFileNames(
            mainWindow,
            "Выберите изображения",
            "",
            "Изображения (*.png *.jpg *.jpeg *.bmp);"  # фильтры
        )
        return files

    @staticmethod
    def ShowProgress_OnNeuralNetworkClassification(mainWindow):
        operation_id = mainWindow.operation_counter
        mainWindow.operation_counter += 1
        progress = QProgressDialog(
            "Идет классификация...",  # текст
            "Отмена",  # текст кнопки отмены
            0,  # минимум
            100,  # максимум (100%)
            mainWindow  # родитель
        )
        progress.setWindowTitle(f"Нейросетевая классификация...")
        progress.setMinimumDuration(0)  # показывать сразу
        progress.setValue(0)
        progress.show()
        mainWindow.progress_bars[operation_id] = progress
        return operation_id

    @staticmethod
    def ShowProgress_OnTrainingModel(mainWindow):
        operation_id = mainWindow.operation_counter
        mainWindow.operation_counter += 1
        progress = QProgressDialog(
            "Идет обучение модели...",  # текст
            "Отмена",  # текст кнопки отмены
            0,  # минимум
            100,  # максимум (100%)
            mainWindow  # родитель
        )
        progress.setWindowTitle(f"Обучение модели...")
        progress.setMinimumDuration(0)  # показывать сразу
        progress.setValue(0)
        progress.show()
        mainWindow.progress_bars[operation_id] = progress
        return operation_id

    @staticmethod
    def ShowProgress_OnTSNE(mainWindow):
        operation_id = mainWindow.operation_counter
        mainWindow.operation_counter += 1
        progress = QProgressDialog(
            "Составление графиков распределения...",  # текст
            "Отмена",  # текст кнопки отмены
            0,  # минимум
            100,  # максимум (100%)
            mainWindow  # родитель
        )
        progress.setWindowTitle(f"Работа TSNE...")
        progress.setMinimumDuration(0)  # показывать сразу
        progress.setValue(0)
        progress.show()
        mainWindow.progress_bars[operation_id] = progress
        return operation_id

    @staticmethod
    def ShowProgress_OnClasterization(mainWindow, dataset_name):
        operation_id = mainWindow.operation_counter
        mainWindow.operation_counter += 1
        progress = QProgressDialog(
            f"Идет кластеризация датасета '{dataset_name}'...",  # текст
            "Отмена",  # текст кнопки отмены
            0,  # минимум
            100,  # максимум (100%)
            mainWindow  # родитель
        )
        progress.setWindowTitle(f"Кластеризация датасета '{dataset_name}'")
        progress.setMinimumDuration(0)  # показывать сразу
        progress.setValue(0)
        progress.show()
        mainWindow.progress_bars[operation_id] = progress
        return operation_id

    @staticmethod
    def ShowProgress_OnCountParams(mainWindow):
        operation_id = mainWindow.operation_counter
        mainWindow.operation_counter += 1
        progress = QProgressDialog(
            "Идет расчет оптимального значения параметров...",  # текст
            "Отмена",  # текст кнопки отмены
            0,  # минимум
            100,  # максимум (100%)
            None  # родитель
        )
        progress.setWindowTitle("Расчет оптимальных параметров")
        progress.setMinimumDuration(0)  # показывать сразу
        progress.setValue(0)
        progress.show()
        mainWindow.progress_bars[operation_id] = progress
        return operation_id

    @staticmethod
    def ShowProgress_OnDuplicates(mainWindow):
        operation_id = mainWindow.operation_counter
        mainWindow.operation_counter += 1
        progress = QProgressDialog(
            "Идет поиск дубликатов...",  # текст
            "Отмена",  # текст кнопки отмены
            0,  # минимум
            100,  # максимум (100%)
            mainWindow  # родитель
        )
        progress.setWindowTitle("Поиск дубликатов")
        progress.setMinimumDuration(0)  # показывать сразу
        progress.setValue(0)
        progress.show()
        mainWindow.progress_bars[operation_id] = progress
        return operation_id

    @staticmethod
    def ShowProgress_OnExportDataset(mainWindow):
        operation_id = mainWindow.operation_counter
        mainWindow.operation_counter += 1
        progress = QProgressDialog(
            "Идет экспорт датасета...",  # текст
            "Отмена",  # текст кнопки отмены
            0,  # минимум
            100,  # максимум (100%)
            mainWindow  # родитель
        )
        progress.setWindowTitle("Экспорт датасета")

        progress.setMinimumDuration(0)  # показывать сразу
        progress.setValue(0)
        progress.show()
        mainWindow.progress_bars[operation_id] = progress
        return operation_id

    @staticmethod
    def ShowProgress(mainWindow, import_object):
        operation_id = mainWindow.operation_counter
        mainWindow.operation_counter += 1
        if import_object == "dataset":
            progress = QProgressDialog(
                "Идет импорт датасета...",  # текст
                "Отмена",  # текст кнопки отмены
                0,  # минимум
                100,  # максимум (100%)
                mainWindow  # родитель
            )
            progress.setWindowTitle("Импорт датасета")
        else:
            progress = QProgressDialog(
                "Идет импорт изображений...",  # текст
                "Отмена",  # текст кнопки отмены
                0,  # минимум
                100,  # максимум (100%)
                mainWindow # родитель
            )
            progress.setWindowTitle("Импорт изображений")

        progress.setMinimumDuration(0)  # показывать сразу
        progress.setValue(0)
        progress.show()
        mainWindow.progress_bars[operation_id] = progress
        return operation_id