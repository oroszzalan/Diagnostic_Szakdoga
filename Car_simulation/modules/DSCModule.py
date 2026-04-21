import core.HexInt as HexInt
from . import CanController
import time

from core.dtc.DTCManager import DSC_DTCManager


class DSC_Module(DSC_DTCManager):
    """
    Dinamikus stabilitásvezérlés szimulációs modul.
    DTC_POOL és DTC_FILE a DSC_DTCManager-ből jön — itt nincs duplikálva.
    """

    def __init__(self, EGS=None, EPS=None, DME=None):
        DSC_DTCManager.__init__(self)

        self.joystick = None
        self.EGS = EGS
        self.EPS = EPS
        self.DME = DME

        self.brakePosition = 0.0
        self.brakePressure = 0.0
        self.vehicle_speed = 0.0

        self.wheelSpeedFL = 0.0
        self.wheelSpeedFR = 0.0
        self.wheelSpeedRL = 0.0
        self.wheelSpeedRR = 0.0

        self.yawRate = 0.0
        self.lateralAccel = 0.0
        self.longitudinalAccel = 0.0

        self.absActive = False
        self.tractionControlActive = False
        self.stabilityControlActive = False
        self.stabilizationStatus = 0

        self.wheelToleranceFL = 1.00
        self.wheelToleranceFR = 1.00
        self.wheelToleranceRL = 1.00
        self.wheelToleranceRR = 1.00

        self.frame_0x2C1 = ""
        self.frame_0x2C3 = ""
        self.frame_0x2C8 = ""

        self.data_0x2C1 = []
        self.data_0x2C3 = []
        self.data_0x2C8 = []

        self.last_0x2C1 = 0
        self.last_0x2C3 = 0
        self.last_0x2C8 = 0

    # ----------------------------------------------------------
    def update_dtc(self):
        """Szenzor-alapú automatikus DSC DTC logika."""
        if self.vehicle_speed > 10:
            speeds = [self.wheelSpeedFL, self.wheelSpeedFR,
                      self.wheelSpeedRL, self.wheelSpeedRR]
            avg = sum(speeds) / 4.0
            codes = ["C0021", "C0022", "C0023", "C0024"]
            for spd, code in zip(speeds, codes):
                if abs(spd - avg) > avg * 0.5 and avg > 5:
                    self.set_fault(code)
                else:
                    self.clear_fault(code)

        self.periodic_save()

    # ----------------------------------------------------------
    def DSC_simulation(self):
        # --- Joystick null-check ---
        if self.joystick is not None:
            axis_brake = self.joystick.get_axis(4)
            brake = max(0.0, min((axis_brake + 1.0) / 2.0, 1.0))
        else:
            # Joystick nélkül megtartja az utoljára kívülről beállított brakePosition-t
            brake = self.brakePosition / 100.0

        self.brakePosition = brake * 100.0
        self.brakePressure = self.brakePosition * 1.6

        throttle = self.DME.throttlePosition / 100.0 if self.DME else 0.0

        if self.EGS is not None:
            self.vehicle_speed = DSC_Module.vehicle_speed_kmh(self.EGS.OutputRpm)
        else:
            self.vehicle_speed = 0.0

        base = self.vehicle_speed
        self.wheelSpeedFL = base * self.wheelToleranceFL
        self.wheelSpeedFR = base * self.wheelToleranceFR
        self.wheelSpeedRL = base * self.wheelToleranceRL
        self.wheelSpeedRR = base * self.wheelToleranceRR

        if self.brakePressure > 10.0:
            bf = 1.0 - min(0.35, self.brakePressure / 300.0)
            self.wheelSpeedFL *= bf
            self.wheelSpeedFR *= bf
            self.wheelSpeedRL *= bf
            self.wheelSpeedRR *= bf

        if throttle > 0.65 and self.brakePressure < 5.0:
            slip_add = (throttle - 0.65) * 20.0
            self.wheelSpeedRL += slip_add
            self.wheelSpeedRR += slip_add

        if self.EPS is not None:
            sr = max(0.0, min(abs(self.EPS.steeringAngle) / 540.0, 1.0))
            inner, outer = 1.0 - sr * 0.08, 1.0 + sr * 0.08
            if self.EPS.steeringAngle > 0:
                self.wheelSpeedFR *= inner; self.wheelSpeedRR *= inner
                self.wheelSpeedFL *= outer; self.wheelSpeedRL *= outer
            elif self.EPS.steeringAngle < 0:
                self.wheelSpeedFL *= inner; self.wheelSpeedRL *= inner
                self.wheelSpeedFR *= outer; self.wheelSpeedRR *= outer

        self.absActive = (
            self.brakePressure > 40.0 and self.vehicle_speed > 10.0 and
            any(s < self.vehicle_speed * 0.80
                for s in [self.wheelSpeedFL, self.wheelSpeedFR,
                           self.wheelSpeedRL, self.wheelSpeedRR])
        )

        self.tractionControlActive = (
            self.vehicle_speed > 5.0 and self.brakePressure < 5.0 and
            (self.wheelSpeedRL > self.vehicle_speed + 5.0 or
             self.wheelSpeedRR > self.vehicle_speed + 5.0)
        )

        if self.EPS is not None:
            self.yawRate = self.EPS.steeringAngle * self.vehicle_speed * 0.0012
        else:
            self.yawRate = 0.0
        self.lateralAccel = abs(self.yawRate) * self.vehicle_speed * 0.02

        self.stabilityControlActive = abs(self.yawRate) > 10.0 and self.vehicle_speed > 30.0

        if self.stabilityControlActive:    self.stabilizationStatus = 3
        elif self.tractionControlActive:   self.stabilizationStatus = 2
        elif self.absActive:               self.stabilizationStatus = 1
        else:                              self.stabilizationStatus = 0

        now = time.time()
        s1 = now - self.last_0x2C1 >= 0.01
        s3 = now - self.last_0x2C3 >= 0.01
        s8 = now - self.last_0x2C8 >= 0.02

        self.DSC_Data(self.brakePosition, self.brakePressure, self.vehicle_speed,
                      self.wheelSpeedFL, self.wheelSpeedFR,
                      self.wheelSpeedRL, self.wheelSpeedRR,
                      self.yawRate, self.lateralAccel, self.longitudinalAccel,
                      self.absActive, self.tractionControlActive,
                      self.stabilityControlActive, self.stabilizationStatus,
                      s1, s3, s8)

        if s1: self.last_0x2C1 = now
        if s3: self.last_0x2C3 = now
        if s8: self.last_0x2C8 = now

        self.update_dtc()

    # ----------------------------------------------------------
    def DSC_Data(self, brakePosition, brakePressure, vehicle_speed,
                 wheelSpeedFL, wheelSpeedFR, wheelSpeedRL, wheelSpeedRR,
                 yawRate, lateralAccel, longitudinalAccel,
                 absActive, tractionControlActive, stabilityControlActive,
                 stabilizationStatus,
                 s1=True, s3=True, s8=True):
        can = CanController.CanController()

        def u16(v): v=int(max(0,min(v,65535))); return (v>>8)&0xFF, v&0xFF
        def u8(v):  return max(0, min(int(v), 255))
        def s16(v):
            v = int(max(-32768, min(v, 32767)))
            if v < 0: v = (1<<16) + v
            return (v>>8)&0xFF, v&0xFF

        vh, vl   = u16(vehicle_speed)
        fh, fl   = u16(wheelSpeedFL * 100)
        frh, frl = u16(wheelSpeedFR * 100)
        rlh, rll = u16(wheelSpeedRL * 100)
        rrh, rrl = u16(wheelSpeedRR * 100)
        bph, bpl = u16(brakePressure * 10)
        yh, yl   = s16(yawRate * 100)
        lh, ll   = s16(lateralAccel * 100)
        lgh, lgl = s16(longitudinalAccel * 100)

        status = ((1 if absActive else 0) |
                  (2 if tractionControlActive else 0) |
                  (4 if stabilityControlActive else 0))

        data_0x2C1 = [HexInt.HexInt(x) for x in
                      [vh, vl, fh, fl, frh, frl, status, u8(stabilizationStatus)]]
        data_0x2C3 = [HexInt.HexInt(x) for x in
                      [u8(brakePosition*255/100), bph, bpl, yh, yl,
                       u8(lateralAccel*10+128), u8(longitudinalAccel*10+128), 0]]
        data_0x2C8 = [HexInt.HexInt(x) for x in
                      [rlh, rll, rrh, rrl, lh, ll, lgh, lgl]]

        self.data_0x2C1 = data_0x2C1
        self.data_0x2C3 = data_0x2C3
        self.data_0x2C8 = data_0x2C8

        if s1: self.frame_0x2C1 = can.Can_Controller(0x2C1, data_0x2C1)
        if s3: self.frame_0x2C3 = can.Can_Controller(0x2C3, data_0x2C3)
        if s8: self.frame_0x2C8 = can.Can_Controller(0x2C8, data_0x2C8)

    @staticmethod
    def vehicle_speed_kmh(output_rpm, final_drive=3.15, wheel_circ_m=2.22):
        return (output_rpm / final_drive) * wheel_circ_m * 60.0 / 1000.0
