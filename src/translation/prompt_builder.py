"""
Prompt Builder

Constructs optimal prompts for accurate LLM translation.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from .language_detector import LANGUAGE_NAMES


class TranslationStyle(Enum):
    """Translation style options."""
    LITERAL = "literal"
    NATURAL = "natural"
    FORMAL = "formal"
    CASUAL = "casual"
    TECHNICAL = "technical"


@dataclass
class PromptConfig:
    """Configuration for prompt generation."""
    style: TranslationStyle = TranslationStyle.NATURAL
    preserve_formatting: bool = True
    include_original: bool = False
    max_context_length: int = 4000


class PromptBuilder:
    """
    Builds optimized prompts for translation via LLM.
    
    Creates structured prompts that:
    - Clearly specify source and target languages
    - Define translation rules and expectations
    - Handle special cases (technical terms, formatting)
    
    Usage:
        builder = PromptBuilder()
        prompt = builder.build_translation_prompt(
            text="こんにちは",
            source_lang="ja",
            target_lang="en"
        )
    """
    
    # Base system prompt for translation
    SYSTEM_PROMPT = """You are a professional translator with expertise in multiple languages. Your translations are:
- Accurate: Preserve the exact meaning of the original text
- Natural: Sound fluent in the target language
- Context-aware: Consider cultural nuances and idioms
- Consistent: Maintain terminology throughout

Rules:
1. Translate the text faithfully without adding or omitting information
2. Preserve the original tone (formal, casual, technical, etc.)
3. Keep proper nouns and technical terms in their original form when appropriate
4. Maintain formatting like line breaks, bullet points, and numbering
5. If a phrase has multiple valid translations, choose the most natural one
6. Do not explain your translation choices - return ONLY the translated text"""

    STYLE_INSTRUCTIONS = {
        TranslationStyle.LITERAL: "Translate as literally as possible while maintaining grammatical correctness.",
        TranslationStyle.NATURAL: "Translate naturally, prioritizing fluency in the target language.",
        TranslationStyle.FORMAL: "Use formal language and polite expressions.",
        TranslationStyle.CASUAL: "Use casual, conversational language.",
        TranslationStyle.TECHNICAL: "Preserve technical terminology precisely.",
    }
    
    def __init__(self, config: Optional[PromptConfig] = None):
        """
        Initialize the prompt builder.
        
        Args:
            config: Optional prompt configuration.
        """
        self.config = config or PromptConfig()
    
    def get_system_prompt(self) -> str:
        """
        Get the system prompt for translation.
        
        Returns:
            The system prompt string.
        """
        return self.SYSTEM_PROMPT
    
    def build_translation_prompt(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        style: Optional[TranslationStyle] = None,
        context: Optional[str] = None
    ) -> str:
        """
        Build a translation prompt.
        
        Args:
            text: The text to translate.
            source_lang: Source language code (e.g., 'ja').
            target_lang: Target language code (e.g., 'en').
            style: Optional translation style override.
            context: Optional context about the text.
            
        Returns:
            The formatted prompt string.
        """
        style = style or self.config.style
        
        # Get language names
        source_name = LANGUAGE_NAMES.get(source_lang, source_lang)
        target_name = LANGUAGE_NAMES.get(target_lang, target_lang)
        
        # Build the prompt
        parts = []
        
        # Language specification
        parts.append(f"Translate the following text from {source_name} to {target_name}.")
        
        # Style instruction
        style_instruction = self.STYLE_INSTRUCTIONS.get(style, "")
        if style_instruction:
            parts.append(style_instruction)
        
        # Formatting instruction
        if self.config.preserve_formatting:
            parts.append("Preserve all formatting including line breaks, bullet points, and numbering.")
        
        # Context if provided
        if context:
            parts.append(f"Context: {context}")
        
        # The text to translate
        parts.append("")
        parts.append("Text to translate:")
        parts.append("---")
        parts.append(text)
        parts.append("---")
        
        # Final instruction
        parts.append("")
        parts.append("Provide ONLY the translation, no explanations or notes.")
        
        return "\n".join(parts)
    
    def build_batch_translation_prompt(
        self,
        texts: list,
        source_lang: str,
        target_lang: str
    ) -> str:
        """
        Build a prompt for batch translation.
        
        Args:
            texts: List of texts to translate.
            source_lang: Source language code.
            target_lang: Target language code.
            
        Returns:
            The formatted prompt string.
        """
        source_name = LANGUAGE_NAMES.get(source_lang, source_lang)
        target_name = LANGUAGE_NAMES.get(target_lang, target_lang)
        
        parts = [
            f"Translate the following {len(texts)} texts from {source_name} to {target_name}.",
            "Return the translations in the same order, separated by '---'.",
            "",
            "Texts to translate:"
        ]
        
        for i, text in enumerate(texts, 1):
            parts.append(f"[{i}] {text}")
        
        parts.append("")
        parts.append("Translations:")
        
        return "\n".join(parts)
    
    def build_detection_prompt(self, text: str) -> str:
        """
        Build a prompt for language detection.
        
        Args:
            text: The text to analyze.
            
        Returns:
            The formatted prompt string.
        """
        return f"""Identify the language of the following text. 
Respond with ONLY the ISO 639-1 language code (e.g., 'en', 'ja', 'zh', 'ko').

Text:
{text}

Language code:"""
    
    def build_quality_check_prompt(
        self,
        original: str,
        translation: str,
        source_lang: str,
        target_lang: str
    ) -> str:
        """
        Build a prompt for translation quality checking.
        
        Args:
            original: The original text.
            translation: The translated text.
            source_lang: Source language code.
            target_lang: Target language code.
            
        Returns:
            The formatted prompt string.
        """
        source_name = LANGUAGE_NAMES.get(source_lang, source_lang)
        target_name = LANGUAGE_NAMES.get(target_lang, target_lang)
        
        return f"""Evaluate this translation from {source_name} to {target_name}.

Original ({source_name}):
{original}

Translation ({target_name}):
{translation}

Rate the translation accuracy from 1-10 and identify any issues.
Format your response as:
Score: X/10
Issues: [list any issues or "None"]
Suggested improvements: [improvements or "None"]"""
    
    def truncate_text(self, text: str, max_length: Optional[int] = None) -> str:
        """
        Truncate text to fit within token limits.
        
        Args:
            text: The text to truncate.
            max_length: Maximum character length.
            
        Returns:
            The truncated text.
        """
        max_length = max_length or self.config.max_context_length
        
        if len(text) <= max_length:
            return text
        
        # Truncate at word boundary
        truncated = text[:max_length]
        last_space = truncated.rfind(' ')
        
        if last_space > max_length * 0.8:
            truncated = truncated[:last_space]
        
        return truncated + "..."
