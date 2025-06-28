import locale
locale.setlocale(locale.LC_NUMERIC, "C")
from PySide6.QtCore import QSettings
import sys
import os
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QLineEdit, QComboBox, QProgressBar, QFileDialog,
    QMessageBox, QStackedWidget, QSizePolicy, QSplitter
)
from PySide6.QtCore import Qt, QThread, Signal, QSize
from PySide6.QtGui import QIcon

# Importowanie pozostałych modułów
from music_player import MusicPlayerWidget
from downloader import DownloaderWidget
# Usunięto import video_player.py
from nightcore_studio import NightCoreStudioWidget
from database_manager import DatabaseManagerWidget
from converter import ConverterWidget

# NOWY WIDŻET: Klasa dla strony "Settings"
class SettingsWidget(QWidget):
    """A widget for application settings, including theme selection."""
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window # Referencja do MainWindow
        
        layout = QVBoxLayout()
        layout.setContentsMargins(50, 50, 50, 50)
        layout.setSpacing(20)
        
        # Tytuł sekcji
        title_label = QLabel("Application Settings")
        title_label.setAlignment(Qt.AlignCenter)
        # Zmieniono: usunięto kolor, dodano objectName
        title_label.setObjectName("h1_label")
        title_label.setStyleSheet("font-size: 32px; font-weight: bold;")
        layout.addWidget(title_label)
        
        # --- Sekcja wyboru motywu ---
        theme_layout = QHBoxLayout()
        theme_label = QLabel("Select Theme:")
        # Zmieniono: usunięto kolor, dodano objectName
        theme_label.setObjectName("h2_label")
        theme_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        
        self.theme_combo = QComboBox()
        self.theme_combo.setStyleSheet("padding: 5px;")
        self.theme_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.load_themes() # Załaduj dostępne motywy do ComboBoxa
        
        theme_layout.addWidget(theme_label)
        theme_layout.addWidget(self.theme_combo)
        
        layout.addLayout(theme_layout)
        
        layout.addStretch() # Rozciągnij, aby elementy były na górze

        self.theme_combo.currentTextChanged.connect(self.apply_selected_theme)
        
        self.setLayout(layout)

    def load_themes(self):
        """Loads available QSS theme files from the Data/themes directory."""
        self.themes_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Data", "themes")
        if not os.path.exists(self.themes_dir):
            os.makedirs(self.themes_dir)

        self.theme_files = [f for f in os.listdir(self.themes_dir) if f.endswith(".qss")]
        
        # POPRAWKA: Wyczyść ComboBox przed dodaniem nowych elementów
        self.theme_combo.clear()

        if not self.theme_files:
            QMessageBox.warning(self, "Warning", "No theme files found in the 'Data/themes' directory.")
            return

        theme_names = [os.path.splitext(f)[0] for f in self.theme_files]
        self.theme_combo.addItems(theme_names)

        # Odczytaj zapisany motyw z ustawień
        settings = QSettings("Faniq", "NightTokyoMultiTool")
        saved_theme = settings.value("selected_theme", "night_tokyo")

        # Ustawienie domyślnego motywu
        if saved_theme in theme_names:
            self.theme_combo.setCurrentText(saved_theme)
        else:
            # Ustaw na pierwszy element, jeśli lista nie jest pusta
            if theme_names:
                self.theme_combo.setCurrentIndex(0) 

    def apply_selected_theme(self, theme_name):
        """Applies the selected theme by loading the corresponding QSS file."""
        theme_file_path = os.path.join(self.themes_dir, f"{theme_name}.qss")
        try:
            with open(theme_file_path, "r") as file:
                style_sheet = file.read()
            self.main_window.apply_style(style_sheet)
            print(f"Applied theme: {theme_name}")
            
            # Zapisz wybrany motyw
            settings = QSettings("Faniq", "NightTokyoMultiTool")
            settings.setValue("selected_theme", theme_name)

        except FileNotFoundError:
            QMessageBox.critical(self, "Error", f"Theme file '{theme_file_path}' not found.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not load theme: {e}")


# Przywrócona klasa dla strony "About"
class AboutWidget(QWidget):
    """A simple widget to display information about the application."""
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.setContentsMargins(50, 100, 50, 100)
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignCenter)

        title_label = QLabel("Noctune")
        title_label.setAlignment(Qt.AlignCenter)
        # Zmieniono: usunięto kolor, dodano objectName
        title_label.setObjectName("app_title_label")
        title_label.setStyleSheet("font-size: 48px; font-weight: bold;")
        
        version_label = QLabel("Version 1.0")
        version_label.setAlignment(Qt.AlignCenter)
        # Zmieniono: usunięto kolor, dodano objectName
        version_label.setObjectName("version_label")
        version_label.setStyleSheet("font-size: 18px;")
        
        description_label = QLabel(
            "This application is a collection of tools for music, "
            "including a music player, a downloader, and a Nightcore audio studio."
        )
        description_label.setAlignment(Qt.AlignCenter)
        description_label.setWordWrap(True)
        # Zmieniono: usunięto kolor, dodano objectName
        description_label.setObjectName("description_label")
        description_label.setStyleSheet("font-size: 16px; max-width: 600px;")

        layout.addWidget(title_label)
        layout.addWidget(version_label)
        layout.addSpacing(20)
        layout.addWidget(description_label)
        
        layout.addStretch()

        author_label = QLabel("Created by: Faniq")
        author_label.setAlignment(Qt.AlignCenter)
        # Zmieniono: usunięto kolor, dodano objectName
        author_label.setObjectName("author_label")
        author_label.setStyleSheet("font-size: 12px;")
        layout.addWidget(author_label)

        self.setLayout(layout)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Noctune")
        self.setGeometry(100, 100, 1200, 854)
        self.setMinimumSize(1200, 854)
        self.init_ui()
        # Zastosuj styl do całej aplikacji po inicjalizacji UI
        # Zmieniona metoda: teraz styl jest ładowany z pliku
        self.load_saved_theme()
 


    def init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.nav_panel = QWidget()
        nav_layout = QVBoxLayout(self.nav_panel)
        nav_layout.setContentsMargins(10, 20, 10, 20)
        nav_layout.setSpacing(15)
        self.nav_panel.setFixedWidth(200)
        self.nav_panel.setObjectName("nav_panel")

        self.stacked_widget = QStackedWidget()

        # Tworzenie przycisków nawigacyjnych za pomocą funkcji pomocniczej
        # Upewnij się, że ikony są w folderze Data/icons/
        self.btn_about = self._create_nav_button(" About", "home_icon.png")
        self.btn_music = self._create_nav_button(" Music Player", "music_icon.png")
        self.btn_downloader = self._create_nav_button(" Downloader", "download_icon.png")
        self.btn_nightcore = self._create_nav_button(" NightCore Studio", "nightcore_icon.png") 
        # NOWY PRZYCISK
        self.btn_database = self._create_nav_button(" Database Manager", "database_icon.png")
        # NOWY PRZYCISK: Tworzenie przycisku dla Settings
        self.btn_settings = self._create_nav_button(" Settings", "settings_icon.png")
        self.btn_converter = self._create_nav_button(" Media Converter", "convert_icon.png")

        # Lista wszystkich przycisków dla łatwiejszego zarządzania stanem
        self.nav_buttons = [
            self.btn_about,
            self.btn_music,
            self.btn_downloader,
            self.btn_nightcore,
            self.btn_database,
            self.btn_converter,
            self.btn_settings
        ]

        # DODANO: Dodaj przyciski do panelu, ale umieść "stretch" przed "Settings"
        nav_layout.addWidget(self.btn_about)
        nav_layout.addWidget(self.btn_music)
        nav_layout.addWidget(self.btn_downloader)
        nav_layout.addWidget(self.btn_nightcore)
        nav_layout.addWidget(self.btn_database)
        nav_layout.addWidget(self.btn_converter)

        # DODANO: Ten "stretch" wypchnie wszystkie poprzednie przyciski do góry
        # i "przyklei" następny widżet do dołu
        nav_layout.addStretch()
        
        # DODANO: Dodaj przycisk Settings na samym końcu
        nav_layout.addWidget(self.btn_settings)


        # Utwórz instancje widżetów
        self.about_widget = AboutWidget() # Poprawna instancja klasy AboutWidget
        self.music_player_widget = MusicPlayerWidget()
        self.downloader_widget = DownloaderWidget()
        self.nightcore_widget = NightCoreStudioWidget()
        self.converter_widget = ConverterWidget()
        # NOWY WIDŻET
        self.database_widget = DatabaseManagerWidget()
        # NOWY WIDŻET: Utworzenie instancji SettingsWidget i przekazanie referencji
        self.settings_widget = SettingsWidget(self)

        # Dodaj widżety do stacked_widget
        self.stacked_widget.addWidget(self.about_widget) # Dodano jako pierwszą stronę
        self.stacked_widget.addWidget(self.music_player_widget)
        self.stacked_widget.addWidget(self.downloader_widget)
        self.stacked_widget.addWidget(self.nightcore_widget)
        self.stacked_widget.addWidget(self.database_widget)
        self.stacked_widget.addWidget(self.converter_widget)
        # NOWY WIDŻET: Dodanie do stacked widgetu
        self.stacked_widget.addWidget(self.settings_widget)

        # Ustaw początkowy widok i zaznaczenie
        self.stacked_widget.setCurrentWidget(self.about_widget) # Ustaw "About" jako startową
        self.btn_about.setChecked(True)

        # Połącz sygnały z przełączaniem widoków
        self.btn_about.clicked.connect(lambda: self.switch_page(self.about_widget, self.btn_about))
        self.btn_music.clicked.connect(lambda: self.switch_page(self.music_player_widget, self.btn_music))
        self.btn_downloader.clicked.connect(lambda: self.switch_page(self.downloader_widget, self.btn_downloader))
        self.btn_nightcore.clicked.connect(lambda: self.switch_page(self.nightcore_widget, self.btn_nightcore))
        # NOWE POŁĄCZENIE
        self.btn_database.clicked.connect(lambda: self.switch_page(self.database_widget, self.btn_database))
        self.btn_converter.clicked.connect(lambda: self.switch_page(self.converter_widget, self.btn_converter))
        # NOWE POŁĄCZENIE: Połączenie przycisku z nową stroną
        self.btn_settings.clicked.connect(lambda: self.switch_page(self.settings_widget, self.btn_settings))

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.nav_panel)
        splitter.addWidget(self.stacked_widget)
        splitter.setSizes([200, 800])

        main_layout.addWidget(splitter)

    def _create_nav_button(self, text, icon_name):
        btn = QPushButton(text)
        btn.setCheckable(True)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(current_dir, "Data", "icons", icon_name)
        if os.path.exists(icon_path):
            btn.setIcon(QIcon(icon_path))
        btn.setIconSize(QSize(24, 24))
        btn.setMinimumHeight(50)
        return btn

    def switch_page(self, widget, clicked_button):
        for btn in self.nav_buttons:
            btn.setChecked(False)
        clicked_button.setChecked(True)
        self.stacked_widget.setCurrentWidget(widget)
        
    def load_saved_theme(self):
        """Loads the saved theme from settings, or default if not set."""
        settings = QSettings("Faniq", "NightTokyoMultiTool")
        saved_theme = settings.value("selected_theme", "night_tokyo")
        qss_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Data", "themes", f"{saved_theme}.qss")
        if os.path.exists(qss_path):
            with open(qss_path, "r") as file:
                style_sheet = file.read()
            self.apply_style(style_sheet)
            print(f"Applied saved theme: {saved_theme}")
        else:
            QMessageBox.warning(self, "Warning", f"Saved theme file not found: {qss_path}")

    def apply_style(self, style_sheet):
        """Applies a given stylesheet to the entire application."""
        qApp.setStyleSheet(style_sheet)



    def resizeEvent(self, event):
        """
        Called when the window is resized.
        Prints the new window size to the console.
        """
        new_size = event.size()
        print(f"Window resized to: Width={new_size.width()}, Height={new_size.height()}")
        # Upewnij się, że wywołujesz metodę klasy bazowej, aby zachować domyślne zachowanie
        super().resizeEvent(event)

if __name__ == "__main__":
    # Importowanie DatabaseManagerWidget w tym miejscu, aby uniknąć problemów z zależnościami
    from database_manager import DatabaseManagerWidget
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())