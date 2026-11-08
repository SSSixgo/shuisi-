import pandas as pd
import os, subprocess
import customtkinter as ctk
from core.config import COLOR_BRAND

def _safe_str(v):
    if v is None: return ""
    try:
        if isinstance(v, float) and pd.isna(v): return ""
    except Exception: pass
    s = str(v).strip()
    return "" if s.lower() in ("nan", "none", "nat") else s

def bind_focus_effects(entry_widget):
    default_color = entry_widget.cget("border_color")
    entry_widget.bind("<FocusIn>", lambda e: entry_widget.configure(border_color=COLOR_BRAND))
    entry_widget.bind("<FocusOut>", lambda e: entry_widget.configure(border_color=default_color))

def _open_folder(path):
    if sys.platform == "win32": os.startfile(path)
    elif sys.platform == "darwin": subprocess.Popen(["open", path])
    else: subprocess.Popen(["xdg-open", path])

def get_resource_path(relative_path):
    import sys
    base = getattr(sys, "_MEIPASS", None) or str(__import__('core.config', fromlist=['BASE_DIR']).BASE_DIR)
    return os.path.join(base, relative_path)