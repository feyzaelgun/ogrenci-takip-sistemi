import tkinter as tk
from tkinter import ttk

def setup_style(root):
    style = ttk.Style()

    root.configure(bg="#e9f3ff")  # Ice Blue arka plan

    style.theme_use("clam")

    # Genel tema renkleri
    style.configure(
        "TFrame",
        background="#e9f3ff"
    )
    style.configure(
        "TLabel",
        background="#e9f3ff",
        foreground="#1c3d5a",
        font=("Segoe UI", 11)
    )
    style.configure(
        "Header.TLabel",
        background="#d3e9ff",
        foreground="#003366",
        font=("Segoe UI", 15, "bold")
    )
    style.configure(
        "TButton",
        background="#c7e0ff",
        foreground="#003366",
        padding=6,
        font=("Segoe UI", 10, "bold")
    )
    style.map(
        "TButton",
        background=[("active", "#b2d6ff")]
    )

    # Modern giriş kutuları
    style.configure(
        "TEntry",
        padding=5,
        fieldbackground="#ffffff",
        bordercolor="#7fbaff",
        lightcolor="#7fbaff"
    )

    # Sidebar
    style.configure(
        "Sidebar.TFrame",
        background="#cfe2f7"
    )
    style.configure(
        "Sidebar.TButton",
        background="#c7d9f4",
        foreground="#003366",
        font=("Segoe UI", 12, "bold"),
        padding=10
    )
    style.map(
        "Sidebar.TButton",
        background=[("active", "#b8ceec")]
    )
