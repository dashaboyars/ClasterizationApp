import os

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QListWidget, QListWidgetItem, QPushButton, QHBoxLayout, QLabel, \
    QComboBox, QDialogButtonBox, QLineEdit
from qtpy import uic

from ui.interaction_subsystem.feedback_manager import FeedbackManager


class TagInputDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Загружаем UI из файла
        ui_path = os.path.join(os.path.dirname(__file__), '../../gui/dialogs/tagInput_dialog.ui')
        uic.loadUi(ui_path, self)

        self.tag_name = None
        self.lineEdit = self.findChild(QLineEdit, "lineEdit")
        self.button_box = self.findChild(QDialogButtonBox, "buttonBox")
        self.btn_ok = self.button_box.button(QDialogButtonBox.StandardButton.Ok)
        self.btn_cancel = self.button_box.button(QDialogButtonBox.StandardButton.Cancel)

        #Тег по умолчанию
        self.fill_defaultTag()

    def accept(self):
        tag_input = self.lineEdit.text()
        correct_input = self.parse_input(tag_input)
        if correct_input:
            self.tag_name = tag_input
            super().accept()

    def parse_input(self, text):
        if len(text) > 15 or len(text) == 0:
            FeedbackManager.WrongTagInput(self, "Длина тега должна быть в дипазоне от 1 до 15 символов")
            return False
        accepted_symbols = "_qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNMЙЦУКЕНГШЩЗХЪЁФЫВАПРОЛДЖЭЯЧСМИТЬБЮйцуёкенгшщзхъфывапролджэячсмитьбю1234567890"
        for symb in text:
            if symb not in accepted_symbols:
                FeedbackManager.WrongTagInput(self, f"Недопустимый символ: {symb}")
                return False
        return True


    def reject(self):
        super().reject()

    def fill_defaultTag(self):
        self.lineEdit.setText("тег_123")