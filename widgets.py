import os
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QPixmap, QMouseEvent, QFont, QPainter, QColor, QKeyEvent
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QScrollArea


class ClickableLabel(QLabel):
    """Clickable label with loading state"""

    def __init__(self, image_path, thumbnail_size=200, parent=None):
        super().__init__(parent)
        self.image_path = image_path
        self.thumbnail_size = thumbnail_size
        self.loaded = False
        self._orig_pixmap = None

        self.setAlignment(Qt.AlignCenter)
        self.setCursor(Qt.ArrowCursor)
        self.setStyleSheet(
            """
            QLabel {
                background-color: #44475a;
                border-radius: 8px;
                border: 2px solid transparent;
            }
            """
        )

        self.show_loading_state()

    def show_loading_state(self):
        """Show loading placeholder"""
        pixmap = QPixmap(self.thumbnail_size, int(self.thumbnail_size * 0.75))
        pixmap.fill(QColor("#44475a"))

        painter = QPainter(pixmap)
        painter.setPen(QColor("#f8f8f2"))
        painter.setFont(QFont("Arial", 8))
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "Loading...")
        painter.end()

        self.setPixmap(pixmap)

        filename = os.path.basename(self.image_path)
        if len(filename) > 25:
            filename = filename[:22] + "..."
        self.setToolTip(filename)

    def set_loaded_pixmap(self, pixmap):
        """Set the actual loaded pixmap"""
        self._orig_pixmap = pixmap
        if self.width() > 0 and self.height() > 0:
            self._render_fit_pixmap(self.width(), self.height())
        else:
            self.setPixmap(pixmap)
        self.loaded = True

        filename = os.path.basename(self.image_path)
        size_info = f"{pixmap.width()}x{pixmap.height()}"
        self.setToolTip(f"{filename}\n{size_info}")

    def _render_fit_pixmap(self, target_w: int, target_h: int):
        """Render current image to fill target size by cropping (cover)."""
        try:
            source = self._orig_pixmap if (self.loaded and self._orig_pixmap) else self.pixmap()
            if not source or source.isNull():
                return
            scaled = source.scaled(
                target_w,
                target_h,
                Qt.KeepAspectRatioByExpanding,
                Qt.SmoothTransformation,
            )
            x = max(0, (scaled.width() - target_w) // 2)
            y = max(0, (scaled.height() - target_h) // 2)
            cropped = scaled.copy(x, y, target_w, target_h)
            self.setPixmap(cropped)
        except Exception:
            self.setPixmap(
                source.scaled(
                    target_w, target_h, Qt.IgnoreAspectRatio, Qt.SmoothTransformation
                )
            )

    def mousePressEvent(self, event: QMouseEvent):
        event.ignore()


class FlexGridWidget(QWidget):
    """Widget that manages flexbox-like layout with minimum heights"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.StrongFocus)
        self.image_labels = []
        self.label_frames = []
        self.selected_index = -1
        self.min_item_height = 100
        self.item_spacing = 0
        self.margin = 0

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(self.margin, self.margin, self.margin, self.margin)
        self.main_layout.setSpacing(self.item_spacing)
        self.main_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        self.rows = []

    def add_image_label(self, label):
        """Add image label to flex layout without extra container"""
        label.setStyleSheet(
            """
            QLabel {
                background-color: #313244;
                border-radius: 12px;
                border: 2px solid transparent;
                padding: 0px;
            }
            """
        )
        label.setMinimumHeight(self.min_item_height)
        self.image_labels.append(label)
        self.label_frames.append(label)

        if self.width() > 100:
            self.layout_items()

    def layout_items(self):
        """Layout items in flexbox-like manner"""
        if not self.label_frames:
            return

        self.clear_layout()

        visible_frames = [w for w in self.label_frames if w.isVisible()]
        if not visible_frames:
            return

        available_width = self.width() - (self.margin * 2)
        if available_width <= 0:
            available_width = 1000

        min_cell = 160
        target_cols = max(2, min(8, available_width // min_cell))
        item_width = max(
            min_cell, (available_width - (self.item_spacing * (target_cols - 1))) // target_cols
        )

        items_per_row = max(1, (available_width + self.item_spacing) // (item_width + self.item_spacing))

        current_row = None
        for visible_index, frame in enumerate(visible_frames):
            if visible_index % items_per_row == 0:
                current_row = QHBoxLayout()
                current_row.setSpacing(self.item_spacing)
                current_row.setContentsMargins(0, 0, 0, 0)
                current_row.setAlignment(Qt.AlignLeft)
                self.rows.append(current_row)
                self.main_layout.addLayout(current_row)

            if frame.parent() != self:
                frame.setParent(self)
            frame.setFixedSize(item_width, int(item_width * 0.75))
            if isinstance(frame, ClickableLabel):
                frame._render_fit_pixmap(frame.width(), frame.height())
            current_row.addWidget(frame)

        self.update_selection()

    def clear_layout(self):
        """Properly clear the layout"""
        for row_layout in self.rows:
            while row_layout.count():
                row_layout.takeAt(0)

        for row_layout in self.rows:
            self.main_layout.removeItem(row_layout)
            row_layout.deleteLater()

        self.rows.clear()

    def update_selection(self):
        """Update visual selection indicator"""
        for i, frame in enumerate(self.label_frames):
            if i == self.selected_index:
                frame.setStyleSheet(
                    """
                    QLabel {
                        background-color: #383a59;
                        border-radius: 12px;
                        border: 2px solid #89b4fa;
                        padding: 4px;
                    }
                    """
                )
            else:
                frame.setStyleSheet(
                    """
                    QLabel {
                        background-color: #313244;
                        border-radius: 12px;
                        border: 2px solid transparent;
                        padding: 4px;
                    }
                    """
                )

    def select_item(self, index):
        """Select an item by index"""
        if 0 <= index < len(self.image_labels):
            self.selected_index = index
            self.update_selection()

            if self.label_frames:
                selected_frame = self.label_frames[index]
                scroll_area = self.parent()
                while scroll_area and not isinstance(scroll_area, QScrollArea):
                    scroll_area = scroll_area.parent()

                if scroll_area:
                    scroll_area.ensureWidgetVisible(selected_frame)

    def filter_by_text(self, text: str) -> int:
        """Filter items by filename substring (case-insensitive). Returns visible count."""
        query = (text or "").strip().lower()
        visible_count = 0
        for label in self.image_labels:
            filename = os.path.basename(label.image_path).lower()
            is_match = (query in filename) if query else True
            label.setVisible(is_match)
            if is_match:
                visible_count += 1
        self.layout_items()
        if not (0 <= self.selected_index < len(self.image_labels)) or not self.image_labels[self.selected_index].isVisible():
            for idx, lbl in enumerate(self.image_labels):
                if lbl.isVisible():
                    self.select_item(idx)
                    break
        else:
            self.update_selection()
        return visible_count

    def select_label(self, label):
        """Select item by label widget and focus grid for keyboard navigation"""
        try:
            index = self.image_labels.index(label)
        except ValueError:
            return
        self.select_item(index)
        self.setFocus()

    def get_items_per_row(self):
        """Calculate current items per row"""
        if not self.rows:
            return 1
        if self.rows:
            first_row = self.rows[0]
            count = 0
            for i in range(first_row.count()):
                item = first_row.itemAt(i)
                if item and item.widget():
                    count += 1
            return max(1, count)
        return 1

    def keyPressEvent(self, event: QKeyEvent):
        """Handle keyboard navigation"""
        if not self.image_labels:
            super().keyPressEvent(event)
            return

        items_per_row = self.get_items_per_row()
        current_index = self.selected_index

        if current_index == -1:
            current_index = 0

        if event.key() == Qt.Key_Right:
            new_index = min(current_index + 1, len(self.image_labels) - 1)
        elif event.key() == Qt.Key_Left:
            new_index = max(current_index - 1, 0)
        elif event.key() == Qt.Key_Down:
            new_index = min(current_index + items_per_row, len(self.image_labels) - 1)
        elif event.key() == Qt.Key_Up:
            new_index = max(current_index - items_per_row, 0)
        elif event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space):
            if 0 <= current_index < len(self.image_labels):
                label = self.image_labels[current_index]
                parent_widget = self.parent()
                while parent_widget and not hasattr(parent_widget, 'execute_wallpaper_command'):
                    parent_widget = parent_widget.parent()
                if parent_widget:
                    parent_widget.execute_wallpaper_command(label.image_path)
            return
        else:
            super().keyPressEvent(event)
            return

        self.select_item(new_index)

    def resizeEvent(self, event):
        """Handle widget resize"""
        super().resizeEvent(event)
        if not hasattr(self, 'resize_timer'):
            self.resize_timer = QTimer()
            self.resize_timer.setSingleShot(True)
            self.resize_timer.timeout.connect(self.layout_items)

        self.resize_timer.stop()
        self.resize_timer.start(50)


