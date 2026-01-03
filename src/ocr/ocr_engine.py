"""
OCR Engine

Dual-engine OCR system combining Tesseract and EasyOCR for maximum accuracy.
"""

import logging
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from PIL import Image

from .image_preprocessor import ImagePreprocessor, PreprocessingConfig
from .text_processor import TextProcessor

# OCR engine availability
try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False


logger = logging.getLogger(__name__)


@dataclass
class TextBlock:
    """A block of text with position information."""
    text: str
    x: int
    y: int
    width: int
    height: int
    confidence: float
    
    @property
    def bbox(self) -> Tuple[int, int, int, int]:
        """Get bounding box as (x, y, x2, y2)."""
        return (self.x, self.y, self.x + self.width, self.y + self.height)


@dataclass
class OCRResult:
    """Result of OCR text extraction."""
    text: str
    confidence: float
    blocks: List[TextBlock] = field(default_factory=list)
    engine_used: str = "unknown"
    languages_detected: List[str] = field(default_factory=list)
    preprocessing_applied: bool = False
    
    @property
    def is_empty(self) -> bool:
        """Check if no text was extracted."""
        return not self.text or not self.text.strip()
    
    @property
    def is_high_confidence(self) -> bool:
        """Check if the result has high confidence (> 80%)."""
        return self.confidence >= 0.8


class OCREngineError(Exception):
    """Exception raised when OCR processing fails."""
    pass


class OCREngine:
    """
    Dual-engine OCR system for maximum accuracy.
    
    Combines Tesseract and EasyOCR to extract text from images:
    - Tesseract: Best for clean, typed text with standard fonts
    - EasyOCR: Superior for complex backgrounds and stylized text
    
    The engine uses confidence scoring to select the best result
    when both engines are available.
    
    Usage:
        engine = OCREngine(languages=['en', 'ja'])
        result = engine.extract_text(image)
        print(result.text)
        print(f"Confidence: {result.confidence:.1%}")
    """
    
    def __init__(
        self,
        languages: Optional[List[str]] = None,
        use_tesseract: bool = True,
        use_easyocr: bool = True,
        tesseract_cmd: Optional[str] = None,
        preprocess: bool = True,
        preprocessing_config: Optional[PreprocessingConfig] = None
    ):
        """
        Initialize the OCR engine.
        
        Args:
            languages: List of language codes to recognize (e.g., ['en', 'ja']).
            use_tesseract: Whether to use Tesseract OCR.
            use_easyocr: Whether to use EasyOCR.
            tesseract_cmd: Path to Tesseract executable.
            preprocess: Whether to preprocess images before OCR.
            preprocessing_config: Custom preprocessing configuration.
        """
        self.languages = languages or ['en']
        self.use_tesseract = use_tesseract and TESSERACT_AVAILABLE
        self.use_easyocr = use_easyocr and EASYOCR_AVAILABLE
        self.preprocess = preprocess
        
        # Validate at least one engine is available
        if not self.use_tesseract and not self.use_easyocr:
            raise OCREngineError(
                "No OCR engine available. Install pytesseract or easyocr."
            )
        
        # Configure Tesseract
        if self.use_tesseract and tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        
        # Initialize EasyOCR reader (lazy)
        self._easyocr_reader: Optional[easyocr.Reader] = None
        
        # Initialize preprocessor
        self._preprocessor = ImagePreprocessor(preprocessing_config)
        
        # Initialize text processor
        self._text_processor = TextProcessor()
        
        # EasyOCR readers for different language groups (lazy initialized)
        self._easyocr_readers: dict = {}
    
    def _get_easyocr_reader(self, lang_group: str = "default") -> "easyocr.Reader":
        """Get or create EasyOCR reader for a language group (lazy initialization)."""
        if lang_group not in self._easyocr_readers:
            # Determine which languages to use based on group
            if lang_group == "chinese":
                langs = ['ch_sim', 'en']
            elif lang_group == "korean":
                langs = ['ko', 'en']
            elif lang_group == "japanese":
                langs = ['ja', 'en']
            else:
                # Default - English only
                langs = ['en']
            
            self._easyocr_readers[lang_group] = easyocr.Reader(langs, gpu=False)
        
        return self._easyocr_readers[lang_group]
    
    def _get_language_groups(self) -> List[str]:
        """Get the language groups to try based on configured languages."""
        groups = []
        mapped = self._map_languages_to_easyocr(self.languages)
        
        # Check which groups are needed
        if 'ch_sim' in mapped or 'ch_tra' in mapped:
            groups.append("chinese")
        if 'ko' in mapped:
            groups.append("korean")
        if 'ja' in mapped:
            groups.append("japanese")
        if 'en' in mapped and not groups:
            groups.append("default")
        
        # If no specific groups, use default
        if not groups:
            groups.append("default")
        
        return groups
    
    def _map_languages_to_easyocr(self, languages: List[str]) -> List[str]:
        """Map language codes to EasyOCR format."""
        # EasyOCR uses different codes for some languages
        mapping = {
            'chi_sim': 'ch_sim',
            'chi_tra': 'ch_tra',
            'zh': 'ch_sim',       # Chinese simplified
            'zh-cn': 'ch_sim',    # Chinese simplified
            'zh-tw': 'ch_tra',    # Chinese traditional
            'jpn': 'ja',
            'kor': 'ko',
        }
        
        result = []
        for lang in languages:
            mapped = mapping.get(lang.lower(), lang)
            # Only add if not already present
            if mapped not in result:
                result.append(mapped)
        
        return result
    
    def _map_languages_to_tesseract(self, languages: List[str]) -> str:
        """Map language codes to Tesseract format."""
        # Tesseract uses different codes
        mapping = {
            'ch_sim': 'chi_sim',
            'ch_tra': 'chi_tra',
            'ja': 'jpn',
            'ko': 'kor',
        }
        
        tesseract_langs = []
        for lang in languages:
            mapped = mapping.get(lang, lang)
            tesseract_langs.append(mapped)
        
        return '+'.join(tesseract_langs)
    
    def extract_text(self, image: Image.Image) -> OCRResult:
        """
        Extract text from an image using dual-engine OCR.
        
        Args:
            image: The input PIL Image.
            
        Returns:
            OCRResult containing extracted text and metadata.
        """
        # Preprocess image if enabled
        processed_image = image
        preprocessing_applied = False
        
        if self.preprocess:
            processed_image = self._preprocessor.process(image)
            preprocessing_applied = True
        
        results = []
        
        # Try Tesseract
        if self.use_tesseract:
            try:
                tesseract_result = self._extract_with_tesseract(processed_image)
                results.append(tesseract_result)
                logger.debug(f"Tesseract result: confidence={tesseract_result.confidence:.2f}")
            except Exception as e:
                logger.warning(f"Tesseract extraction failed: {e}")
        
        # Try EasyOCR
        if self.use_easyocr:
            try:
                easyocr_result = self._extract_with_easyocr(processed_image)
                results.append(easyocr_result)
                logger.debug(f"EasyOCR result: confidence={easyocr_result.confidence:.2f}")
            except Exception as e:
                logger.warning(f"EasyOCR extraction failed: {e}")
        
        if not results:
            raise OCREngineError("All OCR engines failed to extract text")
        
        # Select the best result
        best_result = self._select_best_result(results)
        best_result.preprocessing_applied = preprocessing_applied
        
        # Post-process the text
        processed = self._text_processor.process(best_result.text)
        best_result.text = processed.processed
        
        return best_result
    
    def _extract_with_tesseract(self, image: Image.Image) -> OCRResult:
        """Extract text using Tesseract."""
        if not TESSERACT_AVAILABLE:
            raise OCREngineError("Tesseract is not available")
        
        lang_string = self._map_languages_to_tesseract(self.languages)
        
        # Get detailed data including confidence
        data = pytesseract.image_to_data(
            image, 
            lang=lang_string,
            output_type=pytesseract.Output.DICT
        )
        
        # Extract text blocks with confidence
        blocks = []
        confidences = []
        
        for i in range(len(data['text'])):
            text = data['text'][i].strip()
            conf = int(data['conf'][i])
            
            if text and conf > 0:
                block = TextBlock(
                    text=text,
                    x=data['left'][i],
                    y=data['top'][i],
                    width=data['width'][i],
                    height=data['height'][i],
                    confidence=conf / 100.0
                )
                blocks.append(block)
                confidences.append(conf)
        
        # Combine all text
        full_text = pytesseract.image_to_string(image, lang=lang_string)
        
        # Calculate average confidence
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        return OCRResult(
            text=full_text.strip(),
            confidence=avg_confidence / 100.0,
            blocks=blocks,
            engine_used="tesseract",
            languages_detected=self.languages
        )
    
    def _extract_with_easyocr(self, image: Image.Image) -> OCRResult:
        """Extract text using EasyOCR."""
        if not EASYOCR_AVAILABLE:
            raise OCREngineError("EasyOCR is not available")
        
        import numpy as np
        
        # Convert PIL Image to numpy array
        image_array = np.array(image)
        
        # Try each language group and pick the best result
        all_results = []
        lang_groups = self._get_language_groups()
        
        for lang_group in lang_groups:
            try:
                reader = self._get_easyocr_reader(lang_group)
                results = reader.readtext(image_array)
                
                # Extract text blocks
                blocks = []
                texts = []
                confidences = []
                
                for bbox, text, confidence in results:
                    if text.strip():
                        x1, y1 = bbox[0]
                        x2, y2 = bbox[2]
                        
                        block = TextBlock(
                            text=text,
                            x=int(x1),
                            y=int(y1),
                            width=int(x2 - x1),
                            height=int(y2 - y1),
                            confidence=confidence
                        )
                        blocks.append(block)
                        texts.append(text)
                        confidences.append(confidence)
                
                full_text = ' '.join(texts)
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
                
                if full_text.strip():
                    all_results.append(OCRResult(
                        text=full_text,
                        confidence=avg_confidence,
                        blocks=blocks,
                        engine_used=f"easyocr-{lang_group}",
                        languages_detected=[lang_group]
                    ))
            except Exception as e:
                logger.debug(f"EasyOCR {lang_group} failed: {e}")
                continue
        
        if not all_results:
            raise OCREngineError("EasyOCR failed to extract text with any language group")
        
        # Return the result with highest confidence
        best_result = max(all_results, key=lambda r: r.confidence)
        return best_result
    
    def _select_best_result(self, results: List[OCRResult]) -> OCRResult:
        """
        Select the best OCR result from multiple engines.
        
        Uses a combination of confidence score and text quality metrics.
        """
        if len(results) == 1:
            return results[0]
        
        # Score each result
        scored_results = []
        
        for result in results:
            score = result.confidence
            
            # Bonus for longer text (likely more complete)
            text_length = len(result.text.strip())
            if text_length > 0:
                score += min(0.1, text_length / 1000)
            
            # Bonus for more text blocks (structured extraction)
            if result.blocks:
                score += min(0.05, len(result.blocks) / 100)
            
            # Penalty for empty or very short text
            if text_length < 10:
                score -= 0.3
            
            scored_results.append((score, result))
        
        # Sort by score (descending)
        scored_results.sort(key=lambda x: x[0], reverse=True)
        
        return scored_results[0][1]
    
    def extract_with_positions(self, image: Image.Image) -> List[TextBlock]:
        """
        Extract text blocks with position information.
        
        Args:
            image: The input PIL Image.
            
        Returns:
            List of TextBlock objects with positions.
        """
        result = self.extract_text(image)
        return result.blocks
    
    def get_available_engines(self) -> List[str]:
        """Get list of available OCR engines."""
        engines = []
        if TESSERACT_AVAILABLE:
            engines.append("tesseract")
        if EASYOCR_AVAILABLE:
            engines.append("easyocr")
        return engines
    
    @staticmethod
    def check_tesseract_installation() -> bool:
        """Check if Tesseract is properly installed."""
        if not TESSERACT_AVAILABLE:
            return False
        
        try:
            pytesseract.get_tesseract_version()
            return True
        except Exception:
            return False
