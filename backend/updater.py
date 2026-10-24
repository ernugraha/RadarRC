# backend/updater.py

import urllib.request
import zipfile
import io
import os
import shutil
import json
import tempfile
from PySide6.QtCore import QThread, Signal

# GANTI DENGAN USERNAME DAN REPO GITHUB ANDA
GITHUB_REPO = "ernugraha/RadarRC"
BRANCH = "main"
VERSION_FILE = "data/assets_version.txt" # Menyimpan hash khusus aset

class AutoUpdater(QThread):
    update_finished = Signal(bool, str) # (berhasil, pesan)

    def run(self):
        try:
            # 1. Cek commit terakhir KHUSUS folder 'assets' di GitHub
            api_url = f"https://api.github.com/repos/{GITHUB_REPO}/commits?path=assets&per_page=1"
            req = urllib.request.Request(api_url, headers={'User-Agent': 'RadarRC-Updater'})

            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode())
                if not data:
                    self.update_finished.emit(False, "No assets on github.")
                    return
                latest_sha = data[0]['sha']

            # 2. Cek versi aset lokal
            local_sha = ""
            if os.path.exists(VERSION_FILE):
                with open(VERSION_FILE, "r") as f:
                    local_sha = f.read().strip()

            # Jika sama, tidak perlu update
            if latest_sha == local_sha:
                self.update_finished.emit(False, "Assets are on newest version.")
                return

            # 3. Unduh ZIP kode terbaru
            zip_url = f"https://github.com/{GITHUB_REPO}/archive/refs/heads/{BRANCH}.zip"
            zip_req = urllib.request.Request(zip_url, headers={'User-Agent': 'RadarRC-Updater'})

            with urllib.request.urlopen(zip_req) as response:
                zip_data = response.read()

            # 4. Ekstrak ke folder sementara
            temp_dir = tempfile.mkdtemp()
            with zipfile.ZipFile(io.BytesIO(zip_data)) as z:
                z.extractall(temp_dir)

            # 5. Timpa HANYA folder 'assets'
            extracted_folder = os.path.join(temp_dir, f"RadarRC-{BRANCH}")
            src_assets = os.path.join(extracted_folder, "assets")
            dst_assets = os.path.join(os.getcwd(), "assets")

            if os.path.exists(src_assets):
                shutil.copytree(src_assets, dst_assets, dirs_exist_ok=True)

            # 6. Simpan SHA aset yang baru
            os.makedirs(os.path.dirname(VERSION_FILE), exist_ok=True)
            with open(VERSION_FILE, "w") as f:
                f.write(latest_sha)

            shutil.rmtree(temp_dir)
            self.update_finished.emit(True, "Assets had been updated!")

        except Exception as e:
            self.update_finished.emit(False, f"Failed to update: {e}")
