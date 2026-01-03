"""
Configuration management for Instant Translator.

Handles loading environment variables and application settings.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()


@dataclass
class APIConfig:
    """Configuration for ZenMux API."""
    api_key: str
    base_url: str
    model: str
    timeout: int = 30
    max_retries: int = 3
    
    @classmethod
    def from_env(cls) -> "APIConfig":
        """Load API configuration from environment variables."""
        api_key = os.getenv("ZENMUX_API_KEY", "")
        if not api_key:
            raise ValueError("ZENMUX_API_KEY environment variable is required")
        
        return cls(
            api_key=api_key,
            base_url=os.getenv("ZENMUX_BASE_URL", "https://zenmux.ai/api/v1"),
            model=os.getenv("ZENMUX_MODEL", "deepseek/deepseek-v3.2"),
            timeout=int(os.getenv("API_TIMEOUT", "30")),
            max_retries=int(os.getenv("API_MAX_RETRIES", "3"))
        )


@dataclass
class OCRConfig:
    """Configuration for OCR engines."""
    tesseract_cmd: Optional[str]
    languages: List[str]
    use_easyocr: bool
    use_tesseract: bool
    confidence_threshold: float
    
    @classmethod
    def from_env(cls) -> "OCRConfig":
        """Load OCR configuration from environment variables."""
        languages_str = os.getenv("OCR_LANGUAGES", "en,ja,zh,ko")
        languages = [lang.strip() for lang in languages_str.split(",")]
        
        return cls(
            tesseract_cmd=os.getenv("TESSERACT_CMD"),
            languages=languages,
            use_easyocr=os.getenv("USE_EASYOCR", "true").lower() == "true",
            use_tesseract=os.getenv("USE_TESSERACT", "true").lower() == "true",
            confidence_threshold=float(os.getenv("OCR_CONFIDENCE_THRESHOLD", "0.5"))
        )


@dataclass
class AppConfig:
    """Main application configuration."""
    debug: bool
    default_target_language: str
    window_width: int
    window_height: int
    
    @classmethod
    def from_env(cls) -> "AppConfig":
        """Load application configuration from environment variables."""
        return cls(
            debug=os.getenv("DEBUG", "false").lower() == "true",
            default_target_language=os.getenv("DEFAULT_TARGET_LANGUAGE", "en"),
            window_width=int(os.getenv("WINDOW_WIDTH", "1200")),
            window_height=int(os.getenv("WINDOW_HEIGHT", "800"))
        )


class Config:
    """
    Central configuration class that aggregates all configuration sections.
    
    Usage:
        config = Config.load()
        print(config.api.base_url)
        print(config.ocr.languages)
    """
    
    def __init__(self, api: APIConfig, ocr: OCRConfig, app: AppConfig):
        self.api = api
        self.ocr = ocr
        self.app = app
    
    @classmethod
    def load(cls) -> "Config":
        """Load all configuration from environment."""
        return cls(
            api=APIConfig.from_env(),
            ocr=OCRConfig.from_env(),
            app=AppConfig.from_env()
        )
    
    @classmethod
    def load_safe(cls) -> Optional["Config"]:
        """
        Load configuration safely, returning None if required values are missing.
        
        Useful for testing or validation scenarios.
        """
        try:
            return cls.load()
        except ValueError:
            return None


# Singleton instance for easy access
_config_instance: Optional[Config] = None


def get_config() -> Config:
    """
    Get the global configuration instance.
    
    Raises:
        ValueError: If required configuration is missing.
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = Config.load()
    return _config_instance


def reset_config() -> None:
    """Reset the global configuration instance. Useful for testing."""
    global _config_instance
    _config_instance = None
