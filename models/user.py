class User:
    def __init__(self, id = None, username = None, email = None, password_hash = None ):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash

    #создание пользователя из строки БД
    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id = row['id'],
            username = row['username'],
            email = row['email'],
            password_hash = row['password_hash']
        )