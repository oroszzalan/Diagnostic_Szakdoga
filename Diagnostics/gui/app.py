import time
import tkinter as tk
from tkinter import messagebox, ttk

import serial.tools.list_ports

from config import DATA_TIMEOUT_S, DEFAULT_BAUDRATE, DEFAULT_TIMEOUT, REFRESH_MS
from gui.tabs import (
    build_dme_tab,
    build_dsc_tab,
    build_dtc_tab,
    build_egs_tab,
    build_eps_tab,
    build_overview_tab,
    on_dtc_select,
)
from gui.widgets import add_bool, add_field, update_dtc_listbox
from serial_comm.receiver import DiagReceiverThread
from vehicle.state import VehicleState


class DiagAppGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("BMW Sim Diag GUI")
        self.geometry("1400x900")
        self.minsize(1200, 760)

        self.state_obj = VehicleState()
        self.receiver = None

        self.port_var = tk.StringVar()
        self.baud_var = tk.StringVar(value=str(DEFAULT_BAUDRATE))
        self.status_var = tk.StringVar(value="Nincs csatlakozva")

        self.value_vars = {}
        self.bool_vars = {}

        self._build_ui()
        self.refresh_ports()
        self.after(REFRESH_MS, self.update_gui)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

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
        ttk.Button(controls, text="Élő adatok indítása", command=self.cmd_live_start).pack(side="left", padx=(0, 6))
        ttk.Button(controls, text="Élő adatok leállítása", command=self.cmd_live_stop).pack(side="left", padx=(0, 6))
        ttk.Button(controls, text="Aktív DTC lekérés", command=self.cmd_read_active_dtc).pack(side="left", padx=(0, 6))
        ttk.Button(controls, text="Tárolt DTC lekérés", command=self.cmd_read_stored_dtc).pack(side="left", padx=(0, 6))
        ttk.Button(controls, text="Élő adatok lekérés", command=self.cmd_read_live_snapshot).pack(side="left", padx=(0, 6))
        ttk.Button(controls, text="DTC törlés", command=self.cmd_clear_dtc).pack(side="left", padx=(0, 6))

        main = ttk.Panedwindow(self, orient="horizontal")
        main.pack(fill="both", expand=True, padx=8, pady=8)

        left = ttk.Frame(main)
        right = ttk.Frame(main)
        main.add(left, weight=3)
        main.add(right, weight=2)

        notebook = ttk.Notebook(left)
        notebook.pack(fill="both", expand=True)

        self.tab_overview = ttk.Frame(notebook, padding=10)
        self.tab_dme = ttk.Frame(notebook, padding=10)
        self.tab_dsc = ttk.Frame(notebook, padding=10)
        self.tab_eps = ttk.Frame(notebook, padding=10)
        self.tab_egs = ttk.Frame(notebook, padding=10)
        self.tab_dtc = ttk.Frame(notebook, padding=10)

        notebook.add(self.tab_overview, text="Overview")
        notebook.add(self.tab_dme, text="DME")
        notebook.add(self.tab_dsc, text="DSC")
        notebook.add(self.tab_eps, text="EPS")
        notebook.add(self.tab_egs, text="EGS")
        notebook.add(self.tab_dtc, text="DTC")

        self._build_overview_tab()
        self._build_dme_tab()
        self._build_dsc_tab()
        self._build_eps_tab()
        self._build_egs_tab()
        self._build_dtc_tab()

        stats_frame = ttk.LabelFrame(right, text="Kommunikáció", padding=8)
        stats_frame.pack(fill="x")
        self._add_field(stats_frame, "Frames", "frame_counter", 0)
        self._add_field(stats_frame, "CRC hibák", "crc_errors", 1)
        self._add_field(stats_frame, "Parse hibák", "parse_errors", 2)
        self._add_field(stats_frame, "Utolsó ID", "last_id_hex", 3)
        self._add_field(stats_frame, "Utolsó frissítés", "last_update_age", 4)

        self.timeout_var = tk.StringVar(value="")
        self.timeout_label = ttk.Label(right, textvariable=self.timeout_var, foreground="red", font=("Arial", 10, "bold"))
        self.timeout_label.pack(pady=(4, 0))

        log_frame = ttk.LabelFrame(right, text="Nyers frame log", padding=8)
        log_frame.pack(fill="both", expand=True, pady=(8, 0))
        self.log_text = tk.Text(log_frame, wrap="none", height=20)
        self.log_text.pack(side="left", fill="both", expand=True)
        self.log_text.configure(state="disabled")
        scroll = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        scroll.pack(side="right", fill="y")
        self.log_text.config(yscrollcommand=scroll.set)

    def _build_overview_tab(self):
        build_overview_tab(self)

    def _build_dme_tab(self):
        build_dme_tab(self)

    def _build_dsc_tab(self):
        build_dsc_tab(self)

    def _build_eps_tab(self):
        build_eps_tab(self)

    def _build_egs_tab(self):
        build_egs_tab(self)

    def _build_dtc_tab(self):
        build_dtc_tab(self)

    def _on_dtc_select(self, event):
        on_dtc_select(self, event)

    def _add_field(self, parent, label, key, row):
        add_field(self, parent, label, key, row)

    def _add_bool(self, parent, label, key, row):
        add_bool(self, parent, label, key, row)

    def _update_dtc_listbox(self, lb, codes):
        update_dtc_listbox(lb, codes)

    def send_gateway_command(self, command):
        if not self.receiver or not self.receiver.running:
            messagebox.showwarning("Nincs kapcsolat", "Előbb csatlakozz a gatewayhez.")
            return
        self.receiver.send_command(command)

    def cmd_live_start(self):
        self.send_gateway_command("LIVE_START")

    def cmd_live_stop(self):
        self.send_gateway_command("LIVE_STOP")

    def cmd_read_active_dtc(self):
        self.state_obj.active_dtcs.clear()
        self.send_gateway_command("READ_DTC_ACTIVE")

    def cmd_read_stored_dtc(self):
        self.state_obj.stored_dtcs.clear()
        self.send_gateway_command("READ_DTC_STORED")

    def cmd_read_live_snapshot(self):
        self.send_gateway_command("READ_LIVE")

    def cmd_clear_dtc(self):
        if not self.receiver or not self.receiver.running:
            messagebox.showwarning("Nincs kapcsolat", "Előbb csatlakozz a gatewayhez.")
            return

        dialog = tk.Toplevel(self)
        dialog.title("DTC törlés")
        dialog.resizable(False, False)
        dialog.grab_set()

        ttk.Label(
            dialog,
            text="Biztosan törölni akarod az összes DTC-t?\n(DME / DSC / EGS / EPS — minden modul)",
            padding=16,
        ).pack()

        btn_frame = ttk.Frame(dialog, padding=(8, 0, 8, 12))
        btn_frame.pack()

        def do_clear():
            dialog.destroy()
            self.state_obj.active_dtcs.clear()
            self.state_obj.stored_dtcs.clear()
            self.receiver.send_command("CLEAR_DTC")

        ttk.Button(btn_frame, text="Igen, törlés", command=do_clear).pack(side="left", padx=(0, 8))
        ttk.Button(btn_frame, text="Mégse", command=dialog.destroy).pack(side="left")

        self.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - dialog.winfo_reqwidth()) // 2
        y = self.winfo_y() + (self.winfo_height() - dialog.winfo_reqheight()) // 2
        dialog.geometry(f"+{x}+{y}")

    def refresh_ports(self):
        ports = [p.device for p in serial.tools.list_ports.comports()]
        self.port_combo["values"] = ports
        if ports and (not self.port_var.get() or self.port_var.get() not in ports):
            self.port_var.set(ports[0])

    def toggle_connection(self):
        if self.receiver and self.receiver.running:
            self.disconnect()
        else:
            self.connect()

    def connect(self):
        port = self.port_var.get().strip()
        if not port:
            messagebox.showwarning("Hiányzó port", "Válassz egy COM portot.")
            return
        try:
            baud = int(self.baud_var.get().strip())
        except ValueError:
            messagebox.showwarning("Hibás baudrate", "A baudrate szám legyen.")
            return
        self.receiver = DiagReceiverThread(
            port=port,
            baudrate=baud,
            timeout=DEFAULT_TIMEOUT,
            state=self.state_obj,
            log_callback=self.append_log,
        )
        self.receiver.start()
        self.status_var.set(f"Kapcsolódás: {port} ...")
        self.connect_btn.config(text="Bontás")

    def disconnect(self):
        if self.receiver:
            self.receiver.stop()
            self.receiver = None
        self.status_var.set("Nincs csatlakozva")
        self.connect_btn.config(text="Csatlakozás")

    def append_log(self, msg):
        ts = time.strftime("%H:%M:%S")
        line = f"[{ts}] {msg}\n"

        def _write():
            self.log_text.configure(state="normal")
            self.log_text.insert("end", line)
            self.log_text.see("end")
            if int(self.log_text.index("end-1c").split(".")[0]) > 1000:
                self.log_text.delete("1.0", "200.0")
            self.log_text.configure(state="disabled")

        self.after(0, _write)

    def fmt(self, v, d=2):
        return f"{v:.{d}f}"

    def update_gui(self):
        s = self.state_obj
        gear_text = "R" if s.gear_selector == -1 else str(s.gear_selector)
        age = time.time() - s.last_update if s.last_update else 0.0

        if s.last_update == 0.0:
            self.timeout_var.set("")
        elif age > DATA_TIMEOUT_S:
            self.timeout_var.set(f"⚠ Nincs adat ({age:.1f}s)")
            self.timeout_label.configure(foreground="red")
        else:
            self.timeout_var.set("● Élő adat")
            self.timeout_label.configure(foreground="green")

        ov_values = {
            "ov_vehicle_speed_kmh": self.fmt(s.vehicle_speed_kmh, 1),
            "ov_rpm": self.fmt(s.rpm, 1),
            "ov_gear_text": gear_text,
            "ov_throttle_pct": self.fmt(s.throttle_pct, 1),
            "ov_torque_nm": self.fmt(s.torque_nm, 1),
            "ov_horsepower_hp": self.fmt(s.horsepower_hp, 1),
            "ov_coolant_temp_c": self.fmt(s.coolant_temp_c, 1),
            "ov_oil_temp_c": self.fmt(s.oil_temp_c, 1),
        }
        ov_bools = {
            "ov_abs_active": s.abs_active,
            "ov_tc_active": s.tc_active,
            "ov_dsc_active": s.dsc_active,
        }

        values = {
            "rpm": self.fmt(s.rpm, 1),
            "throttle_pct": self.fmt(s.throttle_pct, 1),
            "maf": self.fmt(s.maf, 2),
            "coolant_temp_c": self.fmt(s.coolant_temp_c, 1),
            "intake_temp_c": self.fmt(s.intake_temp_c, 1),
            "oil_temp_c": self.fmt(s.oil_temp_c, 1),
            "battery_voltage_v": self.fmt(s.battery_voltage_v, 2),
            "oil_pressure_bar": self.fmt(s.oil_pressure_bar, 2),
            "o2_sensor_v": self.fmt(s.o2_sensor_v, 3),
            "knock_sensor": self.fmt(s.knock_sensor, 2),
            "torque_nm": self.fmt(s.torque_nm, 1),
            "horsepower_hp": self.fmt(s.horsepower_hp, 1),
            "vehicle_speed_kmh": self.fmt(s.vehicle_speed_kmh, 1),
            "wheel_fl_kmh": self.fmt(s.wheel_fl_kmh, 2),
            "wheel_fr_kmh": self.fmt(s.wheel_fr_kmh, 2),
            "wheel_rl_kmh": self.fmt(s.wheel_rl_kmh, 2),
            "wheel_rr_kmh": self.fmt(s.wheel_rr_kmh, 2),
            "brake_position_pct": self.fmt(s.brake_position_pct, 1),
            "brake_pressure_bar": self.fmt(s.brake_pressure_bar, 1),
            "yaw_rate_dps": self.fmt(s.yaw_rate_dps, 2),
            "lateral_accel": self.fmt(s.lateral_accel, 2),
            "longitudinal_accel": self.fmt(s.longitudinal_accel, 2),
            "stabilization_status": str(s.stabilization_status),
            "steering_angle_deg": self.fmt(s.steering_angle_deg, 2),
            "steering_rate_dps": self.fmt(s.steering_rate_dps, 2),
            "steering_torque_driver_nm": self.fmt(s.steering_torque_driver_nm, 2),
            "steering_assist_nm": self.fmt(s.steering_assist_nm, 2),
            "eps_motor_current_a": self.fmt(s.eps_motor_current_a, 2),
            "assist_factor": self.fmt(s.assist_factor, 2),
            "gear_text": gear_text,
            "turbine_rpm": self.fmt(s.turbine_rpm, 1),
            "output_rpm": self.fmt(s.output_rpm, 1),
            "trans_oil_temp_c": self.fmt(s.trans_oil_temp_c, 1),
            "converter_slip": self.fmt(s.converter_slip, 3),
            "frame_counter": str(s.frame_counter),
            "crc_errors": str(s.crc_errors),
            "parse_errors": str(s.parse_errors),
            "last_id_hex": f"0x{s.last_id:03X}",
            "last_update_age": self.fmt(age, 2) + " s",
        }
        bool_values = {
            "abs_active": s.abs_active,
            "tc_active": s.tc_active,
            "dsc_active": s.dsc_active,
            "shifting": s.shifting,
            "lockup": s.lockup,
            "reverse_selected": s.reverse_selected,
            "neutral_selected": s.neutral_selected,
        }

        for key, var in self.value_vars.items():
            if key in ov_values:
                var.set(ov_values[key])
            elif key in values:
                var.set(values[key])

        for key, var in self.bool_vars.items():
            if key in ov_bools:
                var.set("Igen" if ov_bools[key] else "Nem")
            elif key in bool_values:
                var.set("Igen" if bool_values[key] else "Nem")

        self._update_dtc_listbox(self.active_dtc_list, s.active_dtcs)
        self._update_dtc_listbox(self.stored_dtc_list, s.stored_dtcs)

        if self.receiver and self.receiver.running:
            self.status_var.set(f"Csatlakozva: {self.receiver.port} @ {self.receiver.baudrate}")

        self.after(REFRESH_MS, self.update_gui)

    def on_close(self):
        try:
            self.disconnect()
        finally:
            self.destroy()
