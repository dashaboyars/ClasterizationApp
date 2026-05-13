from PyQt6.QtWidgets import QWidget, QGridLayout, QLabel
from PyQt6.QtCore import Qt

from ui.visualization_subsystem.anomalyGroup_widget import AnomalyGroupWidget
from ui.visualization_subsystem.classification_session_widget import ClassificationSessionWidget
from ui.visualization_subsystem.cluster_widget import ClusterWidget
from ui.visualization_subsystem.dataset_widget import DatasetWidget
from ui.visualization_subsystem.labeled_group_widget import LabeledGroupWidget
from ui.visualization_subsystem.session_widget import SessionWidget


class WidgetViewer:
    @staticmethod
    def display(parent, scroll_area, widgets, widgets_type, search_query=None, anomaly_group=None, session=None, names=None):
        if scroll_area.widget():
            old_widget = scroll_area.widget()
            scroll_area.takeWidget()
            old_widget.deleteLater()
        # Контейнер
        container = QWidget()

        # Используем QGridLayout для двух колонок
        layout = QGridLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setHorizontalSpacing(5)
        layout.setVerticalSpacing(5)
        layout.setContentsMargins(15, 15, 15, 15)

        if not widgets and anomaly_group is None:
            # Если нет элементов
            if widgets_type == "dataset":
                label = QLabel("Нет датасетов\nНажмите кнопку импорта для создания")
            elif widgets_type == "session":
                label = QLabel("Нет сессий\nДля их создания необходимо выполнить кластеризацию")
            else:
                label = QLabel("Нет кластеров\nЧто-то пошло не так :(")


            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet("""
                       color: #999;
                       font-size: 16px;
                       padding: 50px;
                   """)
            layout.addWidget(label, 0, 0, 1, 2)
        else:
            if widgets_type == "cluster":
                step = 1
            else:
                step = 2
            count_clusters = 0
            idx = 0
            count_groups = 0
            for i, widget in enumerate(widgets):
                if widgets_type == "labeled_group":
                    row = count_groups // step
                    col = count_groups % step
                else:
                    row = i // step
                    col = i % step

                if widgets_type == "dataset":
                    widget = DatasetWidget(widget, search_query, parent)
                    # Подключаем сигналы
                    widget.double_clicked.connect(parent.on_dataset_double_clicked)
                elif widgets_type == "session":
                    widget = SessionWidget(widget, search_query, parent)
                    # Подключаем сигналы
                    widget.double_clicked.connect(parent.on_session_double_clicked)
                elif widgets_type == "classification_session":
                    widget = ClassificationSessionWidget(widget, search_query, parent)
                    # Подключаем сигналы
                    widget.double_clicked.connect(parent.on_classification_session_double_clicked)
                elif widgets_type == "labeled_group":
                    if session.images_labels[names[idx]] is not None and len(session.images_labels[names[idx]]) > 0:
                        widget = LabeledGroupWidget(session, session.images_labels[names[idx]], names[idx], search_query, parent)
                        widget.double_clicked.connect(parent.on_classificationGroup_double_clicked)
                        count_groups += 1
                    idx += 1
                else:
                    widget = ClusterWidget(widget, search_query, parent)
                    # Подключаем сигналы
                    widget.double_clicked.connect(parent.on_cluster_double_clicked)
                    count_clusters += 1

                # Добавляем в сетку с растяжением по ширине
                if type(widget) is not list:
                    layout.addWidget(widget, row, col)
            if anomaly_group is not None:
                widget = AnomalyGroupWidget(anomaly_group, search_query, parent)
                widget.double_clicked.connect(parent.on_anomalyGroup_double_clicked)
                layout.addWidget(widget, count_clusters, 0)

            container.setLayout(layout)

            # Устанавливаем в scroll area
            scroll_area.setWidget(container)
            scroll_area.setWidgetResizable(True)