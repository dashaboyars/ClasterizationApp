from models.user import User

class UserRepository:
    def __init__(self, db):
        self.db = db

    #поиск пользователя по имени
    def get_by_username(self, username):
        cursor = self.db.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        )
        #получаем строку из результата запроса
        row = cursor.fetchone()
        return User.from_row(row)

    def create_user(self, username, email, password_hash):
        cursor = self.db.cursor()

        cursor.execute(
            """
            INSERT INTO users (username, email, password_hash)
            VALUES (?, ?, ?)
            """,
            (username, email, password_hash)
        )
        self.db.commit()

        return self.get_by_username(username)




