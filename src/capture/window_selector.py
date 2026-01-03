"""
Window Selector Widget

Provides a UI component for selecting capture targets (monitors, windows, regions).
"""

from dataclasses import dataclass
from typing import Callable, List, Optional, Union
from enum import Enum

from .screen_capture import ScreenCapture, MonitorInfo, WindowInfo


class CaptureTargetType(Enum):
    """Type of capture target."""
    MONITOR = "monitor"
    WINDOW = "window"
    REGION = "region"


@dataclass
class CaptureTarget:
    """Represents a selected capture target."""
    type: CaptureTargetType
    monitor: Optional[MonitorInfo] = None
    window: Optional[WindowInfo] = None
    region: Optional[tuple] = None  # (x, y, width, height)
    
    @property
    def display_name(self) -> str:
        """Get a human-readable name for this target."""
        if self.type == CaptureTargetType.MONITOR and self.monitor:
            return str(self.monitor)
        elif self.type == CaptureTargetType.WINDOW and self.window:
            return str(self.window)
        elif self.type == CaptureTargetType.REGION and self.region:
            x, y, w, h = self.region
            return f"Region ({x}, {y}) {w}x{h}"
        return "Unknown"


class WindowSelector:
    """
    Window selector logic for choosing capture targets.
    
    This class manages the list of available monitors and windows
    and provides methods for selecting capture targets.
    
    Usage:
        selector = WindowSelector()
        
        # Refresh available targets
        selector.refresh()
        
        # Get available monitors
        monitors = selector.get_monitors()
        
        # Select a target
        target = selector.select_monitor(0)
    """
    
    def __init__(self, screen_capture: Optional[ScreenCapture] = None):
        """
        Initialize the window selector.
        
        Args:
            screen_capture: Optional ScreenCapture instance to use.
                           Creates a new one if not provided.
        """
        self._capture = screen_capture or ScreenCapture()
        self._owns_capture = screen_capture is None
        
        self._monitors: List[MonitorInfo] = []
        self._windows: List[WindowInfo] = []
        self._current_target: Optional[CaptureTarget] = None
        
        # Callbacks for target changes
        self._on_target_changed: List[Callable[[CaptureTarget], None]] = []
        
        # Initial refresh
        self.refresh()
    
    def refresh(self) -> None:
        """Refresh the list of available monitors and windows."""
        self._monitors = self._capture.get_monitors()
        self._windows = self._capture.get_windows()
    
    def get_monitors(self) -> List[MonitorInfo]:
        """Get the list of available monitors."""
        return self._monitors.copy()
    
    def get_windows(self) -> List[WindowInfo]:
        """Get the list of available windows."""
        return self._windows.copy()
    
    def get_current_target(self) -> Optional[CaptureTarget]:
        """Get the currently selected capture target."""
        return self._current_target
    
    def select_monitor(self, monitor_id: int) -> CaptureTarget:
        """
        Select a monitor as the capture target.
        
        Args:
            monitor_id: The monitor index (0-based).
            
        Returns:
            The selected CaptureTarget.
            
        Raises:
            ValueError: If the monitor ID is invalid.
        """
        if monitor_id < 0 or monitor_id >= len(self._monitors):
            raise ValueError(f"Invalid monitor ID: {monitor_id}")
        
        target = CaptureTarget(
            type=CaptureTargetType.MONITOR,
            monitor=self._monitors[monitor_id]
        )
        
        self._set_target(target)
        return target
    
    def select_window(self, window_handle: int) -> CaptureTarget:
        """
        Select a window as the capture target.
        
        Args:
            window_handle: The window handle (HWND).
            
        Returns:
            The selected CaptureTarget.
            
        Raises:
            ValueError: If the window handle is not found.
        """
        window = next(
            (w for w in self._windows if w.handle == window_handle),
            None
        )
        
        if window is None:
            # Refresh and try again
            self.refresh()
            window = next(
                (w for w in self._windows if w.handle == window_handle),
                None
            )
        
        if window is None:
            raise ValueError(f"Window not found: {window_handle}")
        
        target = CaptureTarget(
            type=CaptureTargetType.WINDOW,
            window=window
        )
        
        self._set_target(target)
        return target
    
    def select_window_by_index(self, index: int) -> CaptureTarget:
        """
        Select a window by its index in the window list.
        
        Args:
            index: The window index (0-based).
            
        Returns:
            The selected CaptureTarget.
            
        Raises:
            ValueError: If the index is invalid.
        """
        if index < 0 or index >= len(self._windows):
            raise ValueError(f"Invalid window index: {index}")
        
        window = self._windows[index]
        return self.select_window(window.handle)
    
    def select_region(self, x: int, y: int, width: int, height: int) -> CaptureTarget:
        """
        Select a custom region as the capture target.
        
        Args:
            x: Left coordinate of the region.
            y: Top coordinate of the region.
            width: Width of the region.
            height: Height of the region.
            
        Returns:
            The selected CaptureTarget.
            
        Raises:
            ValueError: If the region dimensions are invalid.
        """
        if width <= 0 or height <= 0:
            raise ValueError(f"Invalid region dimensions: {width}x{height}")
        
        target = CaptureTarget(
            type=CaptureTargetType.REGION,
            region=(x, y, width, height)
        )
        
        self._set_target(target)
        return target
    
    def select_all_monitors(self) -> CaptureTarget:
        """
        Select all monitors combined as the capture target.
        
        Returns:
            The selected CaptureTarget.
        """
        # Create a virtual "all monitors" target
        if self._monitors:
            # Calculate combined bounds
            min_x = min(m.x for m in self._monitors)
            min_y = min(m.y for m in self._monitors)
            max_x = max(m.x + m.width for m in self._monitors)
            max_y = max(m.y + m.height for m in self._monitors)
            
            combined = MonitorInfo(
                id=-1,
                name="All Monitors",
                x=min_x,
                y=min_y,
                width=max_x - min_x,
                height=max_y - min_y,
                is_primary=False
            )
        else:
            combined = MonitorInfo(
                id=-1,
                name="All Monitors",
                x=0,
                y=0,
                width=1920,
                height=1080,
                is_primary=True
            )
        
        target = CaptureTarget(
            type=CaptureTargetType.MONITOR,
            monitor=combined
        )
        
        self._set_target(target)
        return target
    
    def add_target_changed_callback(
        self, 
        callback: Callable[[CaptureTarget], None]
    ) -> None:
        """
        Add a callback to be called when the target changes.
        
        Args:
            callback: Function to call with the new target.
        """
        self._on_target_changed.append(callback)
    
    def remove_target_changed_callback(
        self, 
        callback: Callable[[CaptureTarget], None]
    ) -> None:
        """Remove a previously added callback."""
        if callback in self._on_target_changed:
            self._on_target_changed.remove(callback)
    
    def _set_target(self, target: CaptureTarget) -> None:
        """Set the current target and notify listeners."""
        self._current_target = target
        for callback in self._on_target_changed:
            try:
                callback(target)
            except Exception:
                pass  # Don't let callback errors affect selection
    
    def close(self) -> None:
        """Release resources."""
        if self._owns_capture and self._capture:
            self._capture.close()
    
    def __enter__(self) -> "WindowSelector":
        return self
    
    def __exit__(self, *args) -> None:
        self.close()
