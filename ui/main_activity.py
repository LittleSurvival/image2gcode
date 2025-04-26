import os
import sys
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QFileDialog, QMessageBox,
    QGroupBox, QFormLayout, QSpinBox, QDoubleSpinBox, QCheckBox,
    QLineEdit, QComboBox, QPlainTextEdit, QProgressBar, QToolButton, QStyle
)
from PyQt5.QtGui import QPixmap, QFont, QIcon

from modules.image_loader import ImageLoader
from modules.image_converter import ImageConverter
from modules.svg_path_converter import SVGPathConverter
from modules.gcode_generator import GcodeGenerator
from modules.setting_manager import SettingsManager

class ConversionThread(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, image_path, output_name, settings_manager):
        super().__init__()
        self.image_path = image_path
        self.output_name = output_name
        self.settings_manager = settings_manager

    def run(self):
        try:
            image_converter = ImageConverter(self.settings_manager)
            svg_converter = SVGPathConverter()
            gcode_generator = GcodeGenerator(self.settings_manager)

            svg_path = os.path.join("output", f"{self.output_name}.svg")
            gcode_path = os.path.join("output", f"{self.output_name}.gcode")

            if not os.path.exists("output"):
                os.makedirs("output", exist_ok=True)

            image_converter.convert_to_svg(self.image_path, svg_path)
            svg_path = svg_converter.process_svg(svg_path)
            gcode_generator.convert_to_gcode(svg_path, gcode_path)

            self.finished.emit(gcode_path)
        except Exception as e:
            self.error.emit(str(e))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setFont(QFont("Arial", 10))
        self.settings_manager = SettingsManager()
        self.current_image_path = None

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Image2Gcode Converter")
        self.setGeometry(100, 100, 1200, 700)

        main_widget = QWidget(self)
        main_layout = QHBoxLayout(main_widget)
        self.setCentralWidget(main_widget)

        # Left side: image preview and controls
        left_layout = QVBoxLayout()

        self.image_label = QLabel("Drop an image or click 'Load Image'", self)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("border: 2px dashed #aaa;")
        self.image_label.setFixedSize(400, 400)

        load_btn = QPushButton("Load Image")
        load_btn.clicked.connect(self.browse_image)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.progress_bar.hide()

        self.convert_btn = QPushButton("Convert to G-code")
        self.convert_btn.clicked.connect(self.convert_image)
        self.convert_btn.setEnabled(False)

        left_layout.addWidget(self.image_label)
        left_layout.addWidget(load_btn)
        left_layout.addWidget(self.progress_bar)
        left_layout.addWidget(self.convert_btn)

        # Right side: settings and preview
        right_layout = QVBoxLayout()

        settings_group = QGroupBox("Settings", self)
        form_layout = QFormLayout()

        # Helper to create info icon
        def info_button(text):
            btn = QToolButton(self)
            btn.setIcon(self.style().standardIcon(QStyle.SP_MessageBoxInformation))
            btn.setToolTip(text)
            btn.setAutoRaise(True)
            btn.setEnabled(False)
            return btn

        # SVG Conversion Mode
        self.svg_mode_combo = QComboBox(self)
        self.svg_mode_combo.addItems(["contour", "threshold", "canny"])
        self.svg_mode_combo.setCurrentText(self.settings_manager.get("svg_mode"))
        self.svg_mode_combo.currentTextChanged.connect(self.auto_save)
        h_mode = QWidget()
        hlm = QHBoxLayout(h_mode); hlm.setContentsMargins(0,0,0,0)
        hlm.addWidget(self.svg_mode_combo)
        hlm.addWidget(info_button("Select contour tracing, binary threshold, or Canny edge detection mode."))
        form_layout.addRow("SVG Mode:", h_mode)

        # Threshold
        self.threshold_spin = QSpinBox(self)
        self.threshold_spin.setRange(0, 255)
        self.threshold_spin.setValue(self.settings_manager.get("threshold"))
        self.threshold_spin.valueChanged.connect(self.auto_save)
        h_thr = QWidget(); hl2 = QHBoxLayout(h_thr); hl2.setContentsMargins(0,0,0,0)
        hl2.addWidget(self.threshold_spin)
        hl2.addWidget(info_button("Threshold value for binary conversion."))
        form_layout.addRow("Threshold:", h_thr)

        # Blur kernel size
        self.blur_spin = QSpinBox(self)
        self.blur_spin.setRange(1, 21); self.blur_spin.setSingleStep(2)
        self.blur_spin.setValue(self.settings_manager.get("blur_ksize"))
        self.blur_spin.valueChanged.connect(self.auto_save)
        h_blur = QWidget(); hl3 = QHBoxLayout(h_blur); hl3.setContentsMargins(0,0,0,0)
        hl3.addWidget(self.blur_spin)
        hl3.addWidget(info_button("Odd-sized Gaussian blur kernel to reduce noise."))
        form_layout.addRow("Blur Kernel (odd):", h_blur)

        # Canny low/high
        self.canny_low_spin = QSpinBox(self)
        self.canny_low_spin.setRange(0, 500)
        self.canny_low_spin.setValue(self.settings_manager.get("canny_low"))
        self.canny_low_spin.valueChanged.connect(self.auto_save)
        h_cl = QWidget(); hl4 = QHBoxLayout(h_cl); hl4.setContentsMargins(0,0,0,0)
        hl4.addWidget(self.canny_low_spin)
        hl4.addWidget(info_button("Lower threshold for Canny edge detector."))
        form_layout.addRow("Canny Low:", h_cl)

        self.canny_high_spin = QSpinBox(self)
        self.canny_high_spin.setRange(0, 500)
        self.canny_high_spin.setValue(self.settings_manager.get("canny_high"))
        self.canny_high_spin.valueChanged.connect(self.auto_save)
        h_ch = QWidget(); hl5 = QHBoxLayout(h_ch); hl5.setContentsMargins(0,0,0,0)
        hl5.addWidget(self.canny_high_spin)
        hl5.addWidget(info_button("Upper threshold for Canny edge detector."))
        form_layout.addRow("Canny High:", h_ch)

        # Potrace parameters
        self.turdsize_spin = QSpinBox(self)
        self.turdsize_spin.setRange(0, 100)
        self.turdsize_spin.setValue(self.settings_manager.get("potrace_turdsize"))
        self.turdsize_spin.valueChanged.connect(self.auto_save)
        h_ts = QWidget(); hl6 = QHBoxLayout(h_ts); hl6.setContentsMargins(0,0,0,0)
        hl6.addWidget(self.turdsize_spin)
        hl6.addWidget(info_button("Remove small artifacts under this size."))
        form_layout.addRow("Potrace Turdsize:", h_ts)

        self.alphamax_spin = QDoubleSpinBox(self)
        self.alphamax_spin.setRange(0.0, 1.0); self.alphamax_spin.setSingleStep(0.1)
        self.alphamax_spin.setValue(self.settings_manager.get("potrace_alphamax"))
        self.alphamax_spin.valueChanged.connect(self.auto_save)
        h_am = QWidget(); hl7 = QHBoxLayout(h_am); hl7.setContentsMargins(0,0,0,0)
        hl7.addWidget(self.alphamax_spin)
        hl7.addWidget(info_button("Curve smoothing parameter."))
        form_layout.addRow("Potrace AlphaMax:", h_am)

        # G-code tool commands
        self.tool_on_edit = QLineEdit(self); self.tool_on_edit.setText(self.settings_manager.get("tool_on_cmd"))
        self.tool_on_edit.textChanged.connect(self.auto_save)
        h_to = QWidget(); hl8 = QHBoxLayout(h_to); hl8.setContentsMargins(0,0,0,0)
        hl8.addWidget(self.tool_on_edit)
        hl8.addWidget(info_button("G-code command to turn tool on (e.g. M3)."))
        form_layout.addRow("Tool ON Command:", h_to)

        self.tool_off_edit = QLineEdit(self); self.tool_off_edit.setText(self.settings_manager.get("tool_off_cmd"))
        self.tool_off_edit.textChanged.connect(self.auto_save)
        h_tf = QWidget(); hl9 = QHBoxLayout(h_tf); hl9.setContentsMargins(0,0,0,0)
        hl9.addWidget(self.tool_off_edit)
        hl9.addWidget(info_button("G-code command to turn tool off (e.g. M5)."))
        form_layout.addRow("Tool OFF Command:", h_tf)

        self.output_name_edit = QLineEdit(self); self.output_name_edit.setText(self.settings_manager.get("output_filename"))
        self.output_name_edit.textChanged.connect(self.auto_save)
        h_on = QWidget(); hl10 = QHBoxLayout(h_on); hl10.setContentsMargins(0,0,0,0)
        hl10.addWidget(self.output_name_edit)
        hl10.addWidget(info_button("Base filename for G-code output."))
        form_layout.addRow("Output Filename:", h_on)

        settings_group.setLayout(form_layout)
        right_layout.addWidget(settings_group)

        self.gcode_preview = QPlainTextEdit(self)
        self.gcode_preview.setReadOnly(True)
        self.gcode_preview.setFont(QFont("Courier New"))
        self.gcode_preview.setPlaceholderText("G-code preview will appear here…")
        right_layout.addWidget(self.gcode_preview)

        main_layout.addLayout(left_layout)
        main_layout.addLayout(right_layout)

        self.setAcceptDrops(True)
        self.apply_styles()

    def apply_styles(self):
        self.setStyleSheet("""
            QWidget { background-color: #F3E5F5; }
            QLabel { color: #4A148C; font: 10pt 'Arial'; }
            QPushButton {
              background-color: #CE93D8; color: #FFFFFF;
              border-radius: 8px; padding: 8px 16px;
              font-weight: bold;
            }
            QPushButton:hover { background-color: #BA68C8; }
            QLineEdit, QSpinBox, QDoubleSpinBox {
              background: #FFFFFF; border: 1px solid #B39DDB;
              border-radius: 4px; padding: 4px;
            }
            QGroupBox {
              border: 1px solid #B39DDB; border-radius: 6px;
              margin-top: 1em; padding: 1em; color: #4A148C;
            }
            QGroupBox::title {
              subcontrol-origin: margin; left: 10px; padding: 0 3px;
            }
            QProgressBar {
              border: 2px solid rgba(33,37,43,0.7);
              border-radius: 10px; text-align: center;
              background-color: rgba(33,37,43,0.2);
              color: #4A148C; height: 20px;
            }
            QProgressBar::chunk {
              background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                stop:0 #CE93D8, stop:1 #BA68C8);
              border-radius: 10px;
            }
            QPlainTextEdit {
              background: #FFFFFF; border: 1px solid #B39DDB;
              border-radius: 4px; font-family: 'Courier New'; font-size: 10pt;
            }
        """)

    def browse_image(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Image", "",
            "Images (*.png *.jpg *.jpeg *.bmp *.gif *.tiff);;All Files (*)",
            options=options
        )
        if file_path:
            self.load_image(file_path)

    def load_image(self, file_path):
        try:
            ImageLoader.load_image(file_path)
            self.current_image_path = file_path
            # Set the name of output to input image basename without extension.
            self.output_name_edit.setText(os.path.splitext(os.path.basename(file_path))[0])
            pixmap = QPixmap(file_path)
            pixmap = pixmap.scaled(self.image_label.size(),
                                   Qt.KeepAspectRatio,
                                   Qt.SmoothTransformation)
            self.image_label.setPixmap(pixmap)
            self.convert_btn.setEnabled(True)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            url = event.mimeData().urls()[0]
            if url.isLocalFile() and ImageLoader.is_supported(url.toLocalFile()):
                event.acceptProposedAction()

    def dropEvent(self, event):
        url = event.mimeData().urls()[0]
        if url.isLocalFile():
            self.load_image(url.toLocalFile())

    def auto_save(self, *args):
        # Auto-save settings on any change
        self.settings_manager.set("svg_mode", self.svg_mode_combo.currentText())
        self.settings_manager.set("threshold", self.threshold_spin.value())
        self.settings_manager.set("blur_ksize", self.blur_spin.value())
        self.settings_manager.set("canny_low", self.canny_low_spin.value())
        self.settings_manager.set("canny_high", self.canny_high_spin.value())
        self.settings_manager.set("potrace_turdsize", self.turdsize_spin.value())
        self.settings_manager.set("potrace_alphamax", self.alphamax_spin.value())
        self.settings_manager.set("tool_on_cmd", self.tool_on_edit.text())
        self.settings_manager.set("tool_off_cmd", self.tool_off_edit.text())
        self.settings_manager.set("output_filename", self.output_name_edit.text())

    def convert_image(self):
        if not self.current_image_path:
            QMessageBox.warning(self, "No Image", "Please load an image first.")
            return
        output_name = self.output_name_edit.text().strip()
        if not output_name:
            QMessageBox.warning(self, "No Output Name", "Please specify an output filename.")
            return

        self.progress_bar.show()
        self.convert_btn.setEnabled(False)

        self.thread = ConversionThread(self.current_image_path, output_name, self.settings_manager)
        self.thread.finished.connect(self.on_conversion_finished)
        self.thread.error.connect(self.on_conversion_error)
        self.thread.start()

    def on_conversion_finished(self, gcode_path):
        self.progress_bar.hide()
        QMessageBox.information(self, "Success", f"G-code saved to:\n{gcode_path}")
        try:
            with open(gcode_path, 'r') as f:
                preview = "".join(f.readlines()[:100])
            self.gcode_preview.setPlainText(preview)
        except Exception as e:
            QMessageBox.warning(self, "Preview Error", f"Could not load preview: {e}")
        self.convert_btn.setEnabled(True)

    def on_conversion_error(self, error_msg):
        self.progress_bar.hide()
        QMessageBox.critical(self, "Conversion Error", error_msg)
        self.convert_btn.setEnabled(True)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())