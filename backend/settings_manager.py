# backend/settings_manager.py

import json
import os
import sys

def get_data_dir():
    """Mendapatkan folder penyimpanan yang aman untuk aplikasi."""
    if getattr(sys, 'frozen', False):
        # Mode PyInstaller (.exe / executable)
        if sys.platform == 'win32':
            base_dir = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'RadarRC')
        else:
            base_dir = os.path.join(os.path.expanduser('~'), '.radarrc')
    else:
        # Mode Development (python run.py)
        base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
    os.makedirs(base_dir, exist_ok=True)
    return base_dir

class SettingsManager:
    def __init__(self):
        self.path = os.path.join(get_data_dir(), "settings.json")
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
                print(f"[SETTINGS ERROR] Failed to load file: {e}")

        return defaults

    def save(self, data):
        try:
            self.settings.update(data)
            with open(self.path, "w") as f:
                json.dump(self.settings, f, indent=4)
        except Exception as e:
            print(f"[SETTINGS ERROR] Failed to save: {e}")

    def get(self, key, default=None):
        return self.settings.get(key, default)
