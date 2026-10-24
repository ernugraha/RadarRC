# run.py

import sys
import os
import shutil
import asyncio
from PySide6.QtWidgets import QApplication
from qasync import QEventLoop

# --- BOOTSTRAP UNTUK PYINSTALLER ---
if getattr(sys, 'frozen', False):
    # Tentukan folder user data
    if sys.platform == 'win32':
        base_dir = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'RadarRC')
    else:
        base_dir = os.path.join(os.path.expanduser('~'), '.radarrc')
    os.makedirs(base_dir, exist_ok=True)

    # Salin assets bawaan ke folder user jika belum ada
    user_assets = os.path.join(base_dir, "assets")
    if not os.path.exists(user_assets):
        print("[INFO] First run: Copying bundled assets to user directory...")
        bundled_assets = os.path.join(sys._MEIPASS, "assets")
        if os.path.exists(bundled_assets):
            shutil.copytree(bundled_assets, user_assets)
            print(f"[SUCCESS] Assets copied to {user_assets}")

    # Pindah ke direktori user agar semua path relatif (assets/...) bekerja
    os.chdir(base_dir)
# ------------------------------------

from frontend.main_window import MainWindow
from backend.api_client import DataClient

def main():
    app = QApplication(sys.argv)

    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    window = MainWindow()
    window.show()

    client = DataClient()
    client.connection_status.connect(lambda msg: print(msg))
    client.aircraft_data_received.connect(window.update_aircraft)
    client.atis_data_received.connect(window.update_atis)

    ws_task = loop.create_task(client.connect())

    shutting_down = False

    def on_app_close():
        nonlocal shutting_down
        if shutting_down:
            return
        shutting_down = True

        print("\n[INFO] Closing app...")
        try:
            client.aircraft_data_received.disconnect()
            client.atis_data_received.disconnect()
            client.connection_status.disconnect()
        except Exception:
            pass

        client.stop()
        if not ws_task.done():
            ws_task.cancel()

    app.aboutToQuit.connect(on_app_close)

    with loop:
        sys.exit(loop.run_forever())

if __name__ == "__main__":
    main()
