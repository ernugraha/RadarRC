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
            conn.execute("""
                CREATE TABLE IF NOT EXISTS trails (
                    callsign TEXT PRIMARY KEY,
                    trail_data TEXT
                )
            """)
            conn.commit()

    # --- FLIGHT PLAN ---
    def save_plan(self, callsign, plan_data):
        if not callsign: return
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("INSERT OR REPLACE INTO plans (callsign, plan_data) VALUES (?, ?)", (callsign, json.dumps(plan_data)))
                conn.commit()
        except: pass

    def get_plan(self, callsign):
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute("SELECT plan_data FROM plans WHERE callsign = ?", (callsign,)).fetchone()
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
    def cleanup_stale_data(self, active_callsigns):
        if not active_callsigns: return
        with sqlite3.connect(self.db_path) as conn:
            # Hapus plans
            all_plans = [r[0] for r in conn.execute("SELECT callsign FROM plans").fetchall()]
            to_del_plans = [cs for cs in all_plans if cs not in active_callsigns]
            if to_del_plans:
                conn.execute(f"DELETE FROM plans WHERE callsign IN ({','.join('?'*len(to_del_plans))})", to_del_plans)

            # Hapus trails
            all_trails = [r[0] for r in conn.execute("SELECT callsign FROM trails").fetchall()]
            to_del_trails = [cs for cs in all_trails if cs not in active_callsigns]
            if to_del_trails:
                conn.execute(f"DELETE FROM trails WHERE callsign IN ({','.join('?'*len(to_del_trails))})", to_del_trails)

            conn.commit()
