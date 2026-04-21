import time

from .frame import CANFrame
from vehicle.state import VehicleState


def int_from_bytes_signed_16(hi: int, lo: int) -> int:
    v = (hi << 8) | lo
    return v - 0x10000 if v & 0x8000 else v


def int_from_bytes_unsigned_16(hi: int, lo: int) -> int:
    return (hi << 8) | lo


def decode_obd_dtc_pair(b1: int, b2: int) -> str:
    family = {0b00: "P", 0b01: "C", 0b10: "B", 0b11: "U"}[(b1 >> 6) & 0b11]
    return f"{family}{(b1 >> 4) & 0b11:X}{b1 & 0x0F:X}{(b2 >> 4) & 0x0F:X}{b2 & 0x0F:X}"


def decode_frame_into_state(frame: CANFrame, state: VehicleState) -> None:
    data = frame.data
    cid = frame.can_id

    state.frame_counter += 1
    state.last_id = cid
    state.last_update = time.time()

    if not frame.crc_ok:
        state.crc_errors += 1

    if cid == 0x0A0 and len(data) == 8:
        state.rpm = ((data[0] << 8) | data[1]) / 4.0
        state.throttle_pct = data[2] * 100.0 / 255.0
        state.maf = ((data[3] << 8) | data[4]) / 100.0

    elif cid == 0x0A1 and len(data) == 8:
        state.coolant_temp_c = data[0] - 40
        state.intake_temp_c = data[1] - 40
        state.oil_temp_c = ((data[2] << 8) | data[3]) / 10.0 - 40.0

    elif cid == 0x0A2 and len(data) == 8:
        state.battery_voltage_v = ((data[0] << 8) | data[1]) / 1000.0
        state.oil_pressure_bar = data[2] / 10.0

    elif cid == 0x0A3 and len(data) == 8:
        state.o2_sensor_v = data[0] / 200.0
        state.knock_sensor = data[1] / 2.0

    elif cid == 0x0A4 and len(data) == 8:
        torque_pct = data[0] - 125.0
        state.ref_torque_nm = float((data[1] << 8) | data[2])
        state.torque_nm = (torque_pct / 100.0) * state.ref_torque_nm
        state.horsepower_hp = ((data[3] << 8) | data[4]) / 10.0

    elif cid == 0x1B2 and len(data) == 8:
        state.gear_selector = data[0] - 1
        state.turbine_rpm = (data[1] << 8) | data[2]
        state.output_rpm = (data[3] << 8) | data[4]
        st = data[5]
        state.shifting = bool(st & 1)
        state.lockup = bool(st & 2)
        state.reverse_selected = bool(st & 4)
        state.neutral_selected = bool(st & 8)

    elif cid == 0x1B4 and len(data) == 8:
        state.trans_oil_temp_c = data[0] - 40
        state.converter_slip = data[1] / 200.0

    elif cid == 0x2C1 and len(data) == 8:
        state.vehicle_speed_kmh = float((data[0] << 8) | data[1])
        state.wheel_fl_kmh = ((data[2] << 8) | data[3]) / 100.0
        state.wheel_fr_kmh = ((data[4] << 8) | data[5]) / 100.0
        st = data[6]
        state.abs_active = bool(st & 1)
        state.tc_active = bool(st & 2)
        state.dsc_active = bool(st & 4)
        state.stabilization_status = data[7]

    elif cid == 0x2C3 and len(data) == 8:
        state.brake_position_pct = data[0] * 100.0 / 255.0
        state.brake_pressure_bar = ((data[1] << 8) | data[2]) / 10.0
        state.yaw_rate_dps = int_from_bytes_signed_16(data[3], data[4]) / 100.0
        state.lateral_accel = (data[5] - 128) / 10.0
        state.longitudinal_accel = (data[6] - 128) / 10.0

    elif cid == 0x2C8 and len(data) == 8:
        state.wheel_rl_kmh = ((data[0] << 8) | data[1]) / 100.0
        state.wheel_rr_kmh = ((data[2] << 8) | data[3]) / 100.0
        state.lateral_accel = int_from_bytes_signed_16(data[4], data[5]) / 100.0
        state.longitudinal_accel = int_from_bytes_signed_16(data[6], data[7]) / 100.0

    elif cid == 0x3D0 and len(data) == 8:
        state.steering_angle_deg = (int_from_bytes_unsigned_16(data[0], data[1]) - 32768) / 10.0
        state.steering_rate_dps = (int_from_bytes_unsigned_16(data[2], data[3]) - 32768) / 100.0
        state.steering_torque_driver_nm = (int_from_bytes_unsigned_16(data[4], data[5]) - 32768) / 100.0
        state.steering_assist_nm = (int_from_bytes_unsigned_16(data[6], data[7]) - 32768) / 100.0

    elif cid == 0x3D2 and len(data) == 8:
        state.eps_motor_current_a = int_from_bytes_unsigned_16(data[0], data[1]) / 100.0
        state.assist_factor = data[2] / 255.0

    elif cid == 0x700 and len(data) == 8:
        new_codes = [
            decode_obd_dtc_pair(data[i], data[i + 1])
            for i in range(0, 8, 2)
            if data[i] or data[i + 1]
        ]
        existing = set(state.active_dtcs)
        for code in new_codes:
            if code not in existing:
                state.active_dtcs.append(code)
                existing.add(code)

    elif cid == 0x701 and len(data) == 8:
        new_codes = [
            decode_obd_dtc_pair(data[i], data[i + 1])
            for i in range(0, 8, 2)
            if data[i] or data[i + 1]
        ]
        existing = set(state.stored_dtcs)
        for code in new_codes:
            if code not in existing:
                state.stored_dtcs.append(code)
                existing.add(code)
