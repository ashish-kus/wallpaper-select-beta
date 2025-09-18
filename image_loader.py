import os
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QPixmap


class ImageLoader(QThread):
    """Background thread for loading images"""
    image_loaded = Signal(str, QPixmap)

    def __init__(self, image_paths, thumbnail_size):
        super().__init__()
        self.image_paths = image_paths
        self.thumbnail_size = thumbnail_size
        self.should_stop = False

    def stop(self):
        self.should_stop = True

    def run(self):
        for img_path in self.image_paths:
            if self.should_stop:
                break

            try:
                pixmap = QPixmap(img_path)
                if not pixmap.isNull():
                    scaled_pixmap = pixmap.scaled(
                        self.thumbnail_size,
                        self.thumbnail_size,
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation,
                    )
                    self.image_loaded.emit(img_path, scaled_pixmap)

                self.msleep(10)
            except Exception as e:
                print(f"Error loading {img_path}: {e}")


