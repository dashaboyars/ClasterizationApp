import os

from PyQt6.QtWidgets import QDialog, QLineEdit, QLabel, QPushButton, QStackedWidget
from qtpy import uic

from services.qualityAnalyse_service import QualityAnalyseService

class SessionQualityDialog(QDialog):
    def __init__(self, session, parent=None):
        super().__init__(parent)
        self.parent = parent
        # Загружаем UI из файла
        ui_path = os.path.join(os.path.dirname(__file__), '../../gui/dialogs/session_quality_dialog.ui')
        uic.loadUi(ui_path, self)

        self.session = session

        self.name_lineEdit = self.findChild(QLineEdit, "name_lineEdit")
        self.dataset_lineEdit = self.findChild(QLineEdit, "dataset_lineEdit")
        self.time_lineEdit = self.findChild(QLineEdit, "time_lineEdit")
        self.algorythm_lineEdit = self.findChild(QLineEdit, "algorythm_lineEdit")
        self.size_lineEdit = self.findChild(QLineEdit, "size_lineEdit")
        self.esp_lineEdit = self.findChild(QLineEdit, "esp_lineEdit")
        self.minSamples_lineEdit = self.findChild(QLineEdit, "minSamples_lineEdit")
        self.similarity_lineEdit = self.findChild(QLineEdit, "similarity_lineEdit")
        self.k_lineEdit = self.findChild(QLineEdit, "k_lineEdit")
        self.maxIter_lineEdit = self.findChild(QLineEdit, "maxIter_lineEdit")
        self.tol_lineEdit = self.findChild(QLineEdit, "tol_lineEdit")
        self.initMethod_lineEdit = self.findChild(QLineEdit, "initMethod_lineEdit")
        self.silhouette_lineEdit = self.findChild(QLineEdit, "silhouette_lineEdit")
        self.chi_lineEdit = self.findChild(QLineEdit, "chi_lineEdit")
        self.dbi_lineEdit = self.findChild(QLineEdit, "dbi_lineEdit")

        self.stacked_widget = self.findChild(QStackedWidget, "stackedWidget")

        self.ok_button = self.findChild(QPushButton, "ok_button")
        self.ok_button.clicked.connect(self.cancel)

        self.set_params(session)

        self.name_lineEdit.setReadOnly(True)
        self.dataset_lineEdit.setReadOnly(True)
        self.time_lineEdit.setReadOnly(True)
        self.algorythm_lineEdit.setReadOnly(True)
        self.size_lineEdit.setReadOnly(True)
        self.esp_lineEdit.setReadOnly(True)
        self.minSamples_lineEdit.setReadOnly(True)
        self.similarity_lineEdit.setReadOnly(True)
        self.k_lineEdit.setReadOnly(True)
        self.maxIter_lineEdit.setReadOnly(True)
        self.tol_lineEdit.setReadOnly(True)
        self.initMethod_lineEdit.setReadOnly(True)
        self.silhouette_lineEdit.setReadOnly(True)
        self.chi_lineEdit.setReadOnly(True)
        self.dbi_lineEdit.setReadOnly(True)

    def set_params(self, session):
        from ui.interaction_subsystem.objects_manager import ObjectsManager
        self.name_lineEdit.setText(session.name)

        dataset = ObjectsManager.find_dataset_by_id(self.parent, session.dataset_id)
        self.dataset_lineEdit.setText(dataset.name)

        self.time_lineEdit.setText(str(session.created_at))
        self.algorythm_lineEdit.setText(session.algorythm)

        if session.algorythm == "K-Means":
            self.stacked_widget.setCurrentIndex(0)
            self.k_lineEdit.setText(str(session.params["k"]))
            self.maxIter_lineEdit.setText(str(session.params["max_iterations"]))
            self.tol_lineEdit.setText(str(session.params["tol"]))
            self.initMethod_lineEdit.setText(str(session.params["initialization_method"]))
        else:
            self.stacked_widget.setCurrentIndex(1)
            self.size_lineEdit.setText(str(len(session.clusters_list)))
            self.esp_lineEdit.setText(str(session.params["eps"]))
            self.minSamples_lineEdit.setText(str(session.params["min_samples"]))

        if session.params["similarity_method"] == "Косинусное расстояние (Cosine Similarity)":
            metric = 'cosine'
        elif session.params["similarity_method"] == "Евклидово расстояние (Euclidean)":
            metric = 'euclidean'
        elif session.params["similarity_method"]  == "Манхэттенское расстояние (Manhattan/L1)":
            metric = 'manhattan'
        elif session.params["similarity_method"] == "Чебышева расстояние (Chebyshev)":
            metric = 'chebyshev'
        self.similarity_lineEdit.setText(metric)

        if session.silhouette is None:
            params = ObjectsManager.get_session_params(session, self.parent)
            session.set_quality_params(params)

        if session.silhouette is None:
            self.silhouette_lineEdit.setText("-")
        else:
            self.silhouette_lineEdit.setText(str(session.silhouette))
        if session.CHI_index is None:
            self.chi_lineEdit.setText("-")
        else:
            self.chi_lineEdit.setText(str(session.CHI_index))
        if session.DBI_index is None:
            self.dbi_lineEdit.setText("-")
        else:
            self.dbi_lineEdit.setText(str(session.DBI_index))




    def cancel(self):
        self.parent.opened_windows.remove(self)
        self.close()
