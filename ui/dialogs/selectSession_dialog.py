import os

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QListWidget, QListWidgetItem, QPushButton, QHBoxLayout, QLabel, \
    QComboBox, QDialogButtonBox
from PyQt6.QtCore import Qt
from qtpy import uic

class SelectSessionDialog(QDialog):
    def __init__(self, datasets_list, train_mode=None, parent=None):
        super().__init__(parent)
        # Загружаем UI из файла
        ui_path = os.path.join(os.path.dirname(__file__), '../../gui/dialogs/select_session_dialog.ui')
        uic.loadUi(ui_path, self)

        self.selected_dataset = None
        self.selected_session = None
        self.train_mode = train_mode

        self.datasets = [ds for ds in datasets_list if len(ds.sessions_list) > 0]

        self.sessions_comboBox = self.findChild(QComboBox, "sessions_comboBox")
        self.datasets_comboBox = self.findChild(QComboBox, "datasets_comboBox")
        button_box = self.findChild(QDialogButtonBox, "buttonBox")
        self.btn_ok = button_box.button(QDialogButtonBox.StandardButton.Ok)
        self.btn_cancel = button_box.button(QDialogButtonBox.StandardButton.Cancel)
        self.warning_label = self.findChild(QLabel, "warning_label")

        self.set_warning()


        #настройка комбобоксов
        self.fill_datasetsComboBox()
        self.on_datasetChanged()
        self.datasets_comboBox.currentIndexChanged.connect(self.on_datasetChanged)

        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)

    def reject(self):
        super().reject()

    def accept(self):
        self.selected_dataset = self.datasets_comboBox.currentData()
        self.selected_session = self.sessions_comboBox.currentData()
        super().accept()

    def set_warning(self):
        if not self.train_mode:
            self.warning_label.setText("Обратите внимание: сессия должна содержать 4-5 кластеров с названиями 'Нос', 'Ухо', 'Глотка', 'Гортань', 'Другое'")
        elif self.train_mode == "ear":
            self.warning_label.setText("Обратите внимание: сессия должна содержать 5 кластеров с названиями 'Норма', 'Отит', 'Тимпаносклероз', 'Шунт', 'Инородное тело'")
        elif self.train_mode == "larynx":
            self.warning_label.setText(
                "Обратите внимание: сессия должна содержать 6 кластеров с названиями 'Норма', 'Новообразование', 'Ларингит', 'Полип', 'Узелки', 'Папилломатоз'")
        elif self.train_mode == "nose":
            self.warning_label.setText(
                "Обратите внимание: сессия должна содержать 4 кластера с названиями 'Норма', 'Ринит', 'Синусит', 'Смещенная перегородка'")
        elif self.train_mode == "pharynx":
            self.warning_label.setText(
                "Обратите внимание: сессия должна содержать 6 кластеров с названиями 'Норма', 'Фарингит', 'Тонзиллит', 'Гипертрофия миндалин'")

    def on_datasetChanged(self):
        currentDataset = self.datasets_comboBox.currentData()
        self.fill_sessionComboBox(currentDataset.sessions_list, currentDataset.classification_groups)

    def fill_datasetsComboBox(self):
        self.datasets_comboBox.clear()
        for dataset in self.datasets:
            self.datasets_comboBox.addItem(dataset.name, dataset)

    def fill_sessionComboBox(self, sessions, classif_groups):
        self.sessions_comboBox.clear()
        if self.train_mode == "ear":
            available_labels = ['Норма', 'Отит', 'Тимпаносклероз', 'Шунт', 'Инородное тело']
        elif self.train_mode == "larynx":
            available_labels = ['Норма', 'Новообразование', 'Ларингит', 'Полип', 'Узелки', 'Папилломатоз']
        elif self.train_mode == "nose":
            available_labels = ["Норма", "Ринит", "Синусит", "Смещенная перегородка"]
        elif self.train_mode == "pharynx":
            available_labels = ["Норма", "Фарингит", "Тонзиллит", "Гипертрофия миндалин"]
        else:
            available_labels = ["Глотка", "Гортань", "Ухо", "Нос", "Другое"]
        for session in sessions:
            if len(session.clusters_list) == len(available_labels) or (available_labels[0] == "Глотка"
            and len(session.clusters_list) == 4):
                names = [cluster.name for cluster in session.clusters_list]
                if len(set(names)) == len(names):
                    correct = True
                    for nm in names:
                        if nm not in available_labels:
                            correct = False
                            break
                    if correct:
                        self.sessions_comboBox.addItem(f"Кластеризация: {session.name}", session)
        for group in classif_groups:
            self.sessions_comboBox.addItem(f"Классификация НС: {group.name}", group)


