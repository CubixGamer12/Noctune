import os
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QComboBox, QPushButton, QHBoxLayout, QSizePolicy
from PySide6.QtCore import Signal, Qt # Dodano import Qt

class SettingsWidget(QWidget):
    """
    A widget for application settings, including theme selection.
    """
    theme_changed = Signal(str) # Sygnał, który będzie emitowany po zmianie motywu

    def __init__(self, current_theme_name):
        super().__init__()
        self.current_theme_name = current_theme_name
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(50, 50, 50, 50)
        layout.setSpacing(20)

        # Title
        title_label = QLabel("Settings")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 32px; font-weight: bold; color: #a78bfa;")
        layout.addWidget(title_label)

        # Theme selection
        theme_layout = QHBoxLayout()
        theme_label = QLabel("Select Theme:")
        theme_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        theme_layout.addWidget(theme_label)
        
        self.theme_combo_box = QComboBox()
        self.theme_combo_box.addItems(["Night Tokyo (Dark)", "Dark Flat", "Light Gray"]) # Dodajemy motywy
        
        # Ustawienie początkowej wartości ComboBox na podstawie zapisanego motywu
        index = self.theme_combo_box.findText(self.current_theme_name)
        if index != -1:
            self.theme_combo_box.setCurrentIndex(index)

        self.theme_combo_box.setMinimumWidth(200)
        theme_layout.addWidget(self.theme_combo_box)
        theme_layout.addStretch() # Rozciągliwa przestrzeń po prawej
        
        layout.addLayout(theme_layout)
        
        # Separator (opcjonalnie, dla lepszego wyglądu)
        layout.addSpacing(30)
        
        # Zapisz przycisk (opcjonalnie, można też zmieniać na bieżąco)
        save_button = QPushButton("Apply Theme")
        save_button.setStyleSheet("font-weight: bold;")
        save_button.clicked.connect(self.apply_theme)
        
        layout.addWidget(save_button, alignment=Qt.AlignHCenter)
        
        layout.addStretch() # Wypchnięcie wszystkiego do góry

    def apply_theme(self):
        """Emits a signal with the selected theme name."""
        selected_theme = self.theme_combo_box.currentText()
        self.theme_changed.emit(selected_theme)