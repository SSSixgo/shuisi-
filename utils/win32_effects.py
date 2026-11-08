import sys
try:
    from ctypes import windll, byref, c_int
    import ctypes
    import ctypes.wintypes
    windll.shcore.SetProcessDpiAwareness(1)
    windll.user32.SetProcessDPIAware()
except Exception: pass
import customtkinter as ctk

def apply_win11_effects(window):
    if sys.platform != "win32": return
    try:
        hwnd = windll.user32.GetParent(window.winfo_id())
        pref = c_int(2)
        windll.dwmapi.DwmSetWindowAttribute(hwnd, 33, byref(pref), ctypes.sizeof(pref))
        dark_mode = c_int(1 if ctk.get_appearance_mode() == "Dark" else 0)
        windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, byref(dark_mode), ctypes.sizeof(dark_mode))
    except Exception: pass

def set_taskbar_icon(window):
    if sys.platform != "win32": return
    try:
        hwnd = windll.user32.GetParent(window.winfo_id())
        style = windll.user32.GetWindowLongW(hwnd, -20)
        style = style & ~0x00000080 | 0x00040000
        windll.user32.SetWindowLongW(hwnd, -20, style)
    except Exception: pass