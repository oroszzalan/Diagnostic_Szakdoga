def build_overview_tab(app):
    frm = app.tab_overview
    app._add_field(frm, "Sebesség [km/h]", "ov_vehicle_speed_kmh", 0)
    app._add_field(frm, "RPM", "ov_rpm", 1)
    app._add_field(frm, "Fokozat", "ov_gear_text", 2)
    app._add_field(frm, "Throttle [%]", "ov_throttle_pct", 3)
    app._add_field(frm, "Nyomaték [Nm]", "ov_torque_nm", 4)
    app._add_field(frm, "Teljesítmény [hp]", "ov_horsepower_hp", 5)
    app._add_field(frm, "Hűtővíz [°C]", "ov_coolant_temp_c", 6)
    app._add_field(frm, "Olajhő [°C]", "ov_oil_temp_c", 7)
    app._add_bool(frm, "ABS", "ov_abs_active", 8)
    app._add_bool(frm, "TC", "ov_tc_active", 9)
    app._add_bool(frm, "DSC", "ov_dsc_active", 10)
