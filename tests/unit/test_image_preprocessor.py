"""Unit tests for image preprocessor module."""

import numpy as np
import pytest
from PIL import Image


class TestPreprocessingConfig:
    """Tests for PreprocessingConfig dataclass."""
    
    def test_default_config(self):
        """Test default configuration values."""
        from src.ocr.image_preprocessor import PreprocessingConfig
        
        config = PreprocessingConfig()
        
        assert config.upscale_factor == 2.0
        assert config.contrast_factor == 1.5
        assert config.apply_upscale is True
        assert config.apply_grayscale is True
    
    def test_custom_config(self):
        """Test custom configuration."""
        from src.ocr.image_preprocessor import PreprocessingConfig
        
        config = PreprocessingConfig(
            upscale_factor=3.0,
            apply_binarize=True,
            apply_deskew=False
        )
        
        assert config.upscale_factor == 3.0
        assert config.apply_binarize is True
        assert config.apply_deskew is False


class TestImagePreprocessor:
    """Tests for ImagePreprocessor class."""
    
    def test_preprocessor_init_default(self):
        """Test default initialization."""
        from src.ocr.image_preprocessor import ImagePreprocessor
        
        preprocessor = ImagePreprocessor()
        assert preprocessor.config is not None
    
    def test_preprocessor_init_custom_config(self):
        """Test initialization with custom config."""
        from src.ocr.image_preprocessor import ImagePreprocessor, PreprocessingConfig
        
        config = PreprocessingConfig(upscale_factor=1.5)
        preprocessor = ImagePreprocessor(config)
        
        assert preprocessor.config.upscale_factor == 1.5
    
    def test_upscale_image(self, small_image):
        """Test image upscaling."""
        from src.ocr.image_preprocessor import ImagePreprocessor, PreprocessingConfig
        
        config = PreprocessingConfig(upscale_factor=2.0)
        preprocessor = ImagePreprocessor(config)
        
        result = preprocessor.upscale(small_image)
        
        assert result.width == small_image.width * 2
        assert result.height == small_image.height * 2
    
    def test_upscale_no_change_when_factor_1(self, sample_image):
        """Test that upscale factor 1.0 doesn't change image."""
        from src.ocr.image_preprocessor import ImagePreprocessor, PreprocessingConfig
        
        config = PreprocessingConfig(upscale_factor=1.0)
        preprocessor = ImagePreprocessor(config)
        
        result = preprocessor.upscale(sample_image)
        
        assert result.size == sample_image.size
    
    def test_to_grayscale(self, sample_image):
        """Test grayscale conversion."""
        from src.ocr.image_preprocessor import ImagePreprocessor
        
        preprocessor = ImagePreprocessor()
        result = preprocessor.to_grayscale(sample_image)
        
        assert result.mode == "L"
    
    def test_to_grayscale_already_gray(self, grayscale_image):
        """Test grayscale conversion on already gray image."""
        from src.ocr.image_preprocessor import ImagePreprocessor
        
        preprocessor = ImagePreprocessor()
        result = preprocessor.to_grayscale(grayscale_image)
        
        assert result.mode == "L"
        assert result.size == grayscale_image.size
    
    def test_enhance_contrast(self, sample_image):
        """Test contrast enhancement."""
        from src.ocr.image_preprocessor import ImagePreprocessor
        
        preprocessor = ImagePreprocessor()
        result = preprocessor.enhance_contrast(sample_image)
        
        assert result is not None
        assert result.size == sample_image.size
    
    def test_sharpen(self, sample_image):
        """Test image sharpening."""
        from src.ocr.image_preprocessor import ImagePreprocessor
        
        preprocessor = ImagePreprocessor()
        result = preprocessor.sharpen(sample_image)
        
        assert result is not None
        assert result.size == sample_image.size
    
    def test_denoise(self, sample_image):
        """Test image denoising."""
        from src.ocr.image_preprocessor import ImagePreprocessor
        
        preprocessor = ImagePreprocessor()
        result = preprocessor.denoise(sample_image)
        
        assert result is not None
        assert result.size == sample_image.size
    
    def test_binarize(self, grayscale_image):
        """Test image binarization."""
        from src.ocr.image_preprocessor import ImagePreprocessor
        
        preprocessor = ImagePreprocessor()
        result = preprocessor.binarize(grayscale_image)
        
        assert result is not None
        assert result.mode == "L"
        
        # Check that pixels are only black or white
        pixels = list(result.getdata())
        unique_values = set(pixels)
        assert unique_values.issubset({0, 255})
    
    def test_full_process_pipeline(self, sample_image):
        """Test the full preprocessing pipeline."""
        from src.ocr.image_preprocessor import ImagePreprocessor, PreprocessingConfig
        
        config = PreprocessingConfig(
            apply_upscale=True,
            apply_grayscale=True,
            apply_contrast=True,
            apply_sharpen=True,
            apply_denoise=True,
            apply_deskew=False,  # Disable deskew for simple test
            apply_binarize=False
        )
        preprocessor = ImagePreprocessor(config)
        
        result = preprocessor.process(sample_image)
        
        assert result is not None
        assert result.mode == "L"  # Should be grayscale
    
    def test_process_preserves_mode_when_grayscale_disabled(self, sample_image):
        """Test that mode is preserved when grayscale is disabled."""
        from src.ocr.image_preprocessor import ImagePreprocessor, PreprocessingConfig
        
        config = PreprocessingConfig(
            apply_upscale=False,
            apply_grayscale=False,
            apply_contrast=True,
            apply_sharpen=False,
            apply_denoise=False,
            apply_deskew=False,
            apply_binarize=False
        )
        preprocessor = ImagePreprocessor(config)
        
        result = preprocessor.process(sample_image)
        
        assert result.mode == sample_image.mode
    
    def test_get_optimal_config_small_image(self, small_image):
        """Test optimal config generation for small images."""
        from src.ocr.image_preprocessor import ImagePreprocessor
        
        preprocessor = ImagePreprocessor()
        config = preprocessor.get_optimal_config_for_image(small_image)
        
        # Small images should have higher upscale factor
        assert config.upscale_factor >= 1.5
    
    def test_get_optimal_config_large_image(self):
        """Test optimal config generation for large images."""
        from src.ocr.image_preprocessor import ImagePreprocessor
        
        large_image = Image.new("RGB", (2000, 1500), color=(255, 255, 255))
        
        preprocessor = ImagePreprocessor()
        config = preprocessor.get_optimal_config_for_image(large_image)
        
        # Large images should not be upscaled
        assert config.apply_upscale is False


class TestDeskewing:
    """Tests for deskew functionality."""
    
    @pytest.mark.skip(reason="Requires OpenCV")
    def test_deskew_rotated_image(self):
        """Test deskewing a rotated image."""
        from src.ocr.image_preprocessor import ImagePreprocessor
        
        # Create a slightly rotated image
        img = Image.new("RGB", (400, 300), color=(255, 255, 255))
        rotated = img.rotate(5, expand=True)
        
        preprocessor = ImagePreprocessor()
        result = preprocessor.deskew(rotated)
        
        assert result is not None
    
    def test_deskew_straight_image(self, sample_image):
        """Test deskew on already straight image."""
        from src.ocr.image_preprocessor import ImagePreprocessor
        
        preprocessor = ImagePreprocessor()
        result = preprocessor.deskew(sample_image)
        
        # Should return similar dimensions
        assert abs(result.width - sample_image.width) < 10
