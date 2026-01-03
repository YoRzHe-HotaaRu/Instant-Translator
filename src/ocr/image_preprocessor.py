"""
Image Preprocessor

Enhances images for optimal OCR accuracy through various preprocessing techniques.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False


class PreprocessingStep(Enum):
    """Available preprocessing steps."""
    UPSCALE = "upscale"
    GRAYSCALE = "grayscale"
    CONTRAST = "contrast"
    DENOISE = "denoise"
    BINARIZE = "binarize"
    DESKEW = "deskew"
    SHARPEN = "sharpen"


@dataclass
class PreprocessingConfig:
    """Configuration for image preprocessing."""
    upscale_factor: float = 2.0
    contrast_factor: float = 1.5
    denoise_strength: int = 10
    binarize_threshold: int = 0  # 0 = auto (Otsu's method)
    sharpen_factor: float = 1.2
    
    # Which steps to apply
    apply_upscale: bool = True
    apply_grayscale: bool = True
    apply_contrast: bool = True
    apply_denoise: bool = True
    apply_binarize: bool = False  # Often hurts colored text
    apply_deskew: bool = True
    apply_sharpen: bool = True


class ImagePreprocessor:
    """
    Image preprocessing for OCR optimization.
    
    Applies various image enhancement techniques to improve OCR accuracy:
    - Upscaling: Increases image resolution for small text
    - Grayscale: Removes color noise
    - Contrast: Enhances text visibility
    - Denoising: Removes image noise
    - Binarization: Converts to black/white (optional)
    - Deskewing: Corrects rotated text
    - Sharpening: Enhances edge definition
    
    Usage:
        preprocessor = ImagePreprocessor()
        enhanced = preprocessor.process(image)
    """
    
    def __init__(self, config: Optional[PreprocessingConfig] = None):
        """
        Initialize the preprocessor.
        
        Args:
            config: Optional preprocessing configuration.
        """
        self.config = config or PreprocessingConfig()
    
    def process(self, image: Image.Image) -> Image.Image:
        """
        Apply all enabled preprocessing steps to an image.
        
        Args:
            image: The input PIL Image.
            
        Returns:
            The preprocessed PIL Image.
        """
        result = image.copy()
        
        # Apply each step in order
        if self.config.apply_upscale:
            result = self.upscale(result)
        
        if self.config.apply_grayscale:
            result = self.to_grayscale(result)
        
        if self.config.apply_contrast:
            result = self.enhance_contrast(result)
        
        if self.config.apply_sharpen:
            result = self.sharpen(result)
        
        if self.config.apply_denoise:
            result = self.denoise(result)
        
        if self.config.apply_deskew:
            result = self.deskew(result)
        
        if self.config.apply_binarize:
            result = self.binarize(result)
        
        return result
    
    def upscale(self, image: Image.Image) -> Image.Image:
        """
        Upscale the image for better text recognition.
        
        Args:
            image: The input image.
            
        Returns:
            The upscaled image.
        """
        if self.config.upscale_factor <= 1.0:
            return image
        
        new_width = int(image.width * self.config.upscale_factor)
        new_height = int(image.height * self.config.upscale_factor)
        
        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    def to_grayscale(self, image: Image.Image) -> Image.Image:
        """
        Convert image to grayscale.
        
        Args:
            image: The input image.
            
        Returns:
            The grayscale image.
        """
        if image.mode == "L":
            return image
        
        return image.convert("L")
    
    def enhance_contrast(self, image: Image.Image) -> Image.Image:
        """
        Enhance image contrast using CLAHE or simple enhancement.
        
        Args:
            image: The input image.
            
        Returns:
            The contrast-enhanced image.
        """
        if CV2_AVAILABLE and image.mode == "L":
            # Use CLAHE for better results
            return self._apply_clahe(image)
        else:
            # Fall back to PIL enhancement
            enhancer = ImageEnhance.Contrast(image)
            return enhancer.enhance(self.config.contrast_factor)
    
    def _apply_clahe(self, image: Image.Image) -> Image.Image:
        """Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)."""
        if not CV2_AVAILABLE:
            return image
        
        # Convert to numpy array
        img_array = np.array(image)
        
        # Create CLAHE object
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        
        # Apply CLAHE
        enhanced = clahe.apply(img_array)
        
        return Image.fromarray(enhanced)
    
    def denoise(self, image: Image.Image) -> Image.Image:
        """
        Remove noise from the image.
        
        Args:
            image: The input image.
            
        Returns:
            The denoised image.
        """
        if CV2_AVAILABLE:
            return self._denoise_cv2(image)
        else:
            # Fall back to PIL median filter
            return image.filter(ImageFilter.MedianFilter(size=3))
    
    def _denoise_cv2(self, image: Image.Image) -> Image.Image:
        """Apply OpenCV denoising."""
        img_array = np.array(image)
        
        try:
            if len(img_array.shape) == 2:
                # Grayscale
                denoised = cv2.fastNlMeansDenoising(
                    img_array, 
                    None, 
                    h=self.config.denoise_strength
                )
            else:
                # Color - convert RGB to BGR for OpenCV
                bgr_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
                denoised_bgr = cv2.fastNlMeansDenoisingColored(
                    bgr_array, 
                    None, 
                    h=self.config.denoise_strength,
                    hForColorComponents=self.config.denoise_strength
                )
                # Convert back to RGB
                denoised = cv2.cvtColor(denoised_bgr, cv2.COLOR_BGR2RGB)
            
            return Image.fromarray(denoised)
        except Exception:
            # Fall back to PIL if OpenCV fails
            return image.filter(ImageFilter.MedianFilter(size=3))
    
    def sharpen(self, image: Image.Image) -> Image.Image:
        """
        Sharpen the image to enhance text edges.
        
        Args:
            image: The input image.
            
        Returns:
            The sharpened image.
        """
        enhancer = ImageEnhance.Sharpness(image)
        return enhancer.enhance(self.config.sharpen_factor)
    
    def binarize(self, image: Image.Image) -> Image.Image:
        """
        Convert image to binary (black and white) using thresholding.
        
        Args:
            image: The input image.
            
        Returns:
            The binarized image.
        """
        # Ensure grayscale
        if image.mode != "L":
            image = image.convert("L")
        
        if CV2_AVAILABLE:
            return self._binarize_otsu(image)
        else:
            # Simple threshold
            threshold = self.config.binarize_threshold or 128
            return image.point(lambda p: 255 if p > threshold else 0)
    
    def _binarize_otsu(self, image: Image.Image) -> Image.Image:
        """Apply Otsu's binarization method."""
        img_array = np.array(image)
        
        if self.config.binarize_threshold > 0:
            # Use specified threshold
            _, binary = cv2.threshold(
                img_array, 
                self.config.binarize_threshold, 
                255, 
                cv2.THRESH_BINARY
            )
        else:
            # Use Otsu's method for automatic threshold
            _, binary = cv2.threshold(
                img_array, 
                0, 
                255, 
                cv2.THRESH_BINARY + cv2.THRESH_OTSU
            )
        
        return Image.fromarray(binary)
    
    def deskew(self, image: Image.Image) -> Image.Image:
        """
        Correct image rotation/skew.
        
        Args:
            image: The input image.
            
        Returns:
            The deskewed image.
        """
        if not CV2_AVAILABLE:
            return image
        
        # Convert to numpy array
        img_array = np.array(image)
        
        # Ensure grayscale for analysis
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array
        
        # Detect skew angle
        angle = self._detect_skew_angle(gray)
        
        # Only rotate if skew is significant
        if abs(angle) < 0.5:
            return image
        
        # Rotate to correct skew
        return image.rotate(angle, expand=True, fillcolor="white")
    
    def _detect_skew_angle(self, gray: np.ndarray) -> float:
        """
        Detect the skew angle of text in an image.
        
        Args:
            gray: Grayscale numpy array.
            
        Returns:
            The detected skew angle in degrees.
        """
        # Apply edge detection
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        
        # Detect lines using Hough transform
        lines = cv2.HoughLinesP(
            edges,
            rho=1,
            theta=np.pi / 180,
            threshold=100,
            minLineLength=100,
            maxLineGap=10
        )
        
        if lines is None or len(lines) == 0:
            return 0.0
        
        # Calculate angles of detected lines
        angles = []
        for line in lines:
            x1, y1, x2, y2 = line[0]
            if x2 - x1 != 0:
                angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
                # Only consider near-horizontal lines
                if abs(angle) < 45:
                    angles.append(angle)
        
        if not angles:
            return 0.0
        
        # Return median angle
        return float(np.median(angles))
    
    def get_optimal_config_for_image(self, image: Image.Image) -> PreprocessingConfig:
        """
        Analyze an image and return optimal preprocessing configuration.
        
        Args:
            image: The input image to analyze.
            
        Returns:
            Optimized PreprocessingConfig for this image.
        """
        config = PreprocessingConfig()
        
        # Analyze image properties
        width, height = image.size
        
        # Adjust upscaling based on image size
        if width < 800 or height < 600:
            config.upscale_factor = 2.0
        elif width < 1200 or height < 900:
            config.upscale_factor = 1.5
        else:
            config.apply_upscale = False
        
        # Check if image is already grayscale
        if image.mode == "L":
            config.apply_grayscale = False
        
        # Analyze contrast
        if image.mode != "L":
            gray = image.convert("L")
        else:
            gray = image
        
        # Calculate histogram to determine contrast needs
        histogram = gray.histogram()
        pixels = sum(histogram)
        
        # Check distribution
        low_pixels = sum(histogram[:64]) / pixels
        high_pixels = sum(histogram[192:]) / pixels
        
        if low_pixels > 0.4 or high_pixels > 0.4:
            # High contrast already
            config.contrast_factor = 1.2
        else:
            # Low contrast, increase enhancement
            config.contrast_factor = 1.8
        
        return config
