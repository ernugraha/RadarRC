# frontend/main.py

import tkinter as tk
from .radar_canvas import RadarCanvas
from .websocket_client import WebSocketClient
from . import config


class RadarApp:
    def __init__(self, root):
        self.root = root
        self.root.title(config.WINDOW_TITLE)
        self.root.configure(bg=config.BG_COLOR)

        self.radar = RadarCanvas(root)

        self.ws_client = WebSocketClient(on_data=self._on_data)
        self.ws_client.start()

        self._schedule_update()

    def _on_data(self, data):
        self._latest_data = data

    def _schedule_update(self):
        data = self.ws_client.get_latest()
        self.radar.update(data)
        self.root.after(200, self._schedule_update)


def main():
    root = tk.Tk()

    # 1. Pasang ikon terlebih dahulu sebelum jendela ditahan oleh mainloop
    try:
        icon_img = tk.PhotoImage(file="/home/ernugraha/Documents/Codes/Python/RadarRC/assets/icon.png")
        root.iconphoto(True, icon_img)
    except Exception as e:
        print(f"[RadarRC] Icon couldnt loaded: {e}")

    # 2. Inisialisasi aplikasi utama
    app = RadarApp(root)

    # 3. Jalankan loop UI di paling akhir
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("\n[RadarRC] Frontend stopped.")
        app.ws_client.stop()

if __name__ == "__main__":
    main()
