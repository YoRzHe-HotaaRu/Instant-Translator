"""
Toolbar

Control toolbar component for the Instant Translator application.
"""

from typing import Callable, List, Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QComboBox,
    QLabel, QFrame, QSizePolicy
)
from PyQt6.QtGui import QIcon

from ..capture import WindowSelector, CaptureTarget, MonitorInfo, WindowInfo
from ..translation.language_detector import LANGUAGE_NAMES


class Toolbar(QWidget):
    """
    Main toolbar for the application.
    
    Contains controls for:
    - Screen/window selection
    - Capture button
    - Language selection
    - Settings
    
    Signals:
        capture_requested: Emitted when capture button is clicked.
        target_changed: Emitted when capture target selection changes.
        language_changed: Emitted when target language changes.
    """
    
    capture_requested = pyqtSignal()
    target_changed = pyqtSignal(object)  # CaptureTarget
    language_changed = pyqtSignal(str)  # Target language code
    source_language_changed = pyqtSignal(str)  # Source OCR language code
    
    def __init__(
        self,
        window_selector: Optional[WindowSelector] = None,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        
        self._selector = window_selector or WindowSelector()
        self._owns_selector = window_selector is None
        
        self._setup_ui()
        self._connect_signals()
        self._populate_targets()
        self._populate_source_languages()
        self._populate_languages()
    
    def _setup_ui(self) -> None:
        """Set up the toolbar UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)
        
        # Target selection section
        target_label = QLabel("Capture:")
        target_label.setStyleSheet("font-weight: 600;")
        layout.addWidget(target_label)
        
        self._target_combo = QComboBox()
        self._target_combo.setMinimumWidth(250)
        self._target_combo.setToolTip("Select screen or window to capture")
        layout.addWidget(self._target_combo)
        
        # Refresh button
        self._refresh_btn = QPushButton("⟳")
        self._refresh_btn.setProperty("class", "icon-button")
        self._refresh_btn.setToolTip("Refresh window list")
        self._refresh_btn.setFixedSize(36, 36)
        layout.addWidget(self._refresh_btn)
        
        # Separator
        separator1 = QFrame()
        separator1.setFrameShape(QFrame.Shape.VLine)
        separator1.setStyleSheet("background-color: #2D2D3A;")
        layout.addWidget(separator1)
        
        # Capture button
        self._capture_btn = QPushButton("📸 Capture")
        self._capture_btn.setToolTip("Capture screenshot (Shift+C)")
        self._capture_btn.setMinimumWidth(120)
        layout.addWidget(self._capture_btn)
        
        # Separator
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.Shape.VLine)
        separator2.setStyleSheet("background-color: #2D2D3A;")
        layout.addWidget(separator2)
        
        # Source language section (OCR language)
        source_label = QLabel("Source:")
        source_label.setStyleSheet("font-weight: 600;")
        layout.addWidget(source_label)
        
        self._source_language_combo = QComboBox()
        self._source_language_combo.setMinimumWidth(120)
        self._source_language_combo.setToolTip("Language to detect in images")
        layout.addWidget(self._source_language_combo)
        
        # Spacer
        layout.addStretch()
        
        # Target language section
        lang_label = QLabel("Translate to:")
        lang_label.setStyleSheet("font-weight: 600;")
        layout.addWidget(lang_label)
        
        self._language_combo = QComboBox()
        self._language_combo.setMinimumWidth(150)
        self._language_combo.setToolTip("Target language for translation")
        layout.addWidget(self._language_combo)
        
        # Settings button
        self._settings_btn = QPushButton("⚙️")
        self._settings_btn.setProperty("class", "icon-button")
        self._settings_btn.setToolTip("Settings")
        self._settings_btn.setFixedSize(36, 36)
        layout.addWidget(self._settings_btn)
    
    def _connect_signals(self) -> None:
        """Connect internal signals."""
        self._capture_btn.clicked.connect(self._on_capture_clicked)
        self._target_combo.currentIndexChanged.connect(self._on_target_changed)
        self._language_combo.currentIndexChanged.connect(self._on_language_changed)
        self._source_language_combo.currentIndexChanged.connect(self._on_source_language_changed)
        self._refresh_btn.clicked.connect(self._on_refresh_clicked)
    
    def _populate_targets(self) -> None:
        """Populate the target selection combo box."""
        self._target_combo.clear()
        
        # Add monitors
        monitors = self._selector.get_monitors()
        if monitors:
            self._target_combo.addItem("── Monitors ──", None)
            model = self._target_combo.model()
            model.item(self._target_combo.count() - 1).setEnabled(False)
            
            for monitor in monitors:
                self._target_combo.addItem(
                    f"🖥️ {monitor}",
                    ("monitor", monitor.id)
                )
        
        # Add "All Monitors" option
        self._target_combo.addItem("🖥️ All Monitors", ("all_monitors", -1))
        
        # Add windows
        windows = self._selector.get_windows()
        if windows:
            self._target_combo.addItem("── Windows ──", None)
            model = self._target_combo.model()
            model.item(self._target_combo.count() - 1).setEnabled(False)
            
            for i, window in enumerate(windows[:20]):  # Limit to 20 windows
                title = window.title[:40] + "..." if len(window.title) > 40 else window.title
                self._target_combo.addItem(
                    f"🪟 {title}",
                    ("window", window.handle)
                )
        
        # Select first monitor by default
        if monitors:
            self._target_combo.setCurrentIndex(1)
    
    def _populate_source_languages(self) -> None:
        """Populate the source language (OCR) selection combo box."""
        self._source_language_combo.clear()
        
        # OCR source languages - these are the languages the app can detect
        source_languages = [
            ("auto", "🔍 Auto Detect"),
            ("ko", "🇰🇷 Korean"),
            ("ch_sim", "🇨🇳 Chinese"),
            ("ja", "🇯🇵 Japanese"),
            ("en", "🇬🇧 English"),
        ]
        
        for code, name in source_languages:
            self._source_language_combo.addItem(name, code)
        
        # Default to auto detect
        self._source_language_combo.setCurrentIndex(0)
    
    def _populate_languages(self) -> None:
        """Populate the language selection combo box."""
        self._language_combo.clear()
        
        # Common languages first
        common = ['en', 'ja', 'zh-cn', 'ko', 'es', 'fr', 'de']
        
        for code in common:
            name = LANGUAGE_NAMES.get(code, code)
            self._language_combo.addItem(name, code)
        
        self._language_combo.addItem("────────", None)
        model = self._language_combo.model()
        model.item(self._language_combo.count() - 1).setEnabled(False)
        
        # All other languages
        for code, name in sorted(LANGUAGE_NAMES.items(), key=lambda x: x[1]):
            if code not in common:
                self._language_combo.addItem(name, code)
        
        # Default to English
        self._language_combo.setCurrentIndex(0)
    
    def _on_capture_clicked(self) -> None:
        """Handle capture button click."""
        self.capture_requested.emit()
    
    def _on_target_changed(self, index: int) -> None:
        """Handle target selection change."""
        data = self._target_combo.currentData()
        if data is None:
            return
        
        target_type, target_id = data
        
        try:
            if target_type == "monitor":
                target = self._selector.select_monitor(target_id)
            elif target_type == "all_monitors":
                target = self._selector.select_all_monitors()
            elif target_type == "window":
                target = self._selector.select_window(target_id)
            else:
                return
            
            self.target_changed.emit(target)
            
        except Exception as e:
            print(f"Failed to select target: {e}")
    
    def _on_language_changed(self, index: int) -> None:
        """Handle language selection change."""
        code = self._language_combo.currentData()
        if code:
            self.language_changed.emit(code)
    
    def _on_source_language_changed(self, index: int) -> None:
        """Handle source language selection change."""
        code = self._source_language_combo.currentData()
        if code:
            self.source_language_changed.emit(code)
    
    def _on_refresh_clicked(self) -> None:
        """Handle refresh button click."""
        self._selector.refresh()
        self._populate_targets()
    
    def get_selected_target(self) -> Optional[CaptureTarget]:
        """Get the currently selected capture target."""
        return self._selector.get_current_target()
    
    def get_selected_language(self) -> str:
        """Get the currently selected target language."""
        return self._language_combo.currentData() or "en"
    
    def get_selected_source_language(self) -> str:
        """Get the currently selected source (OCR) language."""
        return self._source_language_combo.currentData() or "auto"
    
    def set_capture_enabled(self, enabled: bool) -> None:
        """Enable or disable the capture button."""
        self._capture_btn.setEnabled(enabled)
    
    def set_capture_text(self, text: str) -> None:
        """Set the capture button text."""
        self._capture_btn.setText(text)
    
    def close(self) -> None:
        """Release resources."""
        if self._owns_selector:
            self._selector.close()
