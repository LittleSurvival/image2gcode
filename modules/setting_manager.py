import yaml
import os

class SettingsManager:
    def __init__(self, config_path="config.yaml"):
        self.config_path = config_path
        self.defaults = {
            "color_tolerance": 1,
            "remove_background": False,
            "background_tolerance": 1.0,
            "max_artifact_size": 0.02,
            "group_by_color": True,
            "tool_on_cmd": "M3",
            "tool_off_cmd": "M5",
            "output_filename": "output",
            "svg_mode": "contour",
            "threshold": 128,
            "blur_ksize": 3,
            "canny_low": 50,
            "canny_high": 150,
            "potrace_turdsize": 2,
            "potrace_alphamax": 1.0
        }
        self.settings = {}
        self.load_settings()

    def load_settings(self):
        if not os.path.exists(self.config_path):
            self.settings = self.defaults.copy()
            self.save_settings()
        else:
            with open(self.config_path, 'r') as f:
                data = yaml.safe_load(f) or {}
            for k,v in self.defaults.items():
                self.settings[k] = data.get(k, v)
            self.save_settings()

    def save_settings(self):
        with open(self.config_path, 'w') as f:
            yaml.dump(self.settings, f)

    def get(self, key):
        return self.settings.get(key)

    def set(self, key, value):
        self.settings[key] = value
        self.save_settings()