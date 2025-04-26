from .raster_svg_converter import RasterSVGConverter

class ImageConverter:
    """
    影像→SVG 的前置轉換器，整合 RasterSVGConverter。
    """
    def __init__(self, settings_manager):
        self.settings = settings_manager
        self.converter = RasterSVGConverter(self.settings)

    def convert_to_svg(self, image_path: str, svg_path: str):
        try:
            self.converter.convert_to_svg(image_path, svg_path)
        except Exception as e:
            raise RuntimeError(f"Image to SVG conversion failed: {e}")