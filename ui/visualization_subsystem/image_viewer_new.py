from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt
from ui.visualization_subsystem.image_list_widget import ImageListWidget
from ui.visualization_subsystem.image_delegate import ImageDelegate


class ImageViewer:
    @staticmethod
    def display(parent, scroll_area, images, dataset, search_query=None, search_mode=None):
        # Очищаем scroll_area
        old_widget = scroll_area.takeWidget()
        if old_widget:
            old_widget.deleteLater()

        # Фильтруем удаленные
        active_images = images

        if not active_images:
            # Показываем сообщение
            container = QWidget()
            layout = QVBoxLayout(container)
            label = QLabel("Нет изображений для отображения")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet("color: #999; font-size: 16px; padding: 50px;")
            layout.addWidget(label)
            scroll_area.setWidget(container)
        else:
            # Создаем список
            list_widget = ImageListWidget(active_images,parent)

            # Устанавливаем делегат для отрисовки
            list_widget.setItemDelegate(ImageDelegate(dataset, list_widget, search_query, search_mode))

            # Подключаем двойной клик
            list_widget.itemDoubleClicked.connect(
                lambda item: parent.on_image_double_clicked(
                    item.data(Qt.ItemDataRole.UserRole)
                )
            )

            scroll_area.setWidget(list_widget)

        scroll_area.setWidgetResizable(True)