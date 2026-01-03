"""Capture module - Screen and window capture functionality."""

from .screen_capture import ScreenCapture, MonitorInfo, WindowInfo, CaptureResult
from .window_selector import WindowSelector, CaptureTarget, CaptureTargetType

__all__ = [
    "ScreenCapture",
    "MonitorInfo", 
    "WindowInfo",
    "CaptureResult",
    "WindowSelector",
    "CaptureTarget",
    "CaptureTargetType"
]
