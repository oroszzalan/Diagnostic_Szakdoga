import time
import json
import os
import random

from DTCDatabase import DME_DTC_POOL, DSC_DTC_POOL, EGS_DTC_POOL, EPS_DTC_POOL


class DTCManager:
    """
    Közös DTC kezelő alap osztály.
    Minden modul (DME, DSC, EGS, EPS) örököl belőle.
    A DTC_POOL-t a DTC_Database.py-ból veszi, nem duplikálja.
    """

    DTC_POOL: dict = {}
    DTC_FILE: str  = "dtc_generic.json"

    def __init__(self):
        self.activeDTC:     dict  = {}
        self.storedDTC:     dict  = {}
        self.last_dtc_save: float = 0.0
        self.load_faults()

    # ----------------------------------------------------------
    def set_fault(self, code: str, description: str = None):
        if description is None:
            description = self.DTC_POOL.get(code, "Unknown Fault")
        now = time.time()
        if code not in self.activeDTC:
            self.activeDTC[code] = {"description": description,
                                    "first_seen": now, "last_seen": now}
        else:
            self.activeDTC[code]["last_seen"] = now

        if code not in self.storedDTC:
            self.storedDTC[code] = {"description": description,
                                    "first_seen": now, "last_seen": now}
        else:
            self.storedDTC[code]["last_seen"] = now

    def clear_fault(self, code: str):
        self.activeDTC.pop(code, None)

    def clear_all_faults(self):
        self.activeDTC.clear()
        self.storedDTC.clear()
        self.save_faults()

    def get_active_codes(self) -> list:
        return list(self.activeDTC.keys())

    def get_stored_codes(self) -> list:
        return list(self.storedDTC.keys())

    def inject_random_faults(self, count: int = 3) -> list:
        if not self.DTC_POOL:
            return []
        n         = random.randint(1, max(1, count))
        already   = set(self.activeDTC.keys())
        available = [c for c in self.DTC_POOL if c not in already]
        if not available:
            available = list(self.DTC_POOL.keys())
        chosen = random.sample(available, min(n, len(available)))
        for code in chosen:
            self.set_fault(code)
            print(f"[DTC INJECT {self.__class__.__name__}] "
                  f"{code}: {self.DTC_POOL[code]}")
        self.save_faults()
        return chosen

    # ----------------------------------------------------------
    def save_faults(self):
        try:
            with open(self.DTC_FILE, "w", encoding="utf-8") as f:
                json.dump({"storedDTC": self.storedDTC}, f, indent=4)
        except Exception as e:
            print(f"DTC save error ({self.DTC_FILE}): {e}")

    def load_faults(self):
        if not os.path.exists(self.DTC_FILE):
            return
        try:
            with open(self.DTC_FILE, "r", encoding="utf-8") as f:
                self.storedDTC = json.load(f).get("storedDTC", {})
        except Exception:
            self.storedDTC = {}

    def periodic_save(self, interval: float = 2.0):
        now = time.time()
        if now - self.last_dtc_save > interval:
            self.save_faults()
            self.last_dtc_save = now


# ============================================================
# Modul-specifikus alosztályok — csak a pool és a fájlnév tér el
# ============================================================
class DME_DTCManager(DTCManager):
    DTC_POOL = DME_DTC_POOL
    DTC_FILE = "dtc_dme.json"


class DSC_DTCManager(DTCManager):
    DTC_POOL = DSC_DTC_POOL
    DTC_FILE = "dtc_dsc.json"


class EGS_DTCManager(DTCManager):
    DTC_POOL = EGS_DTC_POOL
    DTC_FILE = "dtc_egs.json"


class EPS_DTCManager(DTCManager):
    DTC_POOL = EPS_DTC_POOL
    DTC_FILE = "dtc_eps.json"