import tkinter as tk
from tkinter import ttk


def build_dtc_tab(app):
    frm = app.tab_dtc

    lists_frame = ttk.Frame(frm)
    lists_frame.pack(fill="both", expand=True)

    left = ttk.LabelFrame(lists_frame, text="Aktív DTC", padding=8)
    left.pack(side="left", fill="both", expand=True, padx=(0, 4))

    app.active_dtc_list = tk.Listbox(left, font=("Courier", 10), selectmode=tk.SINGLE, activestyle="none")
    app.active_dtc_list.pack(fill="both", expand=True)
    app.active_dtc_list.bind("<<ListboxSelect>>", app._on_dtc_select)

    right = ttk.LabelFrame(lists_frame, text="Tárolt DTC", padding=8)
    right.pack(side="left", fill="both", expand=True, padx=(4, 0))

    app.stored_dtc_list = tk.Listbox(right, font=("Courier", 10), selectmode=tk.SINGLE, activestyle="none")
    app.stored_dtc_list.pack(fill="both", expand=True)
    app.stored_dtc_list.bind("<<ListboxSelect>>", app._on_dtc_select)

    app.dtc_desc_var = tk.StringVar(value="Válassz ki egy DTC kódot a részletekért.")
    desc_frame = ttk.LabelFrame(frm, text="Leírás", padding=8)
    desc_frame.pack(fill="x", pady=(8, 0))
    ttk.Label(desc_frame, textvariable=app.dtc_desc_var, wraplength=700, justify="left").pack(anchor="w")


def on_dtc_select(app, event):
    widget = event.widget
    sel = widget.curselection()
    if not sel:
        return
    item = widget.get(sel[0])
    code = item.split()[0].strip()
    app.dtc_desc_var.set(f"{code}")
