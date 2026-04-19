import time
import threading
from dataclasses import dataclass, field
import tkinter as tk
from tkinter import ttk, messagebox
import CanController
from DTCDatabase import display_string as dtc_display_str

import serial
import serial.tools.list_ports


# ============================================================
# CONFIG
# ============================================================
DEFAULT_BAUDRATE = 38400
DEFAULT_TIMEOUT  = 0.1
REFRESH_MS       = 50
DATA_TIMEOUT_S   = 2.0
DEBUG_RAW        = False




# ============================================================
# CRC
# ============================================================
def can_crc15(bits: str) -> int:
    CRC15_POLY = 0x4599
    crc = 0
    for bit in bits:
        if ((crc >> 14) ^ int(bit)) & 1:
            crc = ((crc << 1) ^ CRC15_POLY) & 0x7FFF
        else:
            crc = (crc << 1) & 0x7FFF
    return crc


# ============================================================
# Destuff
# ============================================================
def destuff_can_bits(stuffed: str) -> str:
    if not stuffed:
        return ""
    out = [stuffed[0]]
    run = 1
    i   = 1
    while i < len(stuffed):
        b   = stuffed[i]
        run = run + 1 if b == out[-1] else 1
        out.append(b)
        i  += 1
        if run == 5:
            if i < len(stuffed):
                i += 1
            run = 1
    return "".join(out)


def reconstruct_frame_from_stuffed(stuffed_bits: str) -> str:
    if len(stuffed_bits) < 10:
        raise ValueError("Frame too short")
    return destuff_can_bits(stuffed_bits[:-9]) + stuffed_bits[-9:]


# ============================================================
# Helpers
# ============================================================
def bits_to_int(bits: str) -> int:
    return int(bits, 2) if bits else 0


def int_from_bytes_signed_16(hi, lo):
    v = (hi << 8) | lo
    return v - 0x10000 if v & 0x8000 else v


def int_from_bytes_unsigned_16(hi, lo):
    return (hi << 8) | lo


# ============================================================
# CAN Frame
# ============================================================
@dataclass
class CANFrame:
    sof: int; can_id: int; rtr: int; ide: int; r0: int; dlc: int
    data: list; crc_rx: int; crc_calc: int; crc_ok: bool
    ack: int; eof: str
    raw_destuffed_bits: str = ""
    raw_stuffed_bits: str = ""


# ============================================================
# Parser
# ============================================================
def parse_standard_can_frame(destuffed_bits: str, stuffed_bits: str = "") -> CANFrame:
    idx = 0

    def take(n):
        nonlocal idx
        if idx + n > len(destuffed_bits):
            raise ValueError("Frame too short")
        s = destuffed_bits[idx:idx + n]; idx += n; return s

    sof    = bits_to_int(take(1))
    can_id = bits_to_int(take(11))
    rtr    = bits_to_int(take(1))
    ide    = bits_to_int(take(1))
    r0     = bits_to_int(take(1))
    dlc    = bits_to_int(take(4))

    if sof != 0:       raise ValueError("Invalid SOF")
    if ide != 0:       raise ValueError("Only standard 11-bit frame supported")
    if rtr != 0:       raise ValueError("RTR frame not supported")
    if dlc > 8:        raise ValueError(f"Invalid DLC: {dlc}")

    data_bits = take(dlc * 8)
    data = [bits_to_int(data_bits[i:i+8]) for i in range(0, len(data_bits), 8)]

    crc_rx    = bits_to_int(take(15))
    crc_delim = take(1)
    ack_bits  = take(2)
    ack       = bits_to_int(ack_bits)
    eof       = take(7)

    crc_input = destuffed_bits[:1+11+1+1+1+4+dlc*8]
    crc_calc  = can_crc15(crc_input)
    crc_ok    = (crc_calc == crc_rx)

    if crc_delim != "1":      raise ValueError(f"Invalid CRC delimiter: {crc_delim}")
    if ack_bits  != "01":     raise ValueError(f"Invalid ACK bits: {ack_bits}")
    if eof       != "1111111": raise ValueError(f"Invalid EOF: {eof}")

    return CANFrame(sof=sof, can_id=can_id, rtr=rtr, ide=ide, r0=r0, dlc=dlc,
                    data=data, crc_rx=crc_rx, crc_calc=crc_calc, crc_ok=crc_ok,
                    ack=ack, eof=eof,
                    raw_destuffed_bits=destuffed_bits, raw_stuffed_bits=stuffed_bits)


# ============================================================
# Vehicle state
# ============================================================
@dataclass
class VehicleState:
    rpm: float = 0.0; throttle_pct: float = 0.0; maf: float = 0.0
    coolant_temp_c: float = 0.0; intake_temp_c: float = 0.0; oil_temp_c: float = 0.0
    battery_voltage_v: float = 0.0; oil_pressure_bar: float = 0.0
    knock_sensor: float = 0.0; o2_sensor_v: float = 0.0
    torque_nm: float = 0.0; ref_torque_nm: float = 750.0; horsepower_hp: float = 0.0

    vehicle_speed_kmh: float = 0.0
    wheel_fl_kmh: float = 0.0; wheel_fr_kmh: float = 0.0
    wheel_rl_kmh: float = 0.0; wheel_rr_kmh: float = 0.0
    brake_position_pct: float = 0.0; brake_pressure_bar: float = 0.0
    yaw_rate_dps: float = 0.0; lateral_accel: float = 0.0; longitudinal_accel: float = 0.0
    abs_active: bool = False; tc_active: bool = False
    dsc_active: bool = False; stabilization_status: int = 0

    steering_angle_deg: float = 0.0; steering_rate_dps: float = 0.0
    steering_torque_driver_nm: float = 0.0; steering_assist_nm: float = 0.0
    eps_motor_current_a: float = 0.0; assist_factor: float = 0.0

    gear_selector: int = 0; turbine_rpm: float = 0.0; output_rpm: float = 0.0
    trans_oil_temp_c: float = 0.0; converter_slip: float = 0.0
    shifting: bool = False; lockup: bool = False
    reverse_selected: bool = False; neutral_selected: bool = True

    active_dtcs: list = field(default_factory=list)
    stored_dtcs: list = field(default_factory=list)

    frame_counter: int = 0; crc_errors: int = 0; parse_errors: int = 0
    last_id: int = 0; last_update: float = 0.0


# ============================================================
# DTC decode helper
# ============================================================
def decode_obd_dtc_pair(b1: int, b2: int) -> str:
    family = {0b00: "P", 0b01: "C", 0b10: "B", 0b11: "U"}[(b1 >> 6) & 0b11]
    return f"{family}{(b1>>4)&0b11:X}{b1&0x0F:X}{(b2>>4)&0x0F:X}{b2&0x0F:X}"




# ============================================================
# Decode frames into state
# ============================================================
def decode_frame_into_state(frame: CANFrame, state: VehicleState):
    data = frame.data
    cid  = frame.can_id

    state.frame_counter += 1
    state.last_id        = cid
    state.last_update    = time.time()

    if not frame.crc_ok:
        state.crc_errors += 1

    if cid == 0x0A0 and len(data) == 8:
        state.rpm          = ((data[0]<<8)|data[1]) / 4.0
        state.throttle_pct = data[2] * 100.0 / 255.0
        state.maf          = ((data[3]<<8)|data[4]) / 100.0

    elif cid == 0x0A1 and len(data) == 8:
        state.coolant_temp_c = data[0] - 40
        state.intake_temp_c  = data[1] - 40
        state.oil_temp_c     = ((data[2]<<8)|data[3]) / 10.0 - 40.0

    elif cid == 0x0A2 and len(data) == 8:
        state.battery_voltage_v = ((data[0]<<8)|data[1]) / 1000.0
        state.oil_pressure_bar  = data[2] / 10.0

    elif cid == 0x0A3 and len(data) == 8:
        state.o2_sensor_v  = data[0] / 200.0
        state.knock_sensor = data[1] / 2.0

    elif cid == 0x0A4 and len(data) == 8:
        torque_pct          = data[0] - 125.0
        state.ref_torque_nm = float((data[1]<<8)|data[2])
        state.torque_nm     = (torque_pct / 100.0) * state.ref_torque_nm
        state.horsepower_hp = ((data[3]<<8)|data[4]) / 10.0

    elif cid == 0x1B2 and len(data) == 8:
        state.gear_selector    = data[0] - 1
        state.turbine_rpm      = (data[1]<<8)|data[2]
        state.output_rpm       = (data[3]<<8)|data[4]
        st = data[5]
        state.shifting         = bool(st & 1)
        state.lockup           = bool(st & 2)
        state.reverse_selected = bool(st & 4)
        state.neutral_selected = bool(st & 8)

    elif cid == 0x1B4 and len(data) == 8:
        state.trans_oil_temp_c = data[0] - 40
        state.converter_slip   = data[1] / 200.0

    elif cid == 0x2C1 and len(data) == 8:
        state.vehicle_speed_kmh = float((data[0]<<8)|data[1])
        state.wheel_fl_kmh      = ((data[2]<<8)|data[3]) / 100.0
        state.wheel_fr_kmh      = ((data[4]<<8)|data[5]) / 100.0
        st = data[6]
        state.abs_active           = bool(st & 1)
        state.tc_active            = bool(st & 2)
        state.dsc_active           = bool(st & 4)
        state.stabilization_status = data[7]

    elif cid == 0x2C3 and len(data) == 8:
        state.brake_position_pct = data[0] * 100.0 / 255.0
        state.brake_pressure_bar = ((data[1]<<8)|data[2]) / 10.0
        state.yaw_rate_dps       = int_from_bytes_signed_16(data[3], data[4]) / 100.0
        state.lateral_accel      = (data[5] - 128) / 10.0
        state.longitudinal_accel = (data[6] - 128) / 10.0

    elif cid == 0x2C8 and len(data) == 8:
        state.wheel_rl_kmh       = ((data[0]<<8)|data[1]) / 100.0
        state.wheel_rr_kmh       = ((data[2]<<8)|data[3]) / 100.0
        state.lateral_accel      = int_from_bytes_signed_16(data[4], data[5]) / 100.0
        state.longitudinal_accel = int_from_bytes_signed_16(data[6], data[7]) / 100.0

    elif cid == 0x3D0 and len(data) == 8:
        state.steering_angle_deg        = (int_from_bytes_unsigned_16(data[0],data[1]) - 32768) / 10.0
        state.steering_rate_dps         = (int_from_bytes_unsigned_16(data[2],data[3]) - 32768) / 100.0
        state.steering_torque_driver_nm = (int_from_bytes_unsigned_16(data[4],data[5]) - 32768) / 100.0
        state.steering_assist_nm        = (int_from_bytes_unsigned_16(data[6],data[7]) - 32768) / 100.0

    elif cid == 0x3D2 and len(data) == 8:
        state.eps_motor_current_a = int_from_bytes_unsigned_16(data[0],data[1]) / 100.0
        state.assist_factor       = data[2] / 255.0

    elif cid == 0x700 and len(data) == 8:
        # Aktív DTC frame — hozzáfűzzük (nem felülírjuk), majd deduplikálunk
        new_codes = [decode_obd_dtc_pair(data[i], data[i+1])
                     for i in range(0, 8, 2) if data[i] or data[i+1]]
        # Hozzáfűzés, duplikátum szűrés
        existing = set(state.active_dtcs)
        for c in new_codes:
            if c not in existing:
                state.active_dtcs.append(c)
                existing.add(c)

    elif cid == 0x701 and len(data) == 8:
        new_codes = [decode_obd_dtc_pair(data[i], data[i+1])
                     for i in range(0, 8, 2) if data[i] or data[i+1]]
        existing = set(state.stored_dtcs)
        for c in new_codes:
            if c not in existing:
                state.stored_dtcs.append(c)
                existing.add(c)


# ============================================================
# Serial receiver thread
# ============================================================
class DiagReceiverThread(threading.Thread):
    def __init__(self, port, baudrate, timeout, state, log_callback=None):
        super().__init__(daemon=True)
        self.port = port; self.baudrate = baudrate; self.timeout = timeout
        self.state = state; self.log_callback = log_callback
        self.running = False; self.ser = None
        self.lock = threading.Lock()

    def log(self, msg):
        if self.log_callback: self.log_callback(msg)

    def send_command(self, command):
        if not self.ser:
            self.log("Nincs aktív soros kapcsolat."); return False
        try:
            self.ser.write((command.strip() + "\r\n").encode("ascii", errors="ignore"))
            self.log(f"TX {command.strip()}"); return True
        except Exception as e:
            self.log(f"Küldési hiba: {e}"); return False

    def stop(self):
        self.running = False
        if self.ser:
            try: self.ser.close()
            except Exception: pass
            self.ser = None

    @staticmethod
    def _split_line(data):
        for sep in (b"\r\n", b"\n", b"\r"):
            idx = data.find(sep)
            if idx != -1:
                return data[:idx], data[idx+len(sep):]
        return None, data

    def run(self):
        try:
            self.ser = serial.Serial(port=self.port, baudrate=self.baudrate, timeout=self.timeout)
        except Exception as e:
            self.log(f"Portnyitási hiba: {e}"); return

        self.running = True
        self.log(f"Csatlakozva: {self.port} @ {self.baudrate}")
        buf = b""

        while self.running:
            try:
                chunk = self.ser.read(512)
                if chunk:
                    buf += chunk

                while b"\n" in buf or b"\r" in buf:
                    line, buf = self._split_line(buf)
                    if line is None: break

                    decoded_line = line.decode("ascii", errors="ignore").strip()

                    if (decoded_line.startswith("OK ") or
                            decoded_line.startswith("ERROR") or
                            decoded_line == "UNKNOWN_COMMAND"):
                        self.log(f"RX TXT {decoded_line}")
                        # Ha OK CLEAR_DTC jön → töröljük a lokális DTC listát is
                        if decoded_line == "OK CLEAR_DTC":
                            with self.lock:
                                self.state.active_dtcs.clear()
                                self.state.stored_dtcs.clear()
                        continue

                    if "frame_" in decoded_line and "=" in decoded_line:
                        decoded_line = decoded_line.split("=", 1)[1].strip()

                    bitline = "".join(ch for ch in decoded_line if ch in "01")

                    if bitline:
                        try:
                            full_destuffed = reconstruct_frame_from_stuffed(bitline)
                            frame = parse_standard_can_frame(full_destuffed, bitline)
                            with self.lock:
                                decode_frame_into_state(frame, self.state)
                            if DEBUG_RAW:
                                self.log(f"RAW     {bitline}")
                                self.log(f"DESTUFF {full_destuffed}")
                            self.log(
                                f"RX 0x{frame.can_id:03X} DLC={frame.dlc} "
                                f"DATA={' '.join(f'{b:02X}' for b in frame.data)} "
                                f"CRC={'OK' if frame.crc_ok else 'BAD'}"
                            )
                        except Exception as e:
                            with self.lock: self.state.parse_errors += 1
                            self.log(f"Parse hiba: {e}")
                    elif decoded_line:
                        self.log(f"RX TXT {decoded_line}")

                time.sleep(0.001)

            except Exception as e:
                self.log(f"Soros kommunikációs hiba: {e}")
                time.sleep(0.1)

        self.log("Kapcsolat lezárva.")


# ============================================================
# GUI
# ============================================================
class DiagAppGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("BMW Sim Diag GUI")
        self.geometry("1400x900")
        self.minsize(1200, 760)

        self.state_obj = VehicleState()
        self.receiver  = None

        self.port_var   = tk.StringVar()
        self.baud_var   = tk.StringVar(value=str(DEFAULT_BAUDRATE))
        self.status_var = tk.StringVar(value="Nincs csatlakozva")

        self.value_vars = {}
        self.bool_vars  = {}

        self._build_ui()
        self.refresh_ports()
        self.after(REFRESH_MS, self.update_gui)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    # ----------------------------------------------------------
    def _build_ui(self):
        top = ttk.Frame(self, padding=8)
        top.pack(fill="x")
        ttk.Label(top, text="COM port:").pack(side="left")
        self.port_combo = ttk.Combobox(top, textvariable=self.port_var, width=18, state="readonly")
        self.port_combo.pack(side="left", padx=(5, 8))
        ttk.Button(top, text="Frissítés", command=self.refresh_ports).pack(side="left", padx=(0, 12))
        ttk.Label(top, text="Baud:").pack(side="left")
        ttk.Entry(top, textvariable=self.baud_var, width=10).pack(side="left", padx=(5, 8))
        self.connect_btn = ttk.Button(top, text="Csatlakozás", command=self.toggle_connection)
        self.connect_btn.pack(side="left", padx=(0, 8))
        ttk.Label(top, textvariable=self.status_var).pack(side="left", padx=(12, 0))

        controls = ttk.LabelFrame(self, text="Gateway vezérlés", padding=8)
        controls.pack(fill="x", padx=8, pady=(0, 8))
        ttk.Button(controls, text="Élő adatok indítása",  command=self.cmd_live_start).pack(side="left", padx=(0,6))
        ttk.Button(controls, text="Élő adatok leállítása", command=self.cmd_live_stop).pack(side="left", padx=(0,6))
        ttk.Button(controls, text="Aktív DTC lekérés",    command=self.cmd_read_active_dtc).pack(side="left", padx=(0,6))
        ttk.Button(controls, text="Tárolt DTC lekérés",   command=self.cmd_read_stored_dtc).pack(side="left", padx=(0,6))
        ttk.Button(controls, text="Élő adatok lekérés",   command=self.cmd_read_live_snapshot).pack(side="left", padx=(0,6))
        ttk.Button(controls, text="DTC törlés",           command=self.cmd_clear_dtc).pack(side="left", padx=(0,6))

        main = ttk.Panedwindow(self, orient="horizontal")
        main.pack(fill="both", expand=True, padx=8, pady=8)

        left  = ttk.Frame(main)
        right = ttk.Frame(main)
        main.add(left,  weight=3)
        main.add(right, weight=2)

        notebook = ttk.Notebook(left)
        notebook.pack(fill="both", expand=True)

        self.tab_overview = ttk.Frame(notebook, padding=10)
        self.tab_dme      = ttk.Frame(notebook, padding=10)
        self.tab_dsc      = ttk.Frame(notebook, padding=10)
        self.tab_eps      = ttk.Frame(notebook, padding=10)
        self.tab_egs      = ttk.Frame(notebook, padding=10)
        self.tab_dtc      = ttk.Frame(notebook, padding=10)

        notebook.add(self.tab_overview, text="Overview")
        notebook.add(self.tab_dme,      text="DME")
        notebook.add(self.tab_dsc,      text="DSC")
        notebook.add(self.tab_eps,      text="EPS")
        notebook.add(self.tab_egs,      text="EGS")
        notebook.add(self.tab_dtc,      text="DTC")

        self._build_overview_tab()
        self._build_dme_tab()
        self._build_dsc_tab()
        self._build_eps_tab()
        self._build_egs_tab()
        self._build_dtc_tab()

        stats_frame = ttk.LabelFrame(right, text="Kommunikáció", padding=8)
        stats_frame.pack(fill="x")
        self._add_field(stats_frame, "Frames",           "frame_counter",   0)
        self._add_field(stats_frame, "CRC hibák",        "crc_errors",      1)
        self._add_field(stats_frame, "Parse hibák",      "parse_errors",    2)
        self._add_field(stats_frame, "Utolsó ID",        "last_id_hex",     3)
        self._add_field(stats_frame, "Utolsó frissítés", "last_update_age", 4)

        self.timeout_var = tk.StringVar(value="")
        self.timeout_label = ttk.Label(right, textvariable=self.timeout_var,
                                       foreground="red", font=("Arial", 10, "bold"))
        self.timeout_label.pack(pady=(4, 0))

        log_frame = ttk.LabelFrame(right, text="Nyers frame log", padding=8)
        log_frame.pack(fill="both", expand=True, pady=(8, 0))
        self.log_text = tk.Text(log_frame, wrap="none", height=20)
        self.log_text.pack(side="left", fill="both", expand=True)
        self.log_text.configure(state="disabled")
        scroll = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        scroll.pack(side="right", fill="y")
        self.log_text.config(yscrollcommand=scroll.set)

    # ----------------------------------------------------------
    def _build_overview_tab(self):
        frm = self.tab_overview
        self._add_field(frm, "Sebesség [km/h]",   "ov_vehicle_speed_kmh", 0)
        self._add_field(frm, "RPM",                "ov_rpm",               1)
        self._add_field(frm, "Fokozat",            "ov_gear_text",         2)
        self._add_field(frm, "Throttle [%]",       "ov_throttle_pct",      3)
        self._add_field(frm, "Nyomaték [Nm]",      "ov_torque_nm",         4)
        self._add_field(frm, "Teljesítmény [hp]",  "ov_horsepower_hp",     5)
        self._add_field(frm, "Hűtővíz [°C]",      "ov_coolant_temp_c",    6)
        self._add_field(frm, "Olajhő [°C]",        "ov_oil_temp_c",        7)
        self._add_bool (frm, "ABS",                "ov_abs_active",        8)
        self._add_bool (frm, "TC",                 "ov_tc_active",         9)
        self._add_bool (frm, "DSC",                "ov_dsc_active",        10)

    def _build_dme_tab(self):
        frm = self.tab_dme
        for i, (label, key) in enumerate([
            ("RPM","rpm"), ("Throttle [%]","throttle_pct"), ("MAF","maf"),
            ("Coolant temp [°C]","coolant_temp_c"), ("Intake temp [°C]","intake_temp_c"),
            ("Oil temp [°C]","oil_temp_c"), ("Battery [V]","battery_voltage_v"),
            ("Oil pressure [bar]","oil_pressure_bar"), ("O2 sensor [V]","o2_sensor_v"),
            ("Knock sensor","knock_sensor"), ("Torque [Nm]","torque_nm"),
            ("Horsepower [hp]","horsepower_hp"),
        ]):
            self._add_field(frm, label, key, i)

    def _build_dsc_tab(self):
        frm = self.tab_dsc
        fields = [
            ("Vehicle speed [km/h]","vehicle_speed_kmh"), ("Wheel FL [km/h]","wheel_fl_kmh"),
            ("Wheel FR [km/h]","wheel_fr_kmh"), ("Wheel RL [km/h]","wheel_rl_kmh"),
            ("Wheel RR [km/h]","wheel_rr_kmh"), ("Brake pos [%]","brake_position_pct"),
            ("Brake pressure","brake_pressure_bar"), ("Yaw rate [deg/s]","yaw_rate_dps"),
            ("Lateral accel","lateral_accel"), ("Longitudinal accel","longitudinal_accel"),
            ("Stabilization status","stabilization_status"),
        ]
        for i, (l, k) in enumerate(fields): self._add_field(frm, l, k, i)
        n = len(fields)
        self._add_bool(frm, "ABS active", "abs_active", n)
        self._add_bool(frm, "TC active",  "tc_active",  n+1)
        self._add_bool(frm, "DSC active", "dsc_active", n+2)

    def _build_eps_tab(self):
        frm = self.tab_eps
        for i, (l, k) in enumerate([
            ("Steering angle [deg]","steering_angle_deg"),
            ("Steering rate [deg/s]","steering_rate_dps"),
            ("Driver torque [Nm]","steering_torque_driver_nm"),
            ("Assist torque [Nm]","steering_assist_nm"),
            ("Motor current [A]","eps_motor_current_a"),
            ("Assist factor","assist_factor"),
        ]):
            self._add_field(frm, l, k, i)

    def _build_egs_tab(self):
        frm = self.tab_egs
        fields = [
            ("Gear","gear_text"), ("Turbine rpm","turbine_rpm"),
            ("Output rpm","output_rpm"), ("Trans oil temp [°C]","trans_oil_temp_c"),
            ("Converter slip","converter_slip"),
        ]
        for i, (l, k) in enumerate(fields): self._add_field(frm, l, k, i)
        n = len(fields)
        self._add_bool(frm, "Shifting", "shifting",         n)
        self._add_bool(frm, "Lockup",   "lockup",           n+1)
        self._add_bool(frm, "Reverse",  "reverse_selected", n+2)
        self._add_bool(frm, "Neutral",  "neutral_selected", n+3)

    def _build_dtc_tab(self):
        """DTC tab — listbox + leírás panel."""
        frm = self.tab_dtc

        # Felső rész: két listbox egymás mellett
        lists_frame = ttk.Frame(frm)
        lists_frame.pack(fill="both", expand=True)

        # Aktív DTC
        left = ttk.LabelFrame(lists_frame, text="Aktív DTC", padding=8)
        left.pack(side="left", fill="both", expand=True, padx=(0, 4))

        self.active_dtc_list = tk.Listbox(left, font=("Courier", 10),
                                           selectmode=tk.SINGLE, activestyle="none")
        self.active_dtc_list.pack(fill="both", expand=True)
        self.active_dtc_list.bind("<<ListboxSelect>>", self._on_dtc_select)

        # Tárolt DTC
        right = ttk.LabelFrame(lists_frame, text="Tárolt DTC", padding=8)
        right.pack(side="left", fill="both", expand=True, padx=(4, 0))

        self.stored_dtc_list = tk.Listbox(right, font=("Courier", 10),
                                           selectmode=tk.SINGLE, activestyle="none")
        self.stored_dtc_list.pack(fill="both", expand=True)
        self.stored_dtc_list.bind("<<ListboxSelect>>", self._on_dtc_select)

        # Alsó rész: kiválasztott kód leírása
        self.dtc_desc_var = tk.StringVar(value="Válassz ki egy DTC kódot a részletekért.")
        desc_frame = ttk.LabelFrame(frm, text="Leírás", padding=8)
        desc_frame.pack(fill="x", pady=(8, 0))
        ttk.Label(desc_frame, textvariable=self.dtc_desc_var,
                  wraplength=700, justify="left").pack(anchor="w")

    def _on_dtc_select(self, event):
        """Listbox kiválasztás → leírás megjelenítése."""
        widget = event.widget
        sel = widget.curselection()
        if not sel:
            return
        item = widget.get(sel[0])
        # item formátuma: "P0300  —  Random Misfire" vagy csak "P0300"
        code = item.split()[0].strip()
        self.dtc_desc_var.set(f"{code}")

    # ----------------------------------------------------------
    def _add_field(self, parent, label, key, row):
        ttk.Label(parent, text=label+":").grid(row=row, column=0, sticky="w", padx=(0,8), pady=3)
        var = tk.StringVar(value="-")
        ttk.Label(parent, textvariable=var).grid(row=row, column=1, sticky="w", pady=3)
        self.value_vars[key] = var

    def _add_bool(self, parent, label, key, row):
        ttk.Label(parent, text=label+":").grid(row=row, column=0, sticky="w", padx=(0,8), pady=3)
        var = tk.StringVar(value="-")
        ttk.Label(parent, textvariable=var).grid(row=row, column=1, sticky="w", pady=3)
        self.bool_vars[key] = var

    # ----------------------------------------------------------
    def send_gateway_command(self, command):
        if not self.receiver or not self.receiver.running:
            messagebox.showwarning("Nincs kapcsolat", "Előbb csatlakozz a gatewayhez.")
            return
        self.receiver.send_command(command)

    def cmd_live_start(self):         self.send_gateway_command("LIVE_START")
    def cmd_live_stop(self):          self.send_gateway_command("LIVE_STOP")
    def cmd_read_active_dtc(self):
        # Lekérés előtt töröljük a lokális listát hogy friss adatot kapjunk
        self.state_obj.active_dtcs.clear()
        self.send_gateway_command("READ_DTC_ACTIVE")
    def cmd_read_stored_dtc(self):
        self.state_obj.stored_dtcs.clear()
        self.send_gateway_command("READ_DTC_STORED")
    def cmd_read_live_snapshot(self): self.send_gateway_command("READ_LIVE")

    def cmd_clear_dtc(self):
        """
        Megerősítő dialóg NÉLKÜL hívja a törlést — a messagebox.askyesno blokkolja
        a Tkinter főszálát és deadlockot okoz a receiver thread-del.
        Helyette: custom nem-blokkoló Toplevel ablak.
        """
        if not self.receiver or not self.receiver.running:
            messagebox.showwarning("Nincs kapcsolat", "Előbb csatlakozz a gatewayhez.")
            return

        # Nem-blokkoló megerősítő ablak
        dialog = tk.Toplevel(self)
        dialog.title("DTC törlés")
        dialog.resizable(False, False)
        dialog.grab_set()   # modális, de NEM blokkolja az event loop-ot

        ttk.Label(dialog,
                  text="Biztosan törölni akarod az összes DTC-t?\n(DME / DSC / EGS / EPS — minden modul)",
                  padding=16).pack()

        btn_frame = ttk.Frame(dialog, padding=(8, 0, 8, 12))
        btn_frame.pack()

        def do_clear():
            dialog.destroy()
            # Lokális lista törlése azonnal
            self.state_obj.active_dtcs.clear()
            self.state_obj.stored_dtcs.clear()
            # Parancs küldése a gateway felé
            self.receiver.send_command("CLEAR_DTC")

        ttk.Button(btn_frame, text="Igen, törlés", command=do_clear).pack(side="left", padx=(0, 8))
        ttk.Button(btn_frame, text="Mégse", command=dialog.destroy).pack(side="left")

        # Ablakot a szülő közepére igazítjuk
        self.update_idletasks()
        x = self.winfo_x() + (self.winfo_width()  - dialog.winfo_reqwidth())  // 2
        y = self.winfo_y() + (self.winfo_height() - dialog.winfo_reqheight()) // 2
        dialog.geometry(f"+{x}+{y}")

    def refresh_ports(self):
        ports = [p.device for p in serial.tools.list_ports.comports()]
        self.port_combo["values"] = ports
        if ports and (not self.port_var.get() or self.port_var.get() not in ports):
            self.port_var.set(ports[0])

    def toggle_connection(self):
        if self.receiver and self.receiver.running: self.disconnect()
        else: self.connect()

    def connect(self):
        port = self.port_var.get().strip()
        if not port:
            messagebox.showwarning("Hiányzó port", "Válassz egy COM portot."); return
        try:
            baud = int(self.baud_var.get().strip())
        except ValueError:
            messagebox.showwarning("Hibás baudrate", "A baudrate szám legyen."); return
        self.receiver = DiagReceiverThread(
            port=port, baudrate=baud, timeout=DEFAULT_TIMEOUT,
            state=self.state_obj, log_callback=self.append_log)
        self.receiver.start()
        self.status_var.set(f"Kapcsolódás: {port} ...")
        self.connect_btn.config(text="Bontás")

    def disconnect(self):
        if self.receiver: self.receiver.stop(); self.receiver = None
        self.status_var.set("Nincs csatlakozva")
        self.connect_btn.config(text="Csatlakozás")

    def append_log(self, msg):
        ts   = time.strftime("%H:%M:%S")
        line = f"[{ts}] {msg}\n"
        def _write():
            self.log_text.configure(state="normal")
            self.log_text.insert("end", line)
            self.log_text.see("end")
            if int(self.log_text.index("end-1c").split(".")[0]) > 1000:
                self.log_text.delete("1.0", "200.0")
            self.log_text.configure(state="disabled")
        self.after(0, _write)

    def fmt(self, v, d=2): return f"{v:.{d}f}"

    # ----------------------------------------------------------
    def update_gui(self):
        s         = self.state_obj
        gear_text = "R" if s.gear_selector == -1 else str(s.gear_selector)
        age       = time.time() - s.last_update if s.last_update else 0.0

        # Timeout jelzés
        if s.last_update == 0.0:
            self.timeout_var.set("")
        elif age > DATA_TIMEOUT_S:
            self.timeout_var.set(f"⚠ Nincs adat ({age:.1f}s)")
            self.timeout_label.configure(foreground="red")
        else:
            self.timeout_var.set("● Élő adat")
            self.timeout_label.configure(foreground="green")

        # Overview értékek
        ov_values = {
            "ov_vehicle_speed_kmh": self.fmt(s.vehicle_speed_kmh, 1),
            "ov_rpm":               self.fmt(s.rpm, 1),
            "ov_gear_text":         gear_text,
            "ov_throttle_pct":      self.fmt(s.throttle_pct, 1),
            "ov_torque_nm":         self.fmt(s.torque_nm, 1),
            "ov_horsepower_hp":     self.fmt(s.horsepower_hp, 1),
            "ov_coolant_temp_c":    self.fmt(s.coolant_temp_c, 1),
            "ov_oil_temp_c":        self.fmt(s.oil_temp_c, 1),
        }
        ov_bools = {
            "ov_abs_active": s.abs_active,
            "ov_tc_active":  s.tc_active,
            "ov_dsc_active": s.dsc_active,
        }

        # Egyéb tab értékek
        values = {
            "rpm": self.fmt(s.rpm,1), "throttle_pct": self.fmt(s.throttle_pct,1),
            "maf": self.fmt(s.maf,2), "coolant_temp_c": self.fmt(s.coolant_temp_c,1),
            "intake_temp_c": self.fmt(s.intake_temp_c,1), "oil_temp_c": self.fmt(s.oil_temp_c,1),
            "battery_voltage_v": self.fmt(s.battery_voltage_v,2),
            "oil_pressure_bar": self.fmt(s.oil_pressure_bar,2),
            "o2_sensor_v": self.fmt(s.o2_sensor_v,3), "knock_sensor": self.fmt(s.knock_sensor,2),
            "torque_nm": self.fmt(s.torque_nm,1), "horsepower_hp": self.fmt(s.horsepower_hp,1),
            "vehicle_speed_kmh": self.fmt(s.vehicle_speed_kmh,1),
            "wheel_fl_kmh": self.fmt(s.wheel_fl_kmh,2), "wheel_fr_kmh": self.fmt(s.wheel_fr_kmh,2),
            "wheel_rl_kmh": self.fmt(s.wheel_rl_kmh,2), "wheel_rr_kmh": self.fmt(s.wheel_rr_kmh,2),
            "brake_position_pct": self.fmt(s.brake_position_pct,1),
            "brake_pressure_bar": self.fmt(s.brake_pressure_bar,1),
            "yaw_rate_dps": self.fmt(s.yaw_rate_dps,2),
            "lateral_accel": self.fmt(s.lateral_accel,2),
            "longitudinal_accel": self.fmt(s.longitudinal_accel,2),
            "stabilization_status": str(s.stabilization_status),
            "steering_angle_deg": self.fmt(s.steering_angle_deg,2),
            "steering_rate_dps": self.fmt(s.steering_rate_dps,2),
            "steering_torque_driver_nm": self.fmt(s.steering_torque_driver_nm,2),
            "steering_assist_nm": self.fmt(s.steering_assist_nm,2),
            "eps_motor_current_a": self.fmt(s.eps_motor_current_a,2),
            "assist_factor": self.fmt(s.assist_factor,2),
            "gear_text": gear_text, "turbine_rpm": self.fmt(s.turbine_rpm,1),
            "output_rpm": self.fmt(s.output_rpm,1),
            "trans_oil_temp_c": self.fmt(s.trans_oil_temp_c,1),
            "converter_slip": self.fmt(s.converter_slip,3),
            "frame_counter": str(s.frame_counter), "crc_errors": str(s.crc_errors),
            "parse_errors": str(s.parse_errors),
            "last_id_hex": f"0x{s.last_id:03X}",
            "last_update_age": self.fmt(age,2) + " s",
        }
        bool_values = {
            "abs_active": s.abs_active, "tc_active": s.tc_active,
            "dsc_active": s.dsc_active, "shifting": s.shifting,
            "lockup": s.lockup, "reverse_selected": s.reverse_selected,
            "neutral_selected": s.neutral_selected,
        }

        for key, var in self.value_vars.items():
            if key in ov_values: var.set(ov_values[key])
            elif key in values:  var.set(values[key])

        for key, var in self.bool_vars.items():
            if key in ov_bools:    var.set("Igen" if ov_bools[key] else "Nem")
            elif key in bool_values: var.set("Igen" if bool_values[key] else "Nem")

        # DTC listboxok frissítése — kód + leírás formátumban
        self._update_dtc_listbox(self.active_dtc_list, s.active_dtcs)
        self._update_dtc_listbox(self.stored_dtc_list, s.stored_dtcs)

        if self.receiver and self.receiver.running:
            self.status_var.set(f"Csatlakozva: {self.receiver.port} @ {self.receiver.baudrate}")

        self.after(REFRESH_MS, self.update_gui)

    def _update_dtc_listbox(self, lb: tk.Listbox, codes: list):
        """Frissíti a DTC listboxot kód + leírás formátumban."""
        new_items = [dtc_display_str(c) for c in codes] if codes else ["-"]
        current   = list(lb.get(0, tk.END))
        if current != new_items:
            lb.delete(0, tk.END)
            for item in new_items:
                lb.insert(tk.END, item)
                # Színezés a kód típusa alapján
                code = item.split()[0]
                if code.startswith("P"):   lb.itemconfig(tk.END, fg="#e06c75")  # piros
                elif code.startswith("C"): lb.itemconfig(tk.END, fg="#e5c07b")  # sárga
                elif code.startswith("U"): lb.itemconfig(tk.END, fg="#56b6c2")  # kék
                elif code.startswith("B"): lb.itemconfig(tk.END, fg="#98c379")  # zöld

    def _update_listbox(self, lb, items):
        current = list(lb.get(0, tk.END))
        new = items if items else ["-"]
        if current != new:
            lb.delete(0, tk.END)
            for item in new: lb.insert(tk.END, item)

    def on_close(self):
        try: self.disconnect()
        finally: self.destroy()


# ============================================================
# Self-test
# ============================================================
def self_test_can_parser():
    cc = CanController.CanController()
    tests = [
        (0x0A0, [0x12,0x34,0x56,0x78,0x9A,0xBC,0xDE,0xF0]),
        (0x2C1, [0x00,0x64,0x01,0x02,0x03,0x04,0x05,0x06]),
        (0x3D0, [0x80,0x00,0x80,0x00,0x80,0x00,0x80,0x00]),
        (0x700, [0x02,0x17,0x05,0x20,0x05,0x62,0x00,0x00]),
    ]
    for can_id, data in tests:
        stuffed        = cc.Can_Controller(can_id, data)
        full_destuffed = reconstruct_frame_from_stuffed(stuffed)
        frame          = parse_standard_can_frame(full_destuffed, stuffed)
        if frame.can_id != can_id:
            raise RuntimeError(f"ID mismatch: 0x{can_id:03X} → 0x{frame.can_id:03X}")
        if frame.data != data:
            raise RuntimeError(f"DATA mismatch for 0x{can_id:03X}")
    print("CAN parser self-test OK")


def main():
    self_test_can_parser()
    app = DiagAppGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
