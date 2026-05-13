import json
import os
import copy

from PyQt6.QtCore import QMimeData, QUrl


class Dataset:
    DATASET_MIME_TYPE = 'application/x-dataset-data'

    def __init__(self, name, file_path, user_id, id=None, created_at = None):
        self.id = id
        self.name = name
        self.file_path = file_path
        self.created_at = created_at
        self.user_id = user_id
        self.images_list = []
        self.sessions_list = []
        self.classification_groups = []
        self.sessions_count = 0
        self.quality_passed = False
        self.no_duplicates = False

    def find_classificationSession_byName(self, name):
        for sn in self.classification_groups:
            if sn.name == name:
                return sn


    def add_existing_images(self, images):
        to_add = copy.deepcopy(images)
        for img in to_add:
            img.status = "uploaded"
        self.images_list = to_add

    def remove_sessions(self, sessions):
        for sn in sessions:
            self.sessions_list.remove(sn)
            self.sessions_count -= 1

    def remove_images(self, imgs):
        for img in imgs:
            self.images_list.remove(img)

    def create_mimeData(self):
        mime_data = QMimeData()

        data = {
            'dataset_id': self.id,
            'filepath': self.file_path,
            'user_id': self.user_id
        }
        mime_data.setData(Dataset.DATASET_MIME_TYPE, json.dumps(data, ensure_ascii=False).encode())

        if hasattr(self, 'file_path') and os.path.exists(self.file_path):
            mime_data.setUrls([QUrl.fromLocalFile(self.file_path)])

        return mime_data

    def get_activeImages(self):
        print(len(self.images_list))
        return [img for img in self.images_list if img.status != "deleted"]

    def count_images(self):
        return len([img for img in self.images_list if img.status != "deleted"])
    # создание датасета из строки БД
    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id = row['id'],
            name = row['name'],
            file_path = row['file_path'],
            created_at = row['create_time'],
            user_id = row['user_id']
        )
