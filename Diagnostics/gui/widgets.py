import tkinter as tk
from tkinter import ttk

from DTCDatabase import display_string as dtc_display_str


def add_field(app, parent, label, key, row):
    ttk.Label(parent, text=label + ":").grid(row=row, column=0, sticky="w", padx=(0, 8), pady=3)
    var = tk.StringVar(value="-")
    ttk.Label(parent, textvariable=var).grid(row=row, column=1, sticky="w", pady=3)
    app.value_vars[key] = var


def add_bool(app, parent, label, key, row):
    ttk.Label(parent, text=label + ":").grid(row=row, column=0, sticky="w", padx=(0, 8), pady=3)
    var = tk.StringVar(value="-")
    ttk.Label(parent, textvariable=var).grid(row=row, column=1, sticky="w", pady=3)
    app.bool_vars[key] = var


def update_dtc_listbox(lb: tk.Listbox, codes: list):
    new_items = [dtc_display_str(code) for code in codes] if codes else ["-"]
    current = list(lb.get(0, tk.END))
    if current != new_items:
        lb.delete(0, tk.END)
        for item in new_items:
            lb.insert(tk.END, item)
            code = item.split()[0]
            idx = lb.size() - 1
            if code.startswith("P"):
                lb.itemconfig(idx, fg="#e06c75")
            elif code.startswith("C"):
                lb.itemconfig(idx, fg="#e5c07b")
            elif code.startswith("U"):
                lb.itemconfig(idx, fg="#56b6c2")
            elif code.startswith("B"):
                lb.itemconfig(idx, fg="#98c379")
