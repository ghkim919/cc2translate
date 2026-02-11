"""번역 히스토리 SQLite 저장소"""

import os
import sqlite3

DB_DIR = os.path.expanduser("~/.local/share/cc2translate")
DB_PATH = os.path.join(DB_DIR, "history.db")
MAX_ENTRIES = 500


def _connect():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            src_text   TEXT NOT NULL,
            tgt_text   TEXT NOT NULL,
            src_lang   TEXT NOT NULL,
            tgt_lang   TEXT NOT NULL,
            model      TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    return conn


def add_entry(src_text, tgt_text, src_lang, tgt_lang, model):
    conn = _connect()
    try:
        conn.execute(
            "INSERT INTO history (src_text, tgt_text, src_lang, tgt_lang, model) "
            "VALUES (?, ?, ?, ?, ?)",
            (src_text, tgt_text, src_lang, tgt_lang, model),
        )
        # 오래된 항목 자동 삭제
        conn.execute(
            "DELETE FROM history WHERE id NOT IN "
            "(SELECT id FROM history ORDER BY id DESC LIMIT ?)",
            (MAX_ENTRIES,),
        )
        conn.commit()
    finally:
        conn.close()


def get_entries(search=""):
    conn = _connect()
    try:
        if search:
            rows = conn.execute(
                "SELECT * FROM history "
                "WHERE src_text LIKE ? OR tgt_text LIKE ? "
                "ORDER BY id DESC",
                (f"%{search}%", f"%{search}%"),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM history ORDER BY id DESC"
            ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def delete_entry(entry_id):
    conn = _connect()
    try:
        conn.execute("DELETE FROM history WHERE id = ?", (entry_id,))
        conn.commit()
    finally:
        conn.close()


def delete_all():
    conn = _connect()
    try:
        conn.execute("DELETE FROM history")
        conn.commit()
    finally:
        conn.close()
