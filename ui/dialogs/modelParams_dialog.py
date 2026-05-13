import os

from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
from qtpy import uic

from repositories.modelVersion_repository import ModelVersionRepository


class ModelParamsTable(QAbstractTableModel):
    def __init__(self, data, headers, parent=None):
        super().__init__(parent)
        self.data = data
        self.headers = headers

    def rowCount(self, parent=QModelIndex()):
        return len(self.data)

    def columnCount(self, parent=QModelIndex()):
        return len(self.headers)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        row = index.row()
        col = index.column()

        if row >= len(self.data):
            return None

        item = self.data[row]

        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0:
                # Пробуем разные варианты имени, так как в БД поле может называться по-разному
                return getattr(item, 'name', getattr(item, 'version', 'Unknown'))

                # --- КОЛОНКА 1: Дата ---
            elif col == 1:
                return getattr(item, 'created_at', '-')

                # --- КОЛОНКА 2: Путь к файлу ---
            elif col == 2:
                full_path = getattr(item, 'onnx_path', getattr(item, 'path', ''))
                if full_path:
                    # Показываем только имя файла, чтобы не загромождать таблицу
                    return os.path.basename(full_path)
                return "-"
            elif col == 3:
                labels = getattr(item, 'label_map', getattr(item, 'labels', ''))
                # Если меток много, можно обрезать строку
                if labels and len(str(labels)) > 30:
                    return str(labels)[:30] + "..."
                return labels

                # --- КОЛОНКА 4: Статус Активности ---
            elif col == 4:
                is_active = getattr(item, 'is_active', False)
                return "✅ Активна" if is_active else "⚪ Неактивна"
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            if section < len(self.headers):
                return self.headers[section]
        return None

class ModelParamsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        ui_path = os.path.join(os.path.dirname(__file__), '../../gui/dialogs/model_params_dialog.ui')
        uic.loadUi(ui_path, self)

        self.tableView = self.findChild(QTableView, "tableView")
        self.btn_ok = self.findChild(QPushButton, "ok_btn")

        self.btn_ok.clicked.connect(self.accept)
        self.changeActive_btn = self.findChild(QPushButton, "changeActive_btn")

        self.changeActive_btn.clicked.connect(self.change_active_model)

        self.set_data(self.parent.models_data)

    def set_data(self, all_versions):
        headers = [
            "Имя", "Дата загрузки", "Путь к файлу", "Список меток", "Активна"
        ]

        table = ModelParamsTable(all_versions, headers, self.parent)
        self.tableView.setModel(table)

        # Растягиваем колонки
        header = self.tableView.horizontalHeader()

        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)  # Имя
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Дата
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # Файл (растягивается)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)  # Метки
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Статус
        # Разрешаем сортировку
        self.tableView.setSortingEnabled(True)

    def change_active_model(self):
        selection = self.tableView.selectionModel()
        if not selection.hasSelection():
            QMessageBox.warning(self, "Нет выбора", "Пожалуйста, выберите модель в таблице.")
            return

        # Получаем индекс выбранной строки
        current_index = selection.currentIndex()
        if not current_index.isValid():
            return

        # Получаем данные из модели таблицы
        model = self.tableView.model()
        if not isinstance(model, ModelParamsTable):
            return

        row = current_index.row()
        if row < 0 or row >= len(model.data):
            return

        selected_item = model.data[row]
        name = selected_item.name
        self.parent.change_active_model(name)
        self.set_data(self.parent.models_data)

        #изменить в БД
        modelVersion_repo = ModelVersionRepository(self.parent.main_conn, self.parent.project_root)
        modelVersion_repo.change_active_version(name)

    def accept(self):
        super().accept()