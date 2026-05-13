import os

from PyQt6.QtWidgets import QDialog, QLineEdit, QLabel, QPushButton
from qtpy import uic

from services.qualityAnalyse_service import QualityAnalyseService


class ClusterParamsDialog(QDialog):
    def __init__(self, cluster, parent=None):
        super().__init__(parent)
        self.parent = parent
        # Загружаем UI из файла
        ui_path = os.path.join(os.path.dirname(__file__), '../../gui/dialogs/clusterParams_dialog.ui')
        uic.loadUi(ui_path, self)

        self.cluster = cluster

        self.name_lineEdit = self.findChild(QLineEdit, "name_lineEdit")
        self.session_lineEdit = self.findChild(QLineEdit, "session_lineEdit")
        self.time_lineEdit = self.findChild(QLineEdit, "time_lineEdit")
        self.size_lineEdit = self.findChild(QLineEdit, "size_lineEdit")
        self.cohesion_lineEdit = self.findChild(QLineEdit, "cohesion_lineEdit")
        self.separation_lineEdit = self.findChild(QLineEdit, "separation_lineEdit")
        self.silhouette_lineEdit = self.findChild(QLineEdit, "silhouette_lineEdit")
        self.density_lineEdit = self.findChild(QLineEdit, "density_lineEdit")
        self.radius_lineEdit = self.findChild(QLineEdit, "radius_lineEdit")
        self.session_info_label = self.findChild(QLabel, "session_info_label")
        self.ok_button = self.findChild(QPushButton, "ok_button")

        self.ok_button.clicked.connect(self.cancel)

        self.set_params(cluster)

        self.name_lineEdit.setReadOnly(True)
        self.session_lineEdit.setReadOnly(True)
        self.time_lineEdit.setReadOnly(True)
        self.size_lineEdit.setReadOnly(True)
        self.cohesion_lineEdit.setReadOnly(True)
        self.separation_lineEdit.setReadOnly(True)
        self.silhouette_lineEdit.setReadOnly(True)
        self.density_lineEdit.setReadOnly(True)
        self.radius_lineEdit.setReadOnly(True)

    def cancel(self):
        self.parent.opened_windows.remove(self)
        self.close()

    def set_params(self, cluster):
        from ui.interaction_subsystem.objects_manager import ObjectsManager
        session = ObjectsManager.find_session_by_id(self.parent, cluster.session_id)
        if cluster.size is None:
            params = ObjectsManager.get_cluster_params(cluster, session, self.parent)
            #сохранение в ui
            cluster.set_quality_params(params)
        self.name_lineEdit.setText(cluster.name)
        self.session_lineEdit.setText(session.name)
        self.time_lineEdit.setText(cluster.create_time)
        self.size_lineEdit.setText(str(cluster.size))
        self.cohesion_lineEdit.setText(str(round(cluster.cohesion, 4)))
        self.separation_lineEdit.setText(str(round(cluster.separation, 4)))
        self.silhouette_lineEdit.setText(str(round(cluster.silhouette, 4)))
        self.density_lineEdit.setText(str(round(cluster.density, 4)))
        self.radius_lineEdit.setText(str(round(cluster.radius, 4)))

        self.session_info_label.setText(f"Получен с помощью: {session.algorythm} (k={len(session.clusters_list)})")