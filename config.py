# config.py

from pathlib import Path
import tkinter as tk
import tkinter.ttk as ttk

# Folder i plik zapisu
APP_DIR = Path.home() / "MajaPlanner"
APP_DIR.mkdir(parents=True, exist_ok=True)
PLIK = str(APP_DIR / "todo_plan.json")

# Motyw (jasne fiolety + ciemne elementy)
THEMES = {
    "Fioletowy": {
        "BG": "#EFE6FF",
        "RIBBON": "#7D4CFF",
        "RIBBON_DARK": "#5F2BFF",
        "CARD": "#D9C8FF",
        "CARD_2": "#CDB9FF",
        "ACCENT": "#9E66FF",
        "ACCENT_HOVER": "#894DFF",
        "TEXT": "#2C2047",
        "MUTED": "#5B4A7C",
        "BORDER": "#B59CFF",
        "ENTRY_BG": "white",
    },
}
PALETA = THEMES["Fioletowy"]

# Kategorie (zgodnie z Twoją listą)
CATEGORIES = [
    "Szkoła",
    "Prywatne",
    "Z przyjaciółmi",
    "Zajęcia poza lekcyjne",
    "Dom",
    "Hobby",
    "Sport",
    "Inne",
]

CATEGORY_COLORS = {
    "Szkoła": "#6C5CE7",
    "Prywatne": "#00B894",
    "Z przyjaciółmi": "#0984E3",
    "Zajęcia poza lekcyjne": "#E84393",
    "Dom": "#E17055",
    "Hobby": "#FD79A8",
    "Sport": "#00CEC9",
    "Inne": "#636E72",
}

def category_color(name: str) -> str:
    return CATEGORY_COLORS.get(name, CATEGORY_COLORS["Inne"])

def style_button(btn, c, primary=True, fsize=10):
    if primary:
        bg, abg, fg = c["ACCENT"], c["ACCENT_HOVER"], "white"
    else:
        bg, abg, fg = c["CARD"], c["CARD_2"], c["TEXT"]
    btn.configure(
        bg=bg, fg=fg, activebackground=abg, activeforeground=fg,
        relief="flat", bd=0, padx=14, pady=8, cursor="hand2",
        font=("Segoe UI", fsize, "bold")
    )
    btn.bind("<Enter>", lambda _e: btn.configure(bg=abg))
    btn.bind("<Leave>", lambda _e: btn.configure(bg=bg))

def sizes(zoomed: bool):
    if zoomed:
        return dict(title=20, subtitle=12, button=12, entry=13, task=14, wrap=520)
    else:
        return dict(title=18, subtitle=10, button=10, entry=12, task=12, wrap=420)
