import os

from PyQt6.QtWidgets import *
from qtpy import uic

from ui.visualization_subsystem.quality_table_model import QualityTable


class QualityAnalyseResultsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        ui_path = os.path.join(os.path.dirname(__file__), '../../gui/dialogs/qualityAnalyse_results_dialog.ui')
        uic.loadUi(ui_path, self)
        self.table_passed = self.findChild(QTableView, "tableView_passed")
        self.table_failed = self.findChild(QTableView, "tableView_failed")
        self.all_images_label = self.findChild(QLabel, "all_images_label")
        self.passed_label = self.findChild(QLabel, "passed_label")
        self.failed_label = self.findChild(QLabel, "failed_label")

        self.btn_acceptChanges = self.findChild(QPushButton, "btn_acceptChanges")
        self.btn_Close = self.findChild(QPushButton, "btn_Close")

        if self.btn_acceptChanges:
            self.btn_acceptChanges.clicked.connect(self.accept_changes)
        if self.btn_Close:
            self.btn_Close.clicked.connect(self.reject_changes)

    def set_results(self, all_images, badQuality_images):
        headers = [
            "Имя файла", "Размер (KB)", "Разрешение", "Кол-во цветов",
            "Резкость", "Шум", "Контраст", "Проблемы"
        ]
        passed_quality = []
        failed_quality = []
        for img in all_images:
            if img.status == "quality_passed":
                img_data = {
                    "file_name": img.filename,
                    "size": img.quality_params['file_size'],
                    "resolution": f"{img.quality_params['resolution_width']}x{img.quality_params['resolution_height']}",
                    "colors": img.quality_params['colors_amount'],
                    "sharpness": img.quality_params['sharpness'],
                    "noise": img.quality_params['noise_level'],
                    "contrast": img.quality_params['contrast'],
                    "problems": "OK",
                }
                passed_quality.append(img_data)
            elif img.status == "quality_failed":
                img_data = {
                    "file_name": img.filename,
                    "size": img.quality_params['file_size'],
                    "resolution": f"{img.quality_params['resolution_width']}x{img.quality_params['resolution_height']}",
                    "colors": img.quality_params['colors_amount'],
                    "sharpness": img.quality_params['sharpness'],
                    "noise": img.quality_params['noise_level'],
                    "contrast": img.quality_params['contrast'],
                    "problems": " ,".join(badQuality_images[img.filename]),
                }
                failed_quality.append(img_data)
        #создание моделей
        failedTable_model = QualityTable(failed_quality, headers)
        passedTable_model = QualityTable(passed_quality, headers)
        # Устанавливаем модели
        self.table_passed.setModel(passedTable_model)
        self.table_failed.setModel(failedTable_model)

        for table in [self.table_passed, self.table_failed]:
            # Растягиваем колонки
            table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            # Разрешаем сортировку
            table.setSortingEnabled(True)

        self.all_images_label.setText(f"Всего изображений: {len(all_images)}")
        self.passed_label.setText(f"Прошли проверку: {len(passed_quality)} изобр.")
        self.failed_label.setText(f"Не прошли проверку: {len(failed_quality)} изобр.")

    def accept_changes(self):
        self.accept()
        return

    def reject_changes(self):
        self.reject()
        return
