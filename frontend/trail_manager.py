# frontend/trail_manager.py

import time
from backend.flight_plan_store import FlightPlanStore

class TrailManager:
    def __init__(self, max_points=10000): # Maksimal 10.000 titik (sangat panjang)
        self.max_points = max_points
        self.trails = {}
        self.db = FlightPlanStore()
        self.last_save_time = 0

    def add_point(self, callsign, x, y, alt):
        if callsign not in self.trails:
            # Muat dari database (jika ada sisa perjalanan sebelumnya)
            self.trails[callsign] = self.db.get_trail(callsign)

        trail = self.trails[callsign]

        # Jangan tambah titik jika pesawat tidak bergerak (mencegah penumpukan)
        if len(trail) > 0:
            last = trail[-1]
            if abs(last["x"] - x) < 0.5 and abs(last["y"] - y) < 0.5:
                return

        trail.append({"x": x, "y": y, "alt": alt})

        if len(trail) > self.max_points:
            trail.pop(0) # Hanya terpotong jika sudah 10.000 titik

    def get_trail(self, callsign):
        if callsign not in self.trails:
            self.trails[callsign] = self.db.get_trail(callsign)
        return self.trails.get(callsign, [])

    def sync_to_db(self):
        now = time.time()
        if now - self.last_save_time > 2.0: # Simpan tiap 2 detik
            for cs, trail in self.trails.items():
                self.db.save_trail(cs, trail)
            self.last_save_time = now

    def cleanup(self, active_callsigns):
        inactive = [cs for cs in self.trails.keys() if cs not in active_callsigns]
        for cs in inactive:
            del self.trails[cs]
