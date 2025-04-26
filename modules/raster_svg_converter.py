import os
import cv2

class RasterSVGConverter:
    def __init__(self, settings_manager):
        self.mode       = settings_manager.get("svg_mode")
        self.thresh     = settings_manager.get("threshold")
        self.blur_ksize = settings_manager.get("blur_ksize")
        self.canny_low  = settings_manager.get("canny_low")
        self.canny_high = settings_manager.get("canny_high")

    def convert_to_svg(self, image_path: str, svg_path: str):
        out_dir = os.path.dirname(svg_path)
        if out_dir and not os.path.exists(out_dir):
            os.makedirs(out_dir, exist_ok=True)

        img  = cv2.imread(image_path, cv2.IMREAD_COLOR)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (self.blur_ksize, self.blur_ksize), 0)

        if self.mode == 'canny':
            mask = cv2.Canny(blur, self.canny_low, self.canny_high)
        else:
            _, bin_img = cv2.threshold(blur, self.thresh, 255, cv2.THRESH_BINARY)
            mask = bin_img if self.mode == 'threshold' else cv2.bitwise_not(bin_img)

        contours, _ = cv2.findContours(mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        h, w = mask.shape

        with open(svg_path, 'w') as f:
            f.write(f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}">')
            for cnt in contours:
                if cv2.contourArea(cnt) < 5:
                    continue
                pts = cnt.reshape(-1, 2)
                d = 'M ' + ' L '.join(f'{x},{y}' for x, y in pts) + ' Z'
                f.write(f'<path d="{d}" stroke="black" fill="none"/>')
            f.write('</svg>')