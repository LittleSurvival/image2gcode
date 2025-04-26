import subprocess
import os

class GcodeGenerator:
    """
    Generates G-code from an SVG using the Rust svg2gcode CLI.
    """
    def __init__(self, settings_manager):
        self.settings = settings_manager

    def convert_to_gcode(self, svg_path: str, gcode_path: str):
        out_dir = os.path.dirname(gcode_path)
        if out_dir and not os.path.exists(out_dir):
            os.makedirs(out_dir, exist_ok=True)

        tool_on  = self.settings.get("tool_on_cmd")
        tool_off = self.settings.get("tool_off_cmd")

        cmd = [
            "svg2gcode",
            svg_path,
            "--off", tool_off,
            "--on",  tool_on,
            "-o",    gcode_path
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
        except FileNotFoundError:
            raise RuntimeError("svg2gcode CLI not found — make sure it's installed and on your PATH")
        
        # the svg2gcode api doesnt include the feature of adding end command, we do it manually
        try:
            with open(gcode_path, "a") as gcode:
                gcode.write("M2; End\n")
        except Exception as err:
            raise RuntimeError(f"Failed to append M2 command to G-code file:\n{err}")

        if result.returncode != 0:
            raise RuntimeError(f"svg2gcode failed:\n{result.stderr.strip()}")