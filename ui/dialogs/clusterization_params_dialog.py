import os

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import *
from qtpy import uic

from services.clasterization_service import ClusterizationService


class ClusterizationParamsDialog(QDialog):
    def __init__(self, images_list, parent=None):
        super().__init__(parent)
        ui_path = os.path.join(os.path.dirname(__file__), '../../gui/dialogs/clasterization_params_dialog.ui')
        uic.loadUi(ui_path, self)

        self.parent = parent
        self.images = images_list
        self.params = None

        #сервисы
        self.clusterization_service = ClusterizationService(parent.db)

        #настройка содержимого окна
        #общие элементы
        self.algorythm_comboBox = self.findChild(QComboBox, "algorythm_comboBox")
        self.stackedWidget = self.findChild(QStackedWidget, "stackedWidget")
        self.stackedWidget.setCurrentIndex(0)
        button_box = self.findChild(QDialogButtonBox, "buttonBox")
        self.btn_ok = button_box.button(QDialogButtonBox.StandardButton.Ok)
        self.btn_cancel = button_box.button(QDialogButtonBox.StandardButton.Cancel)
        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)

        #элементы для K-Means
        #self.btn_find_optimal_k = self.findChild(QPushButton, "find_optimalK_pushButton")
        self.kValue_spinBox = self.findChild(QSpinBox, "kValue_spinBox")
        self.maxIteration_spinBox = self.findChild(QSpinBox, "maxIteration_spinBox")
        self.tol_doubleSpinBox = self.findChild(QDoubleSpinBox, "tol_doubleSpinBox")
        self.initialization_comboBox = self.findChild(QComboBox, "initialization_comboBox")
        self.similarityMethod_KMeans_comboBox = self.findChild(QComboBox, "similarityMethod_KMeans_comboBox")

        #элементы для DBSCAN
        self.eps_doubleSpinBox = self.findChild(QDoubleSpinBox, "eps_doubleSpinBox")
        self.minPoints_spinBox = self.findChild(QSpinBox, "minPoints_spinBox")
        self.similarityMethod_DBSCAN_comboBox = self.findChild(QComboBox, "similarityMethod_DBSCAN_comboBox")
        self.get_optimal_params_pushButton = self.findChild(QPushButton, "get_optimal_params_pushButton")

        #настройка всех элементов
        self.setup_ui()

        self.similarityMethod_KMeans_comboBox.currentIndexChanged.connect(self.on_similarity_method_changed)


    def on_similarity_method_changed(self):
        if self.similarityMethod_KMeans_comboBox.currentText() == "Манхэттенское расстояние (Manhattan/L1)":
            self.initialization_comboBox.clear()
            self.initialization_comboBox.addItems(["K-Means++"])
        else:
            self.initialization_comboBox.clear()
            self.initialization_comboBox.addItems(["K-Means++", "Случайный выбор",
                                                   "Furthest (самые удаленные точки)",
                                                   "First K (первые k точек)"])


    def accept(self):
        if self.algorythm_comboBox.currentText() == "K-Means":
            self.params = {
                'algorythm': "K-Means",
                'k': self.kValue_spinBox.value(),
                'max_iterations': self.maxIteration_spinBox.value(),
                'tol': self.tol_doubleSpinBox.value(),
                'initialization_method': self.initialization_comboBox.currentText(),
                'similarity_method':  self.similarityMethod_KMeans_comboBox.currentText()
            }
        elif self.algorythm_comboBox.currentText() == "DBSCAN":
            self.params = {
                'algorythm': "DBSCAN",
                'eps': self.eps_doubleSpinBox.value(),
                'min_samples': self.minPoints_spinBox.value(),
                'similarity_method': self.similarityMethod_DBSCAN_comboBox.currentText()
            }
        super().accept()

    def reject(self):
        super().reject()

    def setup_ui(self):
        #настройка выбора метода кластеризации
        self.algorythm_comboBox.addItem("K-Means")
        self.algorythm_comboBox.addItem("DBSCAN")
        self.algorythm_comboBox.currentIndexChanged.connect(self.on_algorythm_changed)

        self.setup_KMeans_page()
        self.setup_DBSCAN_page()

    def setup_DBSCAN_page(self):
        #настройка esp и min_samples спин-боксов и кнопки расчета
        #self.set_optimal_esp_minSamples()
        self.get_optimal_params_pushButton.clicked.connect(self.set_optimal_esp_minSamples)

        # настройка комбо-бокса способа измерения похожести
        self.similarityMethod_DBSCAN_comboBox.addItems([
                "Косинусное расстояние (Cosine Similarity)",
                "Евклидово расстояние (Euclidean)",
                "Манхэттенское расстояние (Manhattan/L1)",
                "Чебышева расстояние (Chebyshev)"
            ])




    def setup_KMeans_page(self):
        # настройка кнопки выбора оптимального К
        #self.btn_find_optimal_k.clicked.connect(self.set_optimal_k)

        # настройка комбо-бокса метода инициализации
        self.initialization_comboBox.addItems(["K-Means++", "Случайный выбор",
                                               "Furthest (самые удаленные точки)",
                                               "First K (первые k точек)"])
        self.initialization_comboBox.setCurrentIndex(0)

        # настройка комбо-бокса способа измерения похожести
        self.similarityMethod_KMeans_comboBox.addItems(["Косинусное расстояние (Cosine Similarity)",
                                                        "Евклидово расстояние (Euclidean)",
                                                        "Манхэттенское расстояние (Manhattan/L1)"])


    def on_algorythm_changed(self):
        if self.algorythm_comboBox.currentText() == "K-Means":
            self.stackedWidget.setCurrentIndex(0)
        else:
            self.stackedWidget.setCurrentIndex(1)


    def set_optimal_esp_minSamples(self):
        from ui.interaction_subsystem.feedback_manager import FeedbackManager
        operation_id = FeedbackManager.ShowProgress_OnCountParams(self.parent)
        if self.similarityMethod_DBSCAN_comboBox.currentText() == "Косинусное расстояние (Cosine Similarity)":
            metric = 'cosine'
        elif self.similarityMethod_DBSCAN_comboBox.currentText() == "Евклидово расстояние (Euclidean)":
            metric = 'euclidean'
        elif self.similarityMethod_DBSCAN_comboBox.currentText() == "Манхэттенское расстояние (Manhattan/L1)":
            metric = 'manhattan'
        elif self.similarityMethod_DBSCAN_comboBox.currentText() == "Чебышева расстояние (Chebyshev)":
            metric = 'chebyshev'

        #запуск в фоновом потоке
        def countMinSamplesEsp_task(progress_callback, cancel_check):
            return self.clusterization_service.get_optimal_minSamples_Esp(self.images, metric, progress_callback, cancel_check)

        self.parent.Start_Thread(countMinSamplesEsp_task, "count_minSamples_esp", operation_id, self)


    def set_optimal_k(self):
        from ui.interaction_subsystem.feedback_manager import FeedbackManager
        operation_id = FeedbackManager.ShowProgress_OnCountParams(self.parent)
        #запуск в фоновом потоке
        def countK_task(progress_callback, cancel_check):
            return self.clusterization_service.get_optimal_k(self.images, progress_callback, cancel_check)
        self.parent.Start_Thread(countK_task, "countK", operation_id, self)

    def on_countK_finished(self, result, progress_id):
        self.parent.progress_bars[progress_id].close()
        del self.parent.progress_bars[progress_id]
        del self.parent.threads[progress_id]

        self.kValue_spinBox.setValue(result)

    def on_countEspMinSamples_finished(self, result, progress_id):
        self.parent.progress_bars[progress_id].close()
        del self.parent.progress_bars[progress_id]
        del self.parent.threads[progress_id]

        # устанавливаем значения
        self.eps_doubleSpinBox.setValue(result[1])
        self.minPoints_spinBox.setValue(result[0])

