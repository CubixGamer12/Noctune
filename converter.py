# converter.py

import os
import subprocess
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFileDialog, QComboBox, QProgressBar, QTabWidget, QLineEdit, QSizePolicy, QMessageBox
)
from PySide6.QtCore import Qt, QThread, Signal, QSize

# Threads for conversion
class ConvertThread(QThread):
    progress_changed = Signal(int)
    status_changed = Signal(str)
    conversion_done = Signal(str)

    def __init__(self, input_path, output_path, target_format, is_video=False):
        super().__init__()
        self.input_path = input_path
        self.output_path = output_path
        self.target_format = target_format
        self.is_video = is_video

    def run(self):
        self.status_changed.emit("Converting...")

        output_file = os.path.splitext(os.path.basename(self.input_path))[0] + '.' + self.target_format
        output_full_path = os.path.join(self.output_path, output_file)

        # Build FFmpeg command based on file type
        if self.is_video:
            # Example video conversion command to MP4
            cmd = [
                "ffmpeg", "-y",
                "-i", self.input_path,
                "-c:v", "libx264",
                "-crf", "23",
                "-preset", "medium",
                "-c:a", "aac",
                "-b:a", "192k",
                output_full_path
            ]
        else:
            # Command for audio conversion
            cmd = [
                "ffmpeg", "-y",
                "-i", self.input_path,
                output_full_path
            ]

        try:
            process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if process.returncode == 0:
                self.status_changed.emit("Conversion completed")
                self.conversion_done.emit("Success")
            else:
                self.status_changed.emit("Conversion failed")
                self.conversion_done.emit("Error")
        except Exception as e:
            self.status_changed.emit(f"Error: {e}")
            self.conversion_done.emit("Error")

# Widget for Audio Conversion Tab
class AudioConversionWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.input_path = None
        self.output_path = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)
        layout.setAlignment(Qt.AlignCenter)

        # INPUT
        input_layout = QHBoxLayout()
        select_input_btn = QPushButton("Select Input File")
        select_input_btn.setObjectName("dark_button")
        select_input_btn.clicked.connect(self.select_input)
        self.input_label = QLabel("Input: No file selected")
        self.input_label.setObjectName("status_label")
        input_layout.addWidget(select_input_btn)
        input_layout.addWidget(self.input_label)
        layout.addLayout(input_layout)

        # OUTPUT
        output_layout = QHBoxLayout()
        select_output_btn = QPushButton("Select Output Folder")
        select_output_btn.setObjectName("dark_button")
        select_output_btn.clicked.connect(self.select_output)
        self.output_label = QLabel("Output: No folder selected")
        self.output_label.setObjectName("status_label")
        output_layout.addWidget(select_output_btn)
        output_layout.addWidget(self.output_label)
        layout.addLayout(output_layout)

        # FORMAT
        format_layout = QHBoxLayout()
        format_label = QLabel("Output Format:")
        format_label.setObjectName("status_label")
        self.format_combo = QComboBox()
        self.format_combo.setObjectName("format_combo_box")
        self.format_combo.addItems(["mp3", "wav", "ogg", "flac"])
        format_layout.addWidget(format_label)
        format_layout.addWidget(self.format_combo)
        format_layout.addStretch()
        layout.addLayout(format_layout)

        # PROGRESS BAR
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setAlignment(Qt.AlignCenter)
        self.progress_bar.setObjectName("progress_bar")
        layout.addWidget(self.progress_bar)

        # STATUS LABEL
        self.status_label = QLabel("Ready.")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setObjectName("status_label")
        layout.addWidget(self.status_label)

        # CONVERT BUTTON
        convert_btn = QPushButton("Convert")
        convert_btn.setObjectName("h1_button")
        convert_btn.clicked.connect(self.start_conversion)
        layout.addWidget(convert_btn)

        self.setLayout(layout)

    def select_input(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select audio file", "", "Audio Files (*.mp3 *.wav *.ogg *.flac)")
        if file:
            self.input_path = file
            self.input_label.setText(f"Input: {os.path.basename(file)}")

    def select_output(self):
        folder = QFileDialog.getExistingDirectory(self, "Select output folder")
        if folder:
            self.output_path = folder
            self.output_label.setText(f"Output: {folder}")

    def start_conversion(self):
        if not self.input_path or not self.output_path:
            self.status_label.setText("Select input and output first.")
            return

        fmt = self.format_combo.currentText()
        self.status_label.setText("Starting...")
        self.progress_bar.setValue(0)

        self.thread = ConvertThread(self.input_path, self.output_path, fmt, is_video=False)
        self.thread.status_changed.connect(self.status_label.setText)
        self.thread.conversion_done.connect(self.conversion_done)
        self.thread.start()

    def conversion_done(self, result):
        if result == "Success":
            self.progress_bar.setValue(100)
            self.status_label.setText("Conversion completed!")
            QMessageBox.information(self, "Success", "Audio conversion completed!")
        else:
            self.progress_bar.setValue(0)
            self.status_label.setText("Conversion failed.")
            QMessageBox.critical(self, "Error", "Audio conversion failed. Check console for details.")


# Widget for Video Conversion Tab
class VideoConversionWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.input_path = None
        self.output_path = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)
        layout.setAlignment(Qt.AlignCenter)

        # INPUT
        input_layout = QHBoxLayout()
        select_input_btn = QPushButton("Select Input Video")
        select_input_btn.setObjectName("dark_button")
        select_input_btn.clicked.connect(self.select_input)
        self.input_label = QLabel("Input: No file selected")
        self.input_label.setObjectName("status_label")
        input_layout.addWidget(select_input_btn)
        input_layout.addWidget(self.input_label)
        layout.addLayout(input_layout)
        
        # OUTPUT
        output_layout = QHBoxLayout()
        select_output_btn = QPushButton("Select Output Folder")
        select_output_btn.setObjectName("dark_button")
        select_output_btn.clicked.connect(self.select_output)
        self.output_label = QLabel("Output: No folder selected")
        self.output_label.setObjectName("status_label")
        output_layout.addWidget(select_output_btn)
        output_layout.addWidget(self.output_label)
        layout.addLayout(output_layout)

        # FORMAT
        format_layout = QHBoxLayout()
        format_label = QLabel("Output Format:")
        format_label.setObjectName("status_label")
        self.format_combo = QComboBox()
        self.format_combo.setObjectName("format_combo_box")
        self.format_combo.addItems(["mp4", "webm", "avi", "mov"])
        format_layout.addWidget(format_label)
        format_layout.addWidget(self.format_combo)
        format_layout.addStretch()
        layout.addLayout(format_layout)

        # PROGRESS BAR
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setAlignment(Qt.AlignCenter)
        self.progress_bar.setObjectName("progress_bar")
        layout.addWidget(self.progress_bar)

        # STATUS LABEL
        self.status_label = QLabel("Ready.")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setObjectName("status_label")
        layout.addWidget(self.status_label)

        # CONVERT BUTTON
        convert_btn = QPushButton("Convert")
        convert_btn.setObjectName("h1_button")
        convert_btn.clicked.connect(self.start_conversion)
        layout.addWidget(convert_btn)

        self.setLayout(layout)

    def select_input(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select video file", "", "Video Files (*.mp4 *.mkv *.avi *.mov *.webm)")
        if file:
            self.input_path = file
            self.input_label.setText(f"Input: {os.path.basename(file)}")

    def select_output(self):
        folder = QFileDialog.getExistingDirectory(self, "Select output folder")
        if folder:
            self.output_path = folder
            self.output_label.setText(f"Output: {folder}")

    def start_conversion(self):
        if not self.input_path or not self.output_path:
            self.status_label.setText("Select input and output first.")
            return

        fmt = self.format_combo.currentText()
        self.status_label.setText("Starting...")
        self.progress_bar.setValue(0)

        self.thread = ConvertThread(self.input_path, self.output_path, fmt, is_video=True)
        self.thread.status_changed.connect(self.status_label.setText)
        self.thread.conversion_done.connect(self.conversion_done)
        self.thread.start()

    def conversion_done(self, result):
        if result == "Success":
            self.progress_bar.setValue(100)
            self.status_label.setText("Conversion completed!")
            QMessageBox.information(self, "Success", "Video conversion completed!")
        else:
            self.progress_bar.setValue(0)
            self.status_label.setText("Conversion failed.")
            QMessageBox.critical(self, "Error", "Video conversion failed. Check console for details.")

# Main Converter Widget with Tabs
class ConverterWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Add a fixed space at the top
        main_layout.addSpacing(5)

        # TITLE
        title_label = QLabel("Media Converter")
        title_label.setObjectName("h1_label")
        title_label.setStyleSheet("font-size: 32px; font-weight: bold;")
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Tab Widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("tab_widget")
        
        # Add the tabs
        self.audio_tab = AudioConversionWidget()
        self.video_tab = VideoConversionWidget()

        self.tab_widget.addTab(self.audio_tab, "Audio")
        self.tab_widget.addTab(self.video_tab, "Video")

        main_layout.addWidget(self.tab_widget)
        
        # Stretch at the bottom to push everything up
        main_layout.addStretch()

        self.setLayout(main_layout)