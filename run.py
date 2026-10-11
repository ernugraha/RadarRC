# run.py
"""
RadarRC Launcher
Jalankan ATC24 bridge (subprocess) + frontend (main process).
"""

import subprocess
import sys
import os
import signal
import time

# Deteksi apakah program berjalan sebagai hasil build (.exe / AppImage)
if getattr(sys, 'frozen', False):
    project_root = sys._MEIPASS
else:
    project_root = os.path.dirname(os.path.abspath(__file__))

# Paksa pindah ke direktori yang benar
os.chdir(project_root)

def main():
    print("[RadarRC] Starting ATC24 bridge...")

    # Gunakan project_root sebagai cwd agar backend juga aman saat di-build
    backend_proc = subprocess.Popen(
        [sys.executable, "-m", "backend.atc24_bridge"],
        cwd=project_root,
        stdout=sys.stdout,
        stderr=sys.stderr,
    )

    time.sleep(2)

    try:
        print("[RadarRC] Starting frontend...")
        from frontend.main import main as frontend_main
        frontend_main()
    except KeyboardInterrupt:
        print("\n[RadarRC] Stopped by user.")
    finally:
        print("[RadarRC] Stopping bridge...")
        backend_proc.send_signal(signal.SIGINT)
        try:
            backend_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            backend_proc.kill()
        print("[RadarRC] Done.")


if __name__ == "__main__":
    main()
