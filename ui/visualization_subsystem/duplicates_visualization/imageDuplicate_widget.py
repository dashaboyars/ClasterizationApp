import os

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QCheckBox
from PyQt6.QtGui import QFont, QMouseEvent, QPixmap
from PyQt6.QtCore import Qt, pyqtSignal

class ImageDuplicateWidget(QWidget):
    def __init__(self, image, parent=None):
        super().__init__(parent)
        self.image = image
        self.choosed =True

        # Фиксированная высота
        self.setFixedHeight(100)

        # Основной горизонтальный layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 10, 5, 10)
        main_layout.setSpacing(2)

        #основная часть - миниатюра
        self.icon_label = QLabel()
        self.load_thumbnail()

        #нижняя часть - имя файла и чек-бокс
        self.name_label = QLabel(image.filename)
        self.name_label.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        self.name_label.setStyleSheet("color: #333;")

        self.choosed_checkBox = QCheckBox()
        self.choosed_checkBox.setText("Оставить")
        self.choosed_checkBox.setChecked(True)
        self.choosed_checkBox.toggled.connect(self.choosed_changed)

        #добавляем все в основной layout
        main_layout.addWidget(self.icon_label)
        main_layout.addWidget(self.name_label)
        main_layout.addWidget(self.choosed_checkBox)

        main_layout.addStretch()
        self.setLayout(main_layout)

    def choosed_changed(self, checked):
        if checked:
            self.choosed = True
        else:
            self.choosed = False

    def load_thumbnail(self):
        """Загружает миниатюру"""
        if os.path.exists(self.image.filepath):
            pixmap = QPixmap(self.image.filepath)
            if not pixmap.isNull():
                scaled = pixmap.scaled(60, 60,
                                       Qt.AspectRatioMode.KeepAspectRatio,
                                       Qt.TransformationMode.SmoothTransformation)
                self.icon_label.setPixmap(scaled)
            else:
                self.show_placeholder()
        else:
            self.show_placeholder()

    def show_placeholder(self):
        self.icon_label.setText("🖼️")
        self.icon_label.setStyleSheet("font-size: 40px; color: #999;")