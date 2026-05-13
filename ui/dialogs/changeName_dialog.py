import os

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QListWidget, QListWidgetItem, QPushButton, QHBoxLayout, QLabel, \
    QComboBox, QDialogButtonBox, QLineEdit
from qtpy import uic

from models.clasification_session import ClasificationSession
from models.cluster import Cluster
from models.dataset import Dataset
from models.image import Image
from models.session import Session
from repositories.session_repository import SessionRepository

class ChangeNameDialog(QDialog):
    def __init__(self, item, parent=None):
        super().__init__(parent)
        # Загружаем UI из файла
        ui_path = os.path.join(os.path.dirname(__file__), '../../gui/dialogs/changeName_dialog.ui')
        uic.loadUi(ui_path, self)

        self.name = None
        self.lineEdit = self.findChild(QLineEdit, "lineEdit")
        self.button_box = self.findChild(QDialogButtonBox, "buttonBox")
        self.btn_ok = self.button_box.button(QDialogButtonBox.StandardButton.Ok)
        self.btn_cancel = self.button_box.button(QDialogButtonBox.StandardButton.Cancel)

        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)
        # Имя по умолчанию
        if item:
            self.fillDefaultName(item)

    def accept(self):
        self.name = self.lineEdit.text()
        super().accept()
        self.close()

    def reject(self):
        super().reject()

    def fillDefaultName(self, item):
        if type(item) == Image:
            default_name = item.filename
        if type(item) == Dataset or type(item) == Session or type(item) == Cluster or type(item) == ClasificationSession:
            default_name = item.name
        self.lineEdit.setText(default_name)

