# backend/paths_helper.py
import sys
import os


def get_base_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_data_dir():
    return os.path.join(get_base_dir(), "data")
