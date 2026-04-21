import core.HexInt as HexInt
from . import CanController
from bisect import bisect_left
import time

from core.dtc.DTCManager import DME_DTCManager


class DME_Module(DME_DTCManager):
    """
    Motor elektronika szimulációs modul.
    DTC_POOL és DTC_FILE a DME_DTCManager-ből jön — itt nincs duplikálva.
    """

    def __init__(self):
        DME_DTCManager.__init__(self)

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
        rth, rtl = u16(750)
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
