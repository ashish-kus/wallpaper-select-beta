import os
import json
import subprocess
import shlex
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QMessageBox, QScrollArea, QLineEdit
)
from PySide6.QtGui import QFont, QKeyEvent
from PySide6.QtCore import Qt, QTimer

from widgets import FlexGridWidget, ClickableLabel
from image_loader import ImageLoader


class WallpaperApp(QWidget):
    def __init__(self, config_path):
        super().__init__()
        self.setWindowTitle("Huegen - GUI")
        self.setGeometry(200, 100, 700, 450)

        self.image_loader = None
        self.thumbnail_size = 180
        self.all_image_files = []
        self.next_image_index = 0
        self.batch_size = 16
        self.loading_batch = False

        config = self.load_config(config_path)
        if "wallpaper_dir" not in config:
            QMessageBox.critical(self, "Critical Error", "Missing 'wallpaper_dir' in config")
            raise SystemExit(1)

        self.wallpaper_dir = config["wallpaper_dir"]

        if "wallpaper_command" not in config:
            QMessageBox.critical(self, "Critical Error", "Missing 'wallpaper_command' in config")
            raise SystemExit(1)
        self.wallpaper_command = config["wallpaper_command"]

        if "thumbnail_size" in config:
            self.thumbnail_size = config["thumbnail_size"]

        self.setup_ui()
        self.apply_styles()

        QTimer.singleShot(100, self.load_images_async)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        layout.setContentsMargins(5, 5, 5, 5)

        header_layout = QVBoxLayout()
        header_layout.setSpacing(5)

        title_status_layout = QHBoxLayout()

        title = QLabel("Select Wallpaper")
        title.setFont(QFont("Segoe UI", 12))
        title.setStyleSheet("color: #f8f8f2; margin-bottom: 5px; margin-left: 20px;")
        title_status_layout.addWidget(title)

        title_status_layout.addStretch()

        right_compact = QHBoxLayout()
        right_compact.setSpacing(8)

        self.status_label = QLabel("Loading...")
        self.status_label.setFont(QFont("Segoe UI", 9))
        self.status_label.setStyleSheet(
            """
            color: #6c7086;
            background-color: rgba(108, 112, 134, 0.1);
            padding: 4px 8px;
            border-radius: 12px;
            border: 1px solid rgba(108, 112, 134, 0.2);
            """
        )
        right_compact.addWidget(self.status_label)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.setFixedWidth(200)
        self.search_input.setStyleSheet(
            """
            QLineEdit {
                background-color: #2b2d3a;
                color: #f8f8f2;
                border: 1px solid #3a3d58;
                border-radius: 12px;
                padding: 4px 10px;
                font-size: 10px;
            }
            QLineEdit:focus {
                border-color: #89b4fa;
            }
            """
        )
        right_compact.addWidget(self.search_input)

        title_status_layout.addLayout(right_compact)

        header_layout.addLayout(title_status_layout)

        layout.addLayout(header_layout)

        self.scroll = QScrollArea(self)
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll.setStyleSheet(
            """
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            """
        )

        self.grid_widget = FlexGridWidget()
        self.scroll.setWidget(self.grid_widget)
        layout.addWidget(self.scroll)
        self.scroll.verticalScrollBar().valueChanged.connect(self.on_scroll)

        self.setMinimumSize(800, 600)

        self.grid_widget.setFocus()

        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.apply_search_filter)
        self.search_input.textChanged.connect(self.on_search_text_changed)

    def apply_styles(self):
        self.setStyleSheet(
            """
            QWidget {
                background-color: #1e1e2e;
                color: #f8f8f2;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QScrollBar:vertical {
                background-color: #313244;
                width: 8px;
                border-radius: 4px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background-color: #585b70;
                border-radius: 4px;
                min-height: 30px;
                margin: 2px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #89b4fa;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar:horizontal {
                background-color: #313244;
                height: 8px;
                border-radius: 4px;
                margin: 0;
            }
            QScrollBar::handle:horizontal {
                background-color: #585b70;
                border-radius: 4px;
                min-width: 30px;
                margin: 2px;
            }
            QScrollBar::handle:horizontal:hover {
                background-color: #89b4fa;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
            """
        )

    def load_config(self, path):
        if not os.path.exists(path):
            QMessageBox.critical(self, "Error", f"Config file not found: {path}")
            raise SystemExit(1)

        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to read config:\n{e}")
            raise SystemExit(1)

    def load_images_async(self):
        if not os.path.isdir(self.wallpaper_dir):
            QMessageBox.critical(self, "Error", f"Invalid wallpaper directory: {self.wallpaper_dir}")
            raise SystemExit(1)

        supported_formats = {".png", ".jpg", ".jpeg", ".bmp", ".webp", ".tiff", ".tif"}
        image_files = []

        try:
            for file in os.listdir(self.wallpaper_dir):
                if Path(file).suffix.lower() in supported_formats:
                    image_files.append(os.path.join(self.wallpaper_dir, file))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error reading directory: {e}")
            return

        if not image_files:
            self.status_label.setText("No images found")
            return

        image_files.sort()
        self.all_image_files = image_files
        self.next_image_index = 0
        self.loading_batch = False

        total_count = len(self.all_image_files)
        self.status_label.setText(f"Loading 0/{total_count}")
        self.load_next_batch()

    def create_placeholder_labels(self, image_files):
        for img_path in image_files:
            label = ClickableLabel(img_path, self.thumbnail_size)
            self.grid_widget.add_image_label(label)

        QTimer.singleShot(50, self.grid_widget.layout_items)

    def load_next_batch(self):
        if self.loading_batch:
            return
        if self.next_image_index >= len(self.all_image_files):
            return
        self.loading_batch = True
        end = min(len(self.all_image_files), self.next_image_index + self.batch_size)
        batch = self.all_image_files[self.next_image_index:end]
        self.next_image_index = end
        self.create_placeholder_labels(batch)
        self.image_loader = ImageLoader(batch, self.thumbnail_size)
        self.image_loader.image_loaded.connect(self.on_image_loaded)
        self.image_loader.finished.connect(self.on_loading_finished)
        self.image_loader.start()

    def on_image_loaded(self, image_path, pixmap):
        for label in self.grid_widget.image_labels:
            if label.image_path == image_path:
                label.set_loaded_pixmap(pixmap)
                break

        loaded_count = sum(1 for label in self.grid_widget.image_labels if label.loaded)
        total_count = len(self.all_image_files) or len(self.grid_widget.image_labels)
        self.status_label.setText(f"Loaded {loaded_count}/{total_count}")

    def on_loading_finished(self):
        self.loading_batch = False
        loaded_count = sum(1 for label in self.grid_widget.image_labels if label.loaded)
        total_count = len(self.all_image_files) or len(self.grid_widget.image_labels)
        if total_count == 0:
            self.status_label.setText("No images loaded")
        elif loaded_count == total_count and self.next_image_index >= len(self.all_image_files):
            self.status_label.setText(f"{loaded_count} images")
        else:
            self.status_label.setText(f"Loaded {loaded_count}/{total_count}")

        if self.grid_widget.image_labels and self.grid_widget.selected_index == -1:
            for idx, lbl in enumerate(self.grid_widget.image_labels):
                if lbl.isVisible():
                    self.grid_widget.select_item(idx)
                    break

        QTimer.singleShot(0, self.maybe_load_more)

        self.apply_search_filter()

    def execute_wallpaper_command(self, image_path):
        try:
            command = self.wallpaper_command.replace("{path}", image_path)
            command = command.replace("<selected image path>", image_path)

            filename = os.path.basename(image_path)
            self.status_label.setText(f"Setting: {filename}")

            if os.name == 'nt':
                result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=10)
            else:
                try:
                    args = shlex.split(command)
                    result = subprocess.run(args, capture_output=True, text=True, timeout=10)
                except ValueError:
                    result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=10)

            if result.returncode == 0:
                self.status_label.setText(f"✓ Set: {filename}")
                print(f"Successfully set wallpaper: {image_path}")
                if result.stdout:
                    print(f"Command output: {result.stdout}")
            else:
                stderr_msg = (result.stderr or "").strip()
                stdout_msg = (result.stdout or "").strip()
                summary = stderr_msg or stdout_msg or "Unknown error"
                self.status_label.setText(f"✗ Failed ({result.returncode}): {summary[:50]}...")
                print(f"Command failed with code {result.returncode}")
                if stdout_msg:
                    print(f"STDOUT: {stdout_msg}")
                if stderr_msg:
                    print(f"STDERR: {stderr_msg}")

        except subprocess.TimeoutExpired:
            self.status_label.setText("✗ Timeout")
            print(f"Command timeout for: {image_path}")
        except FileNotFoundError:
            self.status_label.setText("✗ Command not found")
            print(f"Command not found: {self.wallpaper_command}")
        except Exception as e:
            self.status_label.setText(f"✗ Error: {str(e)[:20]}...")
            print(f"Error executing command: {e}")

    def show_command_info(self):
        QMessageBox.information(
            self,
            "Wallpaper Command",
            f"Current command:\n{self.wallpaper_command}\n\n"
            "Placeholders:\n"
            "• {path} or <selected image path> will be replaced with the image path\n\n"
            "Keyboard Navigation:\n"
            "• Arrow keys to navigate\n"
            "• Enter/Space to select wallpaper",
        )

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        modifiers = event.modifiers()
        is_ctrl = bool(modifiers & (Qt.ControlModifier | Qt.MetaModifier))
        printable = (32 <= key <= 126) and not is_ctrl
        edit_key = key in (Qt.Key_Backspace, Qt.Key_Delete)

        if printable or edit_key:
            if hasattr(self, 'search_input'):
                self.search_input.setFocus()
                from PySide6.QtWidgets import QApplication
                QApplication.sendEvent(self.search_input, event)
                return

        self.grid_widget.keyPressEvent(event)

    def on_scroll(self, _value: int):
        self.maybe_load_more()

    def maybe_load_more(self):
        sb = self.scroll.verticalScrollBar()
        if not sb:
            return
        near_bottom = (sb.maximum() - sb.value()) <= max(100, sb.pageStep() // 2)
        if near_bottom:
            self.load_next_batch()

    def on_search_text_changed(self, _text: str):
        self.search_timer.start(120)

    def apply_search_filter(self):
        text = self.search_input.text() if hasattr(self, 'search_input') else ""
        visible = self.grid_widget.filter_by_text(text)
        total = len(self.grid_widget.image_labels)
        if total:
            self.status_label.setText(f"Showing {visible}/{total}")

    def resizeEvent(self, event):
        super().resizeEvent(event)

    def closeEvent(self, event):
        if self.image_loader and self.image_loader.isRunning():
            self.image_loader.stop()
            self.image_loader.wait(1000)
        event.accept()


