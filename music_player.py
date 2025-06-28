import os
import json
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QListWidget, QFileDialog, QSlider, QSizePolicy, QMessageBox, QSpacerItem,
    QListWidgetItem, QInputDialog
)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtGui import QIcon, QPixmap, QDrag
from PySide6.QtCore import Qt, QTimer, QTime, QSettings, QSize, QUrl, QMimeData, QFileSystemWatcher

# --- START ZMIANY ---
# NOWOŚĆ: Klasa QSlider z niestandardową obsługą kółka myszy
# Wprowadzenie tej klasy pozwala kontrolować, czy suwak reaguje na kółko myszy.
class CustomSlider(QSlider):
    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)
        self.setMouseTracking(True) # Włącz śledzenie myszy

    # Nadpisanie metody wheelEvent, aby zignorować ruch kółka myszy
    # podczas interakcji z suwakiem. Zapobiega to przypadkowym zmianom pozycji utworu.
    def wheelEvent(self, event):
        # Ignoruj zdarzenie kółka myszy, aby zapobiec niezamierzonemu przesuwaniu
        event.ignore()
# --- KONIEC ZMIANY ---

AUDIO_EXTENSIONS = ('.mp3', '.wav', '.ogg', '.flac', '.m4a')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ICONS_DIR = os.path.join(BASE_DIR, "Data", "icons")

class MusicPlayerWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Music Player")

        self.settings = QSettings("NightTokyo", "MultiToolMusicPlayer")

        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)

        self.playlist = []  # lista pełnych ścieżek plików
        self.current_index = -1
        self.monitored_folder = "" # Folder do inteligentnej playlisty
        
        # --- START ZMIANY ---
        # Dodajemy flagę do blokowania aktualizacji suwaka
        # Ta flaga będzie ustawiana na True, gdy użytkownik zacznie przesuwać suwak
        # i na False po jego zwolnieniu. Zapobiega to konfliktom aktualizacji.
        self.is_slider_being_dragged = False
        # --- KONIEC ZMIANY ---

        # Watcher dla inteligentnej playlisty
        self.file_system_watcher = QFileSystemWatcher(self)
        self.file_system_watcher.directoryChanged.connect(self.on_monitored_directory_changed)

        self.init_ui()

        # Połączenia sygnałów
        self.player.positionChanged.connect(self.update_progress_slider)
        self.player.durationChanged.connect(self.update_duration)
        self.player.sourceChanged.connect(self.on_source_changed)
        self.player.playbackStateChanged.connect(self.handle_playback_state_change)

        # Wznowienie stanu z poprzedniej sesji
        self.load_settings()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)

        # Tytuł zakładki
        title_label = QLabel("Music Player")
        title_label.setAlignment(Qt.AlignCenter)
        # Zmieniono: usunięto kolor, dodano objectName
        title_label.setObjectName("h1_label")
        title_label.setStyleSheet("font-size: 32px; font-weight: bold;")
        layout.addWidget(title_label)

        # Status i czas
        status_layout = QVBoxLayout()
        self.status_label = QLabel("Ready: No song loaded.")
        self.status_label.setAlignment(Qt.AlignCenter)
        # Zmieniono: usunięto kolor, dodano objectName
        self.status_label.setObjectName("status_label")
        self.status_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        
        status_layout.addWidget(self.status_label)
        
        time_layout = QHBoxLayout()
        self.current_time_label = QLabel("00:00")
        # Zmieniono: usunięto kolor, dodano objectName
        self.current_time_label.setObjectName("time_label")
        self.current_time_label.setStyleSheet("font-size: 14px;")
        
        # --- START ZMIANY ---
        # Używamy CustomSlider zamiast QSlider
        self.progress_slider = CustomSlider(Qt.Horizontal)
        self.progress_slider.setRange(0, 100)
        # Zmieniono: Usuwamy połączenie sliderMoved, aby uniknąć błędów
        # self.progress_slider.sliderMoved.connect(self.set_position)
        
        # Nowe połączenia dla suwaka:
        # Połączenie wciśnięcia suwaka z metodą blokującą aktualizację
        self.progress_slider.sliderPressed.connect(self.slider_pressed)
        # Połączenie zwolnienia suwaka z metodą ustawiającą pozycję odtwarzania
        self.progress_slider.sliderReleased.connect(self.set_position_from_slider)
        # --- KONIEC ZMIANY ---

        self.total_time_label = QLabel("00:00")
        # Zmieniono: usunięto kolor, dodano objectName
        self.total_time_label.setObjectName("time_label")
        self.total_time_label.setStyleSheet("font-size: 14px;")

        time_layout.addWidget(self.current_time_label)
        time_layout.addWidget(self.progress_slider)
        time_layout.addWidget(self.total_time_label)
        
        layout.addLayout(status_layout)
        layout.addLayout(time_layout)

        # Przyciski sterujące
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(20)
        controls_layout.setAlignment(Qt.AlignCenter)

        # Przyciski kontrolne
        self.shuffle_button = self._create_icon_button("shuffle_icon.png", "icon_button", is_checkable=True)
        self.previous_button = self._create_icon_button("previous_icon.png", "icon_button")
        self.play_pause_button = self._create_icon_button("play_icon.png", "icon_button_large", is_checkable=True)
        self.next_button = self._create_icon_button("next_icon.png", "icon_button")
        self.repeat_button = self._create_icon_button("repeat_icon.png", "icon_button", is_checkable=True)

        controls_layout.addWidget(self.shuffle_button)
        controls_layout.addWidget(self.previous_button)
        controls_layout.addWidget(self.play_pause_button)
        controls_layout.addWidget(self.next_button)
        controls_layout.addWidget(self.repeat_button)
        
        # Suwak głośności
        volume_layout = QHBoxLayout()
        volume_layout.setSpacing(10)
        volume_layout.setAlignment(Qt.AlignCenter)
        volume_icon = QLabel()
        volume_icon.setPixmap(QIcon(os.path.join(ICONS_DIR, "volume_icon.png")).pixmap(QSize(24, 24)))
        volume_icon.setObjectName("no_style_label") # Użyj no_style_label dla ikony, aby nie miała tła
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(100)
        self.audio_output.setVolume(1.0)
        self.volume_slider.valueChanged.connect(self.set_volume)

        volume_layout.addWidget(volume_icon)
        volume_layout.addWidget(self.volume_slider)
        volume_layout.setContentsMargins(0, 0, 50, 0) # Wyrównanie do prawej
        
        layout.addLayout(controls_layout)
        layout.addLayout(volume_layout)
        
        # Kontenery na playlisty i foldery
        playlist_layout = QVBoxLayout()
        
        # Przyciski do zarządzania playlistą i folderem
        button_layout = QHBoxLayout()
        load_folder_btn = QPushButton("Load Music Folder")
        load_folder_btn.setObjectName("dark_button")
        load_folder_btn.clicked.connect(self.load_music_folder)

        save_playlist_btn = QPushButton("Save Playlist")
        save_playlist_btn.setObjectName("dark_button")
        save_playlist_btn.clicked.connect(self.save_playlist)
        
        load_playlist_btn = QPushButton("Load Playlist")
        load_playlist_btn.setObjectName("dark_button")
        load_playlist_btn.clicked.connect(self.load_playlist)

        remove_selected_btn = QPushButton("Remove Selected")
        remove_selected_btn.setObjectName("dark_button")
        remove_selected_btn.clicked.connect(self.remove_selected_song)

        clear_playlist_btn = QPushButton("Clear Playlist")
        clear_playlist_btn.setObjectName("dark_button")
        clear_playlist_btn.clicked.connect(self.clear_playlist)

        monitor_folder_btn = QPushButton("Monitor Folder")
        monitor_folder_btn.setObjectName("dark_button")
        monitor_folder_btn.clicked.connect(self.toggle_folder_monitoring)

        button_layout.addWidget(load_folder_btn)
        button_layout.addWidget(save_playlist_btn)
        button_layout.addWidget(load_playlist_btn)
        button_layout.addWidget(remove_selected_btn)
        button_layout.addWidget(clear_playlist_btn)
        button_layout.addWidget(monitor_folder_btn)
        
        playlist_layout.addLayout(button_layout)

        # Lista piosenek
        self.song_list_widget = QListWidget()
        self.song_list_widget.setSelectionMode(QListWidget.ExtendedSelection)
        self.song_list_widget.doubleClicked.connect(self.play_selected_song)
        self.song_list_widget.setDragEnabled(True)
        self.song_list_widget.setAcceptDrops(True)
        self.song_list_widget.setDropIndicatorShown(True)
        self.song_list_widget.setDragDropMode(QListWidget.InternalMove)
        self.song_list_widget.model().rowsMoved.connect(self.handle_rows_moved)

        playlist_layout.addWidget(self.song_list_widget)
        
        layout.addLayout(playlist_layout)

        # Połączenia sygnałów przycisków
        self.play_pause_button.clicked.connect(self.toggle_play_pause)
        self.next_button.clicked.connect(self.next_song)
        self.previous_button.clicked.connect(self.previous_song)
        self.shuffle_button.clicked.connect(self.shuffle_playlist)
        self.repeat_button.clicked.connect(self.toggle_repeat_mode)

    def _create_icon_button(self, icon_name, obj_name, is_checkable=False, is_large=False):
        btn = QPushButton()
        btn.setObjectName(obj_name)
        btn.setCheckable(is_checkable)
        icon_path = os.path.join(ICONS_DIR, icon_name)
        if os.path.exists(icon_path):
            btn.setIcon(QIcon(icon_path))
        btn.setIconSize(QSize(24, 24) if not is_large else QSize(48, 48))
        return btn

    def toggle_play_pause(self):
        if self.player.playbackState() == QMediaPlayer.PlayingState:
            self.player.pause()
            self.play_pause_button.setIcon(QIcon(os.path.join(ICONS_DIR, "play_icon.png")))
        else:
            if not self.player.source() and self.playlist:
                self.play_song_at_index(0)
            else:
                self.player.play()
            self.play_pause_button.setIcon(QIcon(os.path.join(ICONS_DIR, "pause_icon.png")))
    
    def play_song_at_index(self, index):
        if 0 <= index < len(self.playlist):
            self.current_index = index
            file_path = self.playlist[index]
            self.player.setSource(QUrl.fromLocalFile(file_path))
            self.player.play()
            
            # Zaznacz piosenkę na liście
            self.song_list_widget.setCurrentRow(self.current_index)
            
            # Zaktualizuj status
            self.update_status_label(file_path)
            
            # Ustaw ikonę na 'pause'
            self.play_pause_button.setIcon(QIcon(os.path.join(ICONS_DIR, "pause_icon.png")))
        else:
            self.status_label.setText("Ready: No song loaded.")
            self.player.stop()

    def play_selected_song(self):
        selected_index = self.song_list_widget.currentRow()
        if selected_index != -1:
            self.play_song_at_index(selected_index)

    def next_song(self):
        if self.playlist:
            if self.repeat_button.isChecked(): # Tryb powtarzania jednego utworu
                self.play_song_at_index(self.current_index)
            else:
                next_index = (self.current_index + 1) % len(self.playlist)
                self.play_song_at_index(next_index)

    def previous_song(self):
        if self.playlist:
            if self.repeat_button.isChecked():
                self.play_song_at_index(self.current_index)
            else:
                prev_index = (self.current_index - 1 + len(self.playlist)) % len(self.playlist)
                self.play_song_at_index(prev_index)

    # --- START ZMIANY ---
    def update_progress_slider(self, position):
        """
        Updates the slider and current time label based on player's position.
        This update is blocked if the user is dragging the slider.
        """
        # Sprawdź, czy suwak nie jest aktualnie przeciągany przez użytkownika
        if not self.is_slider_being_dragged:
            duration = self.player.duration()
            if duration > 0:
                # Oblicz wartość suwaka w zakresie 0-100 na podstawie procentu postępu
                slider_value = int(position * 100 / duration)
                self.progress_slider.setValue(slider_value)
                
                # Aktualizuj etykietę z czasem
                self.current_time_label.setText(QTime(0, 0).addMSecs(position).toString("mm:ss"))
    # --- KONIEC ZMIANY ---

    def update_duration(self, duration):
    # --- START ZMIANY ---
    # Ulepszona metoda aktualizacji zakresu suwaka
        """Updates the slider's range and total time label."""
        # Ustaw zakres suwaka na 0-100 dla łatwej konwersji
        self.progress_slider.setRange(0, 100)
        
        # Aktualizuj etykietę z całkowitym czasem
        self.total_time_label.setText(QTime(0, 0).addMSecs(duration).toString("mm:ss"))
    # --- KONIEC ZMIANY ---

    # --- START ZMIANY ---
    def slider_pressed(self):
        """Sets a flag to stop updating the slider from the player while it's being dragged."""
        # Ustaw flagę na True, gdy użytkownik zacznie przesuwać suwak
        self.is_slider_being_dragged = True

    def set_position_from_slider(self):
        """Updates the player's position based on the slider's value after it's released."""
        # Po zwolnieniu suwaka ustaw flagę na False
        self.is_slider_being_dragged = False
        
        # Pobierz wartość suwaka (0-100)
        slider_value_percent = self.progress_slider.value()
        
        # Oblicz nową pozycję w milisekundach
        duration = self.player.duration()
        if duration > 0:
            new_position_ms = int(duration * (slider_value_percent / 100.0))
            # Ustaw nową pozycję odtwarzania
            self.player.setPosition(new_position_ms)
    # --- KONIEC ZMIANY ---

    # --- ZMIANA: Usunięta funkcja set_position, która była połączona z sliderMoved.
    # Logic is now in set_position_from_slider
    # def set_position(self, value):
    #     if self.player.duration() > 0:
    #         self.player.setPosition(int(value / 100 * self.player.duration()))
                
    def set_volume(self, value):
        self.audio_output.setVolume(value / 100)

    def handle_playback_state_change(self, state):
        # Sprawdź, czy piosenka się skończyła i czy jest coś w playliście
        if state == QMediaPlayer.StoppedState and self.player.source() and self.player.position() == self.player.duration():
            # Automatycznie przejdź do następnego utworu po zakończeniu
            if self.playlist:
                self.next_song()
                
    def on_source_changed(self, source):
        # Ta funkcja jest wywoływana, gdy źródło zostanie ustawione
        # Używamy jej do aktualizacji etykiety statusu
        if source:
            self.update_status_label(source.toLocalFile())
        else:
            self.update_status_label(None)

    def update_status_label(self, file_path):
        if file_path:
            file_name = os.path.basename(file_path)
            self.status_label.setText(f"Ready: {file_name}")
        else:
            self.status_label.setText("Ready: No song loaded.")

    def load_music_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Music Folder")
        if folder_path:
            self.load_songs_from_folder(folder_path)
            self.monitored_folder = folder_path
            self.save_settings(folder_path)
            self.start_monitoring_folder(folder_path)

    def load_songs_from_folder(self, folder_path):
        self.song_list_widget.clear()
        self.playlist.clear()
        
        # Pobierz listę plików z folderu i podfolderów
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file.lower().endswith(AUDIO_EXTENSIONS):
                    full_path = os.path.join(root, file)
                    self.playlist.append(full_path)

        # Dodaj pliki do QListWidget, wyświetlając tylko nazwę pliku
        for path in self.playlist:
            self.song_list_widget.addItem(os.path.basename(path))

        self.status_label.setText(f"Ready: Loaded {len(self.playlist)} songs from folder.")
        self.current_index = -1
        self.player.setSource(QUrl())
        self.play_pause_button.setIcon(QIcon(os.path.join(ICONS_DIR, "play_icon.png")))

    def save_playlist(self):
        if not self.playlist:
            QMessageBox.warning(self, "No Playlist", "There is no playlist to save.")
            return

        file_path, _ = QFileDialog.getSaveFileName(self, "Save Playlist", "", "Playlist Files (*.m3u)")
        if file_path:
            # Utwórz playlistę w formacie M3U
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("#EXTM3U\n")
                for song_path in self.playlist:
                    f.write(song_path + '\n')
            QMessageBox.information(self, "Success", "Playlist saved successfully!")

    def load_playlist(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Load Playlist", "", "Playlist Files (*.m3u)")
        if file_path:
            try:
                self.song_list_widget.clear()
                self.playlist.clear()
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            self.playlist.append(line)
                            self.song_list_widget.addItem(os.path.basename(line))
                
                self.status_label.setText(f"Ready: Loaded {len(self.playlist)} songs from playlist.")
                self.current_index = -1
                self.player.setSource(QUrl())
                self.play_pause_button.setIcon(QIcon(os.path.join(ICONS_DIR, "play_icon.png")))

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load playlist: {e}")

    def remove_selected_song(self):
        selected_items = self.song_list_widget.selectedItems()
        if not selected_items:
            return

        # Zbieranie indeksów do usunięcia w kolejności malejącej, aby uniknąć problemów z indeksowaniem
        rows_to_remove = [self.song_list_widget.row(item) for item in selected_items]
        rows_to_remove.sort(reverse=True)

        for row in rows_to_remove:
            # Usuń z listy QListWidget
            item = self.song_list_widget.takeItem(row)
            # Usuń z playlisty
            if row < len(self.playlist):
                del self.playlist[row]

        # Zaktualizuj current_index, jeśli to konieczne
        if self.current_index in rows_to_remove:
            self.stop()
            self.current_index = -1
        elif self.current_index > rows_to_remove[0] if rows_to_remove else -1:
            self.current_index -= len(rows_to_remove)
        
        self.status_label.setText(f"Ready: Removed {len(rows_to_remove)} songs. Playlist has {len(self.playlist)} songs.")
        if not self.playlist:
            self.stop()

    def clear_playlist(self):
        if QMessageBox.question(self, "Clear Playlist", "Are you sure you want to clear the entire playlist?",
                                 QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.song_list_widget.clear()
            self.playlist.clear()
            self.current_index = -1
            self.stop()
            self.status_label.setText("Ready: Playlist has been cleared.")
            self.save_settings("") # Wyłącz monitoring folderu

    def stop(self):
        self.player.stop()
        self.progress_slider.setValue(0)
        self.current_time_label.setText("00:00")
        self.total_time_label.setText("00:00")
        self.play_pause_button.setIcon(QIcon(os.path.join(ICONS_DIR, "play_icon.png")))

    def shuffle_playlist(self):
        import random
        if self.playlist:
            # Zapisz ścieżkę aktualnie odtwarzanej piosenki
            currently_playing_path = None
            if self.player.source() and self.player.source().isLocalFile():
                currently_playing_path = self.player.source().toLocalFile()

            random.shuffle(self.playlist)
            
            # Zaktualizuj listę w widżecie
            self.song_list_widget.clear()
            for path in self.playlist:
                self.song_list_widget.addItem(os.path.basename(path))
            
            # ### ZMIANA: Zaktualizuj current_index, aby wskazywał na ten sam utwór po przetasowaniu
            # Utwór będzie kontynuowany, a następny w kolejce będzie zgodny z nową listą.
            if currently_playing_path and currently_playing_path in self.playlist:
                try:
                    self.current_index = self.playlist.index(currently_playing_path)
                    self.song_list_widget.setCurrentRow(self.current_index)
                except ValueError:
                    # Jeśli piosenka nie zostanie znaleziona po przetasowaniu, zresetuj indeks.
                    self.current_index = -1
            else:
                # Jeśli żaden utwór nie był odtwarzany, zresetuj indeks.
                self.current_index = -1
            
            # ### USUNIĘTO: Usunięto automatyczne odtwarzanie po przetasowaniu.
            # Poprzednia pętla `if self.player.playbackState() == QMediaPlayer.PlayingState:` została usunięta.
            
            self.status_label.setText("Ready: Playlist has been shuffled.")

    def toggle_repeat_mode(self):
        if self.repeat_button.isChecked():
            # Powtarzaj tylko bieżący utwór
            icon_path = os.path.join(ICONS_DIR, "repeat_one_icon.png")
            if os.path.exists(icon_path):
                self.repeat_button.setIcon(QIcon(icon_path))
                self.repeat_button.setIconSize(QSize(32, 32))
            self.status_label.setText("Ready: Repeat One enabled.")
        else:
            # Wyłącz powtarzanie
            icon_path = os.path.join(ICONS_DIR, "repeat_icon.png")
            if os.path.exists(icon_path):
                self.repeat_button.setIcon(QIcon(icon_path))
                self.repeat_button.setIconSize(QSize(32, 32))
            self.status_label.setText("Ready: Repeat disabled.")

    def handle_rows_moved(self, parent, start, end, destination, row):
        # Metoda do aktualizacji playlisty po przeciągnięciu i upuszczeniu w QListWidget
        # Qt nie dostarcza łatwego sposobu na uzyskanie docelowego indeksu,
        # więc musimy ręcznie zreorganizować listę playlisty
        
        # Pobierz przeciągnięte elementy
        moved_items = self.playlist[start:end+1]
        
        # Usuń je z oryginalnej lokalizacji
        del self.playlist[start:end+1]
        
        # Wstaw je w nowe miejsce
        if row > start:
            row -= (end - start + 1)
        
        for item in reversed(moved_items):
            self.playlist.insert(row, item)
            
        # Zaktualizuj current_index, jeśli utwór został przeniesiony
        if self.current_index in range(start, end + 1):
            # Jeśli przeniesiony utwór jest aktualnie odtwarzany, zaktualizuj jego indeks
            old_index = self.current_index
            self.current_index = self.playlist.index(self.player.source().toLocalFile())
            print(f"Song moved, new index is {self.current_index}")
            
    def save_settings(self, folder_path):
        """Saves the current music folder setting."""
        self.settings.setValue("music_folder", folder_path)
        print(f"Saved music folder setting: {folder_path}")

    def load_settings(self):
        """Loads the last used music folder from settings."""
        last_folder = self.settings.value("music_folder", "")
        if last_folder and os.path.isdir(last_folder):
            self.load_songs_from_folder(last_folder)
            self.monitored_folder = last_folder
            self.start_monitoring_folder(last_folder)
            print(f"Loaded music folder setting: {last_folder}")
        else:
            print("No saved music folder found or path is invalid.")

    def start_monitoring_folder(self, folder_path):
        # Sprawdź, czy watcher już monitoruje ten folder
        if folder_path in self.file_system_watcher.directories():
            return
            
        # Usuń stare ścieżki, jeśli istnieją
        if self.file_system_watcher.directories():
            self.file_system_watcher.removePaths(self.file_system_watcher.directories())
            
        # Dodaj nową ścieżkę do monitorowania
        if os.path.isdir(folder_path):
            self.file_system_watcher.addPath(folder_path)
            self.status_label.setText(f"Ready: Monitoring folder '{os.path.basename(folder_path)}'.")
            print(f"Started monitoring folder: {folder_path}")
        else:
            self.status_label.setText("Ready: Folder not found, monitoring stopped.")

    def toggle_folder_monitoring(self):
        if self.monitored_folder and self.monitored_folder in self.file_system_watcher.directories():
            # Zatrzymaj monitoring
            self.file_system_watcher.removePath(self.monitored_folder)
            self.status_label.setText("Ready: Folder monitoring stopped.")
            self.save_settings("") # Usuń ścieżkę z ustawień
            self.monitored_folder = ""
        else:
            # Rozpocznij monitoring
            folder_path = QFileDialog.getExistingDirectory(self, "Select Folder to Monitor")
            if folder_path:
                self.start_monitoring_folder(folder_path)
                self.monitored_folder = folder_path
                self.save_settings(folder_path)
            else:
                self.status_label.setText("Ready: No folder selected for monitoring.")
    
    def on_monitored_directory_changed(self, path):
        # Sprawdź, czy to faktycznie monitorowany folder
        if path == self.monitored_folder:
            print(f"Monitored directory changed: {path}. Rescanning...")
            # Zapisz aktualnie odtwarzany utwór i jego pozycję
            current_playing_path = self.player.source().toLocalFile() if self.player.source() else None
            current_position = self.player.position()
            
            # Odśwież playlistę
            self.load_songs_from_folder(self.monitored_folder)

            # Spróbuj wznowić odtwarzanie od tego samego utworu
            if current_playing_path and current_playing_path in self.playlist:
                new_index = self.playlist.index(current_playing_path)
                self.play_song_at_index(new_index)
                self.player.setPosition(current_position)
            elif self.player.playbackState() == QMediaPlayer.PlayingState:
                # Jeśli utwór nie jest już na playliście, ale odtwarzacz gra, zatrzymaj go
                self.stop()
            
    def closeEvent(self, event):
        # Upewnij się, że watcher jest zatrzymany przy zamykaniu aplikacji
        if self.file_system_watcher.directories():
            self.file_system_watcher.removePaths(self.file_system_watcher.directories())
        self.save_settings(self.monitored_folder) # Zapisz stan monitorowanego folderu
        event.accept()