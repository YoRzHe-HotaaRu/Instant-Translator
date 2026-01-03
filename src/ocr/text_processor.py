"""
Text Processor

Cleans and normalizes text extracted from OCR for optimal translation quality.
"""

import re
import unicodedata
from dataclasses import dataclass
from typing import List, Optional, Tuple


@dataclass
class ProcessedText:
    """Result of text processing."""
    original: str
    processed: str
    removed_artifacts: List[str]
    corrections_made: int
    
    @property
    def was_modified(self) -> bool:
        """Check if the text was modified during processing."""
        return self.original != self.processed


class TextProcessor:
    """
    Text processor for cleaning OCR output.
    
    Performs various text cleaning operations:
    - Remove OCR artifacts (random symbols, broken characters)
    - Fix common OCR misrecognitions
    - Normalize whitespace and line breaks
    - Merge broken words across lines
    - Preserve intentional formatting
    
    Usage:
        processor = TextProcessor()
        result = processor.process("Raw OCR text...")
        print(result.processed)
    """
    
    # Common OCR substitution errors
    OCR_CORRECTIONS = {
        # Number/letter confusion
        "0": {"O", "o", "Q"},
        "1": {"l", "I", "|", "!"},
        "5": {"S", "s"},
        "8": {"B"},
        
        # Common misreads
        "rn": {"m"},
        "cl": {"d"},
        "vv": {"w"},
        "li": {"h"},
    }
    
    # Characters that are typically OCR artifacts
    ARTIFACT_PATTERNS = [
        r'[\x00-\x08\x0b\x0c\x0e-\x1f]',  # Control characters
        r'[¬¦§¨©ª«®¯°±²³´µ¶·¸¹º»¼½¾¿]',  # Common OCR noise
        r'[\uf000-\uffff]',  # Private use area characters
    ]
    
    def __init__(
        self,
        fix_common_errors: bool = True,
        normalize_whitespace: bool = True,
        merge_broken_words: bool = True,
        remove_artifacts: bool = True,
        preserve_newlines: bool = True
    ):
        """
        Initialize the text processor.
        
        Args:
            fix_common_errors: Fix common OCR character substitutions.
            normalize_whitespace: Normalize spaces and tabs.
            merge_broken_words: Merge words broken across lines.
            remove_artifacts: Remove OCR artifact characters.
            preserve_newlines: Keep intentional paragraph breaks.
        """
        self.fix_common_errors = fix_common_errors
        self.normalize_whitespace = normalize_whitespace
        self.merge_broken_words = merge_broken_words
        self.remove_artifacts = remove_artifacts
        self.preserve_newlines = preserve_newlines
        
        # Compile artifact patterns
        self._artifact_regex = re.compile(
            '|'.join(self.ARTIFACT_PATTERNS)
        )
    
    def process(self, text: str) -> ProcessedText:
        """
        Process and clean OCR text.
        
        Args:
            text: The raw OCR text.
            
        Returns:
            ProcessedText with cleaned text and processing details.
        """
        if not text:
            return ProcessedText(
                original="",
                processed="",
                removed_artifacts=[],
                corrections_made=0
            )
        
        original = text
        removed_artifacts = []
        corrections_made = 0
        
        # Step 1: Remove artifacts
        if self.remove_artifacts:
            text, artifacts = self._remove_artifacts(text)
            removed_artifacts.extend(artifacts)
        
        # Step 2: Normalize Unicode
        text = self._normalize_unicode(text)
        
        # Step 3: Fix common OCR errors
        if self.fix_common_errors:
            text, count = self._fix_ocr_errors(text)
            corrections_made += count
        
        # Step 4: Handle line breaks
        if self.merge_broken_words:
            text = self._merge_broken_words(text)
        
        # Step 5: Normalize whitespace
        if self.normalize_whitespace:
            text = self._normalize_whitespace(text, self.preserve_newlines)
        
        # Step 6: Final cleanup
        text = text.strip()
        
        return ProcessedText(
            original=original,
            processed=text,
            removed_artifacts=removed_artifacts,
            corrections_made=corrections_made
        )
    
    def _remove_artifacts(self, text: str) -> Tuple[str, List[str]]:
        """Remove OCR artifact characters."""
        removed = []
        
        # Find all artifacts
        for match in self._artifact_regex.finditer(text):
            removed.append(match.group())
        
        # Remove them
        cleaned = self._artifact_regex.sub('', text)
        
        # Also remove isolated single special characters
        # that are likely artifacts
        cleaned = re.sub(r'(?<!\w)[^\w\s,.:;!?\'\"()\[\]{}<>@#$%&*+-=/\\](?!\w)', '', cleaned)
        
        return cleaned, removed
    
    def _normalize_unicode(self, text: str) -> str:
        """Normalize Unicode characters to their canonical forms."""
        # Normalize to NFC form (composed characters)
        text = unicodedata.normalize('NFC', text)
        
        # Replace common Unicode variants with ASCII equivalents
        replacements = {
            '\u2018': "'",  # Left single quote
            '\u2019': "'",  # Right single quote
            '\u201c': '"',  # Left double quote
            '\u201d': '"',  # Right double quote
            '\u2014': '-',  # Em dash
            '\u2013': '-',  # En dash
            '\u2026': '...',  # Ellipsis
            '\u00a0': ' ',  # Non-breaking space
            '\ufeff': '',  # BOM
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        return text
    
    def _fix_ocr_errors(self, text: str) -> Tuple[str, int]:
        """Fix common OCR character substitution errors."""
        corrections = 0
        
        # Context-aware corrections
        words = text.split()
        corrected_words = []
        
        for word in words:
            original_word = word
            
            # Fix common patterns
            # "rn" that should be "m"
            if 'rn' in word.lower():
                # Check if this looks like it should be 'm'
                word = self._try_correct_rn(word)
            
            # "0" that should be "O" in words
            if '0' in word and re.search(r'[a-zA-Z]', word):
                word = re.sub(r'(?<=[a-zA-Z])0(?=[a-zA-Z])', 'O', word)
            
            # "1" that should be "l" or "I"
            if '1' in word and re.search(r'[a-zA-Z]', word):
                # Beginning of word likely "I"
                word = re.sub(r'^1(?=[a-z])', 'I', word)
                # Middle of word likely "l"
                word = re.sub(r'(?<=[a-zA-Z])1(?=[a-zA-Z])', 'l', word)
            
            if word != original_word:
                corrections += 1
            
            corrected_words.append(word)
        
        return ' '.join(corrected_words), corrections
    
    def _try_correct_rn(self, word: str) -> str:
        """Try to correct 'rn' to 'm' based on context."""
        # Common words where 'rn' should be 'm'
        rn_to_m_patterns = [
            (r'\brn(?=ake|any|ore|ost|uch|y\b)', 'm'),
            (r'(?<=co)rn(?=puter|pany|mon)', 'm'),
            (r'(?<=su)rn(?=mit|mer|mary)', 'm'),
        ]
        
        result = word
        for pattern, replacement in rn_to_m_patterns:
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        
        return result
    
    def _merge_broken_words(self, text: str) -> str:
        """Merge words that were broken across lines."""
        # Pattern: word ending with hyphen followed by newline and continuation
        text = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', text)
        
        # Pattern: word split across lines (no hyphen)
        # Only merge if the parts form a likely word
        lines = text.split('\n')
        merged_lines = []
        
        i = 0
        while i < len(lines):
            line = lines[i].rstrip()
            
            # Check if line ends with an incomplete word
            if i < len(lines) - 1 and line and not line[-1] in '.!?:;,':
                next_line = lines[i + 1].lstrip()
                
                # Check if next line starts with lowercase (continuation)
                if next_line and next_line[0].islower():
                    # Likely a continuation
                    merged_lines.append(line + ' ' + next_line)
                    i += 2
                    continue
            
            merged_lines.append(line)
            i += 1
        
        return '\n'.join(merged_lines)
    
    def _normalize_whitespace(self, text: str, preserve_newlines: bool) -> str:
        """Normalize whitespace in text."""
        if preserve_newlines:
            # Normalize spaces within lines but preserve paragraph breaks
            lines = text.split('\n')
            normalized_lines = []
            
            for line in lines:
                # Normalize multiple spaces to single space
                line = re.sub(r'[ \t]+', ' ', line)
                # Remove leading/trailing whitespace
                line = line.strip()
                normalized_lines.append(line)
            
            # Collapse multiple empty lines to single empty line
            text = '\n'.join(normalized_lines)
            text = re.sub(r'\n{3,}', '\n\n', text)
        else:
            # Replace all whitespace with single spaces
            text = re.sub(r'\s+', ' ', text)
        
        return text
    
    def extract_paragraphs(self, text: str) -> List[str]:
        """
        Split text into paragraphs.
        
        Args:
            text: The input text.
            
        Returns:
            List of paragraph strings.
        """
        # Split on double newlines
        paragraphs = re.split(r'\n\s*\n', text)
        
        # Clean each paragraph
        return [p.strip() for p in paragraphs if p.strip()]
    
    def estimate_quality(self, text: str) -> float:
        """
        Estimate the quality of OCR text (0.0 to 1.0).
        
        Higher scores indicate cleaner text.
        
        Args:
            text: The text to analyze.
            
        Returns:
            Quality score between 0.0 and 1.0.
        """
        if not text:
            return 0.0
        
        score = 1.0
        
        # Penalize high artifact count
        artifact_count = len(self._artifact_regex.findall(text))
        if artifact_count > 0:
            score -= min(0.3, artifact_count * 0.02)
        
        # Penalize very short or very long words
        words = text.split()
        if words:
            avg_word_length = sum(len(w) for w in words) / len(words)
            if avg_word_length < 2 or avg_word_length > 15:
                score -= 0.2
        
        # Penalize excessive special characters
        special_ratio = len(re.findall(r'[^a-zA-Z0-9\s.,!?\'"-]', text)) / max(len(text), 1)
        if special_ratio > 0.1:
            score -= min(0.3, special_ratio * 2)
        
        # Penalize lack of spaces (likely merged text)
        if len(text) > 50:
            space_ratio = text.count(' ') / len(text)
            if space_ratio < 0.05:
                score -= 0.3
        
        return max(0.0, min(1.0, score))
