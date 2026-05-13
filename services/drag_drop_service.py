import json

from PyQt6.QtWidgets import QListWidget, QListWidgetItem, QAbstractItemView, QApplication, QTreeView
from PyQt6.QtCore import Qt, QSize, QTimer, QPoint, QMimeData, QUrl
from PyQt6.QtGui import QPixmap, QIcon, QDrag
import os



class DragDropService:
    IMAGE_MIME_TYPE = 'application/x-image-data'
    #для типа объектов при множественном перемещении
    IMAGES_LIST_MIME_TYPE = 'application/x-images-list-data'

    #МЕТОДЫ ДЛЯ РАБОТЫ ИСТОЧНИКА ПЕРЕМЕЩЕНИЯ
    @staticmethod
    def setup_source(widget):
        widget.setDragEnabled(True)
        widget.setAcceptDrops(True)
        widget.setDragDropMode(QAbstractItemView.DragDropMode.DragOnly)

    @staticmethod
    def create_mimeData_fromImages(images, dataset_id, cluster=None,
                                   anomalyGroup=None, classificationSession_id=None,
                                   label=None):

        mime_data = QMimeData()

        images_data = []
        urls = []

        cluster_id = None
        anomalyGroup_id = None
        if cluster:
            cluster_id = cluster.id
        if anomalyGroup:
            anomalyGroup_id = anomalyGroup.id

        for img in images:
            # Сохраняем информацию об изображении
            data = {
                'image_id': img.id if hasattr(img, 'id') else None,
                'dataset_id': dataset_id,
                'filepath': img.filepath if hasattr(img, 'filepath') else None,
                'cluster_id': cluster_id,
                'anomalyGroup_id': anomalyGroup_id,
                'classificationSession_id': classificationSession_id,
                'label':label
            }
            images_data.append(data)
            # Добавляем URL файла
            if hasattr(img, 'filepath') and os.path.exists(img.filepath):
                urls.append(QUrl.fromLocalFile(img.filepath))

        mime_data.setData(DragDropService.IMAGES_LIST_MIME_TYPE,
                          json.dumps(images_data, ensure_ascii=False).encode())

        if urls:
            mime_data.setUrls(urls)

        return mime_data

    @staticmethod
    def start_drag(widget, images):
        drag = QDrag(widget)



        # создание миниатюры для drag
        thumbnail = DragDropService.get_thumbnail(images, 80)
        drag.setPixmap(thumbnail)
        # Устанавливаем точку привязки в центр миниатюры
        drag.setHotSpot(QPoint(thumbnail.width() // 2, thumbnail.height() // 2))
        if widget.parent.currentClassifSession:
            classif_session_id = widget.parent.currentClassifSession.id
        else:
            classif_session_id = None

        mime_data = DragDropService.create_mimeData_fromImages(images,
                                                               widget.parent.currentDataset.id,
                                                               widget.parent.currentCluster,
                                                               widget.parent.currentAnomalies,
                                                               classif_session_id,
                                                               widget.parent.currentGroupLabel)
        drag.setMimeData(mime_data)

        # Выполняем drag
        return drag.exec(Qt.DropAction.CopyAction | Qt.DropAction.MoveAction)

    @staticmethod
    def get_thumbnail(images, size):

        if len(images) == 1:
            img = images[0]
            if type(img) is list:
                img = img[0]
            if os.path.exists(img.filepath):
                pixmap = QPixmap(img.filepath)
                if not pixmap.isNull():
                    pixmap = pixmap.scaled(size, size,
                                           Qt.AspectRatioMode.KeepAspectRatio,
                                           Qt.TransformationMode.SmoothTransformation)
                    return pixmap
                return None

        #для нескольких изображенний - коллаж
        from PyQt6.QtGui import QPainter, QColor, QFont, QPen

        # Создаем квадратное изображение
        preview = QPixmap(size, size)
        preview.fill(Qt.GlobalColor.transparent)

        painter = QPainter(preview)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Фон с полупрозрачностью
        painter.fillRect(preview.rect(), QColor(0, 0, 0, 200))
        # Рисуем до 4 миниатюр в сетке 2x2
        max_thumbnails = min(len(images), 4)
        thumb_size = size // 2
        positions = [
            (0, 0),  # верхний левый
            (thumb_size, 0),  # верхний правый
            (0, thumb_size),  # нижний левый
            (thumb_size, thumb_size)  # нижний правый
        ]

        for i in range(max_thumbnails):
            img = images[i]
            x, y = positions[i]

            if hasattr(img, 'filepath') and os.path.exists(img.filepath):
                pixmap = QPixmap(img.filepath)
                if not pixmap.isNull():
                    # Масштабируем миниатюру
                    thumb = pixmap.scaled(thumb_size, thumb_size,
                                          Qt.AspectRatioMode.KeepAspectRatio,
                                          Qt.TransformationMode.SmoothTransformation)

                    # Рисуем с небольшим отступом
                    draw_x = x + (thumb_size - thumb.width()) // 2
                    draw_y = y + (thumb_size - thumb.height()) // 2
                    painter.drawPixmap(draw_x, draw_y, thumb)

        # Добавляем текст с количеством
        if len(images) > 4:
            painter.setPen(Qt.GlobalColor.white)
            font = QFont("Arial", 10, QFont.Weight.Bold)
            painter.setFont(font)
            text = f"+{len(images) - 4}"
            text_rect = preview.rect()
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, text)

        painter.end()

        return preview

    #МЕТОДЫ ДЛЯ РАБОТЫ ЦЕЛЕВОГО ОБЪЕКТА ПЕРЕМЕЩЕНИЯ
    @staticmethod
    def setup_target(widget):
        widget.tree_view.setAcceptDrops(True)
        widget.tree_view.setDragEnabled(True)
        widget.tree_view.setDragDropMode(QAbstractItemView.DragDropMode.DragDrop)
        widget.tree_view.setDropIndicatorShown(True)

        # Добавляем обработчики событий
        def dragEnterEvent(event):
            if (event.mimeData().hasFormat(DragDropService.IMAGE_MIME_TYPE) or
                    event.mimeData().hasFormat(DragDropService.IMAGES_LIST_MIME_TYPE)):
                event.acceptProposedAction()
            else:
                event.ignore()

        def dragMoveEvent(event):
            index = widget.tree_view.indexAt(event.position().toPoint())
            if index.isValid() and widget.tree_model:
                flags = widget.tree_model.flags(index)
                if flags & Qt.ItemFlag.ItemIsDropEnabled:
                    event.acceptProposedAction()
                    return
            event.ignore()

        def dropEvent(event):
            QTreeView.dropEvent(widget.tree_view, event)

        # Применяем обработчики
        widget.tree_view.dragEnterEvent = dragEnterEvent
        widget.tree_view.dragMoveEvent = dragMoveEvent
        widget.tree_view.dropEvent = dropEvent

    @staticmethod
    def drop_image(target_item, tree_model, image_info):
        from ui.interaction_subsystem.feedback_manager import FeedbackManager
        from ui.interaction_subsystem.objects_manager import ObjectsManager
        target_data = target_item.data(0)
        # Проверяем, куда бросаем изображение
        if target_data.startswith("🖼️ Изображения"):
            # Бросаем на папку "Изображения" датасета
            # Находим датасет
            dataset_item = target_item.parent()
            if dataset_item:
                dataset_name = dataset_item.data(0)[2:]
                # Находим датасет по имени
                for dataset in tree_model.datasets:
                    if dataset.name == dataset_name:
                        # Добавляем изображение в датасет
                        for img in image_info:
                            tree_model.add_image_to_dataset(dataset, img)
                        return True

        elif target_data.startswith("📁"):
            # Бросаем прямо на датасет
            dataset_name = target_data.replace("📁 ", "")
            for dataset in tree_model.datasets:
                if dataset.name == dataset_name:
                    for img in image_info:
                        tree_model.add_image_to_dataset(dataset, img)
                    return True

        elif target_data.startswith("🎯"):
            #перенос на кластер доступен только из кластера ТЕКУЩЕЙ СЕССИИ либо группы аномалий
            firstImg_data = image_info[0]
            cluster_id = firstImg_data.get('cluster_id')
            anomalyGroup_id = firstImg_data.get('anomalyGroup_id')
            # если источник не кластер и не группа аномалий - не переносим
            if not cluster_id and not anomalyGroup_id:
                FeedbackManager.UnsupportedDirectory_Warning(tree_model.parent)
                return False

            #находим целевой кластер
            targetCluster_name = target_item.data(0)[2:]
            session_name = target_item.parent().parent().data(0)[2:]
            dataset_name = target_item.parent().parent().parent().parent().data(0)[2:]
            dataset = ObjectsManager.find_dataset_from_tree(tree_model.parent, dataset_name)
            session = ObjectsManager.find_session_from_tree(dataset, session_name)
            targetCluster = ObjectsManager.find_cluster_from_tree(session, targetCluster_name)

            #если источник - кластер
            if cluster_id:
                source_cluster = tree_model.parent.currentCluster
                if source_cluster.session_id != targetCluster.session_id:
                    FeedbackManager.UnsupportedDirectory_Warning(tree_model.parent)
                    return False
                for img in image_info:
                    ObjectsManager.change_imageCluster(tree_model.parent, source_cluster, targetCluster, img['image_id'], dataset)
                return True
            #если источник - группа аномалий
            elif anomalyGroup_id:
                source_group = tree_model.parent.currentAnomalies
                if source_group.session_id != targetCluster.session_id:
                    FeedbackManager.UnsupportedDirectory_Warning(tree_model.parent)
                    return False
                for img in image_info:
                    ObjectsManager.moveImage_fromAnomalies_toCluster(tree_model.parent, source_group, targetCluster, img['image_id'], dataset)
                return True

        elif target_data.startswith("⚠️"):
            # перенос на группу аномалий доступен только из кластера ТЕКУЩЕЙ СЕССИИ
            firstImg_data = image_info[0]
            cluster_id = firstImg_data.get('cluster_id')
            if not cluster_id:
                FeedbackManager.UnsupportedDirectory_Warning(tree_model.parent)
                return False

            #находим целевую группу аномалий
            targetGroup_name = target_item.data(0)[2:]
            session_name = target_item.parent().data(0)[2:]
            dataset_name = target_item.parent().parent().parent().data(0)[2:]
            dataset = ObjectsManager.find_dataset_from_tree(tree_model.parent, dataset_name)
            session = ObjectsManager.find_session_from_tree(dataset, session_name)
            anomalyGroup = session.anomaly_group

            source_cluster = tree_model.parent.currentCluster
            if source_cluster.session_id != anomalyGroup.session_id:
                FeedbackManager.UnsupportedDirectory_Warning(tree_model.parent)
                return False
            for img in image_info:
                ObjectsManager.moveImage_fromCluster_toAnomalies(tree_model.parent, source_cluster, anomalyGroup, img['image_id'], dataset)
            return True
        elif target_data.startswith("🏷️"):
            #ПЕРЕНОС ВОМЗОЖЕН ТОЛЬКО ИЗ ГРУППЫ ЭТОЙ ЖЕ СЕССИИ КЛАССИФИКАЦИИ
            firstImg_data = image_info[0]
            label = firstImg_data.get('label')
            session_id = firstImg_data.get('classificationSession_id')
            if not label or not session_id:
                FeedbackManager.UnsupportedDirectory_Warning(tree_model.parent)
                return False

            #находим целевую группу и сессию
            targetGroup_name = target_item.data(0)[3:]
            if targetGroup_name == label:
                return True
            session_name = target_item.parent().data(0)[2:]
            dataset_name = target_item.parent().parent().parent().data(0)[2:]
            dataset = ObjectsManager.find_dataset_from_tree(tree_model.parent, dataset_name)
            session = dataset.find_classificationSession_byName(session_name)
            #если сессии разные - не переносим
            if session.id != session_id:
                FeedbackManager.UnsupportedDirectory_Warning(tree_model.parent)
                return False
            for img in image_info:
                ObjectsManager.moveImages_between_labelGroups(tree_model.parent, label,
                                                              targetGroup_name, session, img['image_id'])
            return True

        return False
