"""
LLM Client

Client for communicating with ZenMux API for translation services.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

try:
    from openai import OpenAI, AsyncOpenAI
    from openai import APIError, APIConnectionError, RateLimitError
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

from .prompt_builder import PromptBuilder, TranslationStyle
from .language_detector import LanguageDetector


logger = logging.getLogger(__name__)


@dataclass
class TranslationResult:
    """Result of a translation operation."""
    original_text: str
    translated_text: str
    source_language: str
    target_language: str
    confidence: float
    model_used: str
    tokens_used: int = 0
    latency_ms: float = 0.0
    cached: bool = False
    
    @property
    def is_successful(self) -> bool:
        """Check if translation was successful."""
        return bool(self.translated_text and self.translated_text.strip())


class LLMClientError(Exception):
    """Exception raised when LLM API call fails."""
    pass


class LLMClient:
    """
    Client for LLM-powered translation via ZenMux API.
    
    Features:
    - Automatic retry with exponential backoff
    - Response caching for repeated texts
    - Language detection integration
    - Async and sync operation modes
    
    Usage:
        client = LLMClient(api_key="sk-...", base_url="https://zenmux.ai/api/v1")
        result = client.translate("Hello world", target_lang="ja")
        print(result.translated_text)
    """
    
    DEFAULT_BASE_URL = "https://zenmux.ai/api/v1"
    DEFAULT_MODEL = "deepseek/deepseek-v3.2"
    
    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
        enable_cache: bool = True
    ):
        """
        Initialize the LLM client.
        
        Args:
            api_key: ZenMux API key.
            base_url: API base URL.
            model: Model to use for translation.
            timeout: Request timeout in seconds.
            max_retries: Maximum retry attempts.
            enable_cache: Whether to cache translations.
        """
        if not OPENAI_AVAILABLE:
            raise LLMClientError("openai library is required. Install with: pip install openai")
        
        self.api_key = api_key
        self.base_url = base_url or self.DEFAULT_BASE_URL
        self.model = model or self.DEFAULT_MODEL
        self.timeout = timeout
        self.max_retries = max_retries
        self.enable_cache = enable_cache
        
        # Initialize clients
        self._sync_client = OpenAI(
            api_key=api_key,
            base_url=self.base_url,
            timeout=timeout
        )
        
        self._async_client: Optional[AsyncOpenAI] = None
        
        # Cache for translations
        self._cache: Dict[str, TranslationResult] = {}
        
        # Prompt builder
        self._prompt_builder = PromptBuilder()
        
        # Language detector
        self._language_detector = LanguageDetector()
    
    def _get_async_client(self) -> AsyncOpenAI:
        """Get or create async client."""
        if self._async_client is None:
            self._async_client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=self.timeout
            )
        return self._async_client
    
    def _get_cache_key(self, text: str, source_lang: str, target_lang: str) -> str:
        """Generate cache key for a translation."""
        return f"{source_lang}:{target_lang}:{hash(text)}"
    
    def translate(
        self,
        text: str,
        target_lang: str,
        source_lang: Optional[str] = None,
        style: Optional[TranslationStyle] = None
    ) -> TranslationResult:
        """
        Translate text synchronously.
        
        Args:
            text: Text to translate.
            target_lang: Target language code.
            source_lang: Source language code (auto-detected if not provided).
            style: Translation style.
            
        Returns:
            TranslationResult with translated text.
        """
        # Auto-detect source language if not provided
        if not source_lang:
            detection = self._language_detector.detect(text)
            source_lang = detection.language
            logger.debug(f"Detected source language: {source_lang} (confidence: {detection.confidence:.2f})")
        
        # Check cache
        if self.enable_cache:
            cache_key = self._get_cache_key(text, source_lang, target_lang)
            if cache_key in self._cache:
                cached = self._cache[cache_key]
                cached.cached = True
                return cached
        
        # Skip translation if source and target are the same
        if source_lang == target_lang:
            return TranslationResult(
                original_text=text,
                translated_text=text,
                source_language=source_lang,
                target_language=target_lang,
                confidence=1.0,
                model_used=self.model,
                tokens_used=0,
                latency_ms=0
            )
        
        # Build prompt
        prompt = self._prompt_builder.build_translation_prompt(
            text=text,
            source_lang=source_lang,
            target_lang=target_lang,
            style=style
        )
        
        # Make API request with retry
        start_time = time.time()
        
        for attempt in range(self.max_retries):
            try:
                response = self._sync_client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": self._prompt_builder.get_system_prompt()},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,  # Lower temperature for more consistent translations
                    max_tokens=len(text) * 3  # Rough estimate for output length
                )
                
                latency_ms = (time.time() - start_time) * 1000
                
                # Extract translation
                translated = response.choices[0].message.content.strip()
                
                # Calculate tokens
                tokens_used = response.usage.total_tokens if response.usage else 0
                
                result = TranslationResult(
                    original_text=text,
                    translated_text=translated,
                    source_language=source_lang,
                    target_language=target_lang,
                    confidence=0.95,  # High confidence for successful API calls
                    model_used=self.model,
                    tokens_used=tokens_used,
                    latency_ms=latency_ms
                )
                
                # Cache result
                if self.enable_cache:
                    self._cache[cache_key] = result
                
                return result
                
            except RateLimitError as e:
                logger.warning(f"Rate limit hit, attempt {attempt + 1}/{self.max_retries}")
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    time.sleep(wait_time)
                else:
                    raise LLMClientError(f"Rate limit exceeded after {self.max_retries} attempts: {e}")
                    
            except APIConnectionError as e:
                logger.warning(f"Connection error, attempt {attempt + 1}/{self.max_retries}")
                if attempt < self.max_retries - 1:
                    time.sleep(1)
                else:
                    raise LLMClientError(f"Connection failed after {self.max_retries} attempts: {e}")
                    
            except APIError as e:
                raise LLMClientError(f"API error: {e}")
        
        raise LLMClientError("Translation failed after all retries")
    
    async def translate_async(
        self,
        text: str,
        target_lang: str,
        source_lang: Optional[str] = None,
        style: Optional[TranslationStyle] = None
    ) -> TranslationResult:
        """
        Translate text asynchronously.
        
        Args:
            text: Text to translate.
            target_lang: Target language code.
            source_lang: Source language code (auto-detected if not provided).
            style: Translation style.
            
        Returns:
            TranslationResult with translated text.
        """
        # Auto-detect source language if not provided
        if not source_lang:
            detection = self._language_detector.detect(text)
            source_lang = detection.language
        
        # Check cache
        if self.enable_cache:
            cache_key = self._get_cache_key(text, source_lang, target_lang)
            if cache_key in self._cache:
                cached = self._cache[cache_key]
                cached.cached = True
                return cached
        
        # Skip translation if source and target are the same
        if source_lang == target_lang:
            return TranslationResult(
                original_text=text,
                translated_text=text,
                source_language=source_lang,
                target_language=target_lang,
                confidence=1.0,
                model_used=self.model,
                tokens_used=0,
                latency_ms=0
            )
        
        # Build prompt
        prompt = self._prompt_builder.build_translation_prompt(
            text=text,
            source_lang=source_lang,
            target_lang=target_lang,
            style=style
        )
        
        # Make API request with retry
        client = self._get_async_client()
        start_time = time.time()
        
        for attempt in range(self.max_retries):
            try:
                response = await client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": self._prompt_builder.get_system_prompt()},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=len(text) * 3
                )
                
                latency_ms = (time.time() - start_time) * 1000
                
                translated = response.choices[0].message.content.strip()
                tokens_used = response.usage.total_tokens if response.usage else 0
                
                result = TranslationResult(
                    original_text=text,
                    translated_text=translated,
                    source_language=source_lang,
                    target_language=target_lang,
                    confidence=0.95,
                    model_used=self.model,
                    tokens_used=tokens_used,
                    latency_ms=latency_ms
                )
                
                if self.enable_cache:
                    self._cache[cache_key] = result
                
                return result
                
            except RateLimitError:
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                else:
                    raise LLMClientError("Rate limit exceeded")
                    
            except APIConnectionError:
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(1)
                else:
                    raise LLMClientError("Connection failed")
                    
            except APIError as e:
                raise LLMClientError(f"API error: {e}")
        
        raise LLMClientError("Translation failed")
    
    async def translate_batch_async(
        self,
        texts: List[str],
        target_lang: str,
        source_lang: Optional[str] = None
    ) -> List[TranslationResult]:
        """
        Translate multiple texts concurrently.
        
        Args:
            texts: List of texts to translate.
            target_lang: Target language code.
            source_lang: Source language code.
            
        Returns:
            List of TranslationResult objects.
        """
        tasks = [
            self.translate_async(text, target_lang, source_lang)
            for text in texts
        ]
        
        return await asyncio.gather(*tasks)
    
    def validate_connection(self) -> bool:
        """
        Validate API connection.
        
        Returns:
            True if connection is valid.
        """
        try:
            # Make a minimal API call
            response = self._sync_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=5
            )
            return True
        except Exception as e:
            logger.error(f"Connection validation failed: {e}")
            return False
    
    def clear_cache(self) -> int:
        """
        Clear the translation cache.
        
        Returns:
            Number of entries cleared.
        """
        count = len(self._cache)
        self._cache.clear()
        return count
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache stats.
        """
        return {
            "entries": len(self._cache),
            "enabled": self.enable_cache
        }
    
    def close(self) -> None:
        """Close the client and release resources."""
        if self._sync_client:
            self._sync_client.close()
        if self._async_client:
            asyncio.get_event_loop().run_until_complete(
                self._async_client.close()
            )
