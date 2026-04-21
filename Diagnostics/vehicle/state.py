from dataclasses import dataclass, field


@dataclass
class VehicleState:
    rpm: float = 0.0
    throttle_pct: float = 0.0
    maf: float = 0.0
    coolant_temp_c: float = 0.0
    intake_temp_c: float = 0.0
    oil_temp_c: float = 0.0
    battery_voltage_v: float = 0.0
    oil_pressure_bar: float = 0.0
    knock_sensor: float = 0.0
    o2_sensor_v: float = 0.0
    torque_nm: float = 0.0
    ref_torque_nm: float = 750.0
    horsepower_hp: float = 0.0

    vehicle_speed_kmh: float = 0.0
    wheel_fl_kmh: float = 0.0
    wheel_fr_kmh: float = 0.0
    wheel_rl_kmh: float = 0.0
    wheel_rr_kmh: float = 0.0
    brake_position_pct: float = 0.0
    brake_pressure_bar: float = 0.0
    yaw_rate_dps: float = 0.0
    lateral_accel: float = 0.0
    longitudinal_accel: float = 0.0
    abs_active: bool = False
    tc_active: bool = False
    dsc_active: bool = False
    stabilization_status: int = 0

    steering_angle_deg: float = 0.0
    steering_rate_dps: float = 0.0
    steering_torque_driver_nm: float = 0.0
    steering_assist_nm: float = 0.0
    eps_motor_current_a: float = 0.0
    assist_factor: float = 0.0

    gear_selector: int = 0
    turbine_rpm: float = 0.0
    output_rpm: float = 0.0
    trans_oil_temp_c: float = 0.0
    converter_slip: float = 0.0
    shifting: bool = False
    lockup: bool = False
    reverse_selected: bool = False
    neutral_selected: bool = True

    active_dtcs: list = field(default_factory=list)
    stored_dtcs: list = field(default_factory=list)

    frame_counter: int = 0
    crc_errors: int = 0
    parse_errors: int = 0
    last_id: int = 0
    last_update: float = 0.0
