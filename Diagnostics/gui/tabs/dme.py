def build_dme_tab(app):
    frm = app.tab_dme
    for i, (label, key) in enumerate([
        ("RPM", "rpm"),
        ("Throttle [%]", "throttle_pct"),
        ("MAF", "maf"),
        ("Coolant temp [°C]", "coolant_temp_c"),
        ("Intake temp [°C]", "intake_temp_c"),
        ("Oil temp [°C]", "oil_temp_c"),
        ("Battery [V]", "battery_voltage_v"),
        ("Oil pressure [bar]", "oil_pressure_bar"),
        ("O2 sensor [V]", "o2_sensor_v"),
        ("Knock sensor", "knock_sensor"),
        ("Torque [Nm]", "torque_nm"),
        ("Horsepower [hp]", "horsepower_hp"),
    ]):
        app._add_field(frm, label, key, i)
