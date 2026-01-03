"""Unit tests for prompt builder module."""

import pytest


class TestPromptConfig:
    """Tests for PromptConfig dataclass."""
    
    def test_default_config(self):
        """Test default configuration."""
        from src.translation.prompt_builder import PromptConfig, TranslationStyle
        
        config = PromptConfig()
        
        assert config.style == TranslationStyle.NATURAL
        assert config.preserve_formatting is True
        assert config.max_context_length == 4000
    
    def test_custom_config(self):
        """Test custom configuration."""
        from src.translation.prompt_builder import PromptConfig, TranslationStyle
        
        config = PromptConfig(
            style=TranslationStyle.FORMAL,
            preserve_formatting=False,
            max_context_length=2000
        )
        
        assert config.style == TranslationStyle.FORMAL
        assert config.preserve_formatting is False
        assert config.max_context_length == 2000


class TestTranslationStyle:
    """Tests for TranslationStyle enum."""
    
    def test_style_values(self):
        """Test that all expected styles exist."""
        from src.translation.prompt_builder import TranslationStyle
        
        assert TranslationStyle.LITERAL.value == "literal"
        assert TranslationStyle.NATURAL.value == "natural"
        assert TranslationStyle.FORMAL.value == "formal"
        assert TranslationStyle.CASUAL.value == "casual"
        assert TranslationStyle.TECHNICAL.value == "technical"


class TestPromptBuilder:
    """Tests for PromptBuilder class."""
    
    def test_builder_init_default(self):
        """Test default initialization."""
        from src.translation.prompt_builder import PromptBuilder
        
        builder = PromptBuilder()
        assert builder.config is not None
    
    def test_builder_init_custom_config(self):
        """Test initialization with custom config."""
        from src.translation.prompt_builder import PromptBuilder, PromptConfig, TranslationStyle
        
        config = PromptConfig(style=TranslationStyle.FORMAL)
        builder = PromptBuilder(config)
        
        assert builder.config.style == TranslationStyle.FORMAL
    
    def test_get_system_prompt(self):
        """Test getting the system prompt."""
        from src.translation.prompt_builder import PromptBuilder
        
        builder = PromptBuilder()
        system_prompt = builder.get_system_prompt()
        
        assert len(system_prompt) > 0
        assert "translator" in system_prompt.lower()
    
    def test_build_translation_prompt_basic(self):
        """Test basic translation prompt building."""
        from src.translation.prompt_builder import PromptBuilder
        
        builder = PromptBuilder()
        prompt = builder.build_translation_prompt(
            text="Hello, world!",
            source_lang="en",
            target_lang="ja"
        )
        
        assert "Hello, world!" in prompt
        assert "English" in prompt
        assert "Japanese" in prompt
    
    def test_build_translation_prompt_with_style(self):
        """Test prompt building with specific style."""
        from src.translation.prompt_builder import PromptBuilder, TranslationStyle
        
        builder = PromptBuilder()
        prompt = builder.build_translation_prompt(
            text="Hello",
            source_lang="en",
            target_lang="ja",
            style=TranslationStyle.FORMAL
        )
        
        assert "formal" in prompt.lower()
    
    def test_build_translation_prompt_with_context(self):
        """Test prompt building with context."""
        from src.translation.prompt_builder import PromptBuilder
        
        builder = PromptBuilder()
        prompt = builder.build_translation_prompt(
            text="Submit",
            source_lang="en",
            target_lang="ja",
            context="This is a button text in a web form"
        )
        
        assert "button" in prompt.lower() or "Context" in prompt
    
    def test_build_translation_prompt_formatting_instruction(self):
        """Test that formatting instruction is included by default."""
        from src.translation.prompt_builder import PromptBuilder
        
        builder = PromptBuilder()
        prompt = builder.build_translation_prompt(
            text="Test",
            source_lang="en",
            target_lang="ja"
        )
        
        assert "formatting" in prompt.lower() or "Preserve" in prompt
    
    def test_build_batch_translation_prompt(self):
        """Test batch translation prompt building."""
        from src.translation.prompt_builder import PromptBuilder
        
        builder = PromptBuilder()
        texts = ["Hello", "Goodbye", "Thank you"]
        
        prompt = builder.build_batch_translation_prompt(
            texts=texts,
            source_lang="en",
            target_lang="ja"
        )
        
        assert "3 texts" in prompt
        for text in texts:
            assert text in prompt
    
    def test_build_detection_prompt(self):
        """Test language detection prompt building."""
        from src.translation.prompt_builder import PromptBuilder
        
        builder = PromptBuilder()
        prompt = builder.build_detection_prompt("こんにちは")
        
        assert "こんにちは" in prompt
        assert "language" in prompt.lower()
    
    def test_build_quality_check_prompt(self):
        """Test translation quality check prompt building."""
        from src.translation.prompt_builder import PromptBuilder
        
        builder = PromptBuilder()
        prompt = builder.build_quality_check_prompt(
            original="Hello",
            translation="こんにちは",
            source_lang="en",
            target_lang="ja"
        )
        
        assert "Hello" in prompt
        assert "こんにちは" in prompt
        assert "English" in prompt
        assert "Japanese" in prompt
    
    def test_truncate_text_short(self):
        """Test truncation of short text (no change)."""
        from src.translation.prompt_builder import PromptBuilder
        
        builder = PromptBuilder()
        text = "Short text"
        
        result = builder.truncate_text(text, max_length=100)
        
        assert result == text
    
    def test_truncate_text_long(self):
        """Test truncation of long text."""
        from src.translation.prompt_builder import PromptBuilder
        
        builder = PromptBuilder()
        text = "A" * 1000
        
        result = builder.truncate_text(text, max_length=100)
        
        assert len(result) <= 103  # 100 + "..."
        assert result.endswith("...")
    
    def test_truncate_text_at_word_boundary(self):
        """Test truncation at word boundary."""
        from src.translation.prompt_builder import PromptBuilder
        
        builder = PromptBuilder()
        text = "This is a test sentence that should be truncated at a word boundary"
        
        result = builder.truncate_text(text, max_length=30)
        
        # Should end with "..."
        assert result.endswith("...")
        # Result should be within length limit
        assert len(result) <= 33  # max_length + "..."


class TestPromptLanguageMapping:
    """Tests for language name mapping in prompts."""
    
    def test_common_language_names(self):
        """Test that common languages are properly named in prompts."""
        from src.translation.prompt_builder import PromptBuilder
        
        builder = PromptBuilder()
        
        # Test various language pairs
        test_cases = [
            ("en", "ja", "English", "Japanese"),
            ("en", "zh-cn", "English", "Chinese (Simplified)"),
            ("ja", "ko", "Japanese", "Korean"),
        ]
        
        for source, target, source_name, target_name in test_cases:
            prompt = builder.build_translation_prompt(
                text="Test",
                source_lang=source,
                target_lang=target
            )
            
            assert source_name in prompt
            assert target_name in prompt
