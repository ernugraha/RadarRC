# run.py

import sys
import asyncio
from PySide6.QtWidgets import QApplication
from qasync import QEventLoop

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

        # KUNCI PERBAIKAN: Putuskan semua sinyal agar UI tidak di-update saat sedang dihancurkan
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
