def build_dsc_tab(app):
    frm = app.tab_dsc
    fields = [
        ("Vehicle speed [km/h]", "vehicle_speed_kmh"),
        ("Wheel FL [km/h]", "wheel_fl_kmh"),
        ("Wheel FR [km/h]", "wheel_fr_kmh"),
        ("Wheel RL [km/h]", "wheel_rl_kmh"),
        ("Wheel RR [km/h]", "wheel_rr_kmh"),
        ("Brake pos [%]", "brake_position_pct"),
        ("Brake pressure", "brake_pressure_bar"),
        ("Yaw rate [deg/s]", "yaw_rate_dps"),
        ("Lateral accel", "lateral_accel"),
        ("Longitudinal accel", "longitudinal_accel"),
        ("Stabilization status", "stabilization_status"),
    ]
    for i, (label, key) in enumerate(fields):
        app._add_field(frm, label, key, i)
    n = len(fields)
    app._add_bool(frm, "ABS active", "abs_active", n)
    app._add_bool(frm, "TC active", "tc_active", n + 1)
    app._add_bool(frm, "DSC active", "dsc_active", n + 2)
