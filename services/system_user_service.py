from repositories.user_repository import UserRepository

#для работы с ситемным пользователем (без регистрации и входа)
class SystemUserService:
    SYSTEM_USERNAME = "system_user"
    SYSTEM_EMAIL = "system_user@mail.ru"
    SYSTEM_PASSWORD_HASH = "system_hash"

    def __init__(self, db):
        self.conn = db.connect()
        self.user_repo = UserRepository(self.conn)

    #получаем системного пользователя
    def get_or_create_system_user(self):
        user = self.user_repo.get_by_username(self.SYSTEM_USERNAME)

        if not user:
            user = self.user_repo.create_user(self.SYSTEM_USERNAME, self.SYSTEM_EMAIL, self.SYSTEM_PASSWORD_HASH)
        return user


