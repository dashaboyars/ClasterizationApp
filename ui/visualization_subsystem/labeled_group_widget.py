import os

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PyQt6.QtGui import QFont, QMouseEvent, QPixmap
from PyQt6.QtCore import Qt, pyqtSignal

from ui.interaction_subsystem.menu_manager import MenuManager

class LabeledGroupWidget(QWidget):
    double_clicked = pyqtSignal(object, object, object)

    def __init__(self, session, group, name, search_query=None, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.group = group
        self.name = name
        self.session = session

        # подключение контекстного меню
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

        # Фиксированная высота
        self.setFixedHeight(70)

        # Основной горизонтальный layout
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(0)

        # Левая часть - иконка (эмодзи)
        icon_layout = QVBoxLayout()
        icon_layout.setContentsMargins(0, 0, 0, 0)
        self.icon_label = QLabel()
        self.load_icon()
        self.icon_label.setFixedSize(60, 60)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        icon_layout.addWidget(self.icon_label)

        main_layout.addLayout(icon_layout)

        # Правая часть - информация о группе
        info_layout = QVBoxLayout()
        info_layout.setSpacing(1)

        # Название группы (жирным)
        if name == 'Не в кадре':
            self.name_label = QLabel('Другое')
        else:
            self.name_label = QLabel(name)
        self.name_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.name_label.setStyleSheet("color: #333;")
        info_layout.addWidget(self.name_label)

        self.highlight_searchQuery(search_query)

        # Количество изображений
        self.imagesCount_label = QLabel(f"🖼️ Изображений: {len(group)}")
        self.imagesCount_label.setStyleSheet("color: #666; font-size: 10px;")
        info_layout.addWidget(self.imagesCount_label)

        # Средняя уверенность
        self.medConf_label = QLabel(f"Средняя уверенность: {round(session.get_avg_confidence_byGroup(name) * 100, 2)}%")
        self.medConf_label.setStyleSheet("color: #666; font-size: 10px;")
        info_layout.addWidget(self.medConf_label)

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

    def load_icon(self):
        self.icon_label.setText("🏷️")
        self.icon_label.setFont(QFont("Segoe UI Emoji", 32))

    def show_context_menu(self, position):
        global_pos = self.mapToGlobal(position)
        MenuManager.show_labeledGroup_contextMenu(self.parent, self.session, self.name, global_pos)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            group = self.session.images_labels[self.name]
            self.double_clicked.emit(self.session, group, self.name)