from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QSlider, QHBoxLayout, QPushButton, QFileDialog,
    QMessageBox
)
from PySide6.QtCore import Qt, QUrl
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from processor import process_audio
import os

class NightCoreStudioWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.selected_file = None
        self.save_path = None
        self.temp_preview_file = None  # Ścieżka do tymczasowego pliku podglądu

        # NOWOŚĆ: Odtwarzacz do podglądu
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        
        # Połączenie sygnału, aby posprzątać po zakończeniu odtwarzania
        self.player.playbackStateChanged.connect(self.handle_playback_state_change)

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # Tytuł
        title_label = QLabel("NightCore Studio")
        title_label.setAlignment(Qt.AlignCenter)
        # Zmieniono: usunięto kolor, dodano objectName
        title_label.setObjectName("h1_label")
        title_label.setStyleSheet("font-size: 32px; font-weight: bold;")
        layout.addWidget(title_label)
        
        # File Selection
        file_selection_layout = QHBoxLayout()
        self.select_file_button = QPushButton("Select Audio File")
        self.select_file_button.setObjectName("dark_button")
        self.select_file_button.clicked.connect(self.select_file)
        
        self.file_label = QLabel("No file selected")
        # Zmieniono: usunięto kolor, dodano objectName
        self.file_label.setObjectName("info_label")
        self.file_label.setStyleSheet("font-size: 16px;")
        file_selection_layout.addWidget(self.select_file_button)
        file_selection_layout.addWidget(self.file_label)
        layout.addLayout(file_selection_layout)

        # Save Path Selection
        save_path_layout = QHBoxLayout()
        self.select_save_path_button = QPushButton("Select Save Folder")
        self.select_save_path_button.setObjectName("dark_button")
        self.select_save_path_button.clicked.connect(self.select_save_path)
        
        self.savepath_label = QLabel("No save path selected")
        # Zmieniono: usunięto kolor, dodano objectName
        self.savepath_label.setObjectName("info_label")
        self.savepath_label.setStyleSheet("font-size: 16px;")
        save_path_layout.addWidget(self.select_save_path_button)
        save_path_layout.addWidget(self.savepath_label)
        layout.addLayout(save_path_layout)
        
        # Pitch Slider
        pitch_layout = QHBoxLayout()
        pitch_label = QLabel("Pitch:")
        pitch_label.setFixedWidth(80)
        pitch_label.setObjectName("slider_label")
        pitch_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.pitch_slider = QSlider(Qt.Horizontal)
        
        # ### ZMIANA: Zakres suwaka Pitch (od 0.50 do 2.00, z krokiem 0.01)
        # Będziemy mnożyć wewnętrzną wartość przez 100, aby mieć int do suwaka.
        self.pitch_slider.setRange(50, 200) 
        self.pitch_slider.setValue(125) # ### ZMIANA: Domyślna wartość Pitch na 1.25 (czyli 125 w int)
        
        self.pitch_value_label = QLabel("1.25") # ### ZMIANA: Domyślna wartość wyświetlana
        self.pitch_value_label.setFixedWidth(50)
        self.pitch_value_label.setAlignment(Qt.AlignRight)
        self.pitch_value_label.setObjectName("slider_value_label")
        self.pitch_value_label.setStyleSheet("font-size: 16px;")
        
        # ### ZMIANA: Lambda funkcja do formatowania wartości Pitch jako float
        self.pitch_slider.valueChanged.connect(lambda v: self.pitch_value_label.setText(f"{v/100:.2f}"))
        
        pitch_layout.addWidget(pitch_label)
        pitch_layout.addWidget(self.pitch_slider)
        pitch_layout.addWidget(self.pitch_value_label)
        layout.addLayout(pitch_layout)

        # Speed Slider
        speed_layout = QHBoxLayout()
        speed_label = QLabel("Speed:")
        speed_label.setFixedWidth(80)
        speed_label.setObjectName("slider_label")
        speed_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.speed_slider = QSlider(Qt.Horizontal)
        
        # ### ZMIANA: Zakres suwaka Speed (od 0.50 do 2.00, z krokiem 0.01)
        self.speed_slider.setRange(50, 200)
        self.speed_slider.setValue(130) # ### ZMIANA: Domyślna wartość Speed na 1.30 (czyli 130 w int)
        
        self.speed_value_label = QLabel("1.30") # ### ZMIANA: Domyślna wartość wyświetlana
        self.speed_value_label.setFixedWidth(50)
        self.speed_value_label.setAlignment(Qt.AlignRight)
        self.speed_value_label.setObjectName("slider_value_label")
        self.speed_value_label.setStyleSheet("font-size: 16px;")
        
        # ### ZMIANA: Lambda funkcja do formatowania wartości Speed jako float
        self.speed_slider.valueChanged.connect(lambda v: self.speed_value_label.setText(f"{v/100:.2f}"))
        
        speed_layout.addWidget(speed_label)
        speed_layout.addWidget(self.speed_slider)
        speed_layout.addWidget(self.speed_value_label)
        layout.addLayout(speed_layout)
        
        # Reverb Slider
        reverb_layout = QHBoxLayout()
        reverb_label = QLabel("Reverb:")
        reverb_label.setFixedWidth(80)
        reverb_label.setObjectName("slider_label")
        reverb_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.reverb_slider = QSlider(Qt.Horizontal)
        
        # ### ZMIANA: Zakres suwaka Reverb (od 0 do 20)
        self.reverb_slider.setRange(0, 20)
        self.reverb_slider.setValue(0)
        
        self.reverb_value_label = QLabel("0")
        self.reverb_value_label.setFixedWidth(50)
        self.reverb_value_label.setAlignment(Qt.AlignRight)
        self.reverb_value_label.setObjectName("slider_value_label")
        self.reverb_value_label.setStyleSheet("font-size: 16px;")
        self.reverb_slider.valueChanged.connect(lambda v: self.reverb_value_label.setText(str(v)))
        reverb_layout.addWidget(reverb_label)
        reverb_layout.addWidget(self.reverb_slider)
        reverb_layout.addWidget(self.reverb_value_label)
        layout.addLayout(reverb_layout)
        
        # Bass Slider
        bass_layout = QHBoxLayout()
        bass_label = QLabel("Bass Boost:")
        bass_label.setFixedWidth(80)
        bass_label.setObjectName("slider_label")
        bass_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.bass_slider = QSlider(Qt.Horizontal)
        
        # ### ZMIANA: Zakres suwaka Bass Boost (od 0 do 20)
        self.bass_slider.setRange(0, 20)
        self.bass_slider.setValue(0)
        
        self.bass_value_label = QLabel("0")
        self.bass_value_label.setFixedWidth(50)
        self.bass_value_label.setAlignment(Qt.AlignRight)
        self.bass_value_label.setObjectName("slider_value_label")
        self.bass_value_label.setStyleSheet("font-size: 16px;")
        self.bass_slider.valueChanged.connect(lambda v: self.bass_value_label.setText(str(v)))
        bass_layout.addWidget(bass_label)
        bass_layout.addWidget(self.bass_slider)
        bass_layout.addWidget(self.bass_value_label)
        layout.addLayout(bass_layout)

        # Buttons
        button_layout = QHBoxLayout()
        self.preview_button = QPushButton("Preview")
        self.preview_button.setObjectName("dark_button")
        self.preview_button.clicked.connect(self.start_preview)
        
        self.stop_button = QPushButton("Stop Preview")
        self.stop_button.setObjectName("dark_button")
        self.stop_button.clicked.connect(self.stop_preview)

        self.process_button = QPushButton("Process and Save")
        self.process_button.setObjectName("dark_button")
        self.process_button.clicked.connect(self.process_and_save)

        button_layout.addWidget(self.preview_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.process_button)
        layout.addLayout(button_layout)
        
        layout.addStretch() # Push everything to the top

        self.setLayout(layout)

    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Audio File", "", "Audio Files (*.mp3 *.wav *.ogg *.flac *.m4a)")
        if file_path:
            self.selected_file = file_path
            self.file_label.setText(f"Selected: {os.path.basename(file_path)}")
            # Zatrzymaj podgląd, jeśli jest aktywny
            self.stop_preview()

    def select_save_path(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Save Folder")
        if folder_path:
            self.save_path = folder_path
            self.savepath_label.setText(f"Save Path: {os.path.basename(folder_path)}")
            
    def start_preview(self):
        if not self.selected_file:
            QMessageBox.warning(self, "Warning", "Please select an audio file first!")
            return

        self.stop_preview() # Zawsze zatrzymaj poprzedni podgląd

        # ### ZMIANA: Pobieranie wartości dziesiętnych dla pitch i speed
        pitch = self.pitch_slider.value() / 100.0
        speed = self.speed_slider.value() / 100.0
        
        reverb = self.reverb_slider.value()
        bass = self.bass_slider.value()
        
        # Utwórz tymczasowy plik do podglądu
        temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp")
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
        
        original_filename = os.path.basename(self.selected_file)
        base_name, _ = os.path.splitext(original_filename)
        self.temp_preview_file = os.path.join(temp_dir, f"{base_name}_preview.mp3")

        try:
            self.file_label.setText("Creating preview...")
            process_audio(
                input_path=self.selected_file,
                output_path=self.temp_preview_file,
                pitch=pitch,
                speed=speed,
                reverb=reverb,
                bass=bass
            )
            
            # Odtwórz przetworzony plik
            self.player.setSource(QUrl.fromLocalFile(self.temp_preview_file))
            self.player.play()
            self.file_label.setText("Preview playing...")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create preview: {e}")
            self.file_label.setText("Preview failed.")

    def stop_preview(self):
        self.player.stop()
        self.file_label.setText("Preview stopped.")
        # Opcjonalnie: usunięcie tymczasowego pliku
        if self.temp_preview_file and os.path.exists(self.temp_preview_file):
            try:
                os.remove(self.temp_preview_file)
                self.temp_preview_file = None
            except Exception as e:
                print(f"Could not remove temporary file: {e}")

    def handle_playback_state_change(self, state):
        if state == QMediaPlayer.StoppedState and self.player.source() and self.player.position() == self.player.duration():
            # Po zakończeniu odtwarzania podglądu, posprzątaj
            self.stop_preview()

    def process_and_save(self):
        if not self.selected_file:
            QMessageBox.warning(self, "Warning", "Please select a file to process!")
            return
        if not self.save_path:
            self.savepath_label.setText("Please select a save path!")
            return

        # Zatrzymaj podgląd, jeśli jest aktywny
        self.stop_preview()

        # ### ZMIANA: Pobieranie wartości dziesiętnych dla pitch i speed
        pitch = self.pitch_slider.value() / 100.0
        speed = self.speed_slider.value() / 100.0
        
        reverb = self.reverb_slider.value()
        bass = self.bass_slider.value()
        
        # Tworzenie nazwy pliku wyjściowego
        original_filename = os.path.basename(self.selected_file)
        base_name, _ = os.path.splitext(original_filename)
        output_filename = f"{base_name}_nightcore.mp3"
        output_filepath = os.path.join(self.save_path, output_filename)

        self.file_label.setText(f"Processing file: {original_filename}")
        self.savepath_label.setText(f"Saving to: {self.save_path}")

        try:
            # Użyj zmodyfikowanej funkcji do zapisu pliku wynikowego
            process_audio(
                input_path=self.selected_file,
                output_path=output_filepath, # Teraz podajemy ścieżkę do zapisu
                pitch=pitch,
                speed=speed,
                reverb=reverb,
                bass=bass
            )
            QMessageBox.information(self, "Success", f"File saved to: {output_filepath}")
            self.file_label.setText("Processing finished!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred during processing: {e}")
            self.file_label.setText("Processing failed.")