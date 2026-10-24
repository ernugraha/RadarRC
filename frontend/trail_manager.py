# frontend/trail_manager.py

import time
import math
from backend.flight_plan_store import FlightPlanStore

class TrailManager:
    def __init__(self, max_points=10000):
        self.max_points = max_points
        self.trails = {}
        self.db = FlightPlanStore()
        self.last_save_time = 0

    def add_point(self, callsign, x, y, alt):
        if callsign not in self.trails:
            self.trails[callsign] = self.db.get_trail(callsign)

        trail = self.trails[callsign]

        if len(trail) > 0:
            last = trail[-1]
            # FILTER JARAK: Jika pesawat bergerak kurang dari 2 unit, abaikan.
            # Ini mencegah penumpukan titik saat pesawat hover/berputar di landasan.
            dist = math.hypot(last["x"] - x, last["y"] - y)
            if dist < 2.0:
                return

        trail.append({"x": x, "y": y, "alt": alt})

        if len(trail) > self.max_points:
            trail.pop(0)

    def get_trail(self, callsign):
        if callsign not in self.trails:
            self.trails[callsign] = self.db.get_trail(callsign)
        return self.trails.get(callsign, [])

    def sync_to_db(self):
        now = time.time()
        if now - self.last_save_time > 2.0:
            for cs, trail in self.trails.items():
                self.db.save_trail(cs, trail)
            self.last_save_time = now

    def cleanup(self, active_callsigns):
        inactive = [cs for cs in self.trails.keys() if cs not in active_callsigns]
        for cs in inactive:
            del self.trails[cs]
