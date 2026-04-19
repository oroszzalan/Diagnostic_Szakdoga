import HexInt
import CanController
import time

from DTCManager import DTCManager


class EPS_Module(DTCManager):

    DTC_POOL = {
        # Kormányoszlop szenzor
        "C0450": "Steering Wheel Position Sensor Circuit Fault",
        "C0452": "Steering Wheel Position Sensor Range/Performance",
        "C0455": "Steering Wheel Position Sensor Signal Missing",
        "C0460": "Steering Wheel Position Sensor Circuit Low",
        "C0463": "Steering Wheel Position Sensor Circuit High",
        # EPS motor / teljesítményelektronika
        "C0471": "EPS Motor Circuit Open",
        "C0472": "EPS Motor Circuit Short to Ground",
        "C0473": "EPS Motor Circuit Short to Battery",
        "C0474": "EPS Motor Current Sensor Circuit Fault",
        "C0475": "EPS Motor Overtemperature",
        "C0476": "EPS Motor Position Sensor Fault",
        # Nyomatékszenzor
        "C0490": "Steering Torque Sensor Circuit Fault",
        "C0491": "Steering Torque Sensor Range/Performance",
        "C0492": "Steering Torque Sensor Signal Missing",
        "C0493": "Steering Torque Sensor Signal Erratic",
        # EPS vezérlő
        "C0500": "EPS Control Module Internal Fault",
        "C0501": "EPS Control Module EEPROM Error",
        "C0502": "EPS Control Module Watchdog Reset",
        "C0503": "EPS Control Module Power Supply Low",
        "C0504": "EPS Control Module Power Supply High",
        # Rásegítés
        "C0510": "Power Steering Assist Reduced",
        "C0511": "Power Steering Assist Disabled",
        "C0513": "EPS Thermal Shutdown",
        "C0521": "EPS Assist Torque Calibration Required",
        # Kommunikáció
        "U0126": "Lost Communication with Steering Angle Sensor Module",
        "U0131": "Lost Communication with Power Steering Control Module",
        "U0140": "Lost Communication with Body Control Module",
    }

    DTC_FILE = "dtc_eps.json"

    def __init__(self, DME, DSC):
        DTCManager.__init__(self)

        self.joystick = None
        self.DME = DME
        self.DSC = DSC

        self.steeringAngle          = 0.0
        self.previousSteeringAngle  = 0.0
        self.steeringRate           = 0.0
        self.steeringTorqueDriver   = 0.0
        self.steeringAssistTorque   = 0.0
        self.epsMotorCurrent        = 0.0
        self.assistFactor           = 1.0
        self.last_update_time       = time.time()

        self.maxSteeringAngle = 540.0
        self.maxDriverTorque  = 8.0
        self.maxAssistTorque  = 10.0
        self.maxMotorCurrent  = 60.0

        self.frame_0x3D0 = ""
        self.frame_0x3D2 = ""
        self.data_0x3D0  = []
        self.data_0x3D2  = []

        self.last_0x3D0 = 0
        self.last_0x3D2 = 0

    # ----------------------------------------------------------
    def update_dtc(self):
        """Szenzor-alapú automatikus EPS DTC logika."""
        if self.epsMotorCurrent > self.maxMotorCurrent * 0.95:
            self.set_fault("C0475")   # túlmelegedés
        else:
            self.clear_fault("C0475")

        if abs(self.steeringAngle) > self.maxSteeringAngle * 0.98:
            self.set_fault("C0452")   # végállás / range/performance
        else:
            self.clear_fault("C0452")

        self.periodic_save()

    # ----------------------------------------------------------
    def EPS_simulation(self):
        now = time.time()
        dt  = max(0.001, now - self.last_update_time)
        self.last_update_time = now

        axis = self.joystick.get_axis(0)
        opt  = EPS_Module.apply_deadzone_scaled(axis, 0.15)

        target_angle = opt * self.maxSteeringAngle
        alpha = min(1.0, 8.0 * dt)
        self.steeringAngle += (target_angle - self.steeringAngle) * alpha

        self.steeringRate = (self.steeringAngle - self.previousSteeringAngle) / dt

        torque_from_angle = self.steeringAngle / self.maxSteeringAngle * 4.0
        torque_from_rate  = self.steeringRate * 0.01
        self.steeringTorqueDriver = max(-self.maxDriverTorque,
                                        min(self.maxDriverTorque,
                                            torque_from_angle + torque_from_rate))

        self.assistFactor = max(0.20, min(1.0, 1.0 - self.DSC.vehicle_speed / 180.0))

        if self.DME.rpm > 0:
            self.steeringAssistTorque = max(-self.maxAssistTorque,
                                            min(self.maxAssistTorque,
                                                self.steeringTorqueDriver * self.assistFactor))
        else:
            self.steeringAssistTorque = 0.0

        self.epsMotorCurrent = min(self.maxMotorCurrent,
                                   abs(self.steeringAssistTorque) * 4.5)
        self.previousSteeringAngle = self.steeringAngle

        now = time.time()
        s0 = now - self.last_0x3D0 >= 0.01
        s2 = now - self.last_0x3D2 >= 0.02

        self.EPS_Data(self.steeringAngle, self.steeringRate,
                      self.steeringTorqueDriver, self.steeringAssistTorque,
                      self.epsMotorCurrent, self.assistFactor, s0, s2)

        if s0: self.last_0x3D0 = now
        if s2: self.last_0x3D2 = now

        self.update_dtc()

    # ----------------------------------------------------------
    def EPS_Data(self, steeringAngle, steeringRate, steeringTorqueDriver,
                 steeringAssistTorque, epsMotorCurrent, assistFactor, s0, s2):
        can = CanController.CanController()

        def enc16(v, scale, offset=32768):
            raw = int(v * scale + offset)
            raw = max(0, min(raw, 65535))
            return (raw >> 8) & 0xFF, raw & 0xFF

        def u16(v):
            v = int(max(0, min(v, 65535)))
            return (v >> 8) & 0xFF, v & 0xFF

        def u8(v): return max(0, min(int(v), 255))

        ah, al   = enc16(steeringAngle,        10.0)
        rh, rl   = enc16(steeringRate,         100.0)
        dh, dl   = enc16(steeringTorqueDriver, 100.0)
        ash, asl = enc16(steeringAssistTorque, 100.0)
        ch, cl   = u16(epsMotorCurrent * 100)

        data_0x3D0 = [HexInt.HexInt(x) for x in [ah, al, rh, rl, dh, dl, ash, asl]]
        data_0x3D2 = [HexInt.HexInt(x) for x in [ch, cl, u8(assistFactor*255), 0,0,0,0,0]]

        self.data_0x3D0 = data_0x3D0
        self.data_0x3D2 = data_0x3D2

        if s0: self.frame_0x3D0 = can.Can_Controller(0x3D0, data_0x3D0)
        if s2: self.frame_0x3D2 = can.Can_Controller(0x3D2, data_0x3D2)

    @staticmethod
    def apply_deadzone_scaled(x, deadzone=0.15):
        if abs(x) < deadzone: return 0.0
        return (x - deadzone)/(1.0-deadzone) if x > 0 else (x + deadzone)/(1.0-deadzone)
