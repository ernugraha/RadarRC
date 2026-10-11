# backend/atc24_bridge.py
"""
RadarRC - ATC24 Bridge
Menerima ACFT_DATA + FLIGHT_PLAN, menggabungkan, teruskan ke frontend.
"""

import asyncio
import websockets
import json
import time
from .config import ATC24_WS_URL, WS_HOST, WS_PORT
from .trail_logger import TrailLogger
from .flight_plans import FlightPlanStore


latest_data = {}
logger = None
plan_store = None


def process_aircraft(payload):
    """Proses ACFT_DATA + attach flight plan."""
    if not isinstance(payload, dict):
        return {}
    result = {}
    for callsign, ac in payload.items():
        if not isinstance(ac, dict):
            continue
        pos = ac.get("position", {})
        x = float(pos.get("x", 0)) if isinstance(pos, dict) else 0.0
        y = float(pos.get("y", 0)) if isinstance(pos, dict) else 0.0
        player = ac.get("playerName", "")

        entry = {
            "x": x,
            "y": y,
            "heading": float(ac.get("heading", 0)),
            "altitude": float(ac.get("altitude", 0)),
            "playerName": player,
            "aircraftType": ac.get("aircraftType", ""),
            "speed": float(ac.get("speed", 0)),
            "groundSpeed": float(ac.get("groundSpeed", 0)),
            "isOnGround": bool(ac.get("isOnGround", False)),
            "isEmergency": bool(ac.get("isEmergencyOccuring", False)),
        }

        # Attach flight plan
        plan = plan_store.get(callsign, player)
        if plan:
            entry["plan_callsign"] = plan.get("callsign", "")
            entry["plan_realcallsign"] = plan.get("realcallsign", "")
            entry["plan_departing"] = plan.get("departing", "")
            entry["plan_arriving"] = plan.get("arriving", "")
            entry["plan_route"] = plan.get("route", "")
            entry["plan_flightlevel"] = plan.get("flightlevel", "")
            entry["plan_flightrules"] = plan.get("flightrules", "")

        result[callsign] = entry
    return result


async def atc24_listener():
    global latest_data
    while True:
        try:
            print(f"[ATC24] Connecting to {ATC24_WS_URL}...")
            async with websockets.connect(ATC24_WS_URL, ping_interval=20) as ws:
                print("[ATC24] Connected")
                async for message in ws:
                    try:
                        msg = json.loads(message)
                        t = msg.get("t")

                        if t == "ACFT_DATA":
                            data = process_aircraft(msg.get("d", {}))
                            if data:
                                latest_data = data
                                if logger:
                                    logger.log_batch(data)
                        elif t == "FLIGHT_PLAN":
                            plan_store.add(msg.get("d", {}))
                    except json.JSONDecodeError:
                        pass
                    except Exception as e:
                        print(f"[ATC24] Parse error: {e}")
        except Exception as e:
            print(f"[ATC24] WS error: {e}, retry 5s...")
            await asyncio.sleep(5)


async def local_ws_handler(websocket):
    print("[Local] Frontend connected")
    try:
        while True:
            await websocket.send(json.dumps(latest_data))
            await asyncio.sleep(1)
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        print("[Local] Frontend disconnected")


async def cleanup_loop():
    while True:
        await asyncio.sleep(600)
        if plan_store:
            plan_store.cleanup_old(max_age_seconds=7200)


async def main():
    global logger, plan_store
    print("=" * 60)
    print("  RadarRC - ATC24 Bridge + Flight Plan")
    print("=" * 60)

    logger = TrailLogger()
    print(f"[TrailLogger] DB: {logger.db_path}")

    plan_store = FlightPlanStore()
    s = plan_store.stats()
    print(f"[FlightPlan] Plan aktif: {s['unique_plans']} unique "
          f"({s['keys']} keys, {s['roblox_users']} roblox users)")

    asyncio.create_task(atc24_listener())
    asyncio.create_task(cleanup_loop())

    print(f"[Local] WebSocket: ws://{WS_HOST}:{WS_PORT}")
    async with websockets.serve(local_ws_handler, WS_HOST, WS_PORT):
        await asyncio.Future()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[ATC24] Stopped.")
