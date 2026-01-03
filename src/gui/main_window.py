"""
Main Window

Primary application window for the Instant Translator.
"""

import asyncio
import logging
import threading
from typing import Optional

from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject, QTimer
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QStatusBar, QMessageBox, QApplication
)
from PIL import Image

# Global hotkey support
try:
    import keyboard
    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False

from ..capture import ScreenCapture, WindowSelector, CaptureTarget
from ..ocr import OCREngine, OCRResult
from ..translation import LLMClient, TranslationResult, LanguageDetector

from .toolbar import Toolbar
from .screenshot_panel import ScreenshotPanel
from .translation_panel import TranslationPanel
from .styles import Styles, apply_theme


logger = logging.getLogger(__name__)

# Default hotkey
DEFAULT_HOTKEY = "shift+c"


class TranslationWorker(QObject):
    """
    Worker thread for running OCR and translation.
    
    Signals:
        ocr_completed: Emitted when OCR extraction is done.
        translation_completed: Emitted when translation is done.
        error_occurred: Emitted when an error occurs.
    """
    
    ocr_completed = pyqtSignal(object)  # OCRResult
    translation_completed = pyqtSignal(object)  # TranslationResult
    error_occurred = pyqtSignal(str)
    progress_updated = pyqtSignal(str)
    
    def __init__(
        self,
        ocr_engine: OCREngine,
        llm_client: LLMClient,
        parent: Optional[QObject] = None
    ):
        super().__init__(parent)
        self._ocr_engine = ocr_engine
        self._llm_client = llm_client
        self._image: Optional[Image.Image] = None
        self._text: Optional[str] = None
        self._target_lang: str = "en"
        self._mode: str = "full"  # "full" or "translate_only"
    
    def set_image(self, image: Image.Image, target_lang: str) -> None:
        """Set the image for OCR and translation."""
        self._image = image
        self._target_lang = target_lang
        self._mode = "full"
    
    def set_text(self, text: str, target_lang: str) -> None:
        """Set text for translation only (skip OCR)."""
        self._text = text
        self._target_lang = target_lang
        self._mode = "translate_only"
    
    def process(self) -> None:
        """Run the OCR and/or translation process."""
        try:
            if self._mode == "full" and self._image:
                # Step 1: OCR
                self.progress_updated.emit("Extracting text...")
                ocr_result = self._ocr_engine.extract_text(self._image)
                self.ocr_completed.emit(ocr_result)
                
                if ocr_result.is_empty:
                    self.error_occurred.emit("No text found in image")
                    return
                
                self._text = ocr_result.text
            
            if self._text:
                # Step 2: Translation
                self.progress_updated.emit("Translating...")
                translation_result = self._llm_client.translate(
                    text=self._text,
                    target_lang=self._target_lang
                )
                self.translation_completed.emit(translation_result)
            
        except Exception as e:
            logger.error(f"Processing error: {e}")
            self.error_occurred.emit(str(e))


class MainWindow(QMainWindow):
    """
    Main application window for Instant Translator.
    
    Provides the complete UI including:
    - Toolbar with capture and language controls
    - Split-view with screenshot and translation panels
    - Status bar with progress information
    """
    
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://zenmux.ai/api/v1",
        model: str = "deepseek/deepseek-v3.2",
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        
        # Initialize components
        self._screen_capture = ScreenCapture()
        self._window_selector = WindowSelector(self._screen_capture)
        
        self._ocr_engine = OCREngine(
            languages=['en', 'ko', 'ch_sim'],  # English + Korean + Chinese Simplified
            use_tesseract=True,
            use_easyocr=True
        )
        
        self._llm_client = LLMClient(
            api_key=api_key,
            base_url=base_url,
            model=model
        )
        
        self._current_target_lang = "en"
        self._current_source_lang = "auto"  # Auto detect by default
        
        # Set up UI
        self._setup_window()
        self._setup_ui()
        self._setup_worker()
        self._connect_signals()
        self._setup_global_hotkey()
    
    def _setup_window(self) -> None:
        """Configure the main window."""
        self.setWindowTitle("Instant Translator")
        self.setMinimumSize(1000, 700)
        self.resize(1200, 800)
        
        # Apply theme
        app = QApplication.instance()
        if app:
            self._styles = apply_theme(app)
    
    def _setup_ui(self) -> None:
        """Set up the main UI layout."""
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Toolbar
        self._toolbar = Toolbar(self._window_selector)
        self._toolbar.setStyleSheet("""
            background-color: #1A1A24;
            border-bottom: 1px solid #2D2D3A;
        """)
        layout.addWidget(self._toolbar)
        
        # Main content area with splitter
        self._splitter = QSplitter(Qt.Orientation.Horizontal)
        self._splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #2D2D3A;
                width: 2px;
            }
            QSplitter::handle:hover {
                background-color: #6366F1;
            }
        """)
        
        # Left panel - Screenshot
        self._screenshot_panel = ScreenshotPanel()
        self._screenshot_panel.setStyleSheet("""
            background-color: #1A1A24;
            border-right: 1px solid #2D2D3A;
        """)
        self._splitter.addWidget(self._screenshot_panel)
        
        # Right panel - Translation
        self._translation_panel = TranslationPanel()
        self._translation_panel.setStyleSheet("""
            background-color: #1A1A24;
        """)
        self._splitter.addWidget(self._translation_panel)
        
        # Set initial splitter sizes (50/50)
        self._splitter.setSizes([500, 500])
        
        layout.addWidget(self._splitter, 1)
        
        # Status bar
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        self._status_bar.showMessage("Ready - Select a capture target and click Capture")
    
    def _setup_worker(self) -> None:
        """Set up the worker thread."""
        self._worker_thread = QThread()
        self._worker = TranslationWorker(self._ocr_engine, self._llm_client)
        self._worker.moveToThread(self._worker_thread)
        
        # Connect worker signals
        self._worker.ocr_completed.connect(self._on_ocr_completed)
        self._worker.translation_completed.connect(self._on_translation_completed)
        self._worker.error_occurred.connect(self._on_error)
        self._worker.progress_updated.connect(self._on_progress)
        
        self._worker_thread.started.connect(self._worker.process)
        self._worker_thread.start()
    
    def _connect_signals(self) -> None:
        """Connect UI signals."""
        self._toolbar.capture_requested.connect(self._on_capture)
        self._toolbar.language_changed.connect(self._on_language_changed)
        self._toolbar.source_language_changed.connect(self._on_source_language_changed)
        self._translation_panel.retranslate_requested.connect(self._on_retranslate)
    
    def _on_capture(self) -> None:
        """Handle capture request."""
        target = self._toolbar.get_selected_target()
        
        if not target:
            self._status_bar.showMessage("Please select a capture target first")
            return
        
        try:
            # Disable capture button
            self._toolbar.set_capture_enabled(False)
            self._toolbar.set_capture_text("⏳ Capturing...")
            
            # Perform capture based on target type
            from ..capture import CaptureTargetType
            
            if target.type == CaptureTargetType.MONITOR:
                if target.monitor and target.monitor.id >= 0:
                    result = self._screen_capture.capture_monitor(target.monitor.id)
                else:
                    result = self._screen_capture.capture_all_monitors()
            elif target.type == CaptureTargetType.WINDOW and target.window:
                result = self._screen_capture.capture_window(target.window.handle)
            elif target.type == CaptureTargetType.REGION and target.region:
                x, y, w, h = target.region
                result = self._screen_capture.capture_region(x, y, w, h)
            else:
                raise ValueError("Invalid capture target")
            
            # Display screenshot
            self._screenshot_panel.set_image(result.image, result.source_name)
            
            # Start OCR and translation
            self._translation_panel.set_processing(True)
            self._worker.set_image(result.image, self._current_target_lang)
            
            # Restart thread if not running
            if not self._worker_thread.isRunning():
                self._worker_thread.start()
            else:
                # Trigger processing
                self._worker.process()
            
        except Exception as e:
            logger.error(f"Capture failed: {e}")
            self._status_bar.showMessage(f"Capture failed: {e}")
            QMessageBox.warning(self, "Capture Error", str(e))
        
        finally:
            self._toolbar.set_capture_enabled(True)
            self._toolbar.set_capture_text("📸 Capture")
    
    def _on_language_changed(self, lang_code: str) -> None:
        """Handle target language change."""
        self._current_target_lang = lang_code
        self._status_bar.showMessage(f"Target language: {LanguageDetector.get_language_name(lang_code)}")
    
    def _on_source_language_changed(self, lang_code: str) -> None:
        """Handle source (OCR) language change."""
        self._current_source_lang = lang_code
        
        # Update OCR engine with new language
        if lang_code == "auto":
            # Auto detect: try all languages
            languages = ['en', 'ko', 'ch_sim']
        else:
            # Specific language: only use that + English
            languages = [lang_code]
            if lang_code != 'en':
                languages.append('en')
        
        # Recreate OCR engine with new languages
        self._ocr_engine = OCREngine(
            languages=languages,
            use_tesseract=True,
            use_easyocr=True
        )
        self._worker._ocr_engine = self._ocr_engine
        
        lang_name = {
            "auto": "Auto Detect",
            "ko": "Korean", 
            "ch_sim": "Chinese",
            "ja": "Japanese",
            "en": "English"
        }.get(lang_code, lang_code)
        
        self._status_bar.showMessage(f"Source language: {lang_name}")
    
    def _on_retranslate(self, text: str) -> None:
        """Handle retranslation request."""
        self._translation_panel.set_processing(True)
        self._worker.set_text(text, self._current_target_lang)
        
        if not self._worker_thread.isRunning():
            self._worker_thread.start()
        else:
            self._worker.process()
    
    def _on_ocr_completed(self, result: OCRResult) -> None:
        """Handle OCR completion."""
        self._translation_panel.set_extracted_text(result.text, result.confidence)
        self._status_bar.showMessage(f"Text extracted (confidence: {result.confidence:.0%})")
    
    def _on_translation_completed(self, result: TranslationResult) -> None:
        """Handle translation completion."""
        self._translation_panel.set_processing(False)
        
        source_name = LanguageDetector.get_language_name(result.source_language)
        target_name = LanguageDetector.get_language_name(result.target_language)
        
        self._translation_panel.set_translation(
            result.translated_text,
            source_name,
            target_name
        )
        
        cached_str = " (cached)" if result.cached else ""
        self._status_bar.showMessage(
            f"Translation complete: {source_name} → {target_name}{cached_str} "
            f"({result.latency_ms:.0f}ms)"
        )
    
    def _on_progress(self, message: str) -> None:
        """Handle progress update."""
        self._status_bar.showMessage(message)
    
    def _on_error(self, error: str) -> None:
        """Handle error."""
        self._translation_panel.set_processing(False)
        self._translation_panel.set_status(f"Error: {error}")
        self._status_bar.showMessage(f"Error: {error}")
    
    def _setup_global_hotkey(self) -> None:
        """Set up global hotkey for capture."""
        if not KEYBOARD_AVAILABLE:
            logger.warning("keyboard module not available - global hotkeys disabled")
            return
        
        self._hotkey = DEFAULT_HOTKEY
        
        try:
            # Register global hotkey
            keyboard.add_hotkey(
                self._hotkey,
                self._on_hotkey_triggered,
                suppress=False
            )
            logger.info(f"Global hotkey registered: {self._hotkey.upper()}")
            self._status_bar.showMessage(
                f"Ready - Press {self._hotkey.upper()} to capture from anywhere"
            )
        except Exception as e:
            logger.error(f"Failed to register hotkey: {e}")
    
    def _on_hotkey_triggered(self) -> None:
        """Handle global hotkey press."""
        # Use QTimer to call capture from the main thread
        QTimer.singleShot(100, self._on_capture)
    
    def closeEvent(self, event) -> None:
        """Handle window close."""
        # Unregister hotkey
        if KEYBOARD_AVAILABLE:
            try:
                keyboard.unhook_all()
            except Exception:
                pass
        
        # Clean up
        self._worker_thread.quit()
        self._worker_thread.wait()
        
        self._screen_capture.close()
        self._window_selector.close()
        self._llm_client.close()
        
        event.accept()
