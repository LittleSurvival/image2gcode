import os
from PIL import Image

class ImageLoader:
    """
    Handles loading and validation of image files.
    """
    SUPPORTED_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff')

    @staticmethod
    def is_supported(file_path):
        """
        Check if the file is an image of supported type.
        """
        ext = os.path.splitext(file_path)[1].lower()
        return ext in ImageLoader.SUPPORTED_EXTENSIONS

    @staticmethod
    def load_image(file_path):
        """
        Validate and open an image file using PIL.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Image file not found: {file_path}")
        if not ImageLoader.is_supported(file_path):
            raise ValueError(f"Unsupported file type: {file_path}")
        try:
            img = Image.open(file_path)
            img.verify()  # Verify that it's an image
        except Exception as e:
            raise ValueError(f"Failed to load image: {e}")
        # Re-open after verify because verify() might close the file
        img = Image.open(file_path)
        return img