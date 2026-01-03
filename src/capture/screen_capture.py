"""
Screen Capture Module

Provides functionality to capture screenshots from monitors, windows, or custom regions.
Supports multi-monitor setups and high-DPI displays.
"""

import sys
from dataclasses import dataclass
from typing import List, Optional, Tuple
from PIL import Image

try:
    import mss
    MSS_AVAILABLE = True
except ImportError:
    MSS_AVAILABLE = False

# Windows-specific imports
if sys.platform == "win32":
    try:
        import win32gui
        import win32con
        import win32ui
        import win32api
        from ctypes import windll
        WIN32_AVAILABLE = True
    except ImportError:
        WIN32_AVAILABLE = False
else:
    WIN32_AVAILABLE = False


@dataclass
class MonitorInfo:
    """Information about a display monitor."""
    id: int
    name: str
    x: int
    y: int
    width: int
    height: int
    is_primary: bool
    
    def __str__(self) -> str:
        primary_str = " (Primary)" if self.is_primary else ""
        return f"{self.name}{primary_str} - {self.width}x{self.height}"


@dataclass
class WindowInfo:
    """Information about an application window."""
    handle: int
    title: str
    x: int
    y: int
    width: int
    height: int
    is_visible: bool
    process_name: Optional[str] = None
    
    def __str__(self) -> str:
        return f"{self.title[:50]}..." if len(self.title) > 50 else self.title


@dataclass
class CaptureResult:
    """Result of a screen capture operation."""
    image: Image.Image
    x: int
    y: int
    width: int
    height: int
    source: str  # "monitor", "window", or "region"
    source_name: str
    
    @property
    def size(self) -> Tuple[int, int]:
        """Get the size of the captured image."""
        return (self.width, self.height)


class ScreenCaptureError(Exception):
    """Exception raised when screen capture fails."""
    pass


class ScreenCapture:
    """
    Screen capture utility supporting monitors, windows, and custom regions.
    
    Usage:
        capture = ScreenCapture()
        
        # Get available monitors
        monitors = capture.get_monitors()
        
        # Capture from primary monitor
        result = capture.capture_monitor(0)
        
        # Save the image
        result.image.save("screenshot.png")
    """
    
    def __init__(self):
        """Initialize the screen capture utility."""
        if not MSS_AVAILABLE:
            raise ScreenCaptureError("mss library is required for screen capture")
        
        self._mss = mss.mss()
        self._enable_dpi_awareness()
    
    def _enable_dpi_awareness(self) -> None:
        """Enable DPI awareness for accurate captures on high-DPI displays."""
        if sys.platform == "win32":
            try:
                windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
            except Exception:
                try:
                    windll.user32.SetProcessDPIAware()
                except Exception:
                    pass  # DPI awareness not available
    
    def get_monitors(self) -> List[MonitorInfo]:
        """
        Get information about all available monitors.
        
        Returns:
            List of MonitorInfo objects describing each monitor.
        """
        monitors = []
        
        for i, monitor in enumerate(self._mss.monitors):
            if i == 0:
                # Skip the "all monitors" combined view (index 0)
                continue
            
            monitors.append(MonitorInfo(
                id=i - 1,  # 0-indexed for user
                name=f"Monitor {i}",
                x=monitor["left"],
                y=monitor["top"],
                width=monitor["width"],
                height=monitor["height"],
                is_primary=(i == 1)  # First real monitor is usually primary
            ))
        
        return monitors
    
    def get_windows(self, include_hidden: bool = False) -> List[WindowInfo]:
        """
        Get information about all open windows.
        
        Args:
            include_hidden: If True, include hidden/minimized windows.
            
        Returns:
            List of WindowInfo objects describing each window.
        """
        if not WIN32_AVAILABLE:
            return []
        
        windows = []
        
        def enum_callback(hwnd: int, _) -> bool:
            """Callback for enumerating windows."""
            if not win32gui.IsWindow(hwnd):
                return True
            
            # Check visibility
            is_visible = win32gui.IsWindowVisible(hwnd)
            if not include_hidden and not is_visible:
                return True
            
            # Get window title
            title = win32gui.GetWindowText(hwnd)
            if not title:
                return True
            
            # Skip certain system windows
            if title in ["Program Manager", "Windows Input Experience"]:
                return True
            
            # Get window rectangle
            try:
                rect = win32gui.GetWindowRect(hwnd)
                x, y, x2, y2 = rect
                width = x2 - x
                height = y2 - y
                
                # Skip windows with no size
                if width <= 0 or height <= 0:
                    return True
                
                windows.append(WindowInfo(
                    handle=hwnd,
                    title=title,
                    x=x,
                    y=y,
                    width=width,
                    height=height,
                    is_visible=is_visible
                ))
            except Exception:
                pass
            
            return True
        
        win32gui.EnumWindows(enum_callback, None)
        
        # Sort by title for consistent ordering
        windows.sort(key=lambda w: w.title.lower())
        
        return windows
    
    def capture_monitor(self, monitor_id: int = 0) -> CaptureResult:
        """
        Capture a screenshot of a specific monitor.
        
        Args:
            monitor_id: The monitor index (0-based).
            
        Returns:
            CaptureResult containing the screenshot image.
            
        Raises:
            ScreenCaptureError: If the monitor ID is invalid.
        """
        monitors = self.get_monitors()
        
        if monitor_id < 0 or monitor_id >= len(monitors):
            raise ScreenCaptureError(f"Invalid monitor ID: {monitor_id}. Available: 0-{len(monitors)-1}")
        
        monitor = monitors[monitor_id]
        
        # mss uses 1-indexed monitors (0 is all monitors combined)
        mss_monitor = self._mss.monitors[monitor_id + 1]
        
        # Capture the screenshot
        screenshot = self._mss.grab(mss_monitor)
        
        # Convert to PIL Image
        image = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
        
        return CaptureResult(
            image=image,
            x=monitor.x,
            y=monitor.y,
            width=monitor.width,
            height=monitor.height,
            source="monitor",
            source_name=str(monitor)
        )
    
    def capture_window(self, window_handle: int) -> CaptureResult:
        """
        Capture a screenshot of a specific window.
        
        Args:
            window_handle: The window handle (HWND).
            
        Returns:
            CaptureResult containing the screenshot image.
            
        Raises:
            ScreenCaptureError: If the window cannot be captured.
        """
        if not WIN32_AVAILABLE:
            raise ScreenCaptureError("Window capture is only available on Windows")
        
        try:
            # Get window rectangle
            rect = win32gui.GetWindowRect(window_handle)
            x, y, x2, y2 = rect
            width = x2 - x
            height = y2 - y
            
            if width <= 0 or height <= 0:
                raise ScreenCaptureError("Window has invalid dimensions")
            
            # Get window title for source name
            title = win32gui.GetWindowText(window_handle)
            
            # Capture using region capture
            return self.capture_region(x, y, width, height, source_name=title)
            
        except ScreenCaptureError:
            raise
        except Exception as e:
            raise ScreenCaptureError(f"Failed to capture window: {e}")
    
    def capture_region(
        self, 
        x: int, 
        y: int, 
        width: int, 
        height: int,
        source_name: str = "Custom Region"
    ) -> CaptureResult:
        """
        Capture a screenshot of a specific region.
        
        Args:
            x: Left coordinate of the region.
            y: Top coordinate of the region.
            width: Width of the region.
            height: Height of the region.
            source_name: Optional name for the capture source.
            
        Returns:
            CaptureResult containing the screenshot image.
            
        Raises:
            ScreenCaptureError: If the region is invalid.
        """
        if width <= 0 or height <= 0:
            raise ScreenCaptureError(f"Invalid region dimensions: {width}x{height}")
        
        region = {
            "left": x,
            "top": y,
            "width": width,
            "height": height
        }
        
        try:
            screenshot = self._mss.grab(region)
            image = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
            
            return CaptureResult(
                image=image,
                x=x,
                y=y,
                width=width,
                height=height,
                source="region",
                source_name=source_name
            )
        except Exception as e:
            raise ScreenCaptureError(f"Failed to capture region: {e}")
    
    def capture_all_monitors(self) -> CaptureResult:
        """
        Capture a screenshot spanning all monitors.
        
        Returns:
            CaptureResult containing the combined screenshot.
        """
        # mss monitor 0 is the combined view of all monitors
        all_monitors = self._mss.monitors[0]
        
        screenshot = self._mss.grab(all_monitors)
        image = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
        
        return CaptureResult(
            image=image,
            x=all_monitors["left"],
            y=all_monitors["top"],
            width=all_monitors["width"],
            height=all_monitors["height"],
            source="monitor",
            source_name="All Monitors"
        )
    
    def close(self) -> None:
        """Release resources."""
        if self._mss:
            self._mss.close()
    
    def __enter__(self) -> "ScreenCapture":
        return self
    
    def __exit__(self, *args) -> None:
        self.close()
