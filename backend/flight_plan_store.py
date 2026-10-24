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
            conn.execute("""
                CREATE TABLE IF NOT EXISTS plans (
                    callsign TEXT PRIMARY KEY,
                    plan_data TEXT
                )
            """)
            conn.commit()

    def save_plan(self, callsign, plan_data):
        """Menyimpan atau memperbarui flight plan."""
        if not callsign:
            return

        # Hanya simpan data yang penting (sesuaikan dengan API)
        # Plan dari ATC24 biasanya berisi: aircraft, departing, arriving, route, dll.
        try:
            plan_json = json.dumps(plan_data)
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO plans (callsign, plan_data) VALUES (?, ?)",
                    (callsign, plan_json)
                )
                conn.commit()
        except Exception as e:
            print(f"Error saving plan: {e}")

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
        """Mengambil semua flight plan (untuk keperluan inisialisasi memori)."""
        plans = {}
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT callsign, plan_data FROM plans")
            for row in cursor.fetchall():
                plans[row[0]] = json.loads(row[1])
        return plans

    def cleanup_stale_plans(self, active_callsigns):
        """Menghapus flight plan yang pesawatnya sudah tidak ada di radar."""
        if not active_callsigns:
            return

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT callsign FROM plans")
            all_saved = [row[0] for row in cursor.fetchall()]

            # Cari yang ada di database tapi TIDAK ADA di pesawat aktif
            to_delete = [cs for cs in all_saved if cs not in active_callsigns]

            if to_delete:
                # Hapus dari database
                placeholders = ','.join('?' for _ in to_delete)
                conn.execute(f"DELETE FROM plans WHERE callsign IN ({placeholders})", to_delete)
                conn.commit()
                print(f"[CLEANUP] Menghapus {len(to_delete)} flight plan usang.")
