import core.HexInt as HexInt
from . import CanController
import time

from core.dtc.DTCManager import EGS_DTCManager


class EGS_Module(EGS_DTCManager):
    """
    Elektronikus váltóvezérlés szimulációs modul.
    DTC_POOL és DTC_FILE az EGS_DTCManager-ből jön — itt nincs duplikálva.
    """

    def __init__(self, DME, DSC):
        EGS_DTCManager.__init__(self)

        self.DME = DME
        self.DSC = DSC
        self.joystick = None

        self.EngineRpm = 0
        self.EngineTorque = 0
        self.TurbineRpm = 0
        self.OutputRpm = 0
        self.TransmissionOilTemp = 30
        self.GearSelector = 0
        self.ThrottlePosition = 0
        self.Shifting = False

        self.shift_up        = False
        self.prev_shift_up   = False
        self.prev_shift_down = False
        self.shift_down      = False
        self.current_slip    = 0.30

        self.GEAR_RATIOS = [0.000, 5.000, 3.200, 2.143, 1.720, 1.313, 1.000, 0.823]

        self.frame_0x1B2 = ""
        self.frame_0x1B4 = ""
        self.data_0x1B2  = []
        self.data_0x1B4  = []

        self.last_0x1B2 = 0
        self.last_0x1B4 = 0

    # ----------------------------------------------------------
    def update_dtc(self):
        """Szenzor-alapú automatikus EGS DTC logika."""
        if self.TransmissionOilTemp > 130:
            self.set_fault("P0711")
        else:
            self.clear_fault("P0711")

        if self.GearSelector != 0 and abs(self.current_slip) > 0.90:
            self.set_fault("P0741")
        else:
            self.clear_fault("P0741")

        self.periodic_save()

    # ----------------------------------------------------------
    def EGS_Simulation(self):
        self.EngineRpm        = self.DME.rpm
        self.ThrottlePosition = max(0.0, min(self.DME.throttlePosition / 100.0, 1.0))
        self.EngineTorque     = self.DME.Torque

        # --- Joystick null-check ---
        if self.joystick is not None:
            shift_up   = self.joystick.get_button(5)
            shift_down = self.joystick.get_button(4)
        else:
            shift_up   = False
            shift_down = False

        if shift_up and not self.prev_shift_up:
            self.GearSelector = min(self.GearSelector + 1, len(self.GEAR_RATIOS) - 1)
            self.Shifting = True
        elif shift_down and not self.prev_shift_down:
            self.GearSelector = max(self.GearSelector - 1, -1)
            self.Shifting = True
        else:
            self.Shifting = False

        self.prev_shift_up   = shift_up
        self.prev_shift_down = shift_down

        lockup = EGS_Module.is_lockup(self.DSC.vehicle_speed, self.ThrottlePosition,
                                       self.Shifting, self.TransmissionOilTemp)
        desired_slip  = EGS_Module.target_slip(self.DSC.vehicle_speed, self.ThrottlePosition, lockup)
        self.current_slip = EGS_Module.update_slip(self.current_slip, desired_slip)

        slip_heat   = self.current_slip * 20
        shift_heat  = 3 if self.Shifting else 0
        torque_heat = (self.EngineTorque / 750) * 10
        cooling     = self.DSC.vehicle_speed * 0.03
        target_temp = 90 + slip_heat + shift_heat + torque_heat - (3 if lockup else 0) - cooling
        self.TransmissionOilTemp = max(30, min(self.TransmissionOilTemp, 140))

        if self.DME.rpm > 0:
            self.TransmissionOilTemp += (target_temp - self.TransmissionOilTemp) * 0.0001
        else:
            self.TransmissionOilTemp -= self.TransmissionOilTemp * 0.0001

        self.TurbineRpm = self.EngineRpm * (1 - self.current_slip)
        self.OutputRpm  = EGS_Module.output_rpm(self.TurbineRpm, self.GearSelector, self.GEAR_RATIOS)

        now = time.time()
        s2 = now - self.last_0x1B2 >= 0.01
        s4 = now - self.last_0x1B4 >= 0.10

        self.EGS_Data(self.GearSelector, self.TurbineRpm, self.OutputRpm,
                      self.TransmissionOilTemp, self.current_slip,
                      self.Shifting, lockup, s2, s4)

        if s2: self.last_0x1B2 = now
        if s4: self.last_0x1B4 = now

        self.update_dtc()

    # ----------------------------------------------------------
    def EGS_Data(self, GearSelector, TurbineRpm, OutputRpm, TransmissionOilTemp,
                 current_slip, Shifting, lockup, s2=True, s4=True):
        can = CanController.CanController()

        def u16(v): v=int(max(0,min(v,65535))); return (v>>8)&0xFF, v&0xFF
        def u8(v):  return max(0, min(int(v), 255))

        th, tl = u16(int(TurbineRpm))
        oh, ol = u16(int(OutputRpm))

        status = ((1 if Shifting else 0) |
                  (2 if lockup else 0) |
                  (4 if GearSelector == -1 else 0) |
                  (8 if GearSelector == 0  else 0))

        data_0x1B2 = [HexInt.HexInt(x) for x in
                      [u8(GearSelector+1), th, tl, oh, ol, status, 0, 0]]
        data_0x1B4 = [HexInt.HexInt(x) for x in
                      [u8(TransmissionOilTemp+40), u8(current_slip*200), 0,0,0,0,0,0]]

        self.data_0x1B2 = data_0x1B2
        self.data_0x1B4 = data_0x1B4

        if s2: self.frame_0x1B2 = can.Can_Controller(0x1B2, data_0x1B2)
        if s4: self.frame_0x1B4 = can.Can_Controller(0x1B4, data_0x1B4)

    # ----------------------------------------------------------
    @staticmethod
    def target_slip(speed_kmh, pedal, lockup):
        if lockup: return 0.02
        if speed_kmh < 5:  return 0.45 - 0.10*pedal
        if speed_kmh < 20: return 0.30 - 0.10*pedal
        if speed_kmh < 50: return 0.15 - 0.05*pedal
        return 0.08 - 0.03*pedal

    @staticmethod
    def update_slip(current, target, alpha=0.1):
        return current + alpha*(target - current)

    @staticmethod
    def is_lockup(speed_kmh, pedal, shifting, oil_temp):
        return (not shifting and speed_kmh >= 25 and pedal <= 0.5 and oil_temp >= 40)

    @staticmethod
    def output_rpm(turbine_rpm, gear, gear_ratios):
        if gear == -1: return turbine_rpm / 3.478
        if gear == 0:  return 0.0
        return turbine_rpm / gear_ratios[gear]
