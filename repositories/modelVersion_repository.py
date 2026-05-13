import os
from datetime import datetime

from models.classification_model import ClassificationModel


class ModelVersionRepository:
    def __init__(self, conn, project_root=None):
        self.conn = conn

        if project_root:
            self.project_root = os.path.abspath(project_root)
            self.models_dir = os.path.join(self.project_root, 'clasify_models')
            os.makedirs(self.models_dir, exist_ok=True)

            # Путь к исходной модели
            self.baseline_path = os.path.join(
                self.models_dir, 'ear_larynx_nose_pharynx_trash_mobilenet.onnx'
            )

    def change_active_version(self, name):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE model_versions SET is_active = 0")
        cursor.execute("UPDATE model_versions SET is_active = 1 WHERE name = ?",
                       (name,))
        self.conn.commit()

    def load_all_versions(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM model_versions")
        rows = cursor.fetchall()
        if rows is None:
            return None

        versions = []
        for row in rows:
            model = ClassificationModel.from_row(row)
            versions.append(model)
        return versions

    def save_new_version(self, onnx_path, labels, name):
        labels_str = ",".join(labels)
        cursor = self.conn.cursor()
        cursor.execute("""INSERT INTO model_versions (name, onnx_path, label_map)
                        VALUES (?, ?, ?)""",
                       (name, onnx_path, labels_str))
        self.conn.commit()

        id = cursor.lastrowid
        return self.get_model_by_id(id)

    def get_model_by_id(self, id):
        cursor = self.conn.cursor()
        cursor.execute("""SELECT * FROM model_versions
                        WHERE id = ?""",
                       (id,))
        row = cursor.fetchone()
        if not row:
            return None

        return ClassificationModel.from_row(row)


