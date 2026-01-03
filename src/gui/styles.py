"""
GUI Styles

Custom theming and styling for the Instant Translator application.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ColorPalette:
    """Color palette for the application theme."""
    # Primary colors
    primary: str = "#6366F1"  # Indigo
    primary_hover: str = "#4F46E5"
    primary_light: str = "#A5B4FC"
    
    # Background colors
    background: str = "#0F0F15"  # Dark background
    surface: str = "#1A1A24"
    surface_elevated: str = "#252532"
    
    # Text colors
    text_primary: str = "#F8FAFC"
    text_secondary: str = "#94A3B8"
    text_muted: str = "#64748B"
    
    # Accent colors
    success: str = "#10B981"
    warning: str = "#F59E0B"
    error: str = "#EF4444"
    info: str = "#3B82F6"
    
    # Border colors
    border: str = "#2D2D3A"
    border_focus: str = "#6366F1"


@dataclass  
class Typography:
    """Typography settings."""
    font_family: str = "'Segoe UI', 'SF Pro Display', -apple-system, sans-serif"
    font_size_xs: str = "11px"
    font_size_sm: str = "13px"
    font_size_base: str = "14px"
    font_size_lg: str = "16px"
    font_size_xl: str = "20px"
    font_size_2xl: str = "24px"


@dataclass
class Spacing:
    """Spacing values."""
    xs: str = "4px"
    sm: str = "8px"
    md: str = "16px"
    lg: str = "24px"
    xl: str = "32px"


class Styles:
    """
    Centralized styling for the application.
    
    Provides consistent colors, typography, and component styles.
    """
    
    def __init__(
        self,
        colors: Optional[ColorPalette] = None,
        typography: Optional[Typography] = None,
        spacing: Optional[Spacing] = None
    ):
        self.colors = colors or ColorPalette()
        self.typography = typography or Typography()
        self.spacing = spacing or Spacing()
    
    def get_main_stylesheet(self) -> str:
        """Get the main application stylesheet."""
        return f"""
/* Main Window */
QMainWindow {{
    background-color: {self.colors.background};
}}

/* Central Widget */
QWidget {{
    background-color: transparent;
    color: {self.colors.text_primary};
    font-family: {self.typography.font_family};
    font-size: {self.typography.font_size_base};
}}

/* Labels */
QLabel {{
    color: {self.colors.text_primary};
    background: transparent;
}}

QLabel[class="title"] {{
    font-size: {self.typography.font_size_xl};
    font-weight: bold;
}}

QLabel[class="subtitle"] {{
    font-size: {self.typography.font_size_sm};
    color: {self.colors.text_secondary};
}}

/* Buttons */
QPushButton {{
    background-color: {self.colors.primary};
    color: {self.colors.text_primary};
    border: none;
    border-radius: 6px;
    padding: 10px 20px;
    font-weight: 600;
    font-size: {self.typography.font_size_base};
}}

QPushButton:hover {{
    background-color: {self.colors.primary_hover};
}}

QPushButton:pressed {{
    background-color: {self.colors.primary};
}}

QPushButton:disabled {{
    background-color: {self.colors.surface_elevated};
    color: {self.colors.text_muted};
}}

QPushButton[class="secondary"] {{
    background-color: {self.colors.surface_elevated};
    border: 1px solid {self.colors.border};
}}

QPushButton[class="secondary"]:hover {{
    border-color: {self.colors.primary};
}}

QPushButton[class="icon-button"] {{
    background: transparent;
    padding: 8px;
    border-radius: 4px;
}}

QPushButton[class="icon-button"]:hover {{
    background-color: {self.colors.surface_elevated};
}}

/* ComboBox */
QComboBox {{
    background-color: {self.colors.surface};
    border: 1px solid {self.colors.border};
    border-radius: 6px;
    padding: 8px 12px;
    color: {self.colors.text_primary};
    min-width: 150px;
}}

QComboBox:hover {{
    border-color: {self.colors.primary_light};
}}

QComboBox:focus {{
    border-color: {self.colors.border_focus};
}}

QComboBox::drop-down {{
    border: none;
    width: 24px;
}}

QComboBox::down-arrow {{
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid {self.colors.text_secondary};
    margin-right: 8px;
}}

QComboBox QAbstractItemView {{
    background-color: {self.colors.surface};
    border: 1px solid {self.colors.border};
    border-radius: 6px;
    selection-background-color: {self.colors.primary};
    selection-color: {self.colors.text_primary};
    padding: 4px;
}}

/* Text Edit */
QTextEdit, QPlainTextEdit {{
    background-color: {self.colors.surface};
    border: 1px solid {self.colors.border};
    border-radius: 8px;
    padding: 12px;
    color: {self.colors.text_primary};
    font-size: {self.typography.font_size_base};
    selection-background-color: {self.colors.primary};
}}

QTextEdit:focus, QPlainTextEdit:focus {{
    border-color: {self.colors.border_focus};
}}

/* Scroll Area */
QScrollArea {{
    background: transparent;
    border: none;
}}

QScrollBar:vertical {{
    background-color: {self.colors.surface};
    width: 12px;
    border-radius: 6px;
    margin: 2px;
}}

QScrollBar::handle:vertical {{
    background-color: {self.colors.border};
    border-radius: 5px;
    min-height: 30px;
    margin: 2px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {self.colors.text_muted};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

/* Splitter */
QSplitter::handle {{
    background-color: {self.colors.border};
    width: 2px;
}}

QSplitter::handle:hover {{
    background-color: {self.colors.primary};
}}

/* Status Bar */
QStatusBar {{
    background-color: {self.colors.surface};
    border-top: 1px solid {self.colors.border};
    color: {self.colors.text_secondary};
    font-size: {self.typography.font_size_sm};
    padding: 4px;
}}

/* Group Box */
QGroupBox {{
    background-color: {self.colors.surface};
    border: 1px solid {self.colors.border};
    border-radius: 8px;
    margin-top: 16px;
    padding-top: 16px;
    font-weight: 600;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 8px;
    color: {self.colors.text_secondary};
}}

/* Progress Bar */
QProgressBar {{
    background-color: {self.colors.surface_elevated};
    border: none;
    border-radius: 4px;
    height: 8px;
    text-align: center;
}}

QProgressBar::chunk {{
    background-color: {self.colors.primary};
    border-radius: 4px;
}}

/* Tool Tips */
QToolTip {{
    background-color: {self.colors.surface_elevated};
    color: {self.colors.text_primary};
    border: 1px solid {self.colors.border};
    border-radius: 4px;
    padding: 6px 10px;
    font-size: {self.typography.font_size_sm};
}}

/* Menu */
QMenuBar {{
    background-color: {self.colors.surface};
    border-bottom: 1px solid {self.colors.border};
    padding: 4px;
}}

QMenuBar::item {{
    background: transparent;
    padding: 6px 12px;
    border-radius: 4px;
}}

QMenuBar::item:selected {{
    background-color: {self.colors.surface_elevated};
}}

QMenu {{
    background-color: {self.colors.surface};
    border: 1px solid {self.colors.border};
    border-radius: 8px;
    padding: 4px;
}}

QMenu::item {{
    padding: 8px 24px;
    border-radius: 4px;
}}

QMenu::item:selected {{
    background-color: {self.colors.primary};
}}
"""
    
    def get_panel_stylesheet(self) -> str:
        """Get stylesheet for content panels."""
        return f"""
QWidget[class="panel"] {{
    background-color: {self.colors.surface};
    border: 1px solid {self.colors.border};
    border-radius: 12px;
}}

QWidget[class="panel-header"] {{
    background-color: {self.colors.surface_elevated};
    border-bottom: 1px solid {self.colors.border};
    border-radius: 12px 12px 0 0;
    padding: 12px 16px;
}}
"""
    
    def get_toolbar_stylesheet(self) -> str:
        """Get stylesheet for toolbar."""
        return f"""
QToolBar {{
    background-color: {self.colors.surface};
    border-bottom: 1px solid {self.colors.border};
    padding: 8px 16px;
    spacing: 8px;
}}

QToolBar::separator {{
    background-color: {self.colors.border};
    width: 1px;
    margin: 0 8px;
}}
"""


def apply_theme(app, styles: Optional[Styles] = None) -> Styles:
    """
    Apply the theme to a QApplication.
    
    Args:
        app: The QApplication instance.
        styles: Optional Styles instance to use.
        
    Returns:
        The Styles instance used.
    """
    styles = styles or Styles()
    
    # Combine all stylesheets
    full_stylesheet = "\n".join([
        styles.get_main_stylesheet(),
        styles.get_panel_stylesheet(),
        styles.get_toolbar_stylesheet()
    ])
    
    app.setStyleSheet(full_stylesheet)
    
    return styles
