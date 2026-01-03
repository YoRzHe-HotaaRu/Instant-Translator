"""
Pytest configuration and shared fixtures.
"""

import os
import sys
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


# =============================================================================
# Environment Fixtures
# =============================================================================

@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    """Set up test environment variables."""
    monkeypatch.setenv("ZENMUX_API_KEY", "test-api-key-12345")
    monkeypatch.setenv("ZENMUX_BASE_URL", "https://zenmux.ai/api/v1")
    monkeypatch.setenv("ZENMUX_MODEL", "deepseek/deepseek-v3.2")
    monkeypatch.setenv("DEBUG", "true")


@pytest.fixture
def reset_config():
    """Reset configuration singleton after test."""
    yield
    from src.config import reset_config
    reset_config()


# =============================================================================
# Image Fixtures
# =============================================================================

@pytest.fixture
def sample_image() -> Image.Image:
    """Create a sample test image."""
    img = Image.new("RGB", (800, 600), color=(255, 255, 255))
    return img


@pytest.fixture
def sample_image_with_text() -> Image.Image:
    """Create a sample image that would contain text (simulated)."""
    img = Image.new("RGB", (800, 600), color=(255, 255, 255))
    # In a real scenario, this would have actual text
    return img


@pytest.fixture
def small_image() -> Image.Image:
    """Create a small image for upscaling tests."""
    return Image.new("RGB", (100, 75), color=(200, 200, 200))


@pytest.fixture
def grayscale_image() -> Image.Image:
    """Create a grayscale image."""
    return Image.new("L", (400, 300), color=128)


@pytest.fixture
def low_contrast_image() -> Image.Image:
    """Create a low contrast image."""
    img = Image.new("RGB", (400, 300), color=(128, 128, 128))
    return img


# =============================================================================
# Mock Fixtures
# =============================================================================

@pytest.fixture
def mock_mss():
    """Mock mss screen capture library."""
    with patch("mss.mss") as mock:
        instance = MagicMock()
        
        # Mock monitors
        instance.monitors = [
            {"left": 0, "top": 0, "width": 3840, "height": 2160},  # All monitors
            {"left": 0, "top": 0, "width": 1920, "height": 1080},  # Monitor 1
            {"left": 1920, "top": 0, "width": 1920, "height": 1080},  # Monitor 2
        ]
        
        # Mock grab to return fake screenshot data
        screenshot = MagicMock()
        screenshot.size = (1920, 1080)
        screenshot.bgra = b"\xff" * (1920 * 1080 * 4)  # White pixels
        instance.grab.return_value = screenshot
        
        mock.return_value = instance
        yield mock


@pytest.fixture
def mock_win32gui():
    """Mock win32gui for window enumeration."""
    with patch.dict(sys.modules, {"win32gui": MagicMock(), "win32con": MagicMock(), 
                                   "win32ui": MagicMock(), "win32api": MagicMock()}):
        import win32gui
        
        # Mock window functions
        win32gui.IsWindow.return_value = True
        win32gui.IsWindowVisible.return_value = True
        win32gui.GetWindowText.return_value = "Test Window"
        win32gui.GetWindowRect.return_value = (100, 100, 900, 700)
        
        def mock_enum_windows(callback, param):
            # Simulate finding some windows
            callback(12345, param)
            callback(67890, param)
        
        win32gui.EnumWindows.side_effect = mock_enum_windows
        
        yield win32gui


@pytest.fixture
def mock_tesseract():
    """Mock pytesseract for OCR."""
    with patch("pytesseract.image_to_string") as mock_string, \
         patch("pytesseract.image_to_data") as mock_data:
        
        mock_string.return_value = "Sample extracted text"
        mock_data.return_value = {
            "text": ["Sample", "extracted", "text"],
            "conf": [95, 92, 98],
            "left": [10, 100, 200],
            "top": [10, 10, 10],
            "width": [80, 90, 60],
            "height": [20, 20, 20]
        }
        
        yield mock_string, mock_data


@pytest.fixture
def mock_easyocr():
    """Mock easyocr for OCR."""
    with patch("easyocr.Reader") as mock_reader:
        instance = MagicMock()
        instance.readtext.return_value = [
            ([[10, 10], [90, 10], [90, 30], [10, 30]], "Sample", 0.95),
            ([[100, 10], [190, 10], [190, 30], [100, 30]], "text", 0.92),
        ]
        mock_reader.return_value = instance
        yield mock_reader


@pytest.fixture
def mock_openai():
    """Mock OpenAI client for LLM API."""
    with patch("openai.OpenAI") as mock_sync, \
         patch("openai.AsyncOpenAI") as mock_async:
        
        # Mock sync client
        sync_instance = MagicMock()
        response = MagicMock()
        response.choices = [MagicMock()]
        response.choices[0].message.content = "Translated text"
        response.usage = MagicMock()
        response.usage.total_tokens = 50
        
        sync_instance.chat.completions.create.return_value = response
        mock_sync.return_value = sync_instance
        
        # Mock async client similarly
        mock_async.return_value = MagicMock()
        
        yield mock_sync, mock_async


# =============================================================================
# Sample Data Fixtures
# =============================================================================

@pytest.fixture
def sample_texts():
    """Sample texts for testing."""
    return {
        "english": "Hello, how are you today?",
        "japanese": "こんにちは、今日はお元気ですか？",
        "chinese": "你好，今天你好吗？",
        "korean": "안녕하세요, 오늘 기분이 어떠세요?",
        "mixed": "Hello 世界 こんにちは",
        "technical": "The API returns a JSON response with status code 200.",
        "multiline": "First line.\nSecond line.\nThird line.",
        "with_artifacts": "Sample\x00text\x0bwith\x1fartifacts",
    }


@pytest.fixture
def ocr_error_cases():
    """Common OCR error patterns for testing."""
    return [
        ("rnade", "made"),  # rn -> m
        ("0ne", "One"),  # 0 -> O
        ("he11o", "hello"),  # 1 -> l
        ("c1ean", "clean"),  # 1 -> l
    ]


# =============================================================================
# Test Directory Fixtures
# =============================================================================

@pytest.fixture
def test_assets_dir() -> Path:
    """Get the test assets directory."""
    assets_dir = Path(__file__).parent.parent / "assets" / "test_images"
    assets_dir.mkdir(parents=True, exist_ok=True)
    return assets_dir


@pytest.fixture
def temp_image_file(tmp_path, sample_image) -> Path:
    """Create a temporary image file."""
    img_path = tmp_path / "test_image.png"
    sample_image.save(img_path)
    return img_path
