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

    def on_app_close():
        print("\n[INFO] Closing app...")
        client.stop()
        ws_task.cancel()
        loop.stop()

    app.aboutToQuit.connect(on_app_close)

    with loop:
        sys.exit(loop.run_forever())

if __name__ == "__main__":
    main()
