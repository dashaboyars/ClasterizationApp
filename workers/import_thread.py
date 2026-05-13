from PyQt6.QtCore import QThread, pyqtSignal

#поток для выполнения импорта в фоновом потоке
class BackgroundThread(QThread):
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    progress = pyqtSignal(int, str)

    def __init__(self, import_func):
        super().__init__()
        self.import_func = import_func
        self.isCancelled = False

    def run(self):
        try:
            result = self.import_func(
                progress_callback=lambda v, s: self.progress.emit(v, s),
                cancel_check=lambda: self.isCancelled
            )

            # Если операция не была отменена, отправляем результат
            if not self.isCancelled:
                self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))

    def cancel(self):
        self.isCancelled = True