def can_crc15(bits: str) -> int:
    CRC15_POLY = 0x4599
    crc = 0
    for bit in bits:
        if ((crc >> 14) ^ int(bit)) & 1:
            crc = ((crc << 1) ^ CRC15_POLY) & 0x7FFF
        else:
            crc = (crc << 1) & 0x7FFF
    return crc
