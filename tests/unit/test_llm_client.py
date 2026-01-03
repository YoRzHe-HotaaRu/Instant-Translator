"""Unit tests for LLM client module."""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock


class TestTranslationResult:
    """Tests for TranslationResult dataclass."""
    
    def test_translation_result_creation(self):
        """Test creating a TranslationResult instance."""
        from src.translation.llm_client import TranslationResult
        
        result = TranslationResult(
            original_text="Hello",
            translated_text="こんにちは",
            source_language="en",
            target_language="ja",
            confidence=0.95,
            model_used="deepseek/deepseek-v3.2"
        )
        
        assert result.original_text == "Hello"
        assert result.is_successful is True
    
    def test_is_successful_empty(self):
        """Test is_successful with empty translation."""
        from src.translation.llm_client import TranslationResult
        
        result = TranslationResult(
            original_text="Hello",
            translated_text="",
            source_language="en",
            target_language="ja",
            confidence=0.0,
            model_used="test"
        )
        
        assert result.is_successful is False


class TestLLMClient:
    """Tests for LLMClient class."""
    
    def test_client_init(self):
        """Test LLM client initialization."""
        with patch("src.translation.llm_client.OpenAI"):
            from src.translation.llm_client import LLMClient
            
            client = LLMClient(api_key="test-key")
            assert client.api_key == "test-key"
    
    def test_translate_basic(self):
        """Test basic translation."""
        with patch("src.translation.llm_client.OpenAI") as mock_openai:
            # Setup the mock
            mock_instance = MagicMock()
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Translated text"
            mock_response.usage = MagicMock()
            mock_response.usage.total_tokens = 50
            mock_instance.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_instance
            
            from src.translation.llm_client import LLMClient
            
            client = LLMClient(api_key="test-key")
            result = client.translate("Hello", "ja", "en")
            
            assert result is not None
            assert result.translated_text == "Translated text"
    
    def test_translate_same_language(self):
        """Test translation when source and target are the same."""
        with patch("src.translation.llm_client.OpenAI"):
            from src.translation.llm_client import LLMClient
            
            client = LLMClient(api_key="test-key")
            result = client.translate("Hello", "en", "en")
            
            assert result.translated_text == "Hello"
            assert result.tokens_used == 0
    
    def test_cache_operations(self):
        """Test cache operations."""
        with patch("src.translation.llm_client.OpenAI") as mock_openai:
            # Setup the mock
            mock_instance = MagicMock()
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Translated"
            mock_response.usage = MagicMock()
            mock_response.usage.total_tokens = 50
            mock_instance.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_instance
            
            from src.translation.llm_client import LLMClient
            
            client = LLMClient(api_key="test-key", enable_cache=True)
            
            # First call
            result1 = client.translate("Hello", "ja", "en")
            
            # Second call should be cached
            result2 = client.translate("Hello", "ja", "en")
            assert result2.cached is True
            
            # Clear cache
            count = client.clear_cache()
            assert count == 1
    
    def test_get_cache_stats(self):
        """Test getting cache statistics."""
        with patch("src.translation.llm_client.OpenAI"):
            from src.translation.llm_client import LLMClient
            
            client = LLMClient(api_key="test-key", enable_cache=True)
            stats = client.get_cache_stats()
            
            assert "entries" in stats
            assert "enabled" in stats
