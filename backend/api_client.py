# backend/api_client.py

import json
import asyncio
import websockets
from PySide6.QtCore import QObject, Signal
from backend.flight_plan_store import FlightPlanStore # IMPORT STORE BARU

class DataClient(QObject):
    aircraft_data_received = Signal(dict)
    connection_status = Signal(str)

    def __init__(self):
        super().__init__()
        self.ws_url = "wss://24data.ptfs.app/wss"
        self.is_running = False

        # Inisialisasi Database
        self.plan_store = FlightPlanStore()

        self.reconnect_delay = 3
        self._last_cleanup_time = 0

    def process_aircraft(self, payload):
        if not isinstance(payload, dict):
            return {}

        result = {}
        active_callsigns = set()

        for callsign, ac in payload.items():
            if not isinstance(ac, dict):
                continue

            active_callsigns.add(callsign)
            pos = ac.get("position", {})
            entry = {
                "x": float(pos.get("x", 0)),
                "y": float(pos.get("y", 0)),
                "heading": float(ac.get("heading", 0)),
                "altitude": float(ac.get("altitude", 0)),
                "playerName": ac.get("playerName", ""),
                "aircraftType": ac.get("aircraftType", ""),
                "speed": float(ac.get("speed", 0)),
                "isOnGround": bool(ac.get("isOnGround", False)),
            }

            # Ambil flight plan dari DATABASE (bukan memori)
            plan = self.plan_store.get_plan(callsign)
            if plan:
                entry["plan_departing"] = plan.get("departing", "")
                entry["plan_arriving"] = plan.get("arriving", "")
                entry["plan_route"] = plan.get("route", "")

            result[callsign] = entry

        # Jalankan pembersihan database setiap 30 detik sekali
        now = asyncio.get_event_loop().time()
        if now - self._last_cleanup_time > 30:
            self.plan_store.cleanup_stale_data(active_callsigns) # Ganti nama fungsi
            self._last_cleanup_time = now

        return result

    async def connect(self):
        self.is_running = True

        while self.is_running:
            self.connection_status.emit("[INFO] Connecting to 24Data API...")
            try:
                async with websockets.connect(
                    self.ws_url,
                    origin=None,
                    ping_interval=20,
                    ping_timeout=20
                ) as websocket:
                    self.connection_status.emit("[SUCCESS] Connected to 24Data WebSocket.")
                    self.reconnect_delay = 3

                    while self.is_running:
                        try:
                            message = await websocket.recv()
                            data = json.loads(message)
                            event_type = data.get("t")

                            if event_type == "ACFT_DATA":
                                processed = self.process_aircraft(data.get("d", {}))
                                self.aircraft_data_received.emit(processed)

                            elif event_type == "FLIGHT_PLAN":
                                plan_data = data.get("d", {})
                                callsign = plan_data.get("callsign")
                                if callsign:
                                    self.plan_store.save_plan(callsign, plan_data)

                        except websockets.exceptions.ConnectionClosed:
                            self.connection_status.emit("[WARNING] Connection closed. Reconnecting...")
                            break

            except Exception as e:
                self.connection_status.emit(f"[ERROR] Connection failed: {e}")

            if self.is_running:
                await asyncio.sleep(self.reconnect_delay)
                self.reconnect_delay = min(self.reconnect_delay * 2, 30)

    def stop(self):
        self.is_running = False
