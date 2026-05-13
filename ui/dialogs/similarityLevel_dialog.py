import os

from PyQt6.QtWidgets import QDialog, QLineEdit, QDialogButtonBox, QMessageBox
from qtpy import uic


class SimilarityLevelDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Загружаем UI из файла
        ui_path = os.path.join(os.path.dirname(__file__), '../../gui/dialogs/similarityLevel_dialog.ui')
        uic.loadUi(ui_path, self)

        self.similarityPercent_line = self.findChild(QLineEdit, "similarityPercent_text")
        self.similarityPercent = None

        button_box = self.findChild(QDialogButtonBox, "buttonBox")
        self.btn_ok = button_box.button(QDialogButtonBox.StandardButton.Ok)
        self.btn_cancel = button_box.button(QDialogButtonBox.StandardButton.Cancel)
        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)

    def accept(self):
        input = self.ParsedPercent()
        if type(input) is str:
            QMessageBox.warning(
                self,
                "Некорректный ввод",
                self.similarityPercent
            )
        else:
            self.similarityPercent = input
            super().accept()

    def ParsedPercent(self):
        text = self.similarityPercent_line.text()
        cleaned = text.strip()
        try:
            value = int(cleaned)
            if value < 1 or value > 100:
                return f"Порог схожести должен находится в диапазоне [1; 100]"
            return value

        except (ValueError, TypeError):
            return f"{cleaned} не является числом"

    def reject(self):
        super().reject()