import sqlite3

class DatabaseConnection:
    def __init__(self, db_path):
        self.db_path = db_path

    #подключение к БД
    def connect(self):
        connection = sqlite3.connect(self.db_path)
        # Включаем поддержку внешних ключей
        connection.execute("PRAGMA foreign_keys = ON")
        # Возвращаем строки как словари с доступом по имени
        connection.row_factory = sqlite3.Row
        return connection
