import os

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PyQt6.QtGui import QFont, QMouseEvent, QPixmap
from PyQt6.QtCore import Qt, pyqtSignal

from ui.interaction_subsystem.menu_manager import MenuManager


class DatasetWidget(QWidget):
    double_clicked = pyqtSignal(object)

    def __init__(self, dataset, search_query=None, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.dataset = dataset
        self.is_hovered = False

        self.setAttribute(Qt.WidgetAttribute.WA_Hover)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # подключение контекстного меню
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

        # Фиксированная высота
        self.setFixedHeight(120)

        # Основной горизонтальный layout
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 10, 5, 10)
        main_layout.setSpacing(0)

        # Левая часть - иконка (эмодзи)
        self.icon_label = QLabel()
        self.load_icon()
        self.icon_label.setFixedWidth(80)
        self.icon_label.setFixedHeight(80)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        main_layout.addWidget(self.icon_label)

        # Правая часть - информация о датасете
        info_layout = QVBoxLayout()
        info_layout.setSpacing(1)

        # Название датасета (жирным)
        self.name_label = QLabel(dataset.name)
        self.name_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.name_label.setStyleSheet("color: #333;")
        info_layout.addWidget(self.name_label)

        self.highlight_searchQuery(search_query)

        # Горизонтальный ряд с метаданными (3 колонки)
        metadata_layout = QVBoxLayout()
        metadata_layout.setSpacing(1)

        # Количество изображений
        self.img_label = ""
        self.set_imageAmount()
        metadata_layout.addWidget(self.img_label)

        #Дата создания
        date_label = QLabel(f"📅 {self.formatted_date()}")
        date_label.setStyleSheet("color: #666; font-size: 10px;")
        metadata_layout.addWidget(date_label)

        #количество сессий
        self.session_label = ""
        self.set_sessionAmount()
        metadata_layout.addWidget(self.session_label)

        metadata_layout.addStretch()
        info_layout.addLayout(metadata_layout)

        main_layout.addLayout(info_layout, 1)  # 1 = растягиваться

        self.setLayout(main_layout)
        for child in self.findChildren(QLabel):
            child.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
            # Разрешаем событиям мыши всплывать к родителю
            child.installEventFilter(self)

    def highlight_searchQuery(self, search_query):
        if not search_query:
            return

        text = self.name_label.text()
        start_pos = text.find(search_query)

        if start_pos >= 0:
            before = text[:start_pos]
            match = text[start_pos:start_pos + len(search_query)]
            after = text[start_pos + len(search_query):]

            highlighted_text = f"""
                        {before}
                        <span style='background-color: #ffeb3b; color: #000; font-weight: bold;'>{match}</span>
                        {after}
                    """
            self.name_label.setText(highlighted_text)
            self.name_label.setTextFormat(Qt.TextFormat.RichText)
            self.name_label.setStyleSheet("color: #333;")

    def show_context_menu(self, position):
        global_pos = self.mapToGlobal(position)
        MenuManager.show_dataset_contextMenu(self.parent, self.dataset, global_pos)



    def load_icon(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(current_dir, '../../resources/icons/folder_icon.png')
        icon_path = os.path.normpath(icon_path)

        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path)
            if not pixmap.isNull():
                # Масштабируем иконку до нужного размера
                pixmap = pixmap.scaled(60, 60,
                                       Qt.AspectRatioMode.KeepAspectRatio,
                                       Qt.TransformationMode.SmoothTransformation)
                self.icon_label.setPixmap(pixmap)
                self.icon_label.setStyleSheet("background-color: transparent;")
            else:
                self.icon_label.setText("📁")
                self.icon_label.setFont(QFont("Segoe UI Emoji", 32))
        else:
            self.icon_label.setText("📁")
            self.icon_label.setFont(QFont("Segoe UI Emoji", 32))

    def set_sessionAmount(self):
        self.session_label = QLabel(f"📊Сессий: {self.dataset.sessions_count}")
        self.session_label.setStyleSheet("color: #666; font-size: 10px;")
    def set_imageAmount(self):
        image_count = self.dataset.count_images()
        self.img_label = QLabel(f"🖼️ Изображений: {image_count}")
        self.img_label.setStyleSheet("color: #666; font-size: 10px;")

    def formatted_date(self):
        date_str = self.dataset.created_at[:10]  # берем первые 10 символов
        date_parts = date_str.split('-')
        if len(date_parts) == 3:
            formatted_date = f"{date_parts[2]}.{date_parts[1]}.{date_parts[0]}"
        else:
            formatted_date = date_str
        return formatted_date

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.double_clicked.emit(self.dataset)