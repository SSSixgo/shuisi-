import customtkinter as ctk
from tkinter import messagebox
import json, os, sys
from core.config import *
from core.security import hash_pwd, verify_pwd, _protect_secret, _unprotect_secret
from utils.win32_effects import apply_win11_effects, set_taskbar_icon
from utils.helpers import bind_focus_effects, get_resource_path
from PIL import Image

class LoginWindow(ctk.CTkToplevel):
    def __init__(self, master, auth_path, on_success):
        super().__init__(master)
        self.auth_path = auth_path; self.on_success = on_success; self._closed = False
        self.title("登录验证"); self.geometry("420x540"); self.configure(fg_color=COLOR_BG); self.resizable(False, False)
        if sys.platform == "win32": apply_win11_effects(self); set_taskbar_icon(self)
        self.geometry(f"+{(self.winfo_screenwidth()-420)//2}+{(self.winfo_screenheight()-540)//2}")
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.report_callback_exception = lambda et, ev, tb: __import__('utils.logger', fromlist=['global_exception_handler']).global_exception_handler(et, ev, tb)

        try:
            pil_img = Image.open(get_resource_path("app1.ico"))
            ctk.CTkLabel(self, image=ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(96, 96)), text="").pack(pady=(50, 30))
        except Exception: pass

        card = ctk.CTkFrame(self, fg_color=COLOR_CARD, corner_radius=16, border_width=1, border_color=COLOR_BORDER); card.pack(fill="x", padx=50)
        self.entry_user = ctk.CTkEntry(card, placeholder_text="请输入账号", height=46, corner_radius=8, font=ctk.CTkFont(family=APP_FONT, size=14), border_width=1, border_color=COLOR_BORDER, fg_color=COLOR_INPUT_BG)
        self.entry_user.pack(pady=(30, 15), padx=25, fill="x"); bind_focus_effects(self.entry_user)
        self.entry_pwd = ctk.CTkEntry(card, placeholder_text="请输入密码", show="*", height=46, corner_radius=8, font=ctk.CTkFont(family=APP_FONT, size=14), border_width=1, border_color=COLOR_BORDER, fg_color=COLOR_INPUT_BG)
        self.entry_pwd.pack(pady=(0, 15), padx=25, fill="x"); self.entry_pwd.bind("<Return>", lambda e: self.check_login()); bind_focus_effects(self.entry_pwd)
        self.remember_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(card, text="记住密码", variable=self.remember_var, font=ctk.CTkFont(family=APP_FONT, size=13), text_color=COLOR_TEXT_SUB, fg_color=COLOR_BRAND, hover_color=COLOR_BRAND_LIGHT, border_color=COLOR_BORDER, corner_radius=4).pack(pady=(0, 30), padx=25, anchor="w")
        ctk.CTkButton(self, text="登 录", height=48, corner_radius=8, font=ctk.CTkFont(family=APP_FONT, size=16, weight="bold"), fg_color=COLOR_BRAND, hover_color=("#005A9E", "#339BDB"), command=self.check_login).pack(fill="x", padx=50, pady=(25, 40))
        self.load_auth()

    def load_auth(self):
        if os.path.exists(self.auth_path):
            try:
                with open(self.auth_path, "r", encoding="utf-8") as f: self.auth_data = json.load(f)
            except Exception: self.auth_data = {"username": "admin", "password": hash_pwd("123456")}
        else:
            self.auth_data = {"username": "admin", "password": hash_pwd("123456")}; self.save_auth()
        if self.auth_data.get("remember_pwd") and self.auth_data.get("saved_user") and self.auth_data.get("saved_pwd"):
            try: saved_pwd = _unprotect_secret(self.auth_data["saved_pwd"])
            except Exception: saved_pwd = self.auth_data["saved_pwd"]
            self.entry_user.insert(0, self.auth_data["saved_user"]); self.entry_pwd.insert(0, saved_pwd); self.remember_var.set(True)
        else: self.entry_user.insert(0, self.auth_data.get("username", "admin"))

    def save_auth(self):
        os.makedirs(os.path.dirname(self.auth_path), exist_ok=True)
        with open(self.auth_path + ".tmp", "w", encoding="utf-8") as f: json.dump(self.auth_data, f, ensure_ascii=False, indent=4)
        os.replace(self.auth_path + ".tmp", self.auth_path)

    def check_login(self):
        user, pwd = self.entry_user.get().strip(), self.entry_pwd.get().strip()
        if user == self.auth_data.get("username") and verify_pwd(pwd, self.auth_data.get("password", "")):
            self.auth_data["remember_pwd"] = self.remember_var.get()
            if self.remember_var.get(): self.auth_data["saved_user"] = user; self.auth_data["saved_pwd"] = _protect_secret(pwd)
            else: self.auth_data.pop("saved_user", None); self.auth_data.pop("saved_pwd", None)
            self.save_auth(); self._closed = True; self.destroy()
            try: self.on_success()
            except Exception: pass
        else: messagebox.showerror("错误", "账号或密码不正确！", parent=self); self.entry_pwd.delete(0, "end")

    def on_close(self):
        self._closed = True
        try: self.destroy()
        finally:
            try: self.master.destroy()
            except Exception: pass