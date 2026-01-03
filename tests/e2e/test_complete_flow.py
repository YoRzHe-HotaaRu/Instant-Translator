"""End-to-end tests for the complete application flow."""

import pytest
from unittest.mock import MagicMock, patch


@pytest.mark.e2e
class TestCompleteWorkflow:
    """End-to-end tests for complete application workflow."""
    
    def test_basic_translation_workflow(self, mock_mss, mock_tesseract, mock_openai):
        """Test basic workflow: capture -> OCR -> translate."""
        from src.capture import ScreenCapture, WindowSelector
        from src.ocr import OCREngine, ImagePreprocessor, TextProcessor
        from src.translation import LLMClient, LanguageDetector
        
        # 1. Initialize components
        capture = ScreenCapture()
        selector = WindowSelector(capture)
        preprocessor = ImagePreprocessor()
        detector = LanguageDetector()
        
        with patch("src.ocr.ocr_engine.EASYOCR_AVAILABLE", False):
            ocr_engine = OCREngine(use_easyocr=False)
        
        text_processor = TextProcessor()
        llm_client = LLMClient(api_key="test-key")
        
        # 2. Select target
        monitors = selector.get_monitors()
        assert len(monitors) > 0
        target = selector.select_monitor(0)
        
        # 3. Capture
        result = capture.capture_monitor(target.monitor.id)
        assert result.image is not None
        
        # 4. Preprocess
        processed_image = preprocessor.process(result.image)
        assert processed_image is not None
        
        # 5. OCR
        with patch("src.ocr.ocr_engine.EASYOCR_AVAILABLE", False):
            ocr_result = ocr_engine.extract_text(processed_image)
        assert ocr_result.text != ""
        
        # 6. Process text
        cleaned = text_processor.process(ocr_result.text)
        
        # 7. Detect language
        detection = detector.detect(cleaned.processed)
        
        # 8. Translate
        translation = llm_client.translate(
            text=cleaned.processed,
            target_lang="ja",
            source_lang=detection.language
        )
        
        assert translation.is_successful
        assert translation.translated_text != ""
        
        # Cleanup
        capture.close()
        selector.close()
    
    def test_retranslation_workflow(self, mock_tesseract, mock_openai, sample_image):
        """Test retranslation with edited text."""
        from src.ocr import OCREngine, TextProcessor
        from src.translation import LLMClient
        
        with patch("src.ocr.ocr_engine.EASYOCR_AVAILABLE", False):
            ocr_engine = OCREngine(use_easyocr=False)
            ocr_result = ocr_engine.extract_text(sample_image)
        
        # User edits the OCR result
        edited_text = ocr_result.text + " (corrected)"
        
        # Retranslate
        llm_client = LLMClient(api_key="test-key")
        translation = llm_client.translate(
            text=edited_text,
            target_lang="ja",
            source_lang="en"
        )
        
        assert translation.is_successful
    
    def test_multi_language_workflow(self, mock_tesseract, mock_openai, sample_texts):
        """Test workflow with multiple languages."""
        from src.translation import LLMClient, LanguageDetector
        
        detector = LanguageDetector()
        client = LLMClient(api_key="test-key")
        
        test_cases = [
            (sample_texts["english"], "ja"),
            (sample_texts["japanese"], "en"),
            (sample_texts["chinese"], "en"),
        ]
        
        for text, target_lang in test_cases:
            detection = detector.detect(text)
            
            translation = client.translate(
                text=text,
                target_lang=target_lang,
                source_lang=detection.language
            )
            
            assert translation.is_successful


@pytest.mark.e2e
class TestErrorRecovery:
    """Tests for error recovery scenarios."""
    
    def test_empty_ocr_result(self, mock_mss, sample_image):
        """Test handling of empty OCR result."""
        from src.capture import ScreenCapture
        from src.ocr import TextProcessor
        from src.translation import LanguageDetector
        
        # Simulate empty OCR result
        empty_text = ""
        
        processor = TextProcessor()
        result = processor.process(empty_text)
        
        detector = LanguageDetector()
        detection = detector.detect(result.processed)
        
        # Should fall back to default language
        assert detection.language == "en"
        assert detection.confidence == 0.0
    
    def test_invalid_capture_target(self, mock_mss):
        """Test handling of invalid capture target."""
        from src.capture import ScreenCapture, ScreenCaptureError
        
        capture = ScreenCapture()
        
        with pytest.raises(ScreenCaptureError):
            capture.capture_monitor(999)
        
        capture.close()
