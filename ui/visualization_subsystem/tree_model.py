import copy
import json

from PyQt6.QtCore import QAbstractItemModel, QModelIndex, Qt
from PyQt6.QtGui import QIcon

from repositories.image_repository import ImageRepository
from services.drag_drop_service import DragDropService
from ui.interaction_subsystem.objects_manager import ObjectsManager


#базовый элемент дерева
class TreeItem:
    def __init__(self, data, parent=None):
        self.parent_item = parent
        self.item_data = data
        self.child_items = []

    def appendChild(self, item):
        self.child_items.append(item)

    def child(self, row):
        return self.child_items[row] if row < len(self.child_items) else None

    def childCount(self):
        return len(self.child_items)

    def removeChildAt(self, row):
        if 0 <= row < len(self.child_items):
            del self.child_items[row]
            return True
        return False

    def columnCount(self):
        return 1

    def data(self, column):
        return self.item_data

    def parent(self):
        return self.parent_item

    def row(self):
        if self.parent_item:
            return self.parent_item.child_items.index(self)
        return 0

#модель для отображения данных в виде дерева

class TreeModel(QAbstractItemModel):
    def __init__(self, datasets, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.root_item = TreeItem("Root")
        self.datasets = datasets
        self.setup_model_data(datasets)

    #заполнение модели данными
    def setup_model_data(self, datasets):
        self.beginResetModel()
        # Очищаем корневой элемент
        self.root_item.child_items.clear()

        for dataset in datasets:
            #создание элемента датасета
            dataset_item = TreeItem(f"📁 {dataset.name}", self.root_item)
            active_images = dataset.get_activeImages()
            #добавляет корень изображений как дочерний элемент датасета
            images_root = TreeItem(f"🖼️ Изображения", dataset_item)
            dataset_item.appendChild(images_root)
            #добавляем корень сессий как дочерние элементы датасета
            sessions_root = TreeItem (f"📊 Сессии кластеризации", dataset_item)
            dataset_item.appendChild(sessions_root)
            #добавляем корень сессий классификации НС как дочерние элементы датасета
            classification_sessions_root = TreeItem(f"🧠 Сессии классификации НС", dataset_item)
            dataset_item.appendChild(classification_sessions_root)

            #добавляем изображения как дочерние элементы
            for image in active_images:
                image_item = TreeItem(f"🖼️ {image.filename}", images_root)
                images_root.appendChild(image_item)

            #добавляем сессии как дочерние элементы корня сессий
            for session in dataset.sessions_list:
                session_item = TreeItem(f"📈 {session.name}", sessions_root)
                sessions_root.appendChild(session_item)
                #добавляем корень кластеров как дочерний элемент сессий
                clusters_root = TreeItem(f"🗂️ Кластеры", session_item)
                session_item.appendChild(clusters_root)

                #добаляем группу аномалий как дочерний элемент сессий
                if session.anomaly_group is not None:
                    anomalyGroup_item = TreeItem(f"⚠️ {session.anomaly_group.name}", session_item)
                    session_item.appendChild(anomalyGroup_item)

                #добавляем кластеры для каждой сессии
                for cluster in session.clusters_list:
                    cluster_item = TreeItem(f"🎯 {cluster.name}", clusters_root)
                    clusters_root.appendChild(cluster_item)

            #добавляем сессии классификации НС как дочерние элементы корня сессий НС
            for session in dataset.classification_groups:
                session_item = TreeItem(f"📋 {session.name}", classification_sessions_root)
                classification_sessions_root.appendChild(session_item)
                #добавляем группы как дочерние элементы этой сессии
                for key in session.images_labels.keys():
                    group_item = TreeItem(f"🏷️ {key}", session_item)
                    session_item.appendChild(group_item)

            self.root_item.appendChild(dataset_item)
        self.endResetModel()

    def delete_sessions(self, sessions, dataset):
        dataset_item = self.find_item_by_text(self.root_item, dataset.name)
        sessions_root_item = self.find_item_by_text(dataset_item, "📊")

        for sn in sessions:
            to_delete_item = self.find_item_by_text(sessions_root_item, sn.name)
            self.delete_item(sessions_root_item, to_delete_item)

    def delete_classification_sessions(self, sessions, dataset):
        dataset_item = self.find_item_by_text(self.root_item, dataset.name)
        sessions_root_item = self.find_item_by_text(dataset_item, "🧠")

        for sn in sessions:
            to_delete_item = self.find_item_by_text(sessions_root_item, sn.name)
            self.delete_item(sessions_root_item, to_delete_item)

    def delete_dataset(self, dataset):
        dataset_item = self.find_item_by_text(self.root_item, dataset.name)
        self.delete_item(self.root_item, dataset_item)

    def delete_anomalyGroup(self, session, dataset):
        dataset_item = self.find_item_by_text(self.root_item, dataset.name)
        sessions_root_item = self.find_item_by_text(dataset_item, "📊")
        session_item = self.find_item_by_text(sessions_root_item, session.name)
        anomalyGroup_item = self.find_item_by_text(session_item, "⚠️")

        self.delete_item(session_item, anomalyGroup_item)

    def delete_classificationGroup(self, session, group_name, dataset):
        dataset_item = self.find_item_by_text(self.root_item, dataset.name)
        sessions_root_item = self.find_item_by_text(dataset_item, "🧠")
        session_item = self.find_item_by_text(sessions_root_item, session.name)
        group_item = self.find_item_by_text(session_item, group_name)

        self.delete_item(session_item, group_item)

    def delete_images_from_dataset(self, dataset, images):
        dataset_item = self.find_item_by_text(self.root_item, dataset.name)
        images_root_item = self.find_item_by_text(dataset_item, f"🖼️ Изображения")
        for img in images:
            image_item = self.find_item_by_text(images_root_item, img.filename)
            self.delete_item(images_root_item, image_item)

    def delete_cluster(self, cluster, session, dataset):
        dataset_item = self.find_item_by_text(self.root_item, dataset.name)
        sessions_root_item = self.find_item_by_text(dataset_item, "📊")
        session_item = self.find_item_by_text(sessions_root_item, session.name)
        cluster_root_item = self.find_item_by_text(session_item, "🗂️")

        cluster_item = self.find_item_by_text(cluster_root_item, cluster.name)
        self.delete_item(cluster_root_item, cluster_item)


    def add_images(self, dataset, images):
        dataset_item = self.find_item_by_text(self.root_item, dataset.name)
        images_root = self.find_item_by_text(dataset_item, "🖼️ Изображения")

        for image in images:
            image_item = TreeItem(f"🖼️ {image.filename}", images_root)
            self.insert_item(images_root, image_item)

    def rename_image(self, dataset, new_name, old_name):
        dataset_item = self.find_item_by_text(self.root_item, dataset.name)
        images_root_item = self.find_item_by_text(dataset_item, "🖼️ Изображения")

        image_item = self.find_item_by_text(images_root_item, old_name)
        self.rename_item(image_item, new_name)

    def rename_dataset(self, new_name, old_name):
        dataset_item = self.find_item_by_text(self.root_item, old_name)
        self.rename_item(dataset_item, new_name)

    def rename_session(self, dataset, new_name, old_name):
        dataset_item = self.find_item_by_text(self.root_item, dataset.name)
        sessions_root_item = self.find_item_by_text(dataset_item, "📊")

        session_item = self.find_item_by_text(sessions_root_item, old_name)
        self.rename_item(session_item, new_name)

    def rename_cluster(self, dataset, session, new_name, old_name):
        dataset_item = self.find_item_by_text(self.root_item, dataset.name)
        sessions_root_item = self.find_item_by_text(dataset_item, "📊")
        session_item = self.find_item_by_text(sessions_root_item , session.name)

        cluster_item = self.find_item_by_text(session_item, old_name)
        self.rename_item(cluster_item, new_name)

    def rename_classification_session(self, dataset, new_name, old_name):
        dataset_item = self.find_item_by_text(self.root_item, dataset.name)
        sessions_root_item = self.find_item_by_text(dataset_item, "🧠")

        session_item = self.find_item_by_text(sessions_root_item, old_name)
        self.rename_item(session_item, new_name)

    def rename_item(self, session_item, new_name):
        index = self.index_of_item(session_item)
        if index.isValid():
            item = index.internalPointer()
            item.item_data = item.item_data[:2] + new_name
            self.dataChanged.emit(index, index)


    def add_classification_session(self, session, dataset):
        dataset_item = self.find_item_by_text(self.root_item, dataset.name)
        sessions_root_item = self.find_item_by_text(dataset_item, "🧠")

        new_session_item = TreeItem(f"📋 {session.name}",sessions_root_item)
        # добавляем группы как дочерние элементы этой сессии
        for key in session.images_labels.keys():
            group_item = TreeItem(f"🏷️ {key}", new_session_item)
            new_session_item.appendChild(group_item)

        self.insert_item(sessions_root_item, new_session_item)

    def delete_item(self, parent_item, to_delete_item):
        parent_index = self.index_of_item(parent_item)
        if not parent_index.isValid():
            parent_index = QModelIndex()
        row = -1
        for i in range(parent_item.childCount()):
            if to_delete_item.data(0) in parent_item.child(i).data(0):
                row = i
                break
        if row == -1:
            return False

        self.beginRemoveRows(parent_index, row, row)
        parent_item.removeChildAt(row)
        self.endRemoveRows()
        return True

    def insert_item(self, parent_item, new_item):
        parent_index = self.index_of_item(parent_item)
        if not parent_index.isValid():
            return
        row = parent_item.childCount()
        self.beginInsertRows(parent_index, row, row)
        parent_item.appendChild(new_item)
        self.endInsertRows()

    def add_image(self, image, dataset):
        dataset_item = self.find_item_by_text(self.root_item, dataset.name)
        images_root_item = self.find_item_by_text(dataset_item, "🖼️ Изображения")

        image_item = self.find_item_by_text(images_root_item, image.filename)
        self.insert_item(images_root_item, image_item)


    def add_session(self, session, dataset):
        dataset_item = self.find_item_by_text(self.root_item, dataset.name)
        sessions_root_item = self.find_item_by_text(dataset_item, "📊")

        new_session_item = TreeItem(f"📈 {session.name}",  sessions_root_item)
        # добавляем корень кластеров как дочерний элемент сессий
        clusters_root = TreeItem(f"🗂️ Кластеры", new_session_item)
        new_session_item.appendChild(clusters_root)

        # добаляем группу аномалий как дочерний элемент сессий
        if session.anomaly_group is not None:
            anomalyGroup_item = TreeItem(f"⚠️ {session.anomaly_group.name}", new_session_item)
            new_session_item.appendChild(anomalyGroup_item)

        # добавляем кластеры для каждой сессии
        for cluster in session.clusters_list:
            cluster_item = TreeItem(f"🎯 {cluster.name}", clusters_root)
            clusters_root.appendChild(cluster_item)

        self.insert_item(sessions_root_item, new_session_item)


    def add_dataset(self, dataset):
        new_dataset_item = TreeItem(f"📁 {dataset.name}", self.root_item)
        active_images = dataset.get_activeImages()
        # добавляет корень изображений как дочерний элемент датасета
        images_root = TreeItem(f"🖼️ Изображения", new_dataset_item)
        new_dataset_item.appendChild(images_root)
        # добавляем корень сессий как дочерние элементы датасета
        sessions_root = TreeItem(f"📊 Сессии кластеризации", new_dataset_item)
        new_dataset_item.appendChild(sessions_root)
        # добавляем корень сессий классификации НС как дочерние элементы датасета
        classification_sessions_root = TreeItem(f"🧠 Сессии классификации НС",
                                                new_dataset_item)
        new_dataset_item.appendChild(classification_sessions_root)

        # добавляем изображения как дочерние элементы
        for image in active_images:
            image_item = TreeItem(f"🖼️ {image.filename}", images_root)
            images_root.appendChild(image_item)

        parent_index = QModelIndex()  # корень
        row = self.root_item.childCount()  # текущее количество детей
        self.beginInsertRows(parent_index, row, row)
        self.root_item.appendChild(new_dataset_item)  # добавляем готовый элемент
        self.endInsertRows()


    def index_of_item(self, target_item, parent_index=QModelIndex()):
        """Рекурсивно ищет TreeItem и возвращает его QModelIndex"""
        if not parent_index.isValid():
            parent_item = self.root_item
        else:
            parent_item = parent_index.internalPointer()

        for row in range(parent_item.childCount()):
            child_item = parent_item.child(row)
            if child_item == target_item:  # сравнение по id или по ссылке
                return self.index(row, 0, parent_index)
            idx = self.index_of_item(target_item, self.index(row, 0, parent_index))
            if idx.isValid():
                return idx
        return QModelIndex()

    def find_item_by_text(self, start_item, text_substring):
        if text_substring in start_item.data(0):
            return start_item
        for i in range(start_item.childCount()):
            child = start_item.child(i)
            result = self.find_item_by_text(child, text_substring)
            if result:
                return result
        return None


    def flags(self, index):
        # Базовые флаги
        default_flags = super().flags(index)

        if index.isValid():
            item = index.internalPointer()
            data = item.data(0)

            # Разрешаем drop на папку "Изображения" и на датасеты
            if (data.startswith("🖼️ Изображения") or data.startswith("📁") or data.startswith("🎯")
                    or data.startswith("⚠️") or data.startswith("🏷️")):
                return default_flags | Qt.ItemFlag.ItemIsDropEnabled

            # Для всех остальных элементов запрещаем drop
            else:
                return default_flags & ~Qt.ItemFlag.ItemIsDropEnabled

        # Для корневого элемента (невидимого) разрешаем drop
        return default_flags | Qt.ItemFlag.ItemIsDropEnabled

    def supportedDropActions(self):
        #Поддерживаемые действия при drop
        return Qt.DropAction.CopyAction | Qt.DropAction.MoveAction

    def mimeTypes(self):
        return (DragDropService.IMAGE_MIME_TYPE
                or DragDropService.IMAGES_LIST_MIME_TYPE)

    def dropMimeData(self, data, action, row, column, parent):
        if action == Qt.DropAction.IgnoreAction:
            return False

            # Проверяем, что у нас есть данные об изображении
        if (not data.hasFormat(DragDropService.IMAGE_MIME_TYPE) and not
                data.hasFormat(DragDropService.IMAGES_LIST_MIME_TYPE)):
            return False

        # Получаем данные изображения
        image_data_bytes = data.data(DragDropService.IMAGES_LIST_MIME_TYPE)
        images_data = json.loads(image_data_bytes.data().decode())
        if not isinstance(images_data, list):
            images_data = [images_data]

        # Находим целевой элемент
        if not parent.isValid():
            return False

        target_item = parent.internalPointer()
        res = DragDropService.drop_image(target_item, self, images_data)
        if res:
            # обновляем отображение изображений в дереве и открытом датасете (если открыт)
            #self.parent.setup_tree()
            if self.parent.currentMode == "images_in_dataset":
                self.parent.open_dataset(self.parent.currentDataset, self.parent.currentDataset.images_list)

        return res


    def add_image_to_dataset(self, dataset, image_info):
        old_dataset = ObjectsManager.find_dataset_by_id(self.parent, image_info['dataset_id'])
        img_item = ObjectsManager.find_image_by_id(old_dataset, image_info['image_id'])
        # добавляем изображение в целевой датасет
        dataset.images_list.append(copy.deepcopy(img_item))
        self.add_image(copy.deepcopy(img_item), dataset)

        # удаляем изображение из старого датасета (изменяем статус)
        ObjectsManager.set_status_deleted([img_item])
        self.delete_images_from_dataset(old_dataset, [img_item])

        #сохраняем изменения в БД
        image_repo = ImageRepository(self.parent.main_conn)
        image_repo.change_dataset(img_item, old_dataset, dataset)

    def index(self, row, column, parent=QModelIndex()):
        """Возвращает индекс элемента"""
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        if not parent.isValid():
            parent_item = self.root_item
        else:
            parent_item = parent.internalPointer()

        child_item = parent_item.child(row)
        if child_item:
            return self.createIndex(row, column, child_item)
        return QModelIndex()

    def parent(self, index):
        """Возвращает родительский индекс"""
        if not index.isValid():
            return QModelIndex()

        child_item = index.internalPointer()
        parent_item = child_item.parent()

        if parent_item == self.root_item or not parent_item:
            return QModelIndex()

        return self.createIndex(parent_item.row(), 0, parent_item)

    def rowCount(self, parent=QModelIndex()):
        """Количество строк у элемента"""
        if parent.column() > 0:
            return 0

        if not parent.isValid():
            parent_item = self.root_item
        else:
            parent_item = parent.internalPointer()

        return parent_item.childCount()

    def columnCount(self, parent=QModelIndex()):
        """Количество колонок"""
        return 1

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        """Данные для отображения"""
        if not index.isValid():
            return None

        item = index.internalPointer()

        if role == Qt.ItemDataRole.DisplayRole:
            return item.data(index.column())

        if role == Qt.ItemDataRole.BackgroundRole:
            return None

        if role == Qt.ItemDataRole.DecorationRole:
            # Можно добавить иконки
            data = item.data(0)
            if data.startswith("📁"):
                return None  # здесь можно вернуть QIcon для папки
            elif data.startswith("🖼️"):
                return None  # здесь можно вернуть QIcon для изображения

        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        """Заголовок колонки"""
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return "ВСЕ ДАТАСЕТЫ"
        return None