from PyQt6.QtWidgets import QWidget, QGridLayout, QLabel, QVBoxLayout, QScrollArea, QHBoxLayout
from PyQt6.QtCore import Qt
from ui.visualization_subsystem.duplicates_visualization.imageDuplicate_widget import ImageDuplicateWidget

class DuplicatesViewer:
    @staticmethod
    def display(parent, stacked_widget, groups):
        while stacked_widget.count():
            widget = stacked_widget.widget(0)
            stacked_widget.removeWidget(widget)
            widget.deleteLater()

        for group in groups:
            page = DuplicatesViewer.create_page(group)
            stacked_widget.addWidget(page)

    @staticmethod
    def create_page(group):
        page = QWidget()
        page_layout = QVBoxLayout(page)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        container = QWidget()
        container_layout = QGridLayout(container)

        row = 0
        col = 0

        for img in group:
            image_widget = ImageDuplicateWidget(img)
            container_layout.addWidget(image_widget, row, col)

            col += 1
            if col == 2:
                col = 0
                row += 1

        scroll.setWidget(container)

        page_layout.addWidget(scroll)

        return page


