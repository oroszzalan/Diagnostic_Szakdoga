def build_egs_tab(app):
    frm = app.tab_egs
    fields = [
        ("Gear", "gear_text"),
        ("Turbine rpm", "turbine_rpm"),
        ("Output rpm", "output_rpm"),
        ("Trans oil temp [°C]", "trans_oil_temp_c"),
        ("Converter slip", "converter_slip"),
    ]
    for i, (label, key) in enumerate(fields):
        app._add_field(frm, label, key, i)
    n = len(fields)
    app._add_bool(frm, "Shifting", "shifting", n)
    app._add_bool(frm, "Lockup", "lockup", n + 1)
    app._add_bool(frm, "Reverse", "reverse_selected", n + 2)
    app._add_bool(frm, "Neutral", "neutral_selected", n + 3)
