class CanController:

    @staticmethod
    def calculate_crc(bits):
        CRC15_POLY = 0x4599
        crc = 0

        for bit in bits:
            bit_val = int(bit)

            if ((crc >> 14) ^ bit_val) & 1:
                crc = ((crc << 1) ^ CRC15_POLY) & 0x7FFF
            else:
                crc = (crc << 1) & 0x7FFF
        return crc

    @staticmethod
    def bit_stuff(Can_Frame):
        """
        Standard CAN bit stuffing:
        Insert an opposite bit after every 5 consecutive identical bits.
        """
        if not Can_Frame:
            return ""

        stuffed_frame = Can_Frame[0]
        run = 1

        for i in range(1, len(Can_Frame)):
            b = Can_Frame[i]

            if b == Can_Frame[i - 1]:
                run += 1
            else:
                run = 1

            stuffed_frame += b

            if run == 5:
                # Insert opposite stuffed bit
                stuffed_frame += '1' if b == '0' else '0'
                run = 1  # stuffed bit begins a new run of 1

        return stuffed_frame

    def Can_Controller(self, can_id, data):

        # SOF
        sof = "0"

        # ID
        id_bits = format(can_id, '011b')

        # RTR
        rtr = "0"

        # CONTROL
        ide = "0"
        r0 = "0"
        dlc = format(len(data), '04b')
        control = ide + r0 + dlc

        # DATA
        data_bits = "".join(format(byte, '08b') for byte in data)

        # CRC
        raw_bits = sof + id_bits + rtr + control + data_bits
        crc_value = self.calculate_crc(raw_bits)
        crc_bits = format(crc_value, '015b') + "1"

        # ACK
        ack = "01"

        # EOF
        eof = "1111111"

        Frame_For_Stuffing = sof + id_bits + rtr + control + data_bits + crc_bits

        stuffed_frame = self.bit_stuff(Frame_For_Stuffing)
        stuffed_frame += ack + eof

        return stuffed_frame
