# run.py

import sys
import asyncio
from PySide6.QtWidgets import QApplication
from qasync import QEventLoop

from frontend.main_window import MainWindow
from backend.api_client import DataClient

def main():
    app = QApplication(sys.argv)

    # 1. Buat event loop qasync
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    # 2. Inisialisasi UI
    window = MainWindow()
    window.show()

    # 3. Inisialisasi Backend dan Hubungkan Sinyal
    client = DataClient()

    # Tampilkan log status koneksi ke terminal
    client.connection_status.connect(lambda msg: print(msg))

    # Hubungkan data pesawat dari backend ke fungsi update UI
    client.aircraft_data_received.connect(window.update_aircraft)

    # 4. Jalankan koneksi WebSocket di background
    loop.create_task(client.connect())

    # 5. Jalankan aplikasi
    with loop:
        sys.exit(loop.run_forever())

if __name__ == "__main__":
    main()
