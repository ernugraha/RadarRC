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
VERSION_FILE = "data/version.txt"

class AutoUpdater(QThread):
    update_finished = Signal(bool, str) # (berhasil, pesan)

    def run(self):
        try:
            # 1. Cek commit terakhir di GitHub
            api_url = f"https://api.github.com/repos/{GITHUB_REPO}/commits/{BRANCH}"
            req = urllib.request.Request(api_url, headers={'User-Agent': 'RadarRC-Updater'})

            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode())
                latest_sha = data['sha']

            # 2. Cek versi lokal
            local_sha = ""
            if os.path.exists(VERSION_FILE):
                with open(VERSION_FILE, "r") as f:
                    local_sha = f.read().strip()

            # Jika sama, tidak perlu update
            if latest_sha == local_sha:
                self.update_finished.emit(False, "Aplikasi sudah versi terbaru.")
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

            # 5. Timpa file di folder proyek (KECUALI data dan assets)
            extracted_folder = os.path.join(temp_dir, f"RadarRC-{BRANCH}")

            for item in os.listdir(extracted_folder):
                if item in ["data", "assets", ".git", "venv", "__pycache__"]:
                    continue # Jangan hapus database dan aset gambar

                s = os.path.join(extracted_folder, item)
                d = os.path.join(os.getcwd(), item)

                if os.path.isdir(s):
                    shutil.copytree(s, d, dirs_exist_ok=True)
                else:
                    shutil.copy2(s, d)

            # 6. Simpan SHA baru
            with open(VERSION_FILE, "w") as f:
                f.write(latest_sha)

            shutil.rmtree(temp_dir)
            self.update_finished.emit(True, "Update Downloaded! Application need to be restarted.")

        except Exception as e:
            self.update_finished.emit(False, f"Failed check update: {e}")
