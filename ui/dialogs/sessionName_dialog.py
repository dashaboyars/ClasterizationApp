import os

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QListWidget, QListWidgetItem, QPushButton, QHBoxLayout, QLabel, \
    QComboBox, QDialogButtonBox, QLineEdit
from qtpy import uic

from repositories.session_repository import SessionRepository


class SessionNameDialog(QDialog):
    def __init__(self, dataset_id, parent=None):
        super().__init__(parent)
        # Загружаем UI из файла
        ui_path = os.path.join(os.path.dirname(__file__), '../../gui/dialogs/sessionName_dialog.ui')
        uic.loadUi(ui_path, self)

        self.name = None
        self.lineEdit = self.findChild(QLineEdit, "lineEdit")
        self.button_box = self.findChild(QDialogButtonBox, "buttonBox")
        self.btn_ok = self.button_box.button(QDialogButtonBox.StandardButton.Ok)
        self.btn_cancel = self.button_box.button(QDialogButtonBox.StandardButton.Cancel)

        #Сервисы
        self.session_repo = SessionRepository(parent.main_conn)

        #Имя по умолчанию
        self.fillDefaultName(dataset_id)

    def accept(self):
        self.name = self.lineEdit.text()
        super().accept()

    def reject(self):
        super().reject()

    def fillDefaultName(self, dataset_id):
        existingSessions_count = self.session_repo.count_existingSessions(dataset_id)
        default_name = f"Сессия {existingSessions_count + 1}"
        self.lineEdit.setText(default_name)
