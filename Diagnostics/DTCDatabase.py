"""
DTC_Database.py
---------------
Közös DTC kód adatbázis.
Ezt a fájlt használja:
  - DTCManager (modulok: DME, DSC, EGS, EPS) — pool-ok forrása
  - DiagApp — kód → leírás megjelenítéshez

Ha új kódot veszel fel, ide add hozzá és a modul pool-jába is.
"""

# ============================================================
# DME — Motor elektronika (Engine Control)
# ============================================================
DME_DTC_POOL = {
    # Vezértengelyezés / szelepvezérlés
    "P0010": "Intake Camshaft Position Actuator Circuit Open Bank 1",
    "P0011": "Intake Camshaft Position Timing Over-Advanced Bank 1",
    "P0012": "Intake Camshaft Position Timing Over-Retarded Bank 1",
    "P0013": "Exhaust Camshaft Position Actuator Circuit Open Bank 1",
    "P0014": "Exhaust Camshaft Position Timing Over-Advanced Bank 1",
    "P0015": "Exhaust Camshaft Position Timing Over-Retarded Bank 1",
    "P0016": "Crankshaft/Camshaft Position Correlation Bank 1 Sensor A",
    "P0017": "Crankshaft/Camshaft Position Correlation Bank 1 Sensor B",
    "P0340": "Camshaft Position Sensor Circuit Malfunction Bank 1",
    "P0341": "Camshaft Position Sensor Range/Performance Bank 1",
    "P0365": "Camshaft Position Sensor Circuit Bank 1 Sensor 2",
    "P0390": "Camshaft Position Sensor Circuit Bank 2 Sensor 2",
    # Lambda / O2 szenzor
    "P0030": "O2 Sensor Heater Control Circuit Bank 1 Sensor 1",
    "P0031": "O2 Sensor Heater Circuit Low Bank 1 Sensor 1",
    "P0032": "O2 Sensor Heater Circuit High Bank 1 Sensor 1",
    "P0130": "O2 Sensor Circuit Malfunction Bank 1 Sensor 1",
    "P0131": "O2 Sensor Circuit Low Voltage Bank 1 Sensor 1",
    "P0132": "O2 Sensor Circuit High Voltage Bank 1 Sensor 1",
    "P0133": "O2 Sensor Circuit Slow Response Bank 1 Sensor 1",
    "P0134": "O2 Sensor Circuit No Activity Bank 1 Sensor 1",
    "P0136": "O2 Sensor Circuit Malfunction Bank 1 Sensor 2",
    "P0420": "Catalyst System Efficiency Below Threshold Bank 1",
    "P0430": "Catalyst System Efficiency Below Threshold Bank 2",
    "P0491": "Secondary Air Injection System Insufficient Flow Bank 1",
    "P0492": "Secondary Air Injection System Insufficient Flow Bank 2",
    # Üzemanyag rendszer
    "P0087": "Fuel Rail/System Pressure Too Low",
    "P0088": "Fuel Rail/System Pressure Too High",
    "P0089": "Fuel Pressure Regulator Performance",
    "P0090": "Fuel Pressure Regulator Control Circuit Open",
    "P0171": "System Too Lean Bank 1",
    "P0172": "System Too Rich Bank 1",
    "P0174": "System Too Lean Bank 2",
    "P0175": "System Too Rich Bank 2",
    "P0191": "Fuel Rail Pressure Sensor Circuit Range/Performance",
    "P0192": "Fuel Rail Pressure Sensor Circuit Low Input",
    "P0193": "Fuel Rail Pressure Sensor Circuit High Input",
    # Befecskendező
    "P0201": "Injector Circuit/Open Cylinder 1",
    "P0202": "Injector Circuit/Open Cylinder 2",
    "P0203": "Injector Circuit/Open Cylinder 3",
    "P0204": "Injector Circuit/Open Cylinder 4",
    "P0205": "Injector Circuit/Open Cylinder 5",
    "P0206": "Injector Circuit/Open Cylinder 6",
    "P0207": "Injector Circuit/Open Cylinder 7",
    "P0208": "Injector Circuit/Open Cylinder 8",
    "P0261": "Cylinder 1 Injector Circuit Low",
    "P0264": "Cylinder 2 Injector Circuit Low",
    "P0267": "Cylinder 3 Injector Circuit Low",
    "P0270": "Cylinder 4 Injector Circuit Low",
    # Gyújtás / Misfire
    "P0300": "Random/Multiple Cylinder Misfire Detected",
    "P0301": "Cylinder 1 Misfire Detected",
    "P0302": "Cylinder 2 Misfire Detected",
    "P0303": "Cylinder 3 Misfire Detected",
    "P0304": "Cylinder 4 Misfire Detected",
    "P0305": "Cylinder 5 Misfire Detected",
    "P0306": "Cylinder 6 Misfire Detected",
    "P0307": "Cylinder 7 Misfire Detected",
    "P0308": "Cylinder 8 Misfire Detected",
    "P0316": "Misfire Detected on Startup First 1000 Revolutions",
    "P0320": "Ignition/Distributor Engine Speed Input Circuit Malfunction",
    "P0325": "Knock Sensor 1 Circuit Malfunction Bank 1",
    "P0326": "Knock Sensor 1 Circuit Range/Performance Bank 1",
    "P0327": "Knock Sensor 1 Circuit Low Input Bank 1",
    "P0328": "Knock Sensor 1 Circuit High Input Bank 1",
    "P0330": "Knock Sensor 2 Circuit Malfunction Bank 2",
    # Légtömegmérő / szívórendszer
    "P0100": "Mass or Volume Air Flow Circuit Malfunction",
    "P0101": "Mass or Volume Air Flow Circuit Range/Performance",
    "P0102": "Mass or Volume Air Flow Circuit Low Input",
    "P0103": "Mass or Volume Air Flow Circuit High Input",
    "P0110": "Intake Air Temperature Circuit Malfunction",
    "P0111": "Intake Air Temperature Circuit Range/Performance",
    "P0112": "Intake Air Temperature Circuit Low Input",
    "P0113": "Intake Air Temperature Circuit High Input",
    "P0400": "Exhaust Gas Recirculation Flow Malfunction",
    "P0401": "Exhaust Gas Recirculation Flow Insufficient",
    "P0402": "Exhaust Gas Recirculation Flow Excessive",
    "P0411": "Secondary Air Injection System Incorrect Flow",
    "P0440": "Evaporative Emission Control System Malfunction",
    "P0441": "Evaporative Emission Control System Incorrect Purge Flow",
    "P0455": "Evaporative Emission Control System Leak Detected Gross Leak",
    "P0456": "Evaporative Emission Control System Leak Detected Small Leak",
    "P0661": "Intake Manifold Tuning Valve Control Circuit Low Bank 1",
    "P0662": "Intake Manifold Tuning Valve Control Circuit High Bank 1",
    # Fojtószelep
    "P0120": "Throttle Position Sensor Circuit Malfunction",
    "P0121": "Throttle Position Sensor Range/Performance",
    "P0122": "Throttle Position Sensor Circuit Low Input",
    "P0123": "Throttle Position Sensor Circuit High Input",
    "P0221": "Throttle Position Sensor B Circuit Range/Performance",
    "P0222": "Throttle Position Sensor B Circuit Low Input",
    "P0223": "Throttle Position Sensor B Circuit High Input",
    "P0638": "Throttle Actuator Control Range/Performance Bank 1",
    "P0507": "Idle Control System RPM High",
    "P0505": "Idle Control System Malfunction",
    # Hűtés / hőmérséklet
    "P0115": "Engine Coolant Temperature Circuit Malfunction",
    "P0116": "Engine Coolant Temperature Circuit Range/Performance",
    "P0117": "Engine Coolant Temperature Circuit Low Input",
    "P0118": "Engine Coolant Temperature Circuit High Input",
    "P0125": "Insufficient Coolant Temp for Closed Loop Fuel Control",
    "P0128": "Coolant Thermostat Below Regulating Temperature",
    "P0196": "Engine Oil Temperature Sensor Range/Performance",
    "P0197": "Engine Oil Temperature Sensor Low",
    "P0198": "Engine Oil Temperature Sensor High",
    "P0217": "Engine Coolant Over Temperature Condition",
    "P0219": "Engine Overspeed Condition",
    "P0480": "Cooling Fan 1 Control Circuit Malfunction",
    "P0481": "Cooling Fan 2 Control Circuit Malfunction",
    "P0597": "Thermostat Heater Control Circuit Open",
    "P0598": "Thermostat Heater Control Circuit Low",
    "P0599": "Thermostat Heater Control Circuit High",
    # Olaj / akkumulátor
    "P0520": "Engine Oil Pressure Sensor/Switch Circuit Malfunction",
    "P0521": "Engine Oil Pressure Sensor Range/Performance",
    "P0522": "Engine Oil Pressure Sensor Circuit Low Voltage",
    "P0523": "Engine Oil Pressure Sensor Circuit High Voltage",
    "P0562": "System Voltage Low",
    "P0563": "System Voltage High",
    # Egyéb motor
    "P0500": "Vehicle Speed Sensor Malfunction",
    "P0600": "Serial Communication Link Malfunction",
    "P0603": "Internal Control Module Keep Alive Memory Error",
}

# ============================================================
# DSC — Dinamikus Stabilitásvezérlés (Dynamic Stability Control)
# ============================================================
DSC_DTC_POOL = {
    # Keréksebességérzékelők
    "C0021": "Right Front Wheel Speed Sensor Circuit Fault",
    "C0022": "Left Front Wheel Speed Sensor Circuit Fault",
    "C0023": "Right Rear Wheel Speed Sensor Circuit Fault",
    "C0024": "Left Rear Wheel Speed Sensor Circuit Fault",
    "C0025": "Right Front Wheel Speed Sensor Circuit Range/Performance",
    "C0026": "Left Front Wheel Speed Sensor Circuit Range/Performance",
    "C0027": "Right Rear Wheel Speed Sensor Circuit Range/Performance",
    "C0028": "Left Rear Wheel Speed Sensor Circuit Range/Performance",
    "C0031": "Right Front Wheel Speed Sensor Input Signal Missing",
    "C0034": "Left Front Wheel Speed Sensor Input Signal Missing",
    "C0037": "Right Rear Wheel Speed Sensor Input Signal Missing",
    "C0038": "Left Rear Wheel Speed Sensor Input Signal Missing",
    "C0040": "Right Front Wheel Speed Sensor Circuit Open",
    "C0041": "Right Front Wheel Speed Sensor Circuit Short to Ground",
    "C0042": "Right Front Wheel Speed Sensor Circuit Short to Battery",
    "C0044": "Left Front Wheel Speed Sensor Circuit Open",
    "C0045": "Left Front Wheel Speed Sensor Circuit Short to Ground",
    "C0046": "Left Front Wheel Speed Sensor Circuit Short to Battery",
    "C0047": "Right Rear Wheel Speed Sensor Circuit Open",
    "C0048": "Right Rear Wheel Speed Sensor Circuit Short to Ground",
    "C0050": "Left Rear Wheel Speed Sensor Circuit Open",
    "C0051": "Left Rear Wheel Speed Sensor Circuit Short to Ground",
    "C0221": "Right Front Wheel Speed Sensor Signal Missing",
    "C0222": "Right Front Wheel Speed Sensor Erratic",
    "C0223": "Right Front Wheel Speed Sensor Fault",
    "C0225": "Left Front Wheel Speed Sensor Signal Missing",
    "C0226": "Left Front Wheel Speed Sensor Erratic",
    "C0229": "Right Rear Wheel Speed Sensor Signal Missing",
    "C0233": "Left Rear Wheel Speed Sensor Signal Missing",
    "C0245": "Wheel Speed Sensor Frequency Error",
    # ABS hidraulika
    "C0110": "ABS Motor Circuit Malfunction",
    "C0111": "ABS Motor Circuit Range/Performance",
    "C0112": "ABS Motor Circuit Low",
    "C0113": "ABS Motor Circuit High",
    "C0121": "ABS Valve Relay Circuit Fault",
    "C0122": "ABS Valve Relay Circuit Open",
    "C0123": "ABS Valve Relay Circuit Short to Ground",
    "C0131": "Anti-Lock Brake System Pressure Sensor Fault",
    "C0132": "Anti-Lock Brake System Pressure Sensor Performance",
    "C0141": "Left Front ABS Solenoid Circuit Fault",
    "C0145": "Right Front ABS Solenoid Circuit Fault",
    "C0148": "Right Rear ABS Solenoid Circuit Fault",
    "C0151": "Left Rear ABS Solenoid Circuit Fault",
    "C0161": "ABS/TCS Brake Switch Circuit Fault",
    "C0163": "ABS/TCS Brake Switch Circuit High",
    "C0252": "Active Brake Control System Fault",
    "C0265": "EBCM Relay Circuit Active",
    "C0266": "EBCM Relay Circuit Open",
    "C0267": "Pump Motor Circuit Open/Shorted",
    "C0268": "Pump Motor Circuit Open/Shorted High Side",
    "C0271": "EBCM Malfunction",
    "C0272": "EBCM Internal Fault",
    "C0274": "Excessive Dump Time Left Front",
    "C0281": "Stop Lamp Switch Circuit Fault",
    # Giroszkóp / gyorsulásmérő
    "C0196": "Yaw Rate Sensor Circuit Fault",
    "C0197": "Yaw Rate Sensor Performance",
    "C0198": "Yaw Rate Sensor Signal Erratic",
    "C0199": "Yaw Rate Sensor Supply Voltage Low",
    "C0186": "Lateral Accelerometer Circuit Fault",
    "C0187": "Lateral Accelerometer Performance",
    "C0191": "Longitudinal Accelerometer Circuit Fault",
    # Kormányszög (DSC oldalról)
    "C0450": "Steering Wheel Position Sensor Circuit Fault",
    "C0452": "Steering Wheel Position Sensor Range/Performance",
    "C0455": "Steering Wheel Position Sensor Signal Missing",
    # Kommunikáció
    "U0121": "Lost Communication with ABS Control Module",
    "U0122": "Lost Communication with Vehicle Dynamics Control Module",
    "U0126": "Lost Communication with Steering Angle Sensor Module",
    "U0415": "Invalid Data Received from Anti-Lock Brake System Module",
}

# ============================================================
# EGS — Elektronikus váltóvezérlés (Electronic Gearbox System)
# ============================================================
EGS_DTC_POOL = {
    # Általános váltó hibák
    "P0700": "Transmission Control System Malfunction",
    "P0701": "Transmission Control System Range/Performance",
    "P0702": "Transmission Control System Electrical",
    "P0703": "Brake Switch B Circuit Malfunction",
    "P0705": "Transmission Range Sensor Circuit Malfunction",
    "P0706": "Transmission Range Sensor Circuit Range/Performance",
    "P0707": "Transmission Range Sensor Circuit Low Input",
    "P0708": "Transmission Range Sensor Circuit High Input",
    "P0709": "Transmission Range Sensor Circuit Intermittent",
    # Hőmérséklet szenzor
    "P0711": "Transmission Fluid Temperature Sensor Range/Performance",
    "P0712": "Transmission Fluid Temperature Sensor Circuit Low Input",
    "P0713": "Transmission Fluid Temperature Sensor Circuit High Input",
    "P0714": "Transmission Fluid Temperature Sensor Circuit Intermittent",
    # Fordulatszám szenzor
    "P0715": "Input/Turbine Speed Sensor Circuit Malfunction",
    "P0716": "Input/Turbine Speed Sensor Circuit Range/Performance",
    "P0717": "Input/Turbine Speed Sensor Circuit No Signal",
    "P0718": "Input/Turbine Speed Sensor Circuit Intermittent",
    "P0720": "Output Speed Sensor Circuit Malfunction",
    "P0721": "Output Speed Sensor Range/Performance",
    "P0722": "Output Speed Sensor No Signal",
    "P0723": "Output Speed Sensor Intermittent",
    # Áttétel hibák
    "P0730": "Incorrect Gear Ratio",
    "P0731": "Gear 1 Incorrect Ratio",
    "P0732": "Gear 2 Incorrect Ratio",
    "P0733": "Gear 3 Incorrect Ratio",
    "P0734": "Gear 4 Incorrect Ratio",
    "P0735": "Gear 5 Incorrect Ratio",
    "P0736": "Reverse Incorrect Ratio",
    "P0737": "TCM Engine Speed Output Circuit Malfunction",
    # Nyomatékátalakító
    "P0740": "Torque Converter Clutch Circuit Malfunction",
    "P0741": "Torque Converter Clutch Circuit Performance or Stuck Off",
    "P0742": "Torque Converter Clutch Circuit Stuck On",
    "P0743": "Torque Converter Clutch Circuit Electrical",
    "P0744": "Torque Converter Clutch Circuit Intermittent",
    # Nyomásszabályozó szolénoidok
    "P0745": "Pressure Control Solenoid Malfunction",
    "P0746": "Pressure Control Solenoid Performance or Stuck Off",
    "P0747": "Pressure Control Solenoid Stuck On",
    "P0748": "Pressure Control Solenoid Electrical",
    "P0749": "Pressure Control Solenoid Intermittent",
    # Váltószolénoidok A-E
    "P0750": "Shift Solenoid A Malfunction",
    "P0751": "Shift Solenoid A Performance or Stuck Off",
    "P0752": "Shift Solenoid A Stuck On",
    "P0753": "Shift Solenoid A Electrical",
    "P0754": "Shift Solenoid A Intermittent",
    "P0755": "Shift Solenoid B Malfunction",
    "P0756": "Shift Solenoid B Performance or Stuck Off",
    "P0757": "Shift Solenoid B Stuck On",
    "P0758": "Shift Solenoid B Electrical",
    "P0759": "Shift Solenoid B Intermittent",
    "P0760": "Shift Solenoid C Malfunction",
    "P0761": "Shift Solenoid C Performance or Stuck Off",
    "P0762": "Shift Solenoid C Stuck On",
    "P0763": "Shift Solenoid C Electrical",
    "P0765": "Shift Solenoid D Malfunction",
    "P0766": "Shift Solenoid D Performance or Stuck Off",
    "P0770": "Shift Solenoid E Malfunction",
    "P0771": "Shift Solenoid E Performance or Stuck Off",
    # Váltási hibák
    "P0780": "Shift Malfunction",
    "P0781": "1-2 Shift Malfunction",
    "P0782": "2-3 Shift Malfunction",
    "P0783": "3-4 Shift Malfunction",
    "P0784": "4-5 Shift Malfunction",
    "P0785": "Shift/Timing Solenoid Malfunction",
    "P0786": "Shift/Timing Solenoid Range/Performance",
    # Kommunikáció
    "U0100": "Lost Communication with ECM/PCM A",
    "U0101": "Lost Communication with TCM",
    "U0102": "Lost Communication with Transfer Case Control Module",
    "U0103": "Lost Communication with Gear Shift Module",
}

# ============================================================
# EPS — Elektromos szervokormány (Electric Power Steering)
# ============================================================
EPS_DTC_POOL = {
    # Kormányszög szenzor
    "C0450": "Steering Wheel Position Sensor Circuit Fault",
    "C0451": "Steering Wheel Position Sensor Circuit Range/Performance",
    "C0452": "Steering Wheel Position Sensor Range/Performance",
    "C0453": "Steering Wheel Position Sensor Circuit High",
    "C0455": "Steering Wheel Position Sensor Signal Missing",
    "C0456": "Steering Wheel Position Sensor Signal Erratic",
    "C0460": "Steering Wheel Position Sensor Circuit Low",
    "C0463": "Steering Wheel Position Sensor Circuit High",
    # EPS motor áramkör
    "C0471": "EPS Motor Circuit Open",
    "C0472": "EPS Motor Circuit Short to Ground",
    "C0473": "EPS Motor Circuit Short to Battery",
    "C0474": "EPS Motor Current Sensor Circuit Fault",
    "C0475": "EPS Motor Overtemperature",
    "C0476": "EPS Motor Position Sensor Fault",
    "C0477": "EPS Motor Position Sensor Range/Performance",
    "C0478": "EPS Motor Position Sensor Signal Missing",
    # Nyomatékszenzor
    "C0490": "Steering Torque Sensor Circuit Fault",
    "C0491": "Steering Torque Sensor Range/Performance",
    "C0492": "Steering Torque Sensor Signal Missing",
    "C0493": "Steering Torque Sensor Signal Erratic",
    "C0494": "Steering Torque Sensor Circuit Low",
    "C0495": "Steering Torque Sensor Circuit High",
    # EPS vezérlő modul
    "C0500": "EPS Control Module Internal Fault",
    "C0501": "EPS Control Module EEPROM Error",
    "C0502": "EPS Control Module Watchdog Reset",
    "C0503": "EPS Control Module Power Supply Low",
    "C0504": "EPS Control Module Power Supply High",
    "C0505": "EPS Control Module Temperature Too High",
    # Rásegítés
    "C0510": "Power Steering Assist Reduced",
    "C0511": "Power Steering Assist Disabled",
    "C0512": "Power Steering Assist Circuit Fault",
    "C0513": "EPS Thermal Shutdown",
    "C0514": "EPS Assist Torque Sensor Offset",
    "C0521": "EPS Assist Torque Calibration Required",
    # Kommunikáció
    "U0126": "Lost Communication with Steering Angle Sensor Module",
    "U0131": "Lost Communication with Power Steering Control Module",
    "U0132": "Lost Communication with Body Control Module A",
    "U0140": "Lost Communication with Body Control Module",
    "U0155": "Lost Communication with Instrument Panel Cluster",
}

# ============================================================
# Teljes adatbázis — minden kód egy helyen
# ============================================================
ALL_DTC_POOL: dict = {}
ALL_DTC_POOL.update(DME_DTC_POOL)
ALL_DTC_POOL.update(DSC_DTC_POOL)
ALL_DTC_POOL.update(EGS_DTC_POOL)
ALL_DTC_POOL.update(EPS_DTC_POOL)


def get_description(code: str) -> str:
    """
    Visszaadja a kód leírását.
    Ha ismeretlen, a kód prefix alapján adja meg a kategóriát.
    """
    code = code.strip().upper()
    if code in ALL_DTC_POOL:
        return ALL_DTC_POOL[code]

    # Ismeretlen kód — legalább a kategóriát adjuk meg
    prefix = code[:2] if len(code) >= 2 else code
    category = {
        "P0": "Szabványos hajtáslánc hiba",
        "P1": "Gyártó-specifikus hajtáslánc hiba",
        "P2": "Szabványos hajtáslánc hiba",
        "P3": "Szabványos hajtáslánc hiba",
        "C0": "Szabványos alváz hiba",
        "C1": "Gyártó-specifikus alváz hiba",
        "B0": "Szabványos karosszéria hiba",
        "B1": "Gyártó-specifikus karosszéria hiba",
        "U0": "Szabványos hálózati / kommunikációs hiba",
        "U1": "Gyártó-specifikus hálózati hiba",
    }.get(prefix, "Ismeretlen hibakód")

    return category


def get_module_name(code: str) -> str:
    """Megadja melyik modulhoz tartozik a kód."""
    code = code.strip().upper()
    if code in DME_DTC_POOL: return "DME"
    if code in DSC_DTC_POOL: return "DSC"
    if code in EGS_DTC_POOL: return "EGS"
    if code in EPS_DTC_POOL: return "EPS"
    return "?"


def display_string(code: str) -> str:
    """
    Listboxhoz: 'P0300 [DME]  —  Random/Multiple Cylinder Misfire Detected'
    """
    code   = code.strip().upper()
    module = get_module_name(code)
    desc   = get_description(code)
    return f"{code} [{module}]  —  {desc}"