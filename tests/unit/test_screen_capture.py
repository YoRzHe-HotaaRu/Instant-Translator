"""Unit tests for screen capture module."""

import sys
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image


class TestMonitorInfo:
    """Tests for MonitorInfo dataclass."""
    
    def test_monitor_info_creation(self):
        """Test creating a MonitorInfo instance."""
        from src.capture.screen_capture import MonitorInfo
        
        monitor = MonitorInfo(
            id=0,
            name="Monitor 1",
            x=0,
            y=0,
            width=1920,
            height=1080,
            is_primary=True
        )
        
        assert monitor.id == 0
        assert monitor.name == "Monitor 1"
        assert monitor.width == 1920
        assert monitor.height == 1080
        assert monitor.is_primary is True
    
    def test_monitor_info_str(self):
        """Test MonitorInfo string representation."""
        from src.capture.screen_capture import MonitorInfo
        
        monitor = MonitorInfo(
            id=0, name="Monitor 1", x=0, y=0,
            width=1920, height=1080, is_primary=True
        )
        
        result = str(monitor)
        assert "Monitor 1" in result
        assert "Primary" in result
        assert "1920x1080" in result
    
    def test_secondary_monitor_str(self):
        """Test secondary monitor string representation."""
        from src.capture.screen_capture import MonitorInfo
        
        monitor = MonitorInfo(
            id=1, name="Monitor 2", x=1920, y=0,
            width=1920, height=1080, is_primary=False
        )
        
        result = str(monitor)
        assert "Monitor 2" in result
        assert "Primary" not in result


class TestWindowInfo:
    """Tests for WindowInfo dataclass."""
    
    def test_window_info_creation(self):
        """Test creating a WindowInfo instance."""
        from src.capture.screen_capture import WindowInfo
        
        window = WindowInfo(
            handle=12345,
            title="Test Application",
            x=100, y=100,
            width=800, height=600,
            is_visible=True
        )
        
        assert window.handle == 12345
        assert window.title == "Test Application"
        assert window.width == 800
        assert window.height == 600
    
    def test_window_info_long_title_truncation(self):
        """Test that long titles are truncated in string representation."""
        from src.capture.screen_capture import WindowInfo
        
        long_title = "A" * 100
        window = WindowInfo(
            handle=1, title=long_title, x=0, y=0,
            width=800, height=600, is_visible=True
        )
        
        result = str(window)
        assert len(result) < len(long_title)
        assert "..." in result


class TestCaptureResult:
    """Tests for CaptureResult dataclass."""
    
    def test_capture_result_creation(self, sample_image):
        """Test creating a CaptureResult instance."""
        from src.capture.screen_capture import CaptureResult
        
        result = CaptureResult(
            image=sample_image,
            x=0, y=0,
            width=800, height=600,
            source="monitor",
            source_name="Monitor 1"
        )
        
        assert result.image is sample_image
        assert result.size == (800, 600)
        assert result.source == "monitor"
    
    def test_capture_result_size_property(self, sample_image):
        """Test the size property."""
        from src.capture.screen_capture import CaptureResult
        
        result = CaptureResult(
            image=sample_image,
            x=0, y=0, width=1920, height=1080,
            source="monitor", source_name="Test"
        )
        
        assert result.size == (1920, 1080)


class TestScreenCapture:
    """Tests for ScreenCapture class."""
    
    def test_screen_capture_init(self, mock_mss):
        """Test ScreenCapture initialization."""
        from src.capture.screen_capture import ScreenCapture
        
        capture = ScreenCapture()
        assert capture is not None
        capture.close()
    
    def test_get_monitors(self, mock_mss):
        """Test getting list of monitors."""
        from src.capture.screen_capture import ScreenCapture
        
        capture = ScreenCapture()
        monitors = capture.get_monitors()
        
        assert len(monitors) == 2  # Two monitors from mock
        assert monitors[0].is_primary is True
        capture.close()
    
    def test_capture_monitor_valid_id(self, mock_mss):
        """Test capturing from a valid monitor."""
        from src.capture.screen_capture import ScreenCapture
        
        capture = ScreenCapture()
        result = capture.capture_monitor(0)
        
        assert result is not None
        assert result.source == "monitor"
        assert isinstance(result.image, Image.Image)
        capture.close()
    
    def test_capture_monitor_invalid_id(self, mock_mss):
        """Test capturing from an invalid monitor raises error."""
        from src.capture.screen_capture import ScreenCapture, ScreenCaptureError
        
        capture = ScreenCapture()
        
        with pytest.raises(ScreenCaptureError):
            capture.capture_monitor(999)
        
        capture.close()
    
    def test_capture_region_valid(self, mock_mss):
        """Test capturing a valid region."""
        from src.capture.screen_capture import ScreenCapture
        
        capture = ScreenCapture()
        result = capture.capture_region(0, 0, 100, 100)
        
        assert result is not None
        assert result.source == "region"
        assert result.width == 100
        assert result.height == 100
        capture.close()
    
    def test_capture_region_invalid_dimensions(self, mock_mss):
        """Test capturing with invalid dimensions raises error."""
        from src.capture.screen_capture import ScreenCapture, ScreenCaptureError
        
        capture = ScreenCapture()
        
        with pytest.raises(ScreenCaptureError):
            capture.capture_region(0, 0, -100, 100)
        
        with pytest.raises(ScreenCaptureError):
            capture.capture_region(0, 0, 100, 0)
        
        capture.close()
    
    def test_capture_all_monitors(self, mock_mss):
        """Test capturing all monitors combined."""
        from src.capture.screen_capture import ScreenCapture
        
        capture = ScreenCapture()
        result = capture.capture_all_monitors()
        
        assert result is not None
        assert result.source_name == "All Monitors"
        capture.close()
    
    def test_context_manager(self, mock_mss):
        """Test using ScreenCapture as context manager."""
        from src.capture.screen_capture import ScreenCapture
        
        with ScreenCapture() as capture:
            monitors = capture.get_monitors()
            assert len(monitors) > 0


class TestScreenCaptureIntegration:
    """Integration tests for screen capture (may require actual display)."""
    
    @pytest.mark.skip(reason="Requires actual display")
    def test_real_monitor_capture(self):
        """Test real monitor capture (skip in CI)."""
        from src.capture.screen_capture import ScreenCapture
        
        with ScreenCapture() as capture:
            monitors = capture.get_monitors()
            if monitors:
                result = capture.capture_monitor(0)
                assert result.image is not None
                assert result.image.size[0] > 0
                assert result.image.size[1] > 0
