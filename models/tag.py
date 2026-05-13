class Tag:
    def __init__(self, id = None, name = None):
        self.id = id
        self.name = name
        self.images_list = []

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id = row['id'],
            name = row['name']
        )
