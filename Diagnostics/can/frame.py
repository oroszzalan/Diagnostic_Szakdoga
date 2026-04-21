from dataclasses import dataclass

from .crc import can_crc15


@dataclass
class CANFrame:
    sof: int
    can_id: int
    rtr: int
    ide: int
    r0: int
    dlc: int
    data: list
    crc_rx: int
    crc_calc: int
    crc_ok: bool
    ack: int
    eof: str
    raw_destuffed_bits: str = ""
    raw_stuffed_bits: str = ""


def bits_to_int(bits: str) -> int:
    return int(bits, 2) if bits else 0


def parse_standard_can_frame(destuffed_bits: str, stuffed_bits: str = "") -> CANFrame:
    idx = 0

    def take(n: int) -> str:
        nonlocal idx
        if idx + n > len(destuffed_bits):
            raise ValueError("Frame too short")
        s = destuffed_bits[idx:idx + n]
        idx += n
        return s

    sof = bits_to_int(take(1))
    can_id = bits_to_int(take(11))
    rtr = bits_to_int(take(1))
    ide = bits_to_int(take(1))
    r0 = bits_to_int(take(1))
    dlc = bits_to_int(take(4))

    if sof != 0:
        raise ValueError("Invalid SOF")
    if ide != 0:
        raise ValueError("Only standard 11-bit frame supported")
    if rtr != 0:
        raise ValueError("RTR frame not supported")
    if dlc > 8:
        raise ValueError(f"Invalid DLC: {dlc}")

    data_bits = take(dlc * 8)
    data = [bits_to_int(data_bits[i:i + 8]) for i in range(0, len(data_bits), 8)]

    crc_rx = bits_to_int(take(15))
    crc_delim = take(1)
    ack_bits = take(2)
    ack = bits_to_int(ack_bits)
    eof = take(7)

    crc_input = destuffed_bits[:1 + 11 + 1 + 1 + 1 + 4 + dlc * 8]
    crc_calc = can_crc15(crc_input)
    crc_ok = crc_calc == crc_rx

    if crc_delim != "1":
        raise ValueError(f"Invalid CRC delimiter: {crc_delim}")
    if ack_bits != "01":
        raise ValueError(f"Invalid ACK bits: {ack_bits}")
    if eof != "1111111":
        raise ValueError(f"Invalid EOF: {eof}")

    return CANFrame(
        sof=sof,
        can_id=can_id,
        rtr=rtr,
        ide=ide,
        r0=r0,
        dlc=dlc,
        data=data,
        crc_rx=crc_rx,
        crc_calc=crc_calc,
        crc_ok=crc_ok,
        ack=ack,
        eof=eof,
        raw_destuffed_bits=destuffed_bits,
        raw_stuffed_bits=stuffed_bits,
    )
