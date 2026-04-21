import threading
import time

import serial as pyserial

from can.decoder import decode_frame_into_state
from can.destuff import reconstruct_frame_from_stuffed
from can.frame import parse_standard_can_frame
from config import DEBUG_RAW


class DiagReceiverThread(threading.Thread):
    def __init__(self, port, baudrate, timeout, state, log_callback=None):
        super().__init__(daemon=True)
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.state = state
        self.log_callback = log_callback
        self.running = False
        self.ser = None
        self.lock = threading.Lock()

    def log(self, msg):
        if self.log_callback:
            self.log_callback(msg)

    def send_command(self, command):
        if not self.ser:
            self.log("Nincs aktív soros kapcsolat.")
            return False
        try:
            self.ser.write((command.strip() + "\r\n").encode("ascii", errors="ignore"))
            self.log(f"TX {command.strip()}")
            return True
        except Exception as e:
            self.log(f"Küldési hiba: {e}")
            return False

    def stop(self):
        self.running = False
        if self.ser:
            try:
                self.ser.close()
            except Exception:
                pass
            self.ser = None

    @staticmethod
    def _split_line(data):
        for sep in (b"\r\n", b"\n", b"\r"):
            idx = data.find(sep)
            if idx != -1:
                return data[:idx], data[idx + len(sep):]
        return None, data

    def run(self):
        try:
            self.ser = pyserial.Serial(port=self.port, baudrate=self.baudrate, timeout=self.timeout)
        except Exception as e:
            self.log(f"Portnyitási hiba: {e}")
            return

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
                    if line is None:
                        break

                    decoded_line = line.decode("ascii", errors="ignore").strip()

                    if (
                        decoded_line.startswith("OK ")
                        or decoded_line.startswith("ERROR")
                        or decoded_line == "UNKNOWN_COMMAND"
                    ):
                        self.log(f"RX TXT {decoded_line}")
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
                            with self.lock:
                                self.state.parse_errors += 1
                            self.log(f"Parse hiba: {e}")
                    elif decoded_line:
                        self.log(f"RX TXT {decoded_line}")

                time.sleep(0.001)

            except Exception as e:
                self.log(f"Soros kommunikációs hiba: {e}")
                time.sleep(0.1)

        self.log("Kapcsolat lezárva.")
