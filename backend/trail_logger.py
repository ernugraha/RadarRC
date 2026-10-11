# backend/trail_logger.py
"""RadarRC - Trail Logger: rekam posisi pesawat ke SQLite."""

import sqlite3
import os
import time
from .paths_helper import get_data_dir


class TrailLogger:
    def __init__(self, db_path=None):
        if db_path is None:
            data_dir = get_data_dir()
            os.makedirs(data_dir, exist_ok=True)
            db_path = os.path.join(data_dir, "trails.db")
        self.db_path = db_path
        self._init_db()
        self._last_positions = {}

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS trails (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                callsign TEXT NOT NULL,
                x REAL NOT NULL,
                y REAL NOT NULL,
                altitude REAL,
                heading REAL,
                timestamp REAL NOT NULL
            )
        """)
        c.execute("""
            CREATE INDEX IF NOT EXISTS idx_callsign_time
            ON trails(callsign, timestamp)
        """)
        conn.commit()
        conn.close()

    def log_batch(self, aircraft_data):
        if not aircraft_data:
            return
        now = time.time()
        rows = []
        for cs, info in aircraft_data.items():
            x = info.get("x", 0)
            y = info.get("y", 0)
            last = self._last_positions.get(cs)
            if last and abs(last[0] - x) < 0.5 and abs(last[1] - y) < 0.5:
                continue
            self._last_positions[cs] = (x, y, now)
            rows.append((
                cs, x, y,
                info.get("altitude", 0),
                info.get("heading", 0),
                now,
            ))
        if not rows:
            return
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.executemany(
                "INSERT INTO trails (callsign, x, y, altitude, heading, timestamp) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                rows,
            )
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[TrailLogger] Error: {e}")

    def cleanup_old(self, max_age_seconds=1200):
        cutoff = time.time() - max_age_seconds
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("DELETE FROM trails WHERE timestamp < ?", (cutoff,))
            deleted = c.rowcount
            conn.commit()
            conn.close()
            if deleted > 0:
                print(f"[TrailLogger] Cleanup: {deleted} rows removed")
        except Exception as e:
            print(f"[TrailLogger] Cleanup error: {e}")
