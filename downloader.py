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
        self.status_changed.emit("Fetching info...")
        try:
            ydl_opts = {
                'quiet': True,
                'compat_opts': ['no-youtube-channel-redirect'],
                # 'geo_bypass': True,  # Odkomentuj jeśli masz problemy z regionem
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.url, download=False)
                if info.get('_type') == 'playlist':
                    self.is_playlist = True
                    self.entries = info.get('entries', [])
                else:
                    self.is_playlist = False
                    self.entries = [info]

            self.status_changed.emit(f"Found {len(self.entries)} item(s). Starting download...")
            total_items = len(self.entries)

            for i, entry in enumerate(self.entries):
                if not self.isRunning():  # Pozwala na zatrzymanie wątku
                    break

                # Reset progress bar dla każdego nowego pliku
                self.progress_changed.emit(0)

                filename = entry.get('title', 'Unknown Title')
                self.status_changed.emit(f"Downloading {i + 1}/{total_items}: {filename}...")

                postprocessors = []
                if self.file_format == 'mp3':
                    postprocessors = [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }]
                elif self.file_format == 'wav':
                    postprocessors = [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'wav',
                    }]
                elif self.file_format == 'm4a':
                    postprocessors = [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'm4a',
                    }]
                elif self.file_format == 'opus':
                    postprocessors = [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'opus',
                    }]

                download_opts = {
                    'format': 'bestaudio/best' if self.file_format != 'mp4' else 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                    'outtmpl': os.path.join(self.output_path, '%(title)s.%(ext)s'),
                    'progress_hooks': [self._progress_hook],
                    'postprocessors': postprocessors,
                    'cachedir': False,  # Wyłącz buforowanie, aby uniknąć problemów z uprawnieniami
                    'noplaylist': not self.is_playlist,  # Ustaw na True jeśli to pojedynczy film
                }

                if self.file_format == 'mp4':  # Dodatkowe opcje dla MP4
                    download_opts['merge_output_format'] = 'mp4'

                with yt_dlp.YoutubeDL(download_opts) as ydl:
                    try:
                        video_url = entry.get('url') or entry.get('webpage_url')
                        if not video_url:
                            self.status_changed.emit(f"Skipping entry without URL: {entry.get('title', 'Unknown')}")
                            continue
                        ydl.download([video_url])
                        self.status_changed.emit(f"Finished: {filename}")
                        self.progress_changed.emit(100)  # Ustaw 100% po zakończeniu pobierania pliku
                    except Exception as e:
                        err_trace = traceback.format_exc()
                        print(f"Download error:\n{err_trace}")  # Wypisz pełny błąd do konsoli
                        self.status_changed.emit(f"Error downloading {filename}: {e}")
                        self.download_finished.emit("Error")
                        return

            self.status_changed.emit("All downloads completed!")
            self.download_finished.emit("Success")

        except Exception as e:
            err_trace = traceback.format_exc()
            print(f"General error:\n{err_trace}")  # Wypisz pełny błąd do konsoli
            self.status_changed.emit(f"Error: {e}")
            self.download_finished.emit("Error")

    def _progress_hook(self, d):
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate')
            if total:
                downloaded = d.get('downloaded_bytes', 0)
                percent = int(downloaded / total * 100)
                title = os.path.basename(d.get('filename', '')) if d.get('filename') else "Downloading..."

                playlist_index = d.get('playlist_index')
                playlist_count = d.get('playlist_count')

                if playlist_index and playlist_count:
                    self.status_changed.emit(f"Downloading {playlist_index}/{playlist_count} - {title} - {percent}%")
                else:
                    self.status_changed.emit(f"{title} - {percent}%")
                self.progress_changed.emit(percent)
        elif d['status'] == 'finished':
            self.progress_changed.emit(100)
            self.status_changed.emit(f"Processing: {os.path.basename(d.get('filename', ''))}")
        elif d['status'] == 'error':
            self.status_changed.emit(f"Error: {d.get('error')}")
            self.download_finished.emit("Error")


class DownloaderWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YouTube Downloader")
        self.output_path = os.path.expanduser("~") # Domyślna ścieżka do folderu użytkownika

        self.init_ui()
        self.current_download_thread = None # Aby przechowywać referencję do aktualnego wątku


        self.download_button.setStyleSheet("""
            QPushButton {
                text-align: center;
                padding: 0px;
                margin: 0px;
            }
        """)

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30) # Wewnętrzne marginesy dla widżetu
        layout.setSpacing(15) # Większe odstępy między elementami

        title_label = QLabel("YouTube Video/Playlist Downloader")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setObjectName("h1_label")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; ") # Wyróżnij tytuł
        layout.addWidget(title_label)

        # URL Input
        url_label = QLabel("Video/Playlist URL:")
        url_label.setObjectName("h2_label") # Wyłącz styl dla tej etykiety
        url_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(url_label)
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Paste YouTube URL here...")
        layout.addWidget(self.url_input)

        # Output Folder Selection
        output_layout = QHBoxLayout()
        self_output_label = QLabel("Output folder:")
        self_output_label.setObjectName("h2_label") # Wyłącz styl dla tej etykiety
        self_output_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        output_layout.addWidget(self_output_label)

        self.output_label = QLabel(f"Output folder: {self.output_path}")
        self.output_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        output_layout.addWidget(self.output_label)

        self.select_button = QPushButton("Select Folder")
        self.select_button.setFixedSize(120, 35) # Stały rozmiar przycisku
        output_layout.addWidget(self.select_button)
        layout.addLayout(output_layout)

        # Format Selection
        format_layout = QHBoxLayout()
        format_label = QLabel("Download Format:")
        format_label.setObjectName("h2_label")
        format_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        format_layout.addWidget(format_label)

        self.format_combo = QComboBox()
        self.format_combo.addItems(["mp3", "wav", "m4a", "opus", "mp4"])
        self.format_combo.setMinimumWidth(100)
        format_layout.addWidget(self.format_combo)
        format_layout.addStretch() # Rozciąga przestrzeń, spychając combo do lewej
        layout.addLayout(format_layout)

        # Download Button
        self.download_button = QPushButton("Download")
        self.download_button.setMinimumHeight(45) # Większy przycisk
        layout.addWidget(self.download_button)

        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setAlignment(Qt.AlignCenter)  # Wyśrodkuj tekst
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                text-align: center;
            }
            QProgressBar::chunk {
                text-align: center;  # Dla spójności
            }
        """)
        layout.addWidget(self.progress_bar)

        
        # Status Label
        self.status_label = QLabel("Ready")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setObjectName("no_style_label") # Wyłącz styl dla tej etykiety
        layout.addWidget(self.status_label)

        layout.addStretch() # Spycha elementy do góry
        self.setLayout(layout)

        # Connections
        self.select_button.clicked.connect(self.choose_folder)
        self.download_button.clicked.connect(self.start_download)

    def choose_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select download folder", self.output_path)
        if folder:
            self.output_path = folder
            self.output_label.setText(f"Output folder: {folder}")

    def start_download(self):
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Missing URL", "Please paste a video or playlist URL.")
            return

        if not self.output_path or not os.path.exists(self.output_path):
            QMessageBox.warning(self, "Invalid Output Folder", "Please select a valid output folder.")
            return

        if self.current_download_thread and self.current_download_thread.isRunning():
            QMessageBox.information(self, "Download in Progress", "A download is already in progress. Please wait or restart the application.")
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