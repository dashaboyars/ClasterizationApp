import os
import subprocess
import sys
from datetime import datetime

import numpy as np
from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QDesktopServices


class Image:
    def __init__(self, filename, filepath, format, embedding, quality_params,
                 status = None, uploaded_at = None, dataset_id=None, exif_data=None,id=None):
        self.id = id
        self.filename = filename
        self.filepath = filepath
        self.exif_data = exif_data
        self.format = format
        if isinstance(embedding, bytes):
            self.embedding = np.frombuffer(embedding, dtype=np.float32)
        else:
            self.embedding = embedding
        self.quality_params = quality_params
        self.tags_list = []
        self.clusters_list = [] #можно будет удалить
        self.datasets_list = [] #можно будет удалить
        self.status = status #??
        self.uploaded_at = uploaded_at #??


    def open_file(self):
        normalized = os.path.normpath(self.filepath)
        if sys.platform == 'win32':  # Windows
            subprocess.run(['cmd', '/c', 'start', '', normalized], shell=True)
        elif sys.platform == 'darwin':  # macOS
            subprocess.run(['open', '-a', 'Finder', normalized])
        else:  # Linux
            subprocess.run(['xdg-open', normalized])

    def copy(self):
        new_image = Image(f"{self.filename}-копия",
                          self.filepath,
                          self.format,
                          self.embedding.copy(),
                          self.quality_params.copy(),
                          "uploaded",
                          datetime.now().isoformat())
        new_image.tags_list = self.tags_list.copy()
        return new_image

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        if row['image_status'] is not None:
            image_status = row['image_status']
        else:
            image_status = None

        if row['upload_time'] is not None:
            upload_time = row['upload_time']
        else:
            upload_time = None
        return cls(
            id = row['id'],
            filename = row['file_name'],
            filepath = row['file_path'],
            exif_data = row['exif'],
            format = row['format'],
            embedding = row['vector_data'],
            quality_params={
                'file_size': row['file_size'],
                'resolution_width': row['resolution_width'],
                'resolution_height': row['resolution_height'],
                'colors_amount': row['colors_amount'],
                'sharpness': row['sharpness'],
                'noise_level': row['noise_level'],
                'contrast': row['contrast']
            },
            status = image_status,
            uploaded_at=upload_time
        )

