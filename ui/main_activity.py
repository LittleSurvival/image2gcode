import os
import sys
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QFileDialog, QMessageBox,
    QGroupBox, QFormLayout, QSpinBox, QDoubleSpinBox,
    QLineEdit, QComboBox, QPlainTextEdit, QProgressBar,
    QToolButton, QStyle, QStackedLayout, QButtonGroup, QScrollArea
)
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtSvg import QSvgWidget

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

            os.makedirs("output", exist_ok=True)

            image_converter.convert_to_svg(self.image_path, svg_path)
            svg_path = svg_converter.process_svg(svg_path)
            gcode_generator.convert_to_gcode(svg_path, gcode_path)

            self.finished.emit(gcode_path)
        except Exception as exc:
            self.error.emit(str(exc))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setFont(QFont("Arial", 10))
        self.settings_manager = SettingsManager()
        self.current_image_path = None
        self.last_svg_path = None
        self.last_gcode_path = None

        self.build_ui()

    def build_ui(self):
        self.setWindowTitle("Image2Gcode Converter")
        self.resize(1200, 700)

        root_widget = QWidget()
        self.setCentralWidget(root_widget)

        main_layout = QHBoxLayout(root_widget)

        # ── left panel ──
        left_panel_layout = QVBoxLayout()

        self.image_label = QLabel("Drop an image or click 'Load Image'")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("border: 2px dashed #aaa;")
        self.image_label.setFixedSize(400, 400)

        load_button = QPushButton("Load Image")
        load_button.clicked.connect(self.browse_image)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.hide()

        self.convert_button = QPushButton("Convert to G-code")
        self.convert_button.setEnabled(False)
        self.convert_button.clicked.connect(self.convert_image)

        left_panel_layout.addWidget(self.image_label)
        left_panel_layout.addWidget(load_button)
        left_panel_layout.addWidget(self.progress_bar)
        left_panel_layout.addWidget(self.convert_button)

        # ── right panel ──
        right_panel_layout = QVBoxLayout()

        settings_group = QGroupBox("Settings")
        form_layout = QFormLayout()

        def info_icon(tip: str) -> QToolButton:
            icon_button = QToolButton()
            icon_button.setIcon(self.style().standardIcon(QStyle.SP_MessageBoxInformation))
            icon_button.setToolTip(tip)
            icon_button.setAutoRaise(True)
            icon_button.setEnabled(False)
            return icon_button

        # SVG mode
        self.svg_mode_combo = QComboBox()
        self.svg_mode_combo.addItems(["contour", "threshold", "canny"])
        self.svg_mode_combo.setCurrentText(self.settings_manager.get("svg_mode"))
        self.svg_mode_combo.currentTextChanged.connect(self.save_settings)

        svg_mode_row = QWidget()
        svg_mode_row_layout = QHBoxLayout(svg_mode_row)
        svg_mode_row_layout.setContentsMargins(0, 0, 0, 0)
        svg_mode_row_layout.addWidget(self.svg_mode_combo)
        svg_mode_row_layout.addWidget(info_icon("Select contour tracing, binary threshold, or Canny edge detection mode."))
        form_layout.addRow("SVG Mode:", svg_mode_row)

        # Threshold
        self.threshold_spin = QSpinBox()
        self.threshold_spin.setRange(0, 255)
        self.threshold_spin.setValue(self.settings_manager.get("threshold"))
        self.threshold_spin.valueChanged.connect(self.save_settings)
        form_layout.addRow("Threshold:", self.threshold_spin)

        # Blur kernel
        self.blur_spin = QSpinBox()
        self.blur_spin.setRange(1, 21)
        self.blur_spin.setSingleStep(2)
        self.blur_spin.setValue(self.settings_manager.get("blur_ksize"))
        self.blur_spin.valueChanged.connect(self.save_settings)
        form_layout.addRow("Blur Kernel (odd):", self.blur_spin)

        # Canny thresholds
        self.canny_low_spin = QSpinBox()
        self.canny_low_spin.setRange(0, 500)
        self.canny_low_spin.setValue(self.settings_manager.get("canny_low"))
        self.canny_low_spin.valueChanged.connect(self.save_settings)
        form_layout.addRow("Canny Low:", self.canny_low_spin)

        self.canny_high_spin = QSpinBox()
        self.canny_high_spin.setRange(0, 500)
        self.canny_high_spin.setValue(self.settings_manager.get("canny_high"))
        self.canny_high_spin.valueChanged.connect(self.save_settings)
        form_layout.addRow("Canny High:", self.canny_high_spin)

        # Potrace
        self.turdsize_spin = QSpinBox()
        self.turdsize_spin.setRange(0, 100)
        self.turdsize_spin.setValue(self.settings_manager.get("potrace_turdsize"))
        self.turdsize_spin.valueChanged.connect(self.save_settings)
        form_layout.addRow("Potrace Turdsize:", self.turdsize_spin)

        self.alphamax_spin = QDoubleSpinBox()
        self.alphamax_spin.setRange(0.0, 1.0)
        self.alphamax_spin.setSingleStep(0.1)
        self.alphamax_spin.setValue(self.settings_manager.get("potrace_alphamax"))
        self.alphamax_spin.valueChanged.connect(self.save_settings)
        form_layout.addRow("Potrace AlphaMax:", self.alphamax_spin)

        # Tool commands
        self.tool_on_edit = QLineEdit(self.settings_manager.get("tool_on_cmd"))
        self.tool_on_edit.textChanged.connect(self.save_settings)
        form_layout.addRow("Tool ON Command:", self.tool_on_edit)

        self.tool_off_edit = QLineEdit(self.settings_manager.get("tool_off_cmd"))
        self.tool_off_edit.textChanged.connect(self.save_settings)
        form_layout.addRow("Tool OFF Command:", self.tool_off_edit)

        # Output name
        self.output_name_edit = QLineEdit(self.settings_manager.get("output_filename"))
        self.output_name_edit.textChanged.connect(self.save_settings)
        form_layout.addRow("Output Filename:", self.output_name_edit)

        settings_group.setLayout(form_layout)
        right_panel_layout.addWidget(settings_group)

        # ── selector buttons ──
        selector_bar = QWidget()
        selector_layout = QHBoxLayout(selector_bar)
        selector_layout.setContentsMargins(0, 0, 0, 0)

        self.svg_button = QPushButton("SVG")
        self.code_button = QPushButton("CODE")

        for toggle in (self.svg_button, self.code_button):
            toggle.setCheckable(True)
            toggle.setObjectName("toggleButton")
            toggle.setMinimumWidth(80)

        self.code_button.setChecked(True)

        self.toggle_group = QButtonGroup()
        self.toggle_group.setExclusive(True)
        self.toggle_group.addButton(self.svg_button)
        self.toggle_group.addButton(self.code_button)
        self.toggle_group.buttonClicked.connect(self.update_preview)

        selector_layout.addWidget(self.svg_button)
        selector_layout.addWidget(self.code_button)
        selector_layout.addStretch()
        right_panel_layout.addWidget(selector_bar)

        # ── preview stack ──
        self.svg_widget = QSvgWidget()

        svg_scroll_area = QScrollArea()
        svg_scroll_area.setWidgetResizable(True)
        svg_scroll_area.setWidget(self.svg_widget)

        self.code_preview = QPlainTextEdit()
        self.code_preview.setReadOnly(True)
        self.code_preview.setFont(QFont("Courier New"))

        self.preview_stack = QStackedLayout()
        self.preview_stack.addWidget(svg_scroll_area)   # index 0
        self.preview_stack.addWidget(self.code_preview) # index 1

        preview_container = QWidget()
        preview_container.setLayout(self.preview_stack)
        right_panel_layout.addWidget(preview_container)

        # assemble main layout
        main_layout.addLayout(left_panel_layout)
        main_layout.addLayout(right_panel_layout)

        self.setAcceptDrops(True)
        self.apply_styles()

    def apply_styles(self):
        self.setStyleSheet("""
            QWidget { background-color: #F3E5F5; }
            QLabel  { color:#4A148C; font:10pt 'Arial'; }

            QPushButton {
              background-color:#CE93D8;
              color:#FFFFFF;
              border-radius:8px;
              padding:8px 16px;
              font-weight:bold;
            }
            QPushButton:hover { background-color:#BA68C8; }
            /* toggle buttons */
            QPushButton#toggleButton {
                background-color: #CE93D8;
                color: #FFFFFF;
                border: 1px solid #FFFFFF;
                border-radius: 4px;
                padding: 4px 24px;
            }
            QPushButton#toggleButton:hover {
                background-color: #BA68C8;
            }
            QPushButton#toggleButton:checked {
                background-color: #BA68C8;
                color: #FFFFFF;
                border: 1px solid #FFFFFF;
            }
            QLineEdit, QSpinBox, QDoubleSpinBox {
              background:#FFFFFF;
              border:1px solid #B39DDB;
              border-radius:4px;
              padding:4px;
            }
            QGroupBox {
              border:1px solid #B39DDB;
              border-radius:6px;
              margin-top:1em;
              padding:1em;
              color:#4A148C;
            }
            QGroupBox::title {
              subcontrol-origin:margin;
              left:10px;
              padding:0 3px;
            }
            QProgressBar {
              border:2px solid rgba(33,37,43,0.7);
              border-radius:10px;
              text-align:center;
              background-color:rgba(33,37,43,0.2);
              color:#4A148C;
              height:20px;
            }
            QProgressBar::chunk {
              background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #CE93D8, stop:1 #BA68C8);
              border-radius:10px;
            }
            QPlainTextEdit {
              background:#FFFFFF;
              border:1px solid #B39DDB;
              border-radius:4px;
              font-family:'Courier New';
              font-size:10pt;
            }
        """)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            url = event.mimeData().urls()[0]
            if url.isLocalFile() and ImageLoader.is_supported(url.toLocalFile()):
                event.acceptProposedAction()

    def dropEvent(self, event):
        url = event.mimeData().urls()[0]
        if url.isLocalFile():
            self.load_image(url.toLocalFile())

    def browse_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Image",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.gif *.tiff);;All Files (*)"
        )
        if file_path:
            self.load_image(file_path)

    def load_image(self, file_path: str):
        try:
            ImageLoader.load_image(file_path)
            self.current_image_path = file_path

            base_name = os.path.splitext(os.path.basename(file_path))[0]
            self.output_name_edit.setText(base_name)

            pixmap = QPixmap(file_path)
            pixmap = pixmap.scaled(
                self.image_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.image_label.setPixmap(pixmap)
            self.convert_button.setEnabled(True)
        except Exception as exc:
            QMessageBox.critical(self, "Error", str(exc))

    def save_settings(self):
        sm = self.settings_manager
        sm.set("svg_mode", self.svg_mode_combo.currentText())
        sm.set("threshold", self.threshold_spin.value())
        sm.set("blur_ksize", self.blur_spin.value())
        sm.set("canny_low", self.canny_low_spin.value())
        sm.set("canny_high", self.canny_high_spin.value())
        sm.set("potrace_turdsize", self.turdsize_spin.value())
        sm.set("potrace_alphamax", self.alphamax_spin.value())
        sm.set("tool_on_cmd", self.tool_on_edit.text())
        sm.set("tool_off_cmd", self.tool_off_edit.text())
        sm.set("output_filename", self.output_name_edit.text())

    def convert_image(self):
        if not self.current_image_path:
            QMessageBox.warning(self, "No Image", "Please load an image first.")
            return

        output_name = self.output_name_edit.text().strip()
        if not output_name:
            QMessageBox.warning(self, "No Output Name", "Please specify an output filename.")
            return

        self.progress_bar.show()
        self.convert_button.setEnabled(False)

        self.worker = ConversionThread(self.current_image_path, output_name, self.settings_manager)
        self.worker.finished.connect(self.on_conversion_finished)
        self.worker.error.connect(self.on_conversion_error)
        self.worker.start()

    def on_conversion_finished(self, gcode_path: str):
        self.progress_bar.hide()

        QMessageBox.information(self, "Success", f"G-code saved to:\n{gcode_path}")

        self.last_gcode_path = gcode_path
        self.last_svg_path = os.path.join("output", f"{self.output_name_edit.text().strip()}.svg")

        self.update_preview()
        self.convert_button.setEnabled(True)

    def on_conversion_error(self, error_message: str):
        self.progress_bar.hide()
        QMessageBox.critical(self, "Conversion Error", error_message)
        self.convert_button.setEnabled(True)

    def update_preview(self):
        if self.svg_button.isChecked():
            self.preview_stack.setCurrentIndex(0)
            if self.last_svg_path and os.path.exists(self.last_svg_path):
                self.svg_widget.load(self.last_svg_path)
                original_size = self.svg_widget.renderer().defaultSize()
                self.svg_widget.setFixedSize(original_size)
        else:
            self.preview_stack.setCurrentIndex(1)
            if self.last_gcode_path and os.path.exists(self.last_gcode_path):
                try:
                    with open(self.last_gcode_path, encoding="utf-8", errors="ignore") as file:
                        self.code_preview.setPlainText("".join(file.readlines()[:100]))
                except Exception as exc:
                    self.code_preview.setPlainText(f"Preview Error: {exc}")
            else:
                self.code_preview.clear()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())