class ClassificationModel:
    def __init__(self, id, name, created_at, onnx_path, label_map, is_active):
        self.id = id
        self.name = name
        self.created_at = created_at
        self.onnx_path = onnx_path
        self.label_map = label_map
        self.is_active = is_active

    @classmethod
    def from_row(cls, row):
        if not row:
            return

        labels = row['label_map'].split(",")
        return cls(
            id=row['id'],
            name=row['name'],
            created_at=row['created_at'],
            onnx_path=row['onnx_path'],
            label_map=labels,
            is_active=row['is_active']
        )