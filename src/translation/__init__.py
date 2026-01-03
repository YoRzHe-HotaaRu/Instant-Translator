"""Translation module - LLM-powered translation."""

from .llm_client import LLMClient, TranslationResult
from .prompt_builder import PromptBuilder
from .language_detector import LanguageDetector, DetectionResult

__all__ = [
    "LLMClient",
    "TranslationResult",
    "PromptBuilder",
    "LanguageDetector",
    "DetectionResult"
]
