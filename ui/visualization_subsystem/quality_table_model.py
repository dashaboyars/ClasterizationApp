from PyQt6.QtCore import *
from PyQt6.QtGui import QColor


class QualityTable(QAbstractTableModel):
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

        # Получаем значение по колонке
        if col == 0:
            value = item['file_name']
        elif col == 1:
            value = f"{item['size']:.1f}"
        elif col == 2:
            value = str(item['resolution'])
        elif col == 3:
            value = str(item['colors'])
        elif col == 4:
            value = f"{item['sharpness']:.1f}"
        elif col == 5:
            value = f"{item['noise']:.3f}"
        elif col == 6:
            value = f"{item['contrast']:.3f}"
        elif col == 7:
            value = f"{item['problems']}"
        else:
            value = ""

        if role == Qt.ItemDataRole.DisplayRole:
            return value

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            if section < len(self.headers):
                return self.headers[section]
        return None



