import os

from PyQt6.QtWidgets import *
from qtpy import uic


class QualityParamsDialog(QDialog):
    def __init__(self, parent = None):
        super().__init__(parent)
        ui_path = os.path.join(os.path.dirname(__file__), '../../gui/dialogs/quality_params_dialog.ui')
        uic.loadUi(ui_path, self)
        self.setStyle()
        self.values = None
        #поля ввода
        self.minSize_text = self.findChild(QLineEdit, "minSize_text")
        self.maxSize_text = self.findChild(QLineEdit, "maxSize_text")
        self.minResolution_text = self.findChild(QLineEdit, "minResolution_text")
        self.minColors_text = self.findChild(QLineEdit, "minColor_text")
        self.maxNoise_text = self.findChild(QLineEdit, "maxNoise_text")
        self.minSharpness_text = self.findChild(QLineEdit, "minSharpness_text")
        self.minContrast_text = self.findChild(QLineEdit, "minContrast_text")
        #кнопки
        button_box = self.findChild(QDialogButtonBox, "buttonBox")
        self.btn_ok = button_box.button(QDialogButtonBox.StandardButton.Ok)
        self.btn_cancel = button_box.button(QDialogButtonBox.StandardButton.Cancel)

        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)

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

    def accept(self):
        values = self.ParseInput()
        if type(values) is str:
            QMessageBox.warning(
                self,
                "Некорректный ввод",
                values
            )
        else:
            self.values = values
            super().accept()

    def ParseInput(self):
        minSize = self.Parse_minSize()
        if type(minSize) is str:
            return minSize
        maxSize = self.Parse_maxSize() * 1024
        if type(maxSize) is str:
            return maxSize
        if minSize > maxSize:
            return "Минимальный размер файла не должен превышать максимальный"
        minResolution = self.Parse_Resolution()
        if type(minResolution) is str:
            return minResolution
        minColors = self.Parse_Colors()
        if type(minColors) is str:
            return minColors
        minSharpness = self.Parse_Sharpness()
        if type(minSharpness) is str:
            return minSharpness
        maxNoise = self.Parse_Noise()
        if type(maxNoise) is str:
            return maxNoise
        minContrast = self.Parse_Contrast()
        if type(minContrast) is str:
            return minContrast

        return {
            'min_size': minSize,
            'max_size': maxSize,
            'min_resolution': minResolution,
            'min_colors': minColors,
            'max_noise': maxNoise,
            'min_sharpness': minSharpness,
            'min_contrast': minContrast
        }

    def Parse_Contrast(self):
        text = self.minContrast_text.text()
        cleaned = text.strip().replace(',', '.')
        try:
            value = float(cleaned)
            if value < 0.01 or value > 1.0:
                return f"Уровень контраста должен находиться в диапазоне [0.01; 1]"
            return value


        except (ValueError, TypeError):
            return f"{cleaned} не является числом"
    def Parse_Noise(self):
        text = self.maxNoise_text.text()
        cleaned = text.strip().replace(',', '.')
        try:
            value = float(cleaned)
            if value < 0.01 or value > 1.0:
                return f"Уровень шума должен находиться в диапазоне [0.01; 1]"
            return value


        except (ValueError, TypeError):
            return f"{cleaned} не является числом"

    def Parse_Sharpness(self):
        text = self.minSharpness_text.text()
        cleaned = text.strip().replace(',', '.')
        try:
            value = float(cleaned)
            if value < 10:
                return f"Минимальная резкость не может быть меньше 10"
            return value


        except (ValueError, TypeError):
            return f"{cleaned} не является числом"

    def Parse_Colors(self):
        text = self.minColors_text.text()
        cleaned = text.strip()
        try:
            value = int(cleaned)
            if value < 2:
                return f"Минимальное количество цветом не может быть меньше 2"
            return value


        except (ValueError, TypeError):
            return f"{cleaned} не является целым числом"

    def Parse_Resolution(self):
        text = self.minResolution_text.text()
        cleaned = text.strip()
        try:
            value = int(cleaned)
            if value < 16:
                return f"Минимальный разрешение не должно быть меньше 16 пикс."
            return value


        except (ValueError, TypeError):
            return f"{cleaned} не является целым числом"

    def Parse_minSize(self):
        text = self.minSize_text.text()
        cleaned = text.strip().replace(',', '.')
        try:
            value = float(cleaned)
            if value < 0.1:
                return f"Минимальный размер файла должен быть >= 0.1"
            return value


        except (ValueError, TypeError):
            return f"{cleaned} не является числом"


    def Parse_maxSize(self):
        text = self.maxSize_text.text()
        cleaned = text.strip().replace(',', '.')
        try:
            value = float(cleaned)
            if value > 1000:
                return f"Максимальный размер файла должен быть <= 1000"
            return value


        except (ValueError, TypeError):
            return f"{cleaned} не является числом"


    def reject(self):
        super().reject()