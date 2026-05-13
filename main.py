import sys
import os
import ctypes
from importlib.util import find_spec

# Предзагрузка c10.dll для PyTorch (Windows)
if sys.platform == "win32":
    try:
        spec = find_spec("torch")
        if spec and spec.origin:
            dll_path = os.path.join(os.path.dirname(spec.origin), "lib", "c10.dll")
            if os.path.exists(dll_path):
                ctypes.CDLL(os.path.normpath(dll_path))
    except Exception:
        pass

# Теперь импортируем torch (ранний импорт, чтобы избежать конфликта с PyQt)
import torch

from PyQt6.QtWidgets import QApplication

from database import DatabaseConnection
from ui.main_window import MainWindow
from services.system_user_service import SystemUserService
import traceback

def exception_hook(exctype, value, tb):
    """Перехватывает необработанные исключения и выводит traceback"""
    print("=" * 60)
    print("❌ НЕОБРАБОТАННОЕ ИСКЛЮЧЕНИЕ:")
    print("=" * 60)
    traceback.print_exception(exctype, value, tb)
    print("=" * 60)
    sys.__excepthook__(exctype, value, tb)

# Устанавливаем перехватчик исключений
sys.excepthook = exception_hook
def main():
    # 1. Подключаемся к БД
    db = DatabaseConnection('database/DBClasterizationApp.db')
    db.connect()

    # 2. Получаем системного пользователя
    user_service = SystemUserService(db)
    system_user = user_service.get_or_create_system_user()

    # 3. Запускаем GUI
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = MainWindow(db, system_user)
    window.show()

    # 4. Завершаем работу
    result = app.exec()
    sys.exit(result)


if __name__ == '__main__':
    main()