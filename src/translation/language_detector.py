"""
Language Detector

Detects the source language of text for automatic translation.
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple

# Language detection
try:
    from langdetect import detect, detect_langs, LangDetectException
    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False


@dataclass
class DetectionResult:
    """Result of language detection."""
    language: str
    confidence: float
    alternatives: List[Tuple[str, float]]
    
    @property
    def language_name(self) -> str:
        """Get human-readable language name."""
        return LANGUAGE_NAMES.get(self.language, self.language)


# Language code to name mapping
LANGUAGE_NAMES = {
    'en': 'English',
    'ja': 'Japanese',
    'zh-cn': 'Chinese (Simplified)',
    'zh-tw': 'Chinese (Traditional)',
    'ko': 'Korean',
    'es': 'Spanish',
    'fr': 'French',
    'de': 'German',
    'it': 'Italian',
    'pt': 'Portuguese',
    'ru': 'Russian',
    'ar': 'Arabic',
    'hi': 'Hindi',
    'th': 'Thai',
    'vi': 'Vietnamese',
    'id': 'Indonesian',
    'ms': 'Malay',
    'tl': 'Tagalog',
    'nl': 'Dutch',
    'pl': 'Polish',
    'tr': 'Turkish',
    'uk': 'Ukrainian',
    'cs': 'Czech',
    'sv': 'Swedish',
    'da': 'Danish',
    'fi': 'Finnish',
    'no': 'Norwegian',
    'el': 'Greek',
    'he': 'Hebrew',
    'hu': 'Hungarian',
    'ro': 'Romanian',
    'sk': 'Slovak',
    'bg': 'Bulgarian',
    'hr': 'Croatian',
    'lt': 'Lithuanian',
    'lv': 'Latvian',
    'et': 'Estonian',
    'sl': 'Slovenian',
    'sr': 'Serbian',
    'bn': 'Bengali',
    'ta': 'Tamil',
    'te': 'Telugu',
    'mr': 'Marathi',
    'gu': 'Gujarati',
    'kn': 'Kannada',
    'ml': 'Malayalam',
    'pa': 'Punjabi',
    'ur': 'Urdu',
    'fa': 'Persian',
    'sw': 'Swahili',
    'af': 'Afrikaans',
}


class LanguageDetector:
    """
    Language detector for automatic source language detection.
    
    Uses langdetect library with fallback to character-set analysis
    for CJK (Chinese, Japanese, Korean) languages.
    
    Usage:
        detector = LanguageDetector()
        result = detector.detect("こんにちは世界")
        print(result.language)  # 'ja'
        print(result.confidence)  # 0.99
    """
    
    # Character ranges for CJK detection
    CJK_RANGES = {
        'ja': [
            (0x3040, 0x309F),  # Hiragana
            (0x30A0, 0x30FF),  # Katakana
        ],
        'zh': [
            (0x4E00, 0x9FFF),  # CJK Unified Ideographs
            (0x3400, 0x4DBF),  # CJK Extension A
        ],
        'ko': [
            (0xAC00, 0xD7AF),  # Hangul Syllables
            (0x1100, 0x11FF),  # Hangul Jamo
        ],
    }
    
    def __init__(self, fallback_language: str = 'en'):
        """
        Initialize the language detector.
        
        Args:
            fallback_language: Language to return if detection fails.
        """
        self.fallback_language = fallback_language
        
        if not LANGDETECT_AVAILABLE:
            import warnings
            warnings.warn(
                "langdetect not available. Using character-based detection only."
            )
    
    def detect(self, text: str) -> DetectionResult:
        """
        Detect the language of the given text.
        
        Args:
            text: The text to analyze.
            
        Returns:
            DetectionResult with detected language and confidence.
        """
        if not text or not text.strip():
            return DetectionResult(
                language=self.fallback_language,
                confidence=0.0,
                alternatives=[]
            )
        
        # First, try CJK character detection (more reliable for these)
        cjk_result = self._detect_cjk(text)
        if cjk_result and cjk_result.confidence > 0.5:
            return cjk_result
        
        # Use langdetect for general detection
        if LANGDETECT_AVAILABLE:
            try:
                return self._detect_with_langdetect(text)
            except LangDetectException:
                pass
        
        # Fall back to CJK result or default
        if cjk_result:
            return cjk_result
        
        return DetectionResult(
            language=self.fallback_language,
            confidence=0.5,
            alternatives=[]
        )
    
    def _detect_with_langdetect(self, text: str) -> DetectionResult:
        """Detect language using langdetect library."""
        # Get probabilities for all detected languages
        probs = detect_langs(text)
        
        if not probs:
            raise LangDetectException("No language detected")
        
        # Get the best result
        best = probs[0]
        
        # Get alternatives
        alternatives = [
            (str(p.lang), p.prob)
            for p in probs[1:5]  # Top 4 alternatives
        ]
        
        return DetectionResult(
            language=str(best.lang),
            confidence=best.prob,
            alternatives=alternatives
        )
    
    def _detect_cjk(self, text: str) -> Optional[DetectionResult]:
        """
        Detect CJK languages using character analysis.
        
        This is more reliable than langdetect for short CJK texts.
        """
        counts = {'ja': 0, 'zh': 0, 'ko': 0}
        total_cjk = 0
        
        for char in text:
            code = ord(char)
            
            for lang, ranges in self.CJK_RANGES.items():
                for start, end in ranges:
                    if start <= code <= end:
                        counts[lang] += 1
                        total_cjk += 1
                        break
        
        if total_cjk == 0:
            return None
        
        # Calculate ratios
        total_chars = len([c for c in text if not c.isspace()])
        if total_chars == 0:
            return None
        
        cjk_ratio = total_cjk / total_chars
        
        if cjk_ratio < 0.1:
            return None
        
        # Determine the most likely CJK language
        max_lang = max(counts, key=counts.get)
        max_count = counts[max_lang]
        
        # Japanese detection: presence of hiragana/katakana
        if counts['ja'] > 0:
            # Has Japanese-specific characters
            confidence = min(0.95, (counts['ja'] / total_cjk) + 0.3)
            return DetectionResult(
                language='ja',
                confidence=confidence,
                alternatives=[('zh', 0.1), ('ko', 0.05)]
            )
        
        # Korean detection: presence of Hangul
        if counts['ko'] > 0:
            confidence = min(0.95, (counts['ko'] / total_cjk) + 0.3)
            return DetectionResult(
                language='ko',
                confidence=confidence,
                alternatives=[('zh', 0.1), ('ja', 0.05)]
            )
        
        # Chinese by default if only CJK ideographs
        if counts['zh'] > 0:
            # Simplified vs Traditional detection could be added here
            confidence = min(0.90, cjk_ratio + 0.2)
            return DetectionResult(
                language='zh-cn',
                confidence=confidence,
                alternatives=[('zh-tw', 0.4), ('ja', 0.1)]
            )
        
        return None
    
    def detect_batch(self, texts: List[str]) -> List[DetectionResult]:
        """
        Detect languages for multiple texts.
        
        Args:
            texts: List of texts to analyze.
            
        Returns:
            List of DetectionResult objects.
        """
        return [self.detect(text) for text in texts]
    
    def get_supported_languages(self) -> List[Tuple[str, str]]:
        """
        Get list of supported language codes and names.
        
        Returns:
            List of (code, name) tuples.
        """
        return list(LANGUAGE_NAMES.items())
    
    @staticmethod
    def get_language_name(code: str) -> str:
        """
        Get the human-readable name for a language code.
        
        Args:
            code: The language code (e.g., 'en', 'ja').
            
        Returns:
            The language name (e.g., 'English', 'Japanese').
        """
        return LANGUAGE_NAMES.get(code, code)
