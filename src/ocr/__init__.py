"""OCR module - Text extraction from images."""

from .ocr_engine import OCREngine, OCRResult, TextBlock
from .image_preprocessor import ImagePreprocessor
from .text_processor import TextProcessor

__all__ = [
    "OCREngine",
    "OCRResult",
    "TextBlock",
    "ImagePreprocessor",
    "TextProcessor"
]
