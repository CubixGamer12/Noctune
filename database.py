import sqlite3
import os

DB_FILE = 'songs.db'

def init_db():
    os.makedirs("songs", exist_ok=True)
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute(
            '''CREATE TABLE IF NOT EXISTS songs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE
            )'''
        )

def add_song(name):
    with sqlite3.connect(DB_FILE) as conn:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM songs WHERE name=?", (name,))
        if not cur.fetchone():
            cur.execute("INSERT INTO songs (name) VALUES (?)", (name,))
            conn.commit()

def delete_song_by_id(song_id):
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("DELETE FROM songs WHERE id=?", (song_id,))
        conn.commit()

def get_all_songs():
    with sqlite3.connect(DB_FILE) as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, name FROM songs")
        return cur.fetchall()

def update_song(song_id, new_name):
    with sqlite3.connect(DB_FILE) as conn:
        cur = conn.cursor()
        cur.execute("UPDATE songs SET name=? WHERE id=?", (new_name, song_id))
        conn.commit()

def clear_all_songs():
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("DELETE FROM songs")
        conn.commit()