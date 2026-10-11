# frontend/paths.py
import sys
import os


def is_frozen():
    return getattr(sys, "frozen", False)


def get_base_dir():
    if is_frozen():
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_assets_dir():
    return os.path.join(get_base_dir(), "assets")


def get_config_dir():
    return os.path.join(get_base_dir(), "config")


def get_aircraft_dir():
    return os.path.join(get_assets_dir(), "aircraft")


def get_maps_dir():
    return os.path.join(get_assets_dir(), "maps")


def ensure_dirs():
    for d in [get_assets_dir(), get_aircraft_dir(),
              get_maps_dir(), get_config_dir()]:
        os.makedirs(d, exist_ok=True)
