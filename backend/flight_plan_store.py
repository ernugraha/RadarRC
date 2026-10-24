# backend/flight_plan_store.py

import sqlite3
import json
import os

class FlightPlanStore:
    def __init__(self, db_path="data/flight_plans.db"):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            # Tabel Flight Plan
            conn.execute("""
                CREATE TABLE IF NOT EXISTS plans (
                    callsign TEXT PRIMARY KEY,
                    plan_data TEXT
                )
            """)
            # Tabel Trail (Jejak)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS trails (
                    callsign TEXT PRIMARY KEY,
                    trail_data TEXT
                )
            """)
            conn.commit()

    # ================= FUNGSI FLIGHT PLAN =================
    def save_plan(self, callsign, plan_data):
        """Menyimpan atau memperbarui flight plan."""
        if not callsign:
            return
        try:
            plan_json = json.dumps(plan_data)
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO plans (callsign, plan_data) VALUES (?, ?)",
                    (callsign, plan_json)
                )
                conn.commit()
        except Exception:
            pass

    def get_plan(self, callsign):
        """Mengambil flight plan berdasarkan callsign."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT plan_data FROM plans WHERE callsign = ?", (callsign,)
            )
            row = cursor.fetchone()
            if row:
                return json.loads(row[0])
        return None

    def get_all_plans(self):
        """Mengambil semua flight plan."""
        plans = {}
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT callsign, plan_data FROM plans")
            for row in cursor.fetchall():
                plans[row[0]] = json.loads(row[1])
        return plans

    # ================= FUNGSI TRAIL =================
    def save_trail(self, callsign, trail_points):
        """Menyimpan list koordinat [(x,y,alt), ...] ke database."""
        if not callsign or not trail_points:
            return
        try:
            trail_json = json.dumps(trail_points)
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO trails (callsign, trail_data) VALUES (?, ?)",
                    (callsign, trail_json)
                )
                conn.commit()
        except Exception:
            pass

    def get_trail(self, callsign):
        """Mengambil data trail pesawat."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT trail_data FROM trails WHERE callsign = ?", (callsign,)
            )
            row = cursor.fetchone()
            if row:
                return json.loads(row[0])
        return []

    # ================= FUNGSI CLEANUP =================
    def cleanup_stale_data(self, active_callsigns):
        """Menghapus flight plan DAN trail usang yang pesawatnya sudah tidak ada."""
        if not active_callsigns: return

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT callsign FROM plans")
            all_plans = [row[0] for row in cursor.fetchall()]
            to_delete_plans = [cs for cs in all_plans if cs not in active_callsigns]

            cursor = conn.execute("SELECT callsign FROM trails")
            all_trails = [row[0] for row in cursor.fetchall()]
            to_delete_trails = [cs for cs in all_trails if cs not in active_callsigns]

            if to_delete_plans:
                placeholders = ','.join('?' for _ in to_delete_plans)
                conn.execute(f"DELETE FROM plans WHERE callsign IN ({placeholders})", to_delete_plans)

            if to_delete_trails:
                placeholders = ','.join('?' for _ in to_delete_trails)
                conn.execute(f"DELETE FROM trails WHERE callsign IN ({placeholders})", to_delete_trails)

            conn.commit()
