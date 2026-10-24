# backend/settings_manager.py

import json
import os

class SettingsManager:
    def __init__(self, path="data/settings.json"):
        self.path = path
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        self.settings = self.load()

    def load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, "r") as f:
                    return json.load(f)
            except:
                pass
        return {
            "window_width": 1400,
            "window_height": 900,
            "sidebar_visible": True,
            "show_boundaries": True,
            "show_trails": True,
            "show_labels": False
        }

    def save(self, data):
        self.settings.update(data)
        with open(self.path, "w") as f:
            json.dump(self.settings, f, indent=4)

    def get(self, key, default=None):
        return self.settings.get(key, default)
