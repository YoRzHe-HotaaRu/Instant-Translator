"""
Screenshot Panel

Left panel displaying the captured screenshot with zoom/pan controls.
"""

from typing import Optional

from PyQt6.QtCore import Qt, QRectF, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QFrame, QPushButton, QSizePolicy
)
from PyQt6.QtGui import QPixmap, QImage, QPainter, QWheelEvent, QMouseEvent
from PIL import Image


class ImageViewer(QLabel):
    """
    Zoomable, pannable image viewer.
    
    Supports:
    - Mouse wheel zoom
    - Click and drag pan
    - Fit to window
    """
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        self._pixmap: Optional[QPixmap] = None
        self._zoom_factor: float = 1.0
        self._min_zoom: float = 0.1
        self._max_zoom: float = 5.0
        self._pan_start = None
        
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(200, 200)
        self.setStyleSheet("background-color: #0A0A0F; border-radius: 8px;")
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.setMouseTracking(True)
    
    def set_image(self, image: Image.Image) -> None:
        """
        Set the image to display.
        
        Args:
            image: PIL Image to display.
        """
        # Convert PIL Image to QPixmap
        if image.mode == "RGB":
            data = image.tobytes("raw", "RGB")
            qimage = QImage(data, image.width, image.height, 
                          image.width * 3, QImage.Format.Format_RGB888)
        elif image.mode == "RGBA":
            data = image.tobytes("raw", "RGBA")
            qimage = QImage(data, image.width, image.height,
                          image.width * 4, QImage.Format.Format_RGBA8888)
        else:
            # Convert to RGB
            rgb_image = image.convert("RGB")
            data = rgb_image.tobytes("raw", "RGB")
            qimage = QImage(data, rgb_image.width, rgb_image.height,
                          rgb_image.width * 3, QImage.Format.Format_RGB888)
        
        self._pixmap = QPixmap.fromImage(qimage)
        self._zoom_factor = 1.0
        self._update_display()
    
    def clear_image(self) -> None:
        """Clear the displayed image."""
        self._pixmap = None
        self.clear()
        self.setText("No screenshot captured")
    
    def fit_to_window(self) -> None:
        """Fit the image to the window size."""
        if not self._pixmap:
            return
        
        # Calculate zoom to fit
        widget_size = self.size()
        image_size = self._pixmap.size()
        
        zoom_x = widget_size.width() / image_size.width()
        zoom_y = widget_size.height() / image_size.height()
        
        self._zoom_factor = min(zoom_x, zoom_y) * 0.95  # 95% to add margin
        self._update_display()
    
    def reset_zoom(self) -> None:
        """Reset zoom to 100%."""
        self._zoom_factor = 1.0
        self._update_display()
    
    def zoom_in(self) -> None:
        """Zoom in by 20%."""
        self._zoom_factor = min(self._max_zoom, self._zoom_factor * 1.2)
        self._update_display()
    
    def zoom_out(self) -> None:
        """Zoom out by 20%."""
        self._zoom_factor = max(self._min_zoom, self._zoom_factor / 1.2)
        self._update_display()
    
    def _update_display(self) -> None:
        """Update the displayed image with current zoom."""
        if not self._pixmap:
            return
        
        scaled = self._pixmap.scaled(
            int(self._pixmap.width() * self._zoom_factor),
            int(self._pixmap.height() * self._zoom_factor),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        
        self.setPixmap(scaled)
    
    def wheelEvent(self, event: QWheelEvent) -> None:
        """Handle mouse wheel for zooming."""
        if not self._pixmap:
            return
        
        delta = event.angleDelta().y()
        
        if delta > 0:
            self._zoom_factor = min(self._max_zoom, self._zoom_factor * 1.1)
        else:
            self._zoom_factor = max(self._min_zoom, self._zoom_factor / 1.1)
        
        self._update_display()
    
    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle mouse press for panning."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._pan_start = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
    
    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Handle mouse release."""
        self._pan_start = None
        self.setCursor(Qt.CursorShape.OpenHandCursor)
    
    def get_zoom_percentage(self) -> int:
        """Get current zoom as percentage."""
        return int(self._zoom_factor * 100)


class ScreenshotPanel(QWidget):
    """
    Screenshot panel with image viewer and controls.
    
    Provides:
    - Image display with zoom/pan
    - Zoom controls
    - Image info display
    """
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        self._current_image: Optional[Image.Image] = None
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Set up the panel UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        header = QWidget()
        header.setProperty("class", "panel-header")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 12, 16, 12)
        
        title = QLabel("📷 Screenshot")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Zoom controls
        self._zoom_out_btn = QPushButton("−")
        self._zoom_out_btn.setProperty("class", "icon-button")
        self._zoom_out_btn.setFixedSize(28, 28)
        self._zoom_out_btn.setToolTip("Zoom out")
        header_layout.addWidget(self._zoom_out_btn)
        
        self._zoom_label = QLabel("100%")
        self._zoom_label.setMinimumWidth(50)
        self._zoom_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(self._zoom_label)
        
        self._zoom_in_btn = QPushButton("+")
        self._zoom_in_btn.setProperty("class", "icon-button")
        self._zoom_in_btn.setFixedSize(28, 28)
        self._zoom_in_btn.setToolTip("Zoom in")
        header_layout.addWidget(self._zoom_in_btn)
        
        self._fit_btn = QPushButton("⊡")
        self._fit_btn.setProperty("class", "icon-button")
        self._fit_btn.setFixedSize(28, 28)
        self._fit_btn.setToolTip("Fit to window")
        header_layout.addWidget(self._fit_btn)
        
        layout.addWidget(header)
        
        # Image viewer with scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        scroll_area.setStyleSheet("border: none; background-color: #0A0A0F;")
        
        self._viewer = ImageViewer()
        self._viewer.setText("No screenshot captured\n\nSelect a target and click Capture")
        self._viewer.setStyleSheet("""
            color: #64748B;
            font-size: 14px;
            background-color: #0A0A0F;
        """)
        scroll_area.setWidget(self._viewer)
        
        layout.addWidget(scroll_area, 1)
        
        # Footer with info
        footer = QWidget()
        footer.setStyleSheet("background-color: #1A1A24; border-top: 1px solid #2D2D3A;")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(16, 8, 16, 8)
        
        self._info_label = QLabel("Ready")
        self._info_label.setStyleSheet("color: #94A3B8; font-size: 12px;")
        footer_layout.addWidget(self._info_label)
        
        footer_layout.addStretch()
        
        self._size_label = QLabel("")
        self._size_label.setStyleSheet("color: #64748B; font-size: 12px;")
        footer_layout.addWidget(self._size_label)
        
        layout.addWidget(footer)
        
        # Connect signals
        self._zoom_in_btn.clicked.connect(self._on_zoom_in)
        self._zoom_out_btn.clicked.connect(self._on_zoom_out)
        self._fit_btn.clicked.connect(self._on_fit)
    
    def set_image(self, image: Image.Image, source_name: str = "") -> None:
        """
        Set the screenshot image.
        
        Args:
            image: PIL Image to display.
            source_name: Name of the capture source.
        """
        self._current_image = image
        self._viewer.set_image(image)
        self._viewer.fit_to_window()
        self._update_zoom_label()
        
        # Update info
        if source_name:
            self._info_label.setText(f"Source: {source_name}")
        else:
            self._info_label.setText("Screenshot captured")
        
        self._size_label.setText(f"{image.width} × {image.height}")
    
    def clear(self) -> None:
        """Clear the screenshot."""
        self._current_image = None
        self._viewer.clear_image()
        self._info_label.setText("Ready")
        self._size_label.setText("")
        self._zoom_label.setText("100%")
    
    def get_image(self) -> Optional[Image.Image]:
        """Get the current screenshot image."""
        return self._current_image
    
    def _on_zoom_in(self) -> None:
        """Handle zoom in click."""
        self._viewer.zoom_in()
        self._update_zoom_label()
    
    def _on_zoom_out(self) -> None:
        """Handle zoom out click."""
        self._viewer.zoom_out()
        self._update_zoom_label()
    
    def _on_fit(self) -> None:
        """Handle fit to window click."""
        self._viewer.fit_to_window()
        self._update_zoom_label()
    
    def _update_zoom_label(self) -> None:
        """Update the zoom percentage label."""
        self._zoom_label.setText(f"{self._viewer.get_zoom_percentage()}%")
