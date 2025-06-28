import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QListWidget,
    QInputDialog, QMessageBox, QApplication
)
from PySide6.QtCore import Qt, Signal
import database

class DatabaseManagerWidget(QWidget):
    """A widget for managing entries in the database."""
    def __init__(self):
        super().__init__()
        database.init_db()  # Initialize the database when the widget is created
        self.init_ui()
        self.load_songs()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)

        title_label = QLabel("Song Database Manager")
        title_label.setAlignment(Qt.AlignCenter)
        # Zmieniono: usunięto kolor, dodano objectName
        title_label.setObjectName("h1_label")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(title_label)

        # Add Entry Section
        add_layout = QHBoxLayout()
        self.add_line_edit = QLineEdit()
        self.add_line_edit.setPlaceholderText("Enter song name to add...")
        add_button = QPushButton("Add Song")
        add_button.setObjectName("dark_button")
        add_button.clicked.connect(self.add_song)
        add_layout.addWidget(self.add_line_edit)
        add_layout.addWidget(add_button)
        layout.addLayout(add_layout)

        # List Widget
        self.song_list_widget = QListWidget()
        layout.addWidget(self.song_list_widget)

        # Action Buttons
        button_layout = QHBoxLayout()
        remove_button = QPushButton("Remove Selected")
        remove_button.setObjectName("dark_button")
        remove_button.clicked.connect(self.remove_song)
        
        edit_button = QPushButton("Edit Selected")
        edit_button.setObjectName("dark_button")
        edit_button.clicked.connect(self.edit_song)

        clear_button = QPushButton("Clear Database")
        clear_button.setObjectName("dark_button")
        clear_button.clicked.connect(self.clear_database)
        
        button_layout.addWidget(remove_button)
        button_layout.addWidget(edit_button)
        button_layout.addWidget(clear_button)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)

    def load_songs(self):
        self.song_list_widget.clear()
        songs = database.get_all_songs()
        for song in songs:
            self.song_list_widget.addItem(f"{song[0]} - {song[1]}") # id - name

    def add_song(self):
        song_name = self.add_line_edit.text().strip()
        if song_name:
            database.add_song(song_name)
            self.add_line_edit.clear()
            self.load_songs()
            QMessageBox.information(self, "Success", f"Song '{song_name}' added to the database.")
        else:
            QMessageBox.warning(self, "Input Error", "Please enter a song name.")

    def remove_song(self):
        selected_item = self.song_list_widget.currentItem()
        if selected_item:
            # Extract the ID from the list item's text (e.g., "1 - Song Name")
            song_id = int(selected_item.text().split(' ')[0])
            database.remove_song(song_id)
            self.load_songs()
            QMessageBox.information(self, "Success", "Song removed from the database.")
        else:
            QMessageBox.warning(self, "Selection Error", "Please select a song to remove.")

    def edit_song(self):
        selected_item = self.song_list_widget.currentItem()
        if selected_item:
            song_id = int(selected_item.text().split(' ')[0])
            old_name = " ".join(selected_item.text().split(' ')[2:])
            
            new_name, ok = QInputDialog.getText(self, "Edit Song", "Enter new song name:", QLineEdit.Normal, old_name)
            if ok and new_name:
                database.update_song(song_id, new_name)
                self.load_songs()
                QMessageBox.information(self, "Success", "Song name updated.")
        else:
            QMessageBox.warning(self, "Selection Error", "Please select a song to edit.")
            
    def clear_database(self):
        if QMessageBox.question(self, "Clear Database", "Are you sure you want to clear the entire database? This action cannot be undone.",
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            database.clear_all_songs()
            self.load_songs()
            QMessageBox.information(self, "Success", "Database has been cleared.")