# backend/flight_plans.py
"""Penyimpanan flight plan dengan persistensi + cleanup pintar."""

import json
import os
import time
from .paths_helper import get_data_dir


class FlightPlanStore:
    def __init__(self, path=None):
        if path is None:
            data_dir = get_data_dir()
            os.makedirs(data_dir, exist_ok=True)
            path = os.path.join(data_dir, "flight_plans.json")
        self.path = path
        self.plans = {}
        self.by_roblox = {}
        self._last_seen = {}   # {key_upper: timestamp terakhir muncul di ACFT_DATA}
        self._load()

    # ================================================================
    # NORMALISASI
    # ================================================================
    @staticmethod
    def _norm(s):
        if not s:
            return ""
        return (s.upper()
                .replace(" ", "").replace("-", "")
                .replace("_", "").replace(".", ""))

    # ================================================================
    # LOAD / SAVE
    # ================================================================
    def _load(self):
        if not os.path.isfile(self.path):
            print(f"[FlightPlan] Config not found, will create: {self.path}")
            return
        try:
            with open(self.path, "r") as f:
                data = json.load(f)
            self.plans = data.get("plans", {})
            self.by_roblox = data.get("by_roblox", {})
            self._last_seen = data.get("last_seen", {})
            unique = len(set(id(p) for p in self.plans.values()))
            print(f"[FlightPlan] Loaded {len(self.plans)} key "
                  f"({unique} unique plans) from {self.path}")
        except Exception as e:
            print(f"[FlightPlan] Failed load: {e}")

    def _save(self):
        try:
            with open(self.path, "w") as f:
                json.dump({
                    "plans": self.plans,
                    "by_roblox": self.by_roblox,
                    "last_seen": self._last_seen,
                }, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[FlightPlan] Failed to save: {e}")

    # ================================================================
    # ADD
    # ================================================================
    def add(self, payload):
        if not isinstance(payload, dict):
            return
        callsign = (payload.get("callsign") or "").strip()
        real_cs = (payload.get("realcallsign") or "").strip()
        roblox = (payload.get("robloxName") or "").strip()

        if not (callsign or real_cs or roblox):
            return

        plan = {
            "callsign": callsign,
            "realcallsign": real_cs,
            "robloxName": roblox,
            "aircraft": payload.get("aircraft", ""),
            "flightrules": payload.get("flightrules", ""),
            "departing": payload.get("departing", ""),
            "arriving": payload.get("arriving", ""),
            "route": payload.get("route", ""),
            "flightlevel": payload.get("flightlevel", ""),
            "_updated": time.time(),
        }

        aliases = set()
        for s in [callsign, real_cs]:
            if not s:
                continue
            aliases.add(s.upper())
            aliases.add(self._norm(s))
        aliases.discard("")

        now = time.time()
        for a in aliases:
            self.plans[a] = plan
            self._last_seen[a] = now

        if roblox:
            rbx = roblox.upper()
            self.by_roblox[rbx] = sorted(aliases)

        self._save()

        dep = plan.get("departing", "?")
        arr = plan.get("arriving", "?")
        print(f"[FlightPlan] {callsign or real_cs or roblox} "
              f"-> {dep} to {arr}")

    # ================================================================
    # GET (juga update _last_seen)
    # ================================================================
    def get(self, callsign, roblox_username=None):
        """Cari plan + catat bahwa pesawat ini masih aktif."""
        now = time.time()

        # 1. Direct match
        if callsign:
            cs_up = callsign.upper()
            if cs_up in self.plans:
                self._last_seen[cs_up] = now
                return self.plans[cs_up]
            # 2. Normalized
            cs_norm = self._norm(callsign)
            if cs_norm and cs_norm in self.plans:
                self._last_seen[cs_norm] = now
                return self.plans[cs_norm]

        # 3. Roblox match
        if roblox_username:
            rbx = roblox_username.upper()
            aliases = self.by_roblox.get(rbx)
            if aliases:
                for a in aliases:
                    if a in self.plans:
                        self._last_seen[a] = now
                        return self.plans[a]

        return None

    # ================================================================
    # CLEANUP PINTAR: hanya hapus kalau TUA + TIDAK AKTIF
    # ================================================================
    def cleanup_inactive(self, max_age_seconds=1800, inactive_seconds=300):
        """
        Hapus flight plan yang:
          1. Umur plan > max_age_seconds (default 2 jam), DAN
          2. Pesawatnya tidak terlihat di ACFT_DATA selama inactive_seconds
             (default 10 menit)

        Pesawat yang masih terbang meskipun > 2 jam tetap disimpan.
        """
        now = time.time()

        # Kumpulkan semua unique plans
        unique_plans = {}
        for k, plan in self.plans.items():
            pid = id(plan)
            if pid not in unique_plans:
                unique_plans[pid] = plan

        # Tentukan mana yang harus dihapus
        to_delete_ids = set()
        for pid, plan in unique_plans.items():
            plan_age = now - plan.get("_updated", 0)
            if plan_age < max_age_seconds:
                continue  # masih baru, skip

            # Cek apakah masih aktif — cari last_seen minimum from semua aliasnya
            latest_seen = 0
            for k, p in self.plans.items():
                if id(p) == pid:
                    seen = self._last_seen.get(k, 0)
                    if seen > latest_seen:
                        latest_seen = seen

            inactive_for = now - latest_seen if latest_seen > 0 else plan_age

            if inactive_for > inactive_seconds:
                to_delete_ids.add(pid)

        if not to_delete_ids:
            return 0

        # Filter plans & last_seen
        self.plans = {k: v for k, v in self.plans.items()
                      if id(v) not in to_delete_ids}
        self._last_seen = {k: v for k, v in self._last_seen.items()
                           if k in self.plans}

        # Rebuild roblox index
        self.by_roblox = {}
        for k, v in self.plans.items():
            rbx = v.get("robloxName", "").strip().upper()
            if rbx:
                self.by_roblox.setdefault(rbx, [])
                if k not in self.by_roblox[rbx]:
                    self.by_roblox[rbx].append(k)

        self._save()
        removed = len(to_delete_ids)
        print(f"[FlightPlan] Cleanup: {removed} plans removed "
              f"(old + inactive)")
        return removed

    # ================================================================
    # STATS
    # ================================================================
    def stats(self):
        unique = len(set(id(p) for p in self.plans.values()))
        active = 0
        now = time.time()
        for k in self.plans:
            if now - self._last_seen.get(k, 0) < 600:
                active += 1
        return {
            "unique_plans": unique,
            "keys": len(self.plans),
            "roblox_users": len(self.by_roblox),
            "active_keys": active,
        }
