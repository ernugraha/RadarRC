# backend/settings_manager.py

import json
import os

class SettingsManager:
    def __init__(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.path = os.path.join(base_dir, "data", "settings.json")

        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        self.settings = self.load()

    def load(self):
        defaults = {
            "window_width": 1400, "window_height": 900,
            "sidebar_visible": True, "show_boundaries": True,
            "show_trails": True, "show_labels": False,
            "filter_hide_ground": False, "filter_min_alt": 0,
            "filter_hide_heli": False, "show_airports": True
        }

        if os.path.exists(self.path):
            try:
                with open(self.path, "r") as f:
                    loaded = json.load(f)
                    defaults.update(loaded)
            except Exception as e:
                print(f"[SETTINGS ERROR] Failed load file: {e}")

        return defaults

    def save(self, data):
        try:
            self.settings.update(data)
            with open(self.path, "w") as f:
                json.dump(self.settings, f, indent=4)
        except Exception as e:
            print(f"[SETTINGS ERROR] Failed save: {e}")

    def get(self, key, default=None):
        return self.settings.get(key, default)
