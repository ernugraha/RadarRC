# backend/flight_plan_store.py

import sqlite3
import json
import os
import time

class FlightPlanStore:
    def __init__(self, db_path="data/flight_plans.db"):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            # Hapus tabel lama agar skema baru (berdasarkan username) bisa dibuat
            conn.execute("DROP TABLE IF EXISTS plans")

            # Buat tabel baru berdasarkan username
            conn.execute("""
                CREATE TABLE IF NOT EXISTS plans (
                    roblox_name TEXT PRIMARY KEY,
                    plan_data TEXT
                )
            """)
            # Trail tetap menggunakan callsign
            conn.execute("""
                CREATE TABLE IF NOT EXISTS trails (
                    callsign TEXT PRIMARY KEY,
                    trail_data TEXT
                )
            """)
            conn.commit()

    # --- FLIGHT PLAN (BERDASARKAN USERNAME) ---
    def save_plan(self, roblox_name, plan_data):
        if not roblox_name: return
        try:
            plan_data["_saved_at"] = time.time()
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("INSERT OR REPLACE INTO plans (roblox_name, plan_data) VALUES (?, ?)", (roblox_name, json.dumps(plan_data)))
                conn.commit()
        except: pass

    def get_plan(self, roblox_name):
        if not roblox_name: return None
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute("SELECT plan_data FROM plans WHERE roblox_name = ?", (roblox_name,)).fetchone()
            if row: return json.loads(row[0])
        return None

    # --- TRAILS ---
    def save_trail(self, callsign, trail_points):
        if not callsign or not trail_points: return
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("INSERT OR REPLACE INTO trails (callsign, trail_data) VALUES (?, ?)", (callsign, json.dumps(trail_points)))
                conn.commit()
        except: pass

    def get_trail(self, callsign):
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute("SELECT trail_data FROM trails WHERE callsign = ?", (callsign,)).fetchone()
            if row: return json.loads(row[0])
        return []

    # --- CLEANUP ---
    def cleanup_stale_data(self, active_usernames, active_callsigns):
        if not active_usernames or not active_callsigns: return
        now = time.time()

        with sqlite3.connect(self.db_path) as conn:
            # Hapus plan jika usernamenya tidak aktif DAN umurnya lebih dari 2 jam
            all_plans = conn.execute("SELECT roblox_name, plan_data FROM plans").fetchall()
            to_del_plans = []
            for r_name, plan_json in all_plans:
                if r_name not in active_usernames:
                    plan = json.loads(plan_json)
                    if now - plan.get("_saved_at", 0) > 7200:
                        to_del_plans.append(r_name)

            if to_del_plans:
                conn.execute(f"DELETE FROM plans WHERE roblox_name IN ({','.join('?'*len(to_del_plans))})", to_del_plans)

            # Hapus trail jika callsign tidak aktif
            all_trails = [r[0] for r in conn.execute("SELECT callsign FROM trails").fetchall()]
            to_del_trails = [cs for cs in all_trails if cs not in active_callsigns]
            if to_del_trails:
                conn.execute(f"DELETE FROM trails WHERE callsign IN ({','.join('?'*len(to_del_trails))})", to_del_trails)

            conn.commit()
