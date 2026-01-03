"""Unit tests for language detector module."""

import pytest


class TestDetectionResult:
    """Tests for DetectionResult dataclass."""
    
    def test_detection_result_creation(self):
        """Test creating a DetectionResult instance."""
        from src.translation.language_detector import DetectionResult
        
        result = DetectionResult(
            language="en",
            confidence=0.99,
            alternatives=[("es", 0.05), ("fr", 0.02)]
        )
        
        assert result.language == "en"
        assert result.confidence == 0.99
        assert len(result.alternatives) == 2
    
    def test_language_name_property(self):
        """Test getting the language name."""
        from src.translation.language_detector import DetectionResult
        
        result = DetectionResult(
            language="ja",
            confidence=0.95,
            alternatives=[]
        )
        
        assert result.language_name == "Japanese"
    
    def test_language_name_unknown(self):
        """Test language name for unknown code."""
        from src.translation.language_detector import DetectionResult
        
        result = DetectionResult(
            language="xyz",
            confidence=0.5,
            alternatives=[]
        )
        
        # Unknown codes should return the code itself
        assert result.language_name == "xyz"


class TestLanguageDetector:
    """Tests for LanguageDetector class."""
    
    def test_detector_init_default(self):
        """Test default initialization."""
        from src.translation.language_detector import LanguageDetector
        
        detector = LanguageDetector()
        assert detector.fallback_language == "en"
    
    def test_detector_init_custom_fallback(self):
        """Test initialization with custom fallback."""
        from src.translation.language_detector import LanguageDetector
        
        detector = LanguageDetector(fallback_language="ja")
        assert detector.fallback_language == "ja"
    
    def test_detect_empty_string(self):
        """Test detection on empty string."""
        from src.translation.language_detector import LanguageDetector
        
        detector = LanguageDetector()
        result = detector.detect("")
        
        assert result.language == "en"  # Fallback
        assert result.confidence == 0.0
    
    def test_detect_english(self, sample_texts):
        """Test detecting English text."""
        from src.translation.language_detector import LanguageDetector
        
        detector = LanguageDetector()
        # Use longer, more distinctive English text
        text = "The quick brown fox jumps over the lazy dog. This is a sample of English text."
        result = detector.detect(text)
        
        assert result.language == "en"
        assert result.confidence > 0.5
    
    def test_detect_japanese(self, sample_texts):
        """Test detecting Japanese text."""
        from src.translation.language_detector import LanguageDetector
        
        detector = LanguageDetector()
        result = detector.detect(sample_texts["japanese"])
        
        assert result.language == "ja"
        assert result.confidence > 0.5
    
    def test_detect_chinese(self, sample_texts):
        """Test detecting Chinese text."""
        from src.translation.language_detector import LanguageDetector
        
        detector = LanguageDetector()
        result = detector.detect(sample_texts["chinese"])
        
        # Should detect as Chinese (zh or zh-cn)
        assert result.language.startswith("zh")
        assert result.confidence > 0.5
    
    def test_detect_korean(self, sample_texts):
        """Test detecting Korean text."""
        from src.translation.language_detector import LanguageDetector
        
        detector = LanguageDetector()
        result = detector.detect(sample_texts["korean"])
        
        assert result.language == "ko"
        assert result.confidence > 0.5
    
    def test_detect_mixed_text(self, sample_texts):
        """Test detecting mixed language text."""
        from src.translation.language_detector import LanguageDetector
        
        detector = LanguageDetector()
        result = detector.detect(sample_texts["mixed"])
        
        # Should detect primary language
        assert result.language in ["en", "ja", "zh", "zh-cn"]
    
    def test_detect_batch(self, sample_texts):
        """Test batch language detection."""
        from src.translation.language_detector import LanguageDetector
        
        detector = LanguageDetector()
        texts = [
            sample_texts["english"],
            sample_texts["japanese"],
            sample_texts["chinese"]
        ]
        
        results = detector.detect_batch(texts)
        
        assert len(results) == 3
        assert results[0].language == "en"
        assert results[1].language == "ja"
    
    def test_get_supported_languages(self):
        """Test getting supported languages."""
        from src.translation.language_detector import LanguageDetector
        
        detector = LanguageDetector()
        languages = detector.get_supported_languages()
        
        assert len(languages) > 0
        assert ("en", "English") in languages
        assert ("ja", "Japanese") in languages
    
    def test_get_language_name_static(self):
        """Test static language name lookup."""
        from src.translation.language_detector import LanguageDetector
        
        assert LanguageDetector.get_language_name("en") == "English"
        assert LanguageDetector.get_language_name("ja") == "Japanese"
        assert LanguageDetector.get_language_name("zh-cn") == "Chinese (Simplified)"
        assert LanguageDetector.get_language_name("unknown") == "unknown"


class TestCJKDetection:
    """Tests for CJK language detection."""
    
    def test_hiragana_detection(self):
        """Test detection of Hiragana (Japanese)."""
        from src.translation.language_detector import LanguageDetector
        
        detector = LanguageDetector()
        result = detector.detect("ひらがなテスト")
        
        assert result.language == "ja"
    
    def test_katakana_detection(self):
        """Test detection of Katakana (Japanese)."""
        from src.translation.language_detector import LanguageDetector
        
        detector = LanguageDetector()
        result = detector.detect("カタカナテスト")
        
        assert result.language == "ja"
    
    def test_hangul_detection(self):
        """Test detection of Hangul (Korean)."""
        from src.translation.language_detector import LanguageDetector
        
        detector = LanguageDetector()
        result = detector.detect("한국어 테스트")
        
        assert result.language == "ko"
    
    def test_chinese_only_characters(self):
        """Test detection of Chinese-only characters."""
        from src.translation.language_detector import LanguageDetector
        
        detector = LanguageDetector()
        result = detector.detect("中文测试")
        
        assert result.language.startswith("zh")
    
    def test_short_cjk_text(self):
        """Test CJK detection with short text."""
        from src.translation.language_detector import LanguageDetector
        
        detector = LanguageDetector()
        
        # Single characters may not be reliably detected
        result = detector.detect("あ")
        assert result.language in ["ja", "en"]  # May fall back to default
