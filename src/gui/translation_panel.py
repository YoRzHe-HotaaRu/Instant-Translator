"""
Translation Panel

Right panel displaying extracted text and translation results.
"""

from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTextEdit, QFrame, QPushButton, QApplication,
    QTabWidget, QSizePolicy
)


class TranslationPanel(QWidget):
    """
    Translation panel with OCR text and translation display.
    
    Provides:
    - Tabs for extracted text and translation
    - Copy to clipboard functionality
    - Text editing capability
    
    Signals:
        retranslate_requested: Emitted when retranslation is requested.
        text_copied: Emitted when text is copied to clipboard.
    """
    
    retranslate_requested = pyqtSignal(str)
    text_copied = pyqtSignal()
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
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
        
        title = QLabel("📝 Translation")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Copy button
        self._copy_btn = QPushButton("📋 Copy")
        self._copy_btn.setProperty("class", "secondary")
        self._copy_btn.setToolTip("Copy translation to clipboard")
        header_layout.addWidget(self._copy_btn)
        
        layout.addWidget(header)
        
        # Tab widget for extracted text and translation
        self._tabs = QTabWidget()
        self._tabs.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background-color: #0A0A0F;
            }
            QTabBar::tab {
                background-color: #1A1A24;
                color: #94A3B8;
                padding: 10px 20px;
                border: none;
                border-bottom: 2px solid transparent;
            }
            QTabBar::tab:selected {
                color: #F8FAFC;
                border-bottom: 2px solid #6366F1;
            }
            QTabBar::tab:hover:!selected {
                color: #F8FAFC;
            }
        """)
        
        # Extracted text tab
        extracted_widget = QWidget()
        extracted_layout = QVBoxLayout(extracted_widget)
        extracted_layout.setContentsMargins(0, 0, 0, 0)
        
        self._extracted_text = QTextEdit()
        self._extracted_text.setPlaceholderText("Extracted text will appear here...")
        self._extracted_text.setReadOnly(False)  # Allow editing for correction
        self._extracted_text.setStyleSheet("""
            QTextEdit {
                background-color: #0A0A0F;
                border: none;
                padding: 16px;
                font-size: 14px;
                line-height: 1.6;
            }
        """)
        extracted_layout.addWidget(self._extracted_text)
        
        # Retranslate button for edited text
        retranslate_bar = QWidget()
        retranslate_bar.setStyleSheet("background-color: #1A1A24; border-top: 1px solid #2D2D3A;")
        retranslate_layout = QHBoxLayout(retranslate_bar)
        retranslate_layout.setContentsMargins(16, 8, 16, 8)
        
        retranslate_hint = QLabel("💡 Edit text above to correct OCR errors")
        retranslate_hint.setStyleSheet("color: #64748B; font-size: 12px;")
        retranslate_layout.addWidget(retranslate_hint)
        
        retranslate_layout.addStretch()
        
        self._retranslate_btn = QPushButton("🔄 Retranslate")
        self._retranslate_btn.setProperty("class", "secondary")
        retranslate_layout.addWidget(self._retranslate_btn)
        
        extracted_layout.addWidget(retranslate_bar)
        
        self._tabs.addTab(extracted_widget, "📄 Extracted Text")
        
        # Translation tab
        translation_widget = QWidget()
        translation_layout = QVBoxLayout(translation_widget)
        translation_layout.setContentsMargins(0, 0, 0, 0)
        
        self._translation_text = QTextEdit()
        self._translation_text.setPlaceholderText("Translation will appear here...")
        self._translation_text.setReadOnly(True)
        self._translation_text.setStyleSheet("""
            QTextEdit {
                background-color: #0A0A0F;
                border: none;
                padding: 16px;
                font-size: 15px;
                line-height: 1.8;
            }
        """)
        translation_layout.addWidget(self._translation_text)
        
        self._tabs.addTab(translation_widget, "🌐 Translation")
        
        # Default to translation tab
        self._tabs.setCurrentIndex(1)
        
        layout.addWidget(self._tabs, 1)
        
        # Footer with status
        footer = QWidget()
        footer.setStyleSheet("background-color: #1A1A24; border-top: 1px solid #2D2D3A;")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(16, 8, 16, 8)
        
        self._status_label = QLabel("Ready")
        self._status_label.setStyleSheet("color: #94A3B8; font-size: 12px;")
        footer_layout.addWidget(self._status_label)
        
        footer_layout.addStretch()
        
        self._confidence_label = QLabel("")
        self._confidence_label.setStyleSheet("color: #64748B; font-size: 12px;")
        footer_layout.addWidget(self._confidence_label)
        
        layout.addWidget(footer)
        
        # Connect signals
        self._copy_btn.clicked.connect(self._on_copy)
        self._retranslate_btn.clicked.connect(self._on_retranslate)
    
    def set_extracted_text(self, text: str, confidence: float = 0.0) -> None:
        """
        Set the extracted OCR text.
        
        Args:
            text: The extracted text.
            confidence: OCR confidence score (0-1).
        """
        self._extracted_text.setText(text)
        
        if confidence > 0:
            confidence_pct = int(confidence * 100)
            color = "#10B981" if confidence >= 0.8 else "#F59E0B" if confidence >= 0.5 else "#EF4444"
            self._confidence_label.setText(f"OCR Confidence: {confidence_pct}%")
            self._confidence_label.setStyleSheet(f"color: {color}; font-size: 12px;")
    
    def set_translation(self, text: str, source_lang: str = "", target_lang: str = "") -> None:
        """
        Set the translation result.
        
        Args:
            text: The translated text.
            source_lang: Source language name.
            target_lang: Target language name.
        """
        self._translation_text.setText(text)
        
        if source_lang and target_lang:
            self._status_label.setText(f"Translated: {source_lang} → {target_lang}")
        else:
            self._status_label.setText("Translation complete")
        
        # Switch to translation tab
        self._tabs.setCurrentIndex(1)
    
    def set_status(self, status: str) -> None:
        """Set the status message."""
        self._status_label.setText(status)
    
    def set_processing(self, processing: bool) -> None:
        """Set processing state."""
        if processing:
            self._status_label.setText("Processing...")
            self._copy_btn.setEnabled(False)
            self._retranslate_btn.setEnabled(False)
        else:
            self._copy_btn.setEnabled(True)
            self._retranslate_btn.setEnabled(True)
    
    def get_extracted_text(self) -> str:
        """Get the current extracted text (may be edited by user)."""
        return self._extracted_text.toPlainText()
    
    def get_translation(self) -> str:
        """Get the current translation."""
        return self._translation_text.toPlainText()
    
    def clear(self) -> None:
        """Clear all text."""
        self._extracted_text.clear()
        self._translation_text.clear()
        self._status_label.setText("Ready")
        self._confidence_label.setText("")
    
    def _on_copy(self) -> None:
        """Handle copy button click."""
        # Copy the translation (or extracted if on that tab)
        if self._tabs.currentIndex() == 0:
            text = self._extracted_text.toPlainText()
        else:
            text = self._translation_text.toPlainText()
        
        if text:
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            self._status_label.setText("Copied to clipboard!")
            self.text_copied.emit()
    
    def _on_retranslate(self) -> None:
        """Handle retranslate button click."""
        text = self._extracted_text.toPlainText()
        if text:
            self.retranslate_requested.emit(text)
