import threading
import time
import serial
from . import CanController
import core.HexInt as HexInt


class OBD2Gateway(threading.Thread):
    def __init__(self, port, dme, dsc, egs, eps=None, baudrate=38400, timeout=0.01):
        super().__init__(daemon=True)
        self.port_name = port
        self.baudrate  = baudrate
        self.timeout   = timeout

        self.dme = dme
        self.dsc = dsc
        self.egs = egs
        self.eps = eps

        self.ser = None
        self.running = False
        self.live_stream_enabled = True
        self.live_period   = 0.05
        self.last_live_send = 0.0

        self.can = CanController.CanController()

    # ----------------------------------------------------------
    def open(self):
        self.ser = serial.Serial(
            port=self.port_name,
            baudrate=self.baudrate,
            timeout=self.timeout,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE
        )

    def close(self):
        self.running = False
        if self.ser is not None:
            try: self.ser.close()
            except Exception: pass
            self.ser = None

    def stop(self):
        self.close()

    # ----------------------------------------------------------
    def send_text(self, text: str):
        if self.ser and text:
            self.ser.write((text.strip() + "\r\n").encode("ascii", errors="ignore"))

    def send_frame_string(self, frame: str):
        if self.ser and frame:
            self.ser.write((frame.strip() + "\r\n").encode("ascii", errors="ignore"))

    # ----------------------------------------------------------
    def send_live_frames(self):
        frames = [
            getattr(self.dme, "frame_0x0A0", ""),
            getattr(self.dme, "frame_0x0A1", ""),
            getattr(self.dme, "frame_0x0A2", ""),
            getattr(self.dme, "frame_0x0A3", ""),
            getattr(self.dme, "frame_0x0A4", ""),
            getattr(self.egs, "frame_0x1B2", ""),
            getattr(self.egs, "frame_0x1B4", ""),
            getattr(self.dsc, "frame_0x2C1", ""),
            getattr(self.dsc, "frame_0x2C3", ""),
            getattr(self.dsc, "frame_0x2C8", ""),
        ]

        if self.eps is not None:
            frames.append(getattr(self.eps, "frame_0x3D0", ""))
            frames.append(getattr(self.eps, "frame_0x3D2", ""))

        for frame in frames:
            if frame:
                self.send_frame_string(frame)

    # ----------------------------------------------------------
    def _all_modules(self):
        """Az összes modul listája DTC műveletekhez."""
        mods = [self.dme, self.dsc, self.egs]
        if self.eps is not None:
            mods.append(self.eps)
        return mods

    def _collect_active_codes(self) -> list:
        """Minden modulból összegyűjti az aktív DTC kódokat (max 4 db küldünk)."""
        codes = []
        for mod in self._all_modules():
            if hasattr(mod, "get_active_codes"):
                codes.extend(mod.get_active_codes())
        return codes

    def _collect_stored_codes(self) -> list:
        """Minden modulból összegyűjti a tárolt DTC kódokat (max 4 db küldünk)."""
        codes = []
        for mod in self._all_modules():
            if hasattr(mod, "get_stored_codes"):
                codes.extend(mod.get_stored_codes())
        return codes

    def _clear_all_module_faults(self):
        """Minden modul összes DTC-jét törli."""
        for mod in self._all_modules():
            if hasattr(mod, "clear_all_faults"):
                mod.clear_all_faults()

    # ----------------------------------------------------------
    def encode_dtc_pair(self, code: str):
        code = code.strip().upper()
        if len(code) != 5:
            return [HexInt.HexInt(0x00), HexInt.HexInt(0x00)]

        family = code[0]
        d1 = int(code[1], 16)
        d2 = int(code[2], 16)
        d3 = int(code[3], 16)
        d4 = int(code[4], 16)

        family_bits = {"P": 0b00, "C": 0b01, "B": 0b10, "U": 0b11}.get(family, 0b00)
        first_byte  = (family_bits << 6) | (d1 << 4) | d2
        second_byte = (d3 << 4) | d4

        return [HexInt.HexInt(first_byte), HexInt.HexInt(second_byte)]

    def send_dtc_frame(self, can_id: int, dtc_codes: list):
        """
        Egy CAN frame-be max 4 DTC kód fér (8 byte = 4 × 2 byte).
        Ha több van, több frame-et küld.
        """
        # Ha nincs kód, küldünk egy üres frame-et
        if not dtc_codes:
            data = [HexInt.HexInt(0x00)] * 8
            frame = self.can.Can_Controller(can_id, data)
            self.send_frame_string(frame)
            return

        # Feldolgozás 4-es blokkokban
        for chunk_start in range(0, len(dtc_codes), 4):
            chunk = dtc_codes[chunk_start:chunk_start + 4]
            data = []
            for code in chunk:
                data.extend(self.encode_dtc_pair(code))
            while len(data) < 8:
                data.append(HexInt.HexInt(0x00))
            frame = self.can.Can_Controller(can_id, data[:8])
            self.send_frame_string(frame)

    # ----------------------------------------------------------
    def handle_command(self, cmd: str):
        cmd = cmd.strip().upper()

        if cmd == "LIVE_START":
            self.live_stream_enabled = True
            self.send_text("OK LIVE_START")
            return

        if cmd == "LIVE_STOP":
            self.live_stream_enabled = False
            self.send_text("OK LIVE_STOP")
            return

        if cmd == "READ_LIVE":
            self.send_live_frames()
            self.send_text("OK READ_LIVE")
            return

        if cmd == "READ_DTC_ACTIVE":
            # Minden modulból összegyűjt, elküldi 0x700-on
            codes = self._collect_active_codes()
            self.send_dtc_frame(0x700, codes)
            self.send_text("OK READ_DTC_ACTIVE")
            return

        if cmd == "READ_DTC_STORED":
            # Minden modulból összegyűjt, elküldi 0x701-en
            codes = self._collect_stored_codes()
            self.send_dtc_frame(0x701, codes)
            self.send_text("OK READ_DTC_STORED")
            return

        if cmd == "CLEAR_DTC":
            # MINDEN modul DTC-jét törli
            self._clear_all_module_faults()
            self.send_text("OK CLEAR_DTC")
            return

        self.send_text("UNKNOWN_COMMAND")

    # ----------------------------------------------------------
    def run(self):
        self.open()
        self.running = True
        rx_buffer = b""

        while self.running:
            try:
                chunk = self.ser.read(256)
                if chunk:
                    rx_buffer += chunk

                    while b"\n" in rx_buffer or b"\r" in rx_buffer:
                        line, rx_buffer = self._split_line(rx_buffer)
                        if line is None:
                            break
                        cmd = line.decode("ascii", errors="ignore").strip()
                        if cmd:
                            self.handle_command(cmd)

                now = time.time()
                if self.live_stream_enabled and (now - self.last_live_send >= self.live_period):
                    self.send_live_frames()
                    self.last_live_send = now

                time.sleep(0.002)

            except Exception as e:
                try: self.send_text(f"ERROR {e}")
                except Exception: pass
                time.sleep(0.05)

    @staticmethod
    def _split_line(data: bytes):
        for sep in (b"\r\n", b"\n", b"\r"):
            idx = data.find(sep)
            if idx != -1:
                return data[:idx], data[idx + len(sep):]
        return None, data