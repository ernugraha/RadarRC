# backend/api_client.py

import json
import asyncio
import websockets
from PySide6.QtCore import QObject, Signal

class FlightPlanStore:
    def __init__(self):
        self.plans = {}

    def add(self, plan_data):
        callsign = plan_data.get("callsign")
        if callsign:
            self.plans[callsign] = plan_data

    def get(self, callsign):
        return self.plans.get(callsign, {})

class DataClient(QObject):
    aircraft_data_received = Signal(dict)
    connection_status = Signal(str)

    def __init__(self):
        super().__init__()
        self.ws_url = "wss://24data.ptfs.app/wss"
        self.is_running = False
        self.plan_store = FlightPlanStore()
        self.reconnect_delay = 3  # Detik

    def process_aircraft(self, payload):
        if not isinstance(payload, dict):
            return {}
        result = {}
        for callsign, ac in payload.items():
            if not isinstance(ac, dict):
                continue
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
            plan = self.plan_store.get(callsign)
            if plan:
                entry["plan_departing"] = plan.get("departing", "")
                entry["plan_arriving"] = plan.get("arriving", "")
                entry["plan_route"] = plan.get("route", "")
            result[callsign] = entry
        return result

    async def connect(self):
        self.is_running = True
        while self.is_running:
            self.connection_status.emit(f"[INFO] Connecting to 24Data API...")
            try:
                # KUNCI PERBAIKAN:
                # 1. origin=None (tidak mengirim header Origin)
                # 2. ping_interval=25 & ping_timeout=25 (heartbeat yang wajar)
                async with websockets.connect(
                    self.ws_url,
                    origin=None,
                    ping_interval=25,
                    ping_timeout=25
                ) as websocket:
                    self.connection_status.emit("[SUCCESS] Connected to 24Data WebSocket.")
                    self.reconnect_delay = 3  # Reset delay setelah berhasil

                    while self.is_running:
                        try:
                            message = await websocket.recv()
                            data = json.loads(message)
                            event_type = data.get("t")
                            if event_type == "ACFT_DATA":
                                processed = self.process_aircraft(data.get("d", {}))
                                self.aircraft_data_received.emit(processed)
                            elif event_type == "FLIGHT_PLAN":
                                self.plan_store.add(data.get("d", {}))
                        except websockets.exceptions.ConnectionClosed as e:
                            # Mencetak alasan penutupan yang sebenarnya
                            self.connection_status.emit(f"[WARNING] Connection closed by server. Code: {e.code}, Reason: {e.reason}. Reconnecting...")
                            break
                        except Exception as e:
                            self.connection_status.emit(f"[ERROR] An error occurred while receiving a message: {e}")
                            break

            except Exception as e:
                self.connection_status.emit(f"[ERROR] Failed to connect: {e}")

            if self.is_running:
                await asyncio.sleep(self.reconnect_delay)
                # Menambah delay secara perlahan agar tidak spam server (exponential backoff sederhana)
                self.reconnect_delay = min(self.reconnect_delay * 2, 30)

    def stop(self):
        self.is_running = False
