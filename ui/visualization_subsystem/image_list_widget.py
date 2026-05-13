import json

from PyQt6.QtWidgets import QListWidget, QListWidgetItem, QAbstractItemView, QApplication
from PyQt6.QtCore import Qt, QSize, QTimer, QPoint, QMimeData, pyqtSignal
from PyQt6.QtGui import QPixmap, QIcon, QDrag
import os

from services.drag_drop_service import DragDropService
from ui.interaction_subsystem.feedback_manager import FeedbackManager
from ui.interaction_subsystem.menu_manager import MenuManager
from ui.interaction_subsystem.objects_manager import ObjectsManager


class ImageListWidget(QListWidget):
    images_copy_requested = pyqtSignal(list)# сигнал на копирование
    images_paste_requested = pyqtSignal() #сигнал на вставку
    images_delete_requested = pyqtSignal(list)  # сигнал на удаление

    def __init__(self, images, parent=None):
            super().__init__(parent)
            self.parent = parent
            self.images = images
            #начальная позиция перетаскивания
            self.drag_start_pos = None
            #перетаскиваемый элемент
            self.dragged_item = None

            # Настройки для двух колонок
            self.setViewMode(QListWidget.ViewMode.IconMode)
            self.setIconSize(QSize(80, 80))  # размер миниатюры

            if self.parent.currentMode == "images_in_cluster":
                self.setGridSize(QSize(350, 120))
            else:
                self.setGridSize(QSize(300, 120))
                self.setMinimumWidth(720)
            self.setSpacing(5)

            #множественное выделение
            self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

            # Настройки drag & drop
            DragDropService.setup_source(self)

            #подключение контекстного меню
            self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            self.customContextMenuRequested.connect(self.show_context_menu)

            # Добавляем все изображения как элементы списка
            for img in images:
                item = QListWidgetItem()
                item.setData(Qt.ItemDataRole.UserRole, img)  # сохраняем объект
                item.setTextAlignment(Qt.AlignmentFlag.AlignLeft)
                self.addItem(item)

            # Таймеры для ленивой загрузки
            self._scroll_timer = QTimer()
            self._scroll_timer.setSingleShot(True)
            self._scroll_timer.timeout.connect(self.load_visible_thumbnails)

            QTimer.singleShot(100, self.load_visible_thumbnails)
            self.verticalScrollBar().valueChanged.connect(self.on_scroll)

    def show_context_menu(self, position):
        item = self.itemAt(position)

        if not item and not self.selectedItems():
            return

        if item and not item in self.selectedItems():
            self.clearSelection()
            item.setSelected(True)

        selected_images = self.get_selected_images()
        MenuManager.show_image_contextMenu(self, selected_images, position, self.parent.currentDataset)

    def on_scroll(self):
        self._scroll_timer.start(50)

    def keyPressEvent(self, e):
        #Ctrl+C копирование изображений
        if e.modifiers() == Qt.KeyboardModifier.ControlModifier and e.key() == Qt.Key.Key_C:
            selected_images = self.get_selected_images()
            if selected_images:
                ObjectsManager.copy_images(self.parent, selected_images)
                self.images_copy_requested.emit(selected_images)
            e.accept()
            return
        #Ctrl+V вставка скопированных изображений
        if e.modifiers() == Qt.KeyboardModifier.ControlModifier and e.key() == Qt.Key.Key_V:
            self.paste_images()
            self.images_paste_requested.emit()
            e.accept()
            return
        #Delete удаление изображения из датасета
        if e.key() == Qt.Key.Key_Delete:
            selected_images = self.get_selected_images()
            if selected_images:
                ObjectsManager.set_status_deleted(selected_images)
                ObjectsManager.update_imagesStatus(self.parent, selected_images, self.parent.currentDataset.id)
                self.images_delete_requested.emit(selected_images)
                self.parent.currentDataset.remove_images(selected_images)
                self.parent.update_ui()
            e.accept()
            return
        super().keyPressEvent(e)

    def paste_images(self):
        if self.parent.currentMode == "images_in_dataset" and self.parent.images_copied:
            mime_data = QApplication.clipboard().mimeData()
            image_data_bytes = mime_data.data(DragDropService.IMAGES_LIST_MIME_TYPE)
            images_data = json.loads(image_data_bytes.data().decode())
            for img_info in images_data:
                ObjectsManager.add_imageCopy_to_dataset(self.parent, self.parent.currentDataset, img_info)
            self.parent.update_ui()
        else:
            FeedbackManager.UnsupportedDirectory_Warning(self.parent)

    def load_visible_thumbnails(self):
        """Обновляет отображение для видимых элементов"""
        self.viewport().update()

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.drag_start_pos = e.position().toPoint()
            self.dragged_item = self.itemAt(self.drag_start_pos)

        super().mousePressEvent(e)

    def get_selected_images(self):
        selected_images = []

        for item in self.selectedItems():
            img = item.data(Qt.ItemDataRole.UserRole)
            if img:
                if type(img) is list:
                    selected_images.append(img[0])
                else:
                    selected_images.append(img)
        return selected_images

    def mouseMoveEvent(self, e):
        if not (e.buttons() & Qt.MouseButton.LeftButton):
            return

        if not self.drag_start_pos or not self.dragged_item:
            return

        # Проверяем, ушла ли мышь на достаточное расстояние
        distance = (e.position().toPoint() - self.drag_start_pos).manhattanLength()
        if distance < QApplication.startDragDistance():
            return

        # создаем drag object
        img = self.dragged_item.data(Qt.ItemDataRole.UserRole)
        images = self.get_selected_images()

        DragDropService.start_drag(self, images)

        # Сбрасываем состояние
        self.drag_start_position = None
        self.dragged_item = None



