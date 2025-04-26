# Image2Gcode

**Image2Gcode** is a desktop application that converts raster images into G-code for CNC machines or laser engravers. It provides a user-friendly PyQt5 GUI with adjustable settings, performing image-to-SVG conversion using [pixels2svg](https://pypi.org/project/pixels2svg/) and SVG-to-Gcode conversion via the [svg2gcode](https://pypi.org/project/svg2gcode/) tool.

## Features

- Drag-and-drop or file dialog to select images (PNG, JPG, BMP, etc.).
- Conversion of image to SVG (polygon outlines of pixel groups).
- Conversion of SVG to G-code for CNC/laser using svg2gcode.
- Settings panel to adjust:
  - Color tolerance for pixel grouping.
  - Background removal options.
  - Group shapes by color on output SVG.
  - Custom G-code tool ON/OFF commands (M3/M5 by default).
  - Default output filename.
- Persistent settings saved in `config.yaml`.
- Async processing to prevent UI freezing.
- Error handling with user-friendly alerts.

## Prerequisites

- Python 3.7 or higher
- [Docker](https://www.docker.com/) (if using the Docker container)

## Installation

### Local

1. **Install Rust and Cargo:** This project uses `svg2gcode-cli` which requires Rust's package manager, Cargo. Install Rust (which includes Cargo) by following the official instructions at [https://doc.rust-lang.org/cargo/getting-started/installation.html](https://doc.rust-lang.org/cargo/getting-started/installation.html).
2. **Clone the repository:** `git clone <repository_url>` or download the source code.
3. **(Optional) Create and activate a Python virtual environment:**
   ```bash
   python -m venv venv
   # On Linux/macOS:
   source venv/bin/activate
   # On Windows:
   .\venv\Scripts\activate
   ```
4. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
5. **Install the SVG to G-code converter:**
   ```bash
   cargo install svg2gcode-cli
   ```
6. **Ensure the `output/` directory exists:** The application will attempt to create it automatically on the first run if it's missing.

### Docker

1. Clone the repository or copy the source code into a directory.
2. Build the Docker image: docker build -t image2gcode
3. Run the container (with X11 for GUI support):
docker run -it --rm
-e DISPLAY=$DISPLAY
-v /tmp/.X11-unix:/tmp/.X11-unix
-v $(pwd)/output:/app/output
image2gcode

*Note: You may need to allow X11 connections with `xhost +local:docker`.*

## Usage

1. Launch the application:
- Locally: `python app.py`
- Docker: as shown above.
2. In the GUI, load an image via drag-and-drop or the **Load Image** button.
3. Adjust settings in the **Settings** panel as needed.
4. Specify an output filename (default comes from settings).
5. Click **Convert to G-code**. The G-code will be saved in the `output/` directory.
6. Use the generated `.gcode` file with your CNC or laser software.

## Project Structure


## Notes

- Ensure `pixels2svg` and `svg2gcode` are compatible with your images. Large images may produce large SVG/G-code files.
- The default tool ON/OFF commands assume a laser (M3/M5). Adjust in settings if your machine uses different commands.
- If the application cannot find `svg2gcode`, ensure it's installed (`pip install svg2gcode`) or use the Docker image which has it pre-installed.

## License

This project is open-source and available under the MIT License.