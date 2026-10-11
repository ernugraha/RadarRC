# frontend/websocket_client.py

import asyncio
import websockets
import json
import threading
from .config import WS_URL

class WebSocketClient:
    def __init__(self, on_data):
        """
        on_data: callback function yang dipanggil setiap data baru diterima.
                 Signature: on_data(dict)
        """
        self.on_data = on_data
        self._latest = {}
        self._lock = threading.Lock()
        self._running = True

    def start(self):
        """Jalankan klien di thread terpisah."""
        thread = threading.Thread(target=self._run, daemon=True)
        thread.start()

    def _run(self):
        asyncio.run(self._listen())

    async def _listen(self):
        while self._running:
            try:
                async with websockets.connect(WS_URL) as ws:
                    print(f"[RadarRC] Connected to {WS_URL}")
                    async for message in ws:
                        try:
                            data = json.loads(message)
                            with self._lock:
                                self._latest = data
                            # Panggil callback
                            self.on_data(data)
                        except json.JSONDecodeError:
                            pass
            except Exception as e:
                print(f"[RadarRC] WebSocket error: {e}. retry in dalam 3 detik...")
                await asyncio.sleep(3)

    def get_latest(self):
        with self._lock:
            return self._latest.copy()

    def stop(self):
        self._running = False