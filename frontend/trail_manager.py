# frontend/trail_manager.py

import time
from backend.flight_plan_store import FlightPlanStore

class TrailManager:
    def __init__(self, max_points=300):
        self.max_points = max_points
        self.trails = {} # { "BAW123": [{"x": 10, "y": 20, "alt": 3000}, ...] }
        self.db = FlightPlanStore()
        self.last_save_time = 0

    def add_point(self, callsign, x, y, alt):
        if callsign not in self.trails:
            # Muat dari database jika ada (Persistensi)
            saved_trail = self.db.get_trail(callsign)
            self.trails[callsign] = saved_trail if saved_trail else []

        trail = self.trails[callsign]

        # Hindari duplikasi titik jika pesawat diam
        if len(trail) > 0:
            last = trail[-1]
            if abs(last["x"] - x) < 0.5 and abs(last["y"] - y) < 0.5:
                return

        trail.append({"x": x, "y": y, "alt": alt})

        # Batasi panjang memori
        if len(trail) > self.max_points:
            trail.pop(0)

    def get_trail(self, callsign):
        return self.trails.get(callsign, [])

    def sync_to_db(self):
        """Menyimpan semua trail aktif ke database setiap 2 detik."""
        now = time.time()
        if now - self.last_save_time > 2.0:
            for cs, trail in self.trails.items():
                self.db.save_trail(cs, trail)
            self.last_save_time = now

    def cleanup(self, active_callsigns):
        """Hapus dari memori jika pesawat hilang."""
        inactive = [cs for cs in self.trails.keys() if cs not in active_callsigns]
        for cs in inactive:
            del self.trails[cs]
