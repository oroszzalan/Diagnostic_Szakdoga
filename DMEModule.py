import HexInt
import CanController
from bisect import bisect_left
import time

from DTCManager import DTCManager


class DME_Module(DTCManager):

    DTC_POOL = {
        # Gyújtás / befecskendezés
        "P0201": "Injector Circuit/Open Cylinder 1",
        "P0202": "Injector Circuit/Open Cylinder 2",
        "P0203": "Injector Circuit/Open Cylinder 3",
        "P0204": "Injector Circuit/Open Cylinder 4",
        "P0261": "Cylinder 1 Injector Circuit Low",
        "P0300": "Random/Multiple Cylinder Misfire Detected",
        "P0301": "Cylinder 1 Misfire Detected",
        "P0302": "Cylinder 2 Misfire Detected",
        "P0303": "Cylinder 3 Misfire Detected",
        "P0304": "Cylinder 4 Misfire Detected",
        "P0305": "Cylinder 5 Misfire Detected",
        "P0306": "Cylinder 6 Misfire Detected",
        "P0307": "Cylinder 7 Misfire Detected",
        "P0308": "Cylinder 8 Misfire Detected",
        "P0316": "Misfire Detected on Startup (First 1000 Revolutions)",
        # Üzemanyag rendszer
        "P0087": "Fuel Rail/System Pressure Too Low",
        "P0088": "Fuel Rail/System Pressure Too High",
        "P0171": "System Too Lean Bank 1",
        "P0172": "System Too Rich Bank 1",
        "P0174": "System Too Lean Bank 2",
        "P0175": "System Too Rich Bank 2",
        "P0191": "Fuel Rail Pressure Sensor Circuit Range/Performance",
        # Légtömegmérő / szívólevegő
        "P0100": "Mass or Volume Air Flow Circuit Malfunction",
        "P0102": "Mass or Volume Air Flow Circuit Low Input",
        "P0103": "Mass or Volume Air Flow Circuit High Input",
        "P0110": "Intake Air Temperature Circuit Malfunction",
        "P0113": "Intake Air Temperature Circuit High Input",
        # Fojtószelep
        "P0120": "Throttle Position Sensor Circuit Malfunction",
        "P0121": "Throttle Position Sensor Range/Performance",
        "P0221": "Throttle Position Sensor B Circuit Range/Performance",
        "P0638": "Throttle Actuator Control Range/Performance Bank 1",
        # Hűtés / olaj
        "P0115": "Engine Coolant Temperature Circuit Malfunction",
        "P0125": "Insufficient Coolant Temp for Closed Loop Fuel Control",
        "P0128": "Coolant Thermostat Below Regulating Temperature",
        "P0196": "Engine Oil Temperature Sensor Range/Performance",
        "P0217": "Engine Coolant Over Temperature Condition",
        "P0219": "Engine Overspeed Condition",
        "P0520": "Engine Oil Pressure Sensor/Switch Circuit Malfunction",
        "P0521": "Engine Oil Pressure Sensor Range/Performance",
        "P0597": "Thermostat Heater Control Circuit Open",
        # Lambda / kipufogó
        "P0030": "O2 Sensor Heater Control Circuit Bank 1 Sensor 1",
        "P0130": "O2 Sensor Circuit Malfunction Bank 1 Sensor 1",
        "P0133": "O2 Sensor Circuit Slow Response Bank 1 Sensor 1",
        "P0420": "Catalyst System Efficiency Below Threshold Bank 1",
        "P0430": "Catalyst System Efficiency Below Threshold Bank 2",
        "P0491": "Secondary Air Injection System Insufficient Flow Bank 1",
        "P0492": "Secondary Air Injection System Insufficient Flow Bank 2",
        # Egyéb motor
        "P0016": "Crankshaft/Camshaft Position Correlation Bank 1 Sensor A",
        "P0340": "Camshaft Position Sensor Circuit Malfunction Bank 1",
        "P0365": "Camshaft Position Sensor Circuit Bank 1 Sensor 2",
        "P0390": "Camshaft Position Sensor Circuit Bank 2 Sensor 2",
        "P0400": "Exhaust Gas Recirculation Flow Malfunction",
        "P0440": "Evaporative Emission Control System Malfunction",
        "P0455": "Evaporative Emission Control System Leak Detected",
        "P0480": "Cooling Fan 1 Control Circuit Malfunction",
        "P0500": "Vehicle Speed Sensor Malfunction",
        "P0505": "Idle Control System Malfunction",
        "P0562": "System Voltage Low",
        "P0563": "System Voltage High",
        "P0603": "Internal Control Module Keep Alive Memory Error",
        "P0661": "Intake Manifold Tuning Valve Control Circuit Low Bank 1",
    }

    DTC_FILE = "dtc_dme.json"

    def __init__(self):
        # DTCManager inicializálás (load_faults)
        DTCManager.__init__(self)

        self.joystick = None
        self.rpm = 0
        self.throttlePosition = 0.0
        self.coolantTemp = 40.0
        self.oilTemp = 5.0
        self.oilPressure = 0.0
        self.batteryVoltage = 12.0
        self.airIntakeTemp = 10.0
        self.massAirflow = 0.0
        self.knockSensor = 0.0
        self.O2sensor = 0.0
        self.Torque = 0.0
        self.HorsePower = 0.0

        self.last_time = time.time()
        self.dt = 0.0

        self.fuelTankLiters = 67.0
        self.fuelLevelLiters = 67.0
        self.fuelPercent = 100.0

        self.frame_0x0A0 = ""
        self.frame_0x0A1 = ""
        self.frame_0x0A2 = ""
        self.frame_0x0A3 = ""
        self.frame_0x0A4 = ""

        self.data_0x0A0 = []
        self.data_0x0A1 = []
        self.data_0x0A2 = []
        self.data_0x0A3 = []
        self.data_0x0A4 = []

        self.last_0x0A0 = 0
        self.last_0x0A1 = 0
        self.last_0x0A2 = 0
        self.last_0x0A3 = 0
        self.last_0x0A4 = 0

    # ----------------------------------------------------------
    def update_dtc(self):
        """Szenzor-alapú automatikus DTC logika."""
        if self.coolantTemp > 130:
            self.set_fault("P0217")
        else:
            self.clear_fault("P0217")

        if self.rpm > 1000 and self.oilPressure < 0.5:
            self.set_fault("P0520")
        else:
            self.clear_fault("P0520")

        if self.batteryVoltage < 11.5:
            self.set_fault("P0562")
        else:
            self.clear_fault("P0562")

        if self.batteryVoltage > 15.5:
            self.set_fault("P0563")
        else:
            self.clear_fault("P0563")

        if self.O2sensor < 0.0 or self.O2sensor > 1.2:
            self.set_fault("P0130")
        else:
            self.clear_fault("P0130")

        self.periodic_save()

    # ----------------------------------------------------------
    def DME_simulation(self):
        now = time.time()
        self.dt = max(0.0, min(now - self.last_time, 0.1))
        self.last_time = now

        throttle = 0.0
        if self.joystick is not None:
            throttle = (self.joystick.get_axis(5) + 1.0) / 2.0
            throttle = max(0.0, min(1.0, throttle))
        self.throttlePosition = throttle * 100.0

        if self.rpm > 0:
            target_coolant = max(5.0, min(90.0 + throttle * 25.0, 170.0))
            target_oil     = max(5.0, min(80.0 + throttle * 0.5,  120.0))

            self.coolantTemp += (target_coolant - self.coolantTemp) * min(1.0, 0.08 * self.dt)
            self.oilTemp     += (target_oil     - self.oilTemp)     * min(1.0, 0.02 * self.dt)

            self.oilPressure    = 1.0 + throttle * 4.0
            self.batteryVoltage = 13.8
            self.massAirflow    = max(0.0, (self.rpm / 1000.0) * (1.5 + throttle * 8.0))
            self.knockSensor    = throttle * 10.0
            self.O2sensor       = 0.1 + throttle * 0.8
            self.Torque         = DME_Module.engine_torque(self.rpm, throttle)
            self.HorsePower     = (self.Torque * self.rpm) / 7127.0

            fuel_burn = (1.2 + throttle * 12.0 + (self.rpm / 6700.0) * 6.0) * (self.dt / 3600.0)
            self.fuelLevelLiters = max(0.0, min(self.fuelLevelLiters - fuel_burn, self.fuelTankLiters))
            self.fuelPercent = (self.fuelLevelLiters / self.fuelTankLiters) * 100.0
        else:
            self.coolantTemp += (40.0 - self.coolantTemp) * min(1.0, 0.02  * self.dt)
            self.oilTemp     += (5.0  - self.oilTemp)     * min(1.0, 0.015 * self.dt)
            self.coolantTemp  = max(5.0, min(self.coolantTemp, 170.0))
            self.oilTemp      = max(5.0, min(self.oilTemp, 120.0))
            self.batteryVoltage = 12.0
            self.oilPressure = self.massAirflow = self.knockSensor = 0.0
            self.O2sensor = self.Torque = self.HorsePower = 0.0
            self.fuelPercent = (self.fuelLevelLiters / self.fuelTankLiters) * 100.0

        now = time.time()
        s0 = now - self.last_0x0A0 >= 0.02
        s1 = now - self.last_0x0A1 >= 0.10
        s2 = now - self.last_0x0A2 >= 0.20
        s3 = now - self.last_0x0A3 >= 0.05
        s4 = now - self.last_0x0A4 >= 0.02

        self.DME_Data(self.rpm, self.throttlePosition, self.massAirflow,
                      self.coolantTemp, self.airIntakeTemp, self.oilTemp,
                      self.batteryVoltage, self.oilPressure,
                      self.knockSensor, self.O2sensor,
                      self.HorsePower, self.Torque,
                      s0, s1, s2, s3, s4)

        if s0: self.last_0x0A0 = now
        if s1: self.last_0x0A1 = now
        if s2: self.last_0x0A2 = now
        if s3: self.last_0x0A3 = now
        if s4: self.last_0x0A4 = now

        self.update_dtc()

    # ----------------------------------------------------------
    @staticmethod
    def tmax_from_rpm(rpm):
        MAP = [(700,100),(1000,300),(1500,550),(1800,750),(2500,750),
               (3500,750),(4500,750),(5500,750),(6000,720),(6500,650),(6700,550)]
        if rpm <= MAP[0][0]:  return MAP[0][1]
        if rpm >= MAP[-1][0]: return MAP[-1][1]
        rpms = [p[0] for p in MAP]
        i = bisect_left(rpms, rpm)
        r1,t1 = MAP[i-1]; r2,t2 = MAP[i]
        return t1 + (t2-t1)*(rpm-r1)/(r2-r1)

    @staticmethod
    def engine_torque(rpm, throttle, t_idle=70.0, corr=1.0):
        t_max = DME_Module.tmax_from_rpm(rpm)
        return (t_idle + (t_max - t_idle) * max(0.0, min(1.0, throttle))) * corr

    # ----------------------------------------------------------
    def DME_Data(self, rpm, throttlePosition, massAirflow, coolantTemp, intakeTemp,
                 oilTemp, batteryVoltage, oilPressure, knockSensor, O2sensor,
                 HorsePower, torque,
                 s0=True, s1=True, s2=True, s3=True, s4=True):
        can = CanController.CanController()

        def u16(v): v=int(v); v=max(0,min(v,65535)); return (v>>8)&0xFF, v&0xFF
        def u8(v):  return max(0, min(int(v), 255))

        rh, rl   = u16(rpm * 4)
        mh, ml   = u16(massAirflow * 100)
        oh, ol   = u16((oilTemp + 40) * 10)
        vh, vl   = u16(batteryVoltage * 1000)
        rth, rtl = u16(750)                          # ref torque
        hph, hpl = u16(HorsePower * 10)

        tpct = max(-125.0, min((torque / 750.0) * 100.0, 130.0))

        data_0x0A0 = [HexInt.HexInt(x) for x in [rh, rl, u8(throttlePosition*255/100), mh, ml, 0,0,0]]
        data_0x0A1 = [HexInt.HexInt(x) for x in [u8(coolantTemp+40), u8(intakeTemp+40), oh, ol, 0,0,0,0]]
        data_0x0A2 = [HexInt.HexInt(x) for x in [vh, vl, u8(oilPressure*10), 0,0,0,0,0]]
        data_0x0A3 = [HexInt.HexInt(x) for x in [u8(O2sensor*200), u8(knockSensor*2), 0,0,0,0,0,0]]
        data_0x0A4 = [HexInt.HexInt(x) for x in [u8(tpct+125), rth, rtl, hph, hpl, 0,0,0]]

        self.data_0x0A0 = data_0x0A0; self.data_0x0A1 = data_0x0A1
        self.data_0x0A2 = data_0x0A2; self.data_0x0A3 = data_0x0A3
        self.data_0x0A4 = data_0x0A4

        if s0: self.frame_0x0A0 = can.Can_Controller(0x0A0, data_0x0A0)
        if s1: self.frame_0x0A1 = can.Can_Controller(0x0A1, data_0x0A1)
        if s2: self.frame_0x0A2 = can.Can_Controller(0x0A2, data_0x0A2)
        if s3: self.frame_0x0A3 = can.Can_Controller(0x0A3, data_0x0A3)
        if s4: self.frame_0x0A4 = can.Can_Controller(0x0A4, data_0x0A4)
