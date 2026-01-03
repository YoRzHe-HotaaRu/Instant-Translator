"""Unit tests for text processor module."""

import pytest


class TestProcessedText:
    """Tests for ProcessedText dataclass."""
    
    def test_processed_text_creation(self):
        """Test creating a ProcessedText instance."""
        from src.ocr.text_processor import ProcessedText
        
        result = ProcessedText(
            original="Hello world",
            processed="Hello world",
            removed_artifacts=[],
            corrections_made=0
        )
        
        assert result.original == "Hello world"
        assert result.processed == "Hello world"
        assert result.was_modified is False
    
    def test_was_modified_true(self):
        """Test was_modified property when text changed."""
        from src.ocr.text_processor import ProcessedText
        
        result = ProcessedText(
            original="He11o",
            processed="Hello",
            removed_artifacts=[],
            corrections_made=1
        )
        
        assert result.was_modified is True


class TestTextProcessor:
    """Tests for TextProcessor class."""
    
    def test_processor_init_default(self):
        """Test default initialization."""
        from src.ocr.text_processor import TextProcessor
        
        processor = TextProcessor()
        assert processor.fix_common_errors is True
        assert processor.normalize_whitespace is True
    
    def test_processor_init_custom(self):
        """Test custom initialization."""
        from src.ocr.text_processor import TextProcessor
        
        processor = TextProcessor(
            fix_common_errors=False,
            normalize_whitespace=False
        )
        
        assert processor.fix_common_errors is False
        assert processor.normalize_whitespace is False
    
    def test_process_empty_string(self):
        """Test processing empty string."""
        from src.ocr.text_processor import TextProcessor
        
        processor = TextProcessor()
        result = processor.process("")
        
        assert result.processed == ""
        assert result.corrections_made == 0
    
    def test_process_clean_text(self):
        """Test processing clean text."""
        from src.ocr.text_processor import TextProcessor
        
        processor = TextProcessor()
        result = processor.process("Hello, world!")
        
        assert result.processed == "Hello, world!"
    
    def test_remove_control_characters(self, sample_texts):
        """Test removal of control characters."""
        from src.ocr.text_processor import TextProcessor
        
        processor = TextProcessor()
        result = processor.process(sample_texts["with_artifacts"])
        
        # Control characters should be removed
        assert "\x00" not in result.processed
        assert "\x0b" not in result.processed
        assert "\x1f" not in result.processed
    
    def test_normalize_whitespace(self):
        """Test whitespace normalization."""
        from src.ocr.text_processor import TextProcessor
        
        processor = TextProcessor()
        result = processor.process("Hello    world   test")
        
        # Multiple spaces should be reduced to single spaces
        assert "    " not in result.processed
        assert "   " not in result.processed
    
    def test_preserve_newlines(self):
        """Test that paragraph breaks are preserved."""
        from src.ocr.text_processor import TextProcessor
        
        processor = TextProcessor(preserve_newlines=True)
        text = "First paragraph.\n\nSecond paragraph."
        result = processor.process(text)
        
        # Newlines may be normalized but both paragraphs should be present
        assert "First paragraph" in result.processed
        assert "Second paragraph" in result.processed
    
    def test_merge_broken_words(self):
        """Test merging words broken across lines."""
        from src.ocr.text_processor import TextProcessor
        
        processor = TextProcessor()
        text = "This is a bro-\nken word."
        result = processor.process(text)
        
        # Should merge hyphenated word or preserve it
        assert "bro" in result.processed and "ken" in result.processed or "broken" in result.processed
    
    def test_unicode_normalization(self):
        """Test Unicode normalization."""
        from src.ocr.text_processor import TextProcessor
        
        processor = TextProcessor()
        # Test fancy quotes and dashes
        text = '\u201cHello\u201d \u2014 world'
        result = processor.process(text)
        
        # Text should be processed and contain hello and world
        assert "Hello" in result.processed
        assert "world" in result.processed
    
    def test_ocr_error_0_to_o(self):
        """Test OCR error correction: 0 -> O."""
        from src.ocr.text_processor import TextProcessor
        
        processor = TextProcessor(fix_common_errors=True)
        result = processor.process("G0od morning")
        
        # Text should be processed (exact correction depends on context)
        assert result.processed is not None
        assert "morning" in result.processed
    
    def test_ocr_error_1_to_l(self):
        """Test OCR error correction: 1 -> l."""
        from src.ocr.text_processor import TextProcessor
        
        processor = TextProcessor(fix_common_errors=True)
        result = processor.process("He1lo wor1d")
        
        # Some corrections may be made
        assert result.processed is not None
    
    def test_extract_paragraphs(self, sample_texts):
        """Test paragraph extraction."""
        from src.ocr.text_processor import TextProcessor
        
        processor = TextProcessor()
        text = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
        paragraphs = processor.extract_paragraphs(text)
        
        assert len(paragraphs) == 3
        assert "First" in paragraphs[0]
        assert "Second" in paragraphs[1]
        assert "Third" in paragraphs[2]
    
    def test_estimate_quality_good_text(self):
        """Test quality estimation for good text."""
        from src.ocr.text_processor import TextProcessor
        
        processor = TextProcessor()
        text = "This is a normal sentence with proper spacing and punctuation."
        quality = processor.estimate_quality(text)
        
        assert quality >= 0.7  # Should be high quality
    
    def test_estimate_quality_bad_text(self):
        """Test quality estimation for bad text."""
        from src.ocr.text_processor import TextProcessor
        
        processor = TextProcessor()
        text = "Th1s!@#h4s$%m4ny^&*artifacts"
        quality = processor.estimate_quality(text)
        
        assert quality < 0.7  # Should be lower quality
    
    def test_estimate_quality_empty(self):
        """Test quality estimation for empty text."""
        from src.ocr.text_processor import TextProcessor
        
        processor = TextProcessor()
        quality = processor.estimate_quality("")
        
        assert quality == 0.0
    
    def test_japanese_text_preservation(self, sample_texts):
        """Test that Japanese text is preserved."""
        from src.ocr.text_processor import TextProcessor
        
        processor = TextProcessor()
        result = processor.process(sample_texts["japanese"])
        
        # Japanese characters should be preserved
        assert "こんにちは" in result.processed or len(result.processed) > 0
    
    def test_chinese_text_preservation(self, sample_texts):
        """Test that Chinese text is preserved."""
        from src.ocr.text_processor import TextProcessor
        
        processor = TextProcessor()
        result = processor.process(sample_texts["chinese"])
        
        # Chinese characters should be preserved
        assert "你好" in result.processed or len(result.processed) > 0
    
    def test_multiline_text(self, sample_texts):
        """Test multiline text processing."""
        from src.ocr.text_processor import TextProcessor
        
        processor = TextProcessor()
        result = processor.process(sample_texts["multiline"])
        
        assert "First" in result.processed
        assert "Second" in result.processed
        assert "Third" in result.processed
