"""
db.py – lightweight SQLite history store for TERMAI
Keeps a rolling log of executed commands and their results.

Table: history
    id   INTEGER  PK
    cmd  TEXT     – user’s natural-language instruction
    res  TEXT     – truncated result / error (first 3000 chars)
    lang TEXT     – language code (he/en/…)
    dt   DATETIME – default current_timestamp
"""

import sqlite3
import os
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "history.db"

# ---------- init -------------------------------------------------------------
def init_db():
    """Create DB/table if missing."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """CREATE TABLE IF NOT EXISTS history(
              id   INTEGER PRIMARY KEY AUTOINCREMENT,
              cmd  TEXT,
              res  TEXT,
              lang TEXT,
              dt   DATETIME DEFAULT CURRENT_TIMESTAMP
        )"""
    )
    conn.close()

# call on import
init_db()

# ---------- helpers ----------------------------------------------------------
def insert_history(cmd: str, res: str, lang: str):
    """Store executed command & first 3000 chars of result."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO history(cmd, res, lang) VALUES (?,?,?)",
        (cmd, res[:3000], lang),
    )
    conn.commit()
    conn.close()

def get_history(limit: int = 30):
    """Return last N rows (default 30) newest first."""
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT cmd, res, lang, dt FROM history "
        "ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return rows

