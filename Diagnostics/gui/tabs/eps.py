def build_eps_tab(app):
    frm = app.tab_eps
    for i, (label, key) in enumerate([
        ("Steering angle [deg]", "steering_angle_deg"),
        ("Steering rate [deg/s]", "steering_rate_dps"),
        ("Driver torque [Nm]", "steering_torque_driver_nm"),
        ("Assist torque [Nm]", "steering_assist_nm"),
        ("Motor current [A]", "eps_motor_current_a"),
        ("Assist factor", "assist_factor"),
    ]):
        app._add_field(frm, label, key, i)
