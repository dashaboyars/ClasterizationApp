class AnomalyGroup:
    def __init__(self, id, name, session_id, created_at=None):
        self.id = id
        self.name = name
        self.created_at = created_at
        self.session_id = session_id
        self.images_list = []

    # создание группы аномалий из строки БД
    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id=row['id'],
            name=row['name'],
            created_at=row['created_at'],
            session_id=row['session_id']
        )
