import time
import json
import os
import random

from .DTCDatabase import DME_DTC_POOL, DSC_DTC_POOL, EGS_DTC_POOL, EPS_DTC_POOL


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DTC_STORAGE_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "..", "data", "dtc"))


class DTCManager:
    """
    Közös DTC kezelő alap osztály.
    Minden modul (DME, DSC, EGS, EPS) örököl belőle.
    A DTC_POOL-t a DTC_Database.py-ból veszi, nem duplikálja.
    """

    DTC_POOL: dict = {}
    DTC_FILE: str = "dtc_generic.json"

    def __init__(self):
        self.activeDTC: dict = {}
        self.storedDTC: dict = {}
        self.last_dtc_save: float = 0.0
        self.load_faults()

    def _get_dtc_file_path(self) -> str:
        os.makedirs(DTC_STORAGE_DIR, exist_ok=True)
        return os.path.join(DTC_STORAGE_DIR, self.DTC_FILE)

    def set_fault(self, code: str, description: str = None):
        if description is None:
            description = self.DTC_POOL.get(code, "Unknown Fault")
        now = time.time()

        if code not in self.activeDTC:
            self.activeDTC[code] = {
                "description": description,
                "first_seen": now,
                "last_seen": now,
            }
        else:
            self.activeDTC[code]["last_seen"] = now

        if code not in self.storedDTC:
            self.storedDTC[code] = {
                "description": description,
                "first_seen": now,
                "last_seen": now,
            }
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

        n = random.randint(1, max(1, count))
        already = set(self.activeDTC.keys())
        available = [c for c in self.DTC_POOL if c not in already]

        if not available:
            available = list(self.DTC_POOL.keys())

        chosen = random.sample(available, min(n, len(available)))

        for code in chosen:
            self.set_fault(code)
            print(f"[DTC INJECT {self.__class__.__name__}] {code}: {self.DTC_POOL[code]}")

        self.save_faults()
        return chosen

    def save_faults(self):
        try:
            path = self._get_dtc_file_path()
            with open(path, "w", encoding="utf-8") as f:
                json.dump({"storedDTC": self.storedDTC}, f, indent=4)
        except Exception as e:
            print(f"DTC save error ({self.DTC_FILE}): {e}")

    def load_faults(self):
        path = self._get_dtc_file_path()
        if not os.path.exists(path):
            return

        try:
            with open(path, "r", encoding="utf-8") as f:
                self.storedDTC = json.load(f).get("storedDTC", {})
        except Exception:
            self.storedDTC = {}

    def periodic_save(self, interval: float = 2.0):
        now = time.time()
        if now - self.last_dtc_save > interval:
            self.save_faults()
            self.last_dtc_save = now


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