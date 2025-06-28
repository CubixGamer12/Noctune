import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QComboBox, QProgressBar, QFileDialog,
    QMessageBox, QSizePolicy
)
from PySide6.QtCore import Qt, QThread, Signal
import yt_dlp
import traceback

class DownloadThread(QThread):
    progress_changed = Signal(int)
    status_changed = Signal(str)
    download_finished = Signal(str)  # Sygnał informujący o zakończeniu pobierania

    def __init__(self, url, output_path, file_format):
        super().__init__()
        self.url = url
        self.output_path = output_path
        self.file_format = file_format.lower()
        self.is_playlist = False
        self.entries = []  # Do przechowywania informacji o elementach playlisty

    def run(self):
        for i, entry in enumerate(self.entries):
            if not entry:
                continue

            title = entry.get('title', 'video')
            safe_title = ''.join(c for c in title if c.isalnum() or c in (' ', '.', '_')).strip()
            output_template = os.path.join(self.output_path, f"{safe_title}.%(ext)s")

            if 'audio' in self.file_format:
                postprocessors = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                }]
                format_str = 'bestaudio/best'
            else:
                postprocessors = [{
                    'key': 'FFmpegVideoConvertor',
                    'preferredformat': 'mp4',
                }]
                format_str = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best'

            ydl_opts_download = {
                'format': format_str,
                'postprocessors': postprocessors,
                'outtmpl': output_template,
                'progress_hooks': [self.download_hook],
                'quiet': True,
                'no_warnings': True,
            }

            video_url = entry.get('webpage_url')

            if not video_url:
                self.status_changed.emit(f"Skipping entry without URL")
                continue

            self.status_changed.emit(f"Downloading: {title} ({i + 1}/{len(self.entries)})")
            with yt_dlp.YoutubeDL(ydl_opts_download) as ydl_download:
                ydl_download.download([video_url])
                
class DownloaderWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.current_download_thread = None # Przechowuje referencję do wątku

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # Tytuł
        title_label = QLabel("YouTube/Playlist Downloader")
        title_label.setAlignment(Qt.AlignCenter)
        # Zmieniono: usunięto kolor, dodano objectName
        title_label.setObjectName("h1_label")
        title_label.setStyleSheet("font-size: 32px; font-weight: bold;")
        layout.addWidget(title_label)

        # URL Input
        url_layout = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Enter video URL (YouTube, Playlist, etc.)")
        url_layout.addWidget(self.url_input)
        
        # Format selection
        self.format_combo = QComboBox()
        self.format_combo.addItems(["MP3 (Audio)", "MP4 (Video)"])
        self.format_combo.setFixedWidth(150)
        url_layout.addWidget(self.format_combo)
        
        layout.addLayout(url_layout)

        # Output Path Selection
        path_layout = QHBoxLayout()
        self.output_label = QLabel("Output Folder: Not selected")
        # Zmieniono: usunięto kolor, dodano objectName
        self.output_label.setObjectName("info_label")
        self.output_label.setStyleSheet("font-size: 14px;")
        
        select_path_button = QPushButton("Select Output Folder")
        select_path_button.setObjectName("dark_button")
        select_path_button.clicked.connect(self.select_output_folder)
        
        path_layout.addWidget(self.output_label)
        path_layout.addWidget(select_path_button)
        layout.addLayout(path_layout)
        
        # Download Button
        self.download_button = QPushButton("Download")
        self.download_button.setObjectName("dark_button")
        self.download_button.setMinimumHeight(40)
        self.download_button.clicked.connect(self.start_download)
        layout.addWidget(self.download_button)
        
        # Progress Bar and Status
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel("Status: Idle")
        self.status_label.setAlignment(Qt.AlignCenter)
        # Zmieniono: usunięto kolor, dodano objectName
        self.status_label.setObjectName("status_label")
        self.status_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(self.status_label)

        layout.addStretch() # Push everything to the top
        
        self.setLayout(layout)
        self.output_path = None # Domyślna ścieżka do pobierania

    def select_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if folder:
            self.output_path = folder
            self.output_label.setText(f"Output Folder: {os.path.basename(folder)}")

    def start_download(self):
        url = self.url_input.text()
        if not url:
            QMessageBox.warning(self, "Input Error", "Please enter a URL.")
            return

        if not self.output_path:
            QMessageBox.warning(self, "Output Error", "Please select an output folder for the download.")
            return

        file_format = self.format_combo.currentText()

        self.status_label.setText("Starting download...")
        self.progress_bar.setValue(0)
        self.download_button.setEnabled(False) # Wyłącz przycisk podczas pobierania

        self.current_download_thread = DownloadThread(url, self.output_path, file_format)
        self.current_download_thread.progress_changed.connect(self.progress_bar.setValue)
        self.current_download_thread.status_changed.connect(self.status_label.setText)
        self.current_download_thread.download_finished.connect(self.download_finished)
        self.current_download_thread.start()

    def download_finished(self, status):
        self.download_button.setEnabled(True) # Włącz przycisk po zakończeniu
        if status == "Success":
            self.status_label.setText("Download completed successfully!")
            QMessageBox.information(self, "Download Complete", "The download has finished successfully!")
        elif status == "Error":
            self.status_label.setText("Download failed!")
            QMessageBox.critical(self, "Download Error", "An error occurred during download. Please check the URL and your network connection.")
        else: # Should not happen, but for robustness
            self.status_label.setText("Download finished with unknown status.")

        self.progress_bar.setValue(0) # Resetuj pasek postępu
        self.current_download_thread = None # Zwalnia referencję do wątku