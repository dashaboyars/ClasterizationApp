import os
from PyQt6.QtWidgets import *
from qtpy import uic

from ui.visualization_subsystem.duplicates_visualization.duplicates_viewer import DuplicatesViewer
from ui.visualization_subsystem.duplicates_visualization.imageDuplicate_widget import ImageDuplicateWidget


class DuplicatesDialog(QDialog):
    def __init__(self, groups, parent=None):
        super().__init__(parent)
        ui_path = os.path.join(os.path.dirname(__file__), '../../gui/dialogs/duplicates_dialog.ui')
        uic.loadUi(ui_path, self)

        #поле для результата
        self.to_delete = []

        self.stacked_widget = self.findChild(QStackedWidget, "stackedWidget")
        self.groups = groups
        self.count_groups = len(groups)

        #находим все надписи
        self.groupCount_label = self.findChild(QLabel, "groupCount_label")
        self.currentGroup_label = self.findChild(QLabel, "currentGroup_label")

        #находим все кнопки
        self.btn_save = self.findChild(QPushButton, "save_button")
        self.btn_cancel = self.findChild(QPushButton, "cancel_button")
        self.btn_next = self.findChild(QPushButton, "nextGroup_button")
        self.btn_prev = self.findChild(QPushButton, "prevGroup_button")

        #находим все чек боксы
        self.saveAll_oneGroup_checkBox = self.findChild(QCheckBox, "saveAll_oneGroup_checkBox")
        self.deleteAll_oneGroup_checkBox = self.findChild(QCheckBox, "deleteAll_oneGroup_checkBox")
        self.saveOne_allGroups_checkBox = self.findChild(QCheckBox, "saveOne_allGroups_checkBox")
        self.deleteAll_allGroups_checkBox = self.findChild(QCheckBox, "deleteAll_allGroups_checkBox")
        self.saveAll_allGroups_checkBox = self.findChild(QCheckBox, "saveAll_allGroups_checkBox")

        #подписываем на события
        self.btn_cancel.clicked.connect(self.cancel)
        self.btn_save.clicked.connect(self.accept)
        self.btn_next.clicked.connect(self.next_group)
        self.btn_prev.clicked.connect(self.prev_group)

        self.deleteAll_oneGroup_checkBox.toggled.connect(self.deleteAll_oneGroup_changed)
        self.deleteAll_allGroups_checkBox.toggled.connect(self.deleteAll_allGroups_changed)
        self.saveAll_allGroups_checkBox.toggled.connect(self.saveAll_allGroups_changed)
        self.saveOne_allGroups_checkBox.toggled.connect(self.saveOne_allGroups_changed)
        self.saveAll_oneGroup_checkBox.toggled.connect(self.saveAll_oneGroup_changed)
        #загружаем страницы
        self.load_ui()

    def saveOne_allGroups_changed(self, checked):
        if checked:
            self.saveAll_allGroups_checkBox.setChecked(False)
            self.deleteAll_allGroups_checkBox.setChecked(False)
            self.deleteAll_oneGroup_checkBox.setChecked(False)
            self.saveAll_oneGroup_checkBox.setChecked(False)

            all_groups = self.get_allWidgetGroups()
            for img_group in all_groups:
                one_saved = False
                for img in img_group:
                    if not one_saved:
                        img.choosed = True
                        img.choosed_checkBox.setChecked(True)
                        one_saved = True
                    else:
                        img.choosed = False
                        img.choosed_checkBox.setChecked(False)

    def saveAll_allGroups_changed(self, checked):
        if checked:
            self.saveOne_allGroups_checkBox.setChecked(False)
            self.deleteAll_allGroups_checkBox.setChecked(False)
            self.deleteAll_oneGroup_checkBox.setChecked(False)
            self.saveAll_oneGroup_checkBox.setChecked(True)

            all_groups = self.get_allWidgetGroups()
            for img_groups in all_groups:
                for img in img_groups:
                    img.choosed = True
                    img.choosed_checkBox.setChecked(True)
    def deleteAll_allGroups_changed(self, checked):
        if checked:
            self.saveOne_allGroups_checkBox.setChecked(False)
            self.saveAll_allGroups_checkBox.setChecked(False)
            self.deleteAll_oneGroup_checkBox.setChecked(True)
            self.saveAll_oneGroup_checkBox.setChecked(False)

            all_groups = self.get_allWidgetGroups()
            for img_groups in all_groups:
                for img in img_groups:
                    img.choosed = False
                    img.choosed_checkBox.setChecked(False)


    def get_allWidgetGroups(self):
        widget_groups =[]
        for i in range(self.stacked_widget.count()):
            page = self.stacked_widget.widget(i)
            scroll = page.findChild(QScrollArea)
            container = scroll.widget()
            image_widgets = container.findChildren(ImageDuplicateWidget)
            widget_groups.append(image_widgets)
        return widget_groups

    def saveAll_oneGroup_changed(self, checked):
        if checked:
            self.deleteAll_oneGroup_checkBox.setChecked(False)
            self.saveOne_allGroups_checkBox.setChecked(False)
            self.deleteAll_allGroups_checkBox.setChecked(False)

            # проверяем стоят ли галочки на изображениях других групп
            all_choosed = True
            changed = False
            for i in range(self.stacked_widget.count()):
                page = self.stacked_widget.widget(i)
                image_widgets = page.findChildren(ImageDuplicateWidget)
                # если нашли текущее окно - ставим все галочки
                if i == self.stacked_widget.currentIndex():
                    for img in image_widgets:
                        img.choosed = True
                        img.choosed_checkBox.setChecked(True)
                else:
                    for img in image_widgets:
                        if not img.choosed:
                            all_choosed = False
                            break
                if not all_choosed and changed:
                    break
            if all_choosed:
                self.saveAll_allGroups_checkBox.setChecked(True)
    def deleteAll_oneGroup_changed(self, checked):
        if checked:
            self.saveAll_oneGroup_checkBox.setChecked(False)
            self.saveAll_allGroups_checkBox.setChecked(False)
            self.saveOne_allGroups_checkBox.setChecked(False)

            #проверяем стоят ли галочки на изображениях других групп
            nothing_choosed = True
            changed = False
            for i in range(self.stacked_widget.count()):
                page = self.stacked_widget.widget(i)
                scroll = page.findChild(QScrollArea)
                container = scroll.widget()
                image_widgets = container.findChildren(ImageDuplicateWidget)
                #если нашли текущее окно - убираем все галочки
                print(f"Текущая страница: {self.stacked_widget.currentIndex()}")
                print(f"Текущий индекс {i}")
                if i == self.stacked_widget.currentIndex():
                    print("меняем")
                    for img in image_widgets:
                        img.choosed = False
                        img.choosed_checkBox.setChecked(False)
                    changed = True
                else:
                    for img in image_widgets:
                        if img.choosed:
                            nothing_choosed = False
                            break
                if not nothing_choosed and changed:
                    break

            if nothing_choosed:
                self.deleteAll_allGroups_checkBox.setChecked(True)


    def load_ui(self):
        self.groupCount_label.setText(f"Найдено групп дубликатов: {self.count_groups}")
        DuplicatesViewer.display(self, self.stacked_widget, self.groups)
        self.stacked_widget.setCurrentIndex(0)
        if self.count_groups != 0:
            self.currentGroup_label.setText(f"Группа 1: {len(self.groups[0])} изобр.")
        self.btn_prev.setEnabled(False)
        if self.count_groups <= 1:
            self.btn_next.setEnabled(False)

        #по умолчанию все изображения надо будет оставить
        self.saveAll_allGroups_checkBox.setChecked(True)
        self.saveAll_oneGroup_checkBox.setChecked(True)


    def next_group(self):
        new_index = self.stacked_widget.currentIndex() + 1
        self.set_state_byPage(new_index)


    def prev_group(self):
        new_index = self.stacked_widget.currentIndex() - 1
        self.set_state_byPage(new_index)
        return

    def set_state_byPage(self, index):
        #устанавливаем надписи и кнопки
        self.stacked_widget.setCurrentIndex(index)
        if index == self.count_groups - 1:
            self.btn_next.setEnabled(False)
            self.btn_prev.setEnabled(True)
        elif index == 0:
            self.btn_next.setEnabled(True)
            self.btn_prev.setEnabled(False)
        else:
            self.btn_next.setEnabled(True)
            self.btn_prev.setEnabled(True)

        self.currentGroup_label.setText(f"Группа {index + 1}: {len(self.groups[index])} изобр.")

        # устанавливаем нужное состояние чек-боксов
        if not self.saveAll_allGroups_checkBox.isChecked() and not self.deleteAll_allGroups_checkBox.isChecked() and not self.saveOne_allGroups_checkBox.isChecked():
            page = self.stacked_widget.widget(index)
            image_widgets = page.findChildren(ImageDuplicateWidget)

            all_choosed = True
            nothing_choosed = True
            for img in image_widgets:
                if img.choosed:
                    nothing_choosed = False
                else:
                    all_choosed = False
                if not all_choosed and not nothing_choosed:
                    break

            if all_choosed:
                self.deleteAll_oneGroup_checkBox.setChecked(False)
                self.saveAll_oneGroup_checkBox.setChecked(True)
            elif nothing_choosed:
                self.deleteAll_oneGroup_checkBox.setChecked(True)
                self.saveAll_oneGroup_checkBox.setChecked(False)
            else:
                self.deleteAll_oneGroup_checkBox.setChecked(False)
                self.saveAll_oneGroup_checkBox.setChecked(False)

    def cancel(self):
        super().reject()

    def accept(self):
        #заполняем список изображений на удаление
        self.fill_toDelete_list()
        super().accept()

    def fill_toDelete_list(self):
        widget_groups = self.get_allWidgetGroups()
        for group in widget_groups:
            for img_widget in group:
                if not img_widget.choosed:
                    self.to_delete.append(img_widget.image)
