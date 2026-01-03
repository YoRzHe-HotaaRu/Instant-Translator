"""
Instant Translator - Main Entry Point

Run the application with: python -m src.main
"""

import os
import sys
import logging

from dotenv import load_dotenv


def setup_logging() -> None:
    """Configure application logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def main() -> int:
    """Main entry point for the application."""
    # Load environment variables
    load_dotenv()
    
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Get API configuration
    api_key = os.getenv("ZENMUX_API_KEY")
    base_url = os.getenv("ZENMUX_BASE_URL", "https://zenmux.ai/api/v1")
    model = os.getenv("ZENMUX_MODEL", "deepseek/deepseek-v3.2")
    
    if not api_key:
        logger.error("ZENMUX_API_KEY environment variable is required")
        logger.info("Please create a .env file with your API key:")
        logger.info("  ZENMUX_API_KEY=your_api_key_here")
        return 1
    
    # Import PyQt6 here to allow graceful error if not installed
    try:
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import Qt
    except ImportError:
        logger.error("PyQt6 is not installed. Install with: pip install PyQt6")
        return 1
    
    # Enable high DPI scaling BEFORE creating QApplication
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    # Import our main window
    from .gui import MainWindow
    
    # Create the application
    app = QApplication(sys.argv)
    app.setApplicationName("Instant Translator")
    app.setApplicationVersion("1.0.0")
    
    # Create and show main window
    window = MainWindow(
        api_key=api_key,
        base_url=base_url,
        model=model
    )
    window.show()
    
    logger.info("Instant Translator started")
    
    # Run the event loop
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
