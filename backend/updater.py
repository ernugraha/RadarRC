# backend/updater.py

import urllib.request
import zipfile
import io
import os
import sys
import shutil
import json
import tempfile
from PySide6.QtCore import QThread, Signal

# CHANGE WITH YOUR GITHUB USERNAME AND REPO
GITHUB_REPO = "ernugraha/RadarRC"
BRANCH = "main"

def get_data_dir():
    """Mendapatkan folder penyimpanan yang aman untuk aplikasi."""
    if getattr(sys, 'frozen', False):
        if sys.platform == 'win32':
            base_dir = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'RadarRC')
        else:
            base_dir = os.path.join(os.path.expanduser('~'), '.radarrc')
    else:
        base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
    os.makedirs(base_dir, exist_ok=True)
    return base_dir

def get_assets_dir():
    """Lokasi folder assets yang bisa ditulis (writable)."""
    if getattr(sys, 'frozen', False):
        # Di versi .exe, assets ada di folder user (sudah disalin oleh run.py)
        return os.path.join(get_data_dir(), 'assets')
    else:
        # Di mode development, assets ada di folder proyek
        return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'assets')

class AutoUpdater(QThread):
    update_finished = Signal(bool, str)

    def run(self):
        version_file = os.path.join(get_data_dir(), "assets_version.txt")
        asset_dir = get_assets_dir()

        try:
            # 1. Cek commit terbaru folder 'assets' di GitHub
            api_url = f"https://api.github.com/repos/{GITHUB_REPO}/commits?path=assets&per_page=1"
            req = urllib.request.Request(api_url, headers={'User-Agent': 'RadarRC-Updater'})

            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode())
                if not data:
                    self.update_finished.emit(False, "No asset data found on GitHub.")
                    return
                latest_sha = data[0]['sha']

            # 2. Cek versi lokal
            local_sha = ""
            if os.path.exists(version_file):
                with open(version_file, "r") as f:
                    local_sha = f.read().strip()

            if latest_sha == local_sha:
                self.update_finished.emit(False, "Assets are already up to date.")
                return

            # 3. Unduh ZIP
            zip_url = f"https://github.com/{GITHUB_REPO}/archive/refs/heads/{BRANCH}.zip"
            zip_req = urllib.request.Request(zip_url, headers={'User-Agent': 'RadarRC-Updater'})

            with urllib.request.urlopen(zip_req) as response:
                zip_data = response.read()

            # 4. Extract ke folder sementara
            temp_dir = tempfile.mkdtemp()
            with zipfile.ZipFile(io.BytesIO(zip_data)) as z:
                z.extractall(temp_dir)

            # 5. Timpa folder 'assets'
            extracted_folder = os.path.join(temp_dir, f"RadarRC-{BRANCH}")
            src_assets = os.path.join(extracted_folder, "assets")

            if os.path.exists(src_assets):
                shutil.copytree(src_assets, asset_dir, dirs_exist_ok=True)

            # 6. Simpan SHA baru
            with open(version_file, "w") as f:
                f.write(latest_sha)

            shutil.rmtree(temp_dir)
            self.update_finished.emit(True, "Assets (Icons, Logos, Maps) updated successfully!")

        except Exception as e:
            self.update_finished.emit(False, f"Failed to check for updates: {e}")
