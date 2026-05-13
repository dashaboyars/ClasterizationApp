import os

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QListWidget, QListWidgetItem, QPushButton, QHBoxLayout, QLabel, \
    QComboBox, QDialogButtonBox
from PyQt6.QtCore import Qt
from qtpy import uic


class SelectDatasetDialog(QDialog):
    def __init__(self, datasets_list, parent=None):
        super().__init__(parent)
        # Загружаем UI из файла
        ui_path = os.path.join(os.path.dirname(__file__), '../../gui/dialogs/select_dataset_dialog.ui')
        uic.loadUi(ui_path, self)

        self.datasets = datasets_list
        self.selected_dataset = None

        self.comboBox = self.findChild(QComboBox, "selectDataset_comboBox")
        button_box = self.findChild(QDialogButtonBox, "buttonBox")
        self.btn_ok = button_box.button(QDialogButtonBox.StandardButton.Ok)
        self.btn_cancel = button_box.button(QDialogButtonBox.StandardButton.Cancel)
        self.fill_comboBox()
        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)

        self.setWindowTitle("Выбор датасета")

    def setStyle(self):
        self.setStyleSheet("""
                        QLabel {
                            color: black;
                        }
                        QLineEdit {
                            color: black;
                            background-color: white;  /* фон белый для контраста */
                        }
                        QPushButton {
                            color: black;
                        }
                    """)

    def reject(self):
        super().reject()

    def accept(self):
        self.selected_dataset = self.comboBox.currentData()
        super().accept()
    def fill_comboBox(self):
        self.comboBox.clear()
        for dataset in self.datasets:
            self.comboBox.addItem(dataset.name, dataset)

    def get_selected_dataset(self):
        return self.selected_dataset

