"""Integration tests for the full translation pipeline."""

import pytest
from unittest.mock import MagicMock, patch
from PIL import Image


@pytest.mark.integration
class TestCaptureToOCR:
    """Integration tests for capture to OCR pipeline."""
    
    def test_capture_and_preprocess(self, mock_mss, sample_image):
        """Test capturing and preprocessing an image."""
        from src.capture import ScreenCapture
        from src.ocr import ImagePreprocessor
        
        with ScreenCapture() as capture:
            result = capture.capture_monitor(0)
            
            preprocessor = ImagePreprocessor()
            processed = preprocessor.process(result.image)
            
            assert processed is not None
            assert processed.mode == "L"  # Grayscale
    
    def test_capture_region_and_ocr(self, mock_mss, mock_tesseract):
        """Test capturing a region and extracting text."""
        from src.capture import ScreenCapture
        from src.ocr import OCREngine
        
        with ScreenCapture() as capture:
            result = capture.capture_region(0, 0, 800, 600)
            
            # Mock OCR engine that only uses tesseract
            with patch("src.ocr.ocr_engine.EASYOCR_AVAILABLE", False):
                engine = OCREngine(use_easyocr=False)
                ocr_result = engine.extract_text(result.image)
                
                assert ocr_result.text != ""


@pytest.mark.integration
class TestOCRToTranslation:
    """Integration tests for OCR to translation pipeline."""
    
    def test_text_extraction_and_detection(self, sample_image, mock_tesseract):
        """Test extracting text and detecting language."""
        from src.ocr import OCREngine, TextProcessor
        from src.translation import LanguageDetector
        
        with patch("src.ocr.ocr_engine.EASYOCR_AVAILABLE", False):
            engine = OCREngine(use_easyocr=False)
            ocr_result = engine.extract_text(sample_image)
            
            processor = TextProcessor()
            processed = processor.process(ocr_result.text)
            
            detector = LanguageDetector()
            detection = detector.detect(processed.processed)
            
            assert detection.language is not None
    
    def test_ocr_to_translation_prompt(self, sample_image, mock_tesseract):
        """Test building translation prompt from OCR result."""
        from src.ocr import OCREngine
        from src.translation import PromptBuilder, LanguageDetector
        
        with patch("src.ocr.ocr_engine.EASYOCR_AVAILABLE", False):
            engine = OCREngine(use_easyocr=False)
            ocr_result = engine.extract_text(sample_image)
            
            detector = LanguageDetector()
            detection = detector.detect(ocr_result.text)
            
            builder = PromptBuilder()
            prompt = builder.build_translation_prompt(
                text=ocr_result.text,
                source_lang=detection.language,
                target_lang="en"
            )
            
            assert len(prompt) > 0
            assert ocr_result.text in prompt or "Sample" in prompt


@pytest.mark.integration
class TestFullPipeline:
    """Integration tests for the complete pipeline."""
    
    def test_capture_ocr_translate(self, mock_mss, mock_tesseract, mock_openai):
        """Test the complete capture -> OCR -> translate pipeline."""
        from src.capture import ScreenCapture
        from src.ocr import OCREngine
        from src.translation import LLMClient
        
        with ScreenCapture() as capture:
            # Capture
            capture_result = capture.capture_monitor(0)
            assert capture_result.image is not None
            
            # OCR
            with patch("src.ocr.ocr_engine.EASYOCR_AVAILABLE", False):
                engine = OCREngine(use_easyocr=False)
                ocr_result = engine.extract_text(capture_result.image)
                assert ocr_result.text != ""
                
                # Translate
                client = LLMClient(api_key="test-key")
                translation = client.translate(
                    text=ocr_result.text,
                    target_lang="ja"
                )
                
                assert translation.is_successful
    
    def test_pipeline_with_text_processing(self, mock_tesseract, mock_openai, sample_image):
        """Test pipeline including text processing."""
        from src.ocr import OCREngine, TextProcessor
        from src.translation import LLMClient, LanguageDetector
        
        with patch("src.ocr.ocr_engine.EASYOCR_AVAILABLE", False):
            # OCR
            engine = OCREngine(use_easyocr=False)
            ocr_result = engine.extract_text(sample_image)
            
            # Process text
            processor = TextProcessor()
            processed = processor.process(ocr_result.text)
            
            # Detect language
            detector = LanguageDetector()
            detection = detector.detect(processed.processed)
            
            # Translate
            client = LLMClient(api_key="test-key")
            translation = client.translate(
                text=processed.processed,
                target_lang="en",
                source_lang=detection.language
            )
            
            assert translation.translated_text != ""
