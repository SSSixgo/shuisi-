import customtkinter as ctk
from tkinter import messagebox
import json, os
from core.config import *
from core.security import hash_pwd, _protect_secret
from utils.helpers import bind_focus_effects
from utils.win32_effects import apply_win11_effects

class AuthConfigWindow(ctk.CTkToplevel):
    def __init__(self, master, app):
        super().__init__(master); self.app = app
        self.title("修改账号密码"); self.geometry("400x360"); self.configure(fg_color=COLOR_BG); self.transient(master); self.grab_set(); apply_win11_effects(self)
        ctk.CTkLabel(self, text="修改登录凭证", font=ctk.CTkFont(family=APP_FONT, size=20, weight="bold"), text_color=COLOR_TEXT_MAIN).pack(pady=(25, 20))
        frame = ctk.CTkFrame(self, fg_color="transparent"); frame.pack(padx=40, fill="x")
        ctk.CTkLabel(frame, text="新账号:", font=ctk.CTkFont(family=APP_FONT), text_color=COLOR_TEXT_MAIN).pack(anchor="w", pady=(5, 2))
        entry_user = ctk.CTkEntry(frame, height=38, corner_radius=8, font=ctk.CTkFont(family=APP_FONT), fg_color=COLOR_INPUT_BG, border_color=COLOR_BORDER); entry_user.pack(fill="x", pady=(0, 12)); bind_focus_effects(entry_user)
        ctk.CTkLabel(frame, text="新密码:", font=ctk.CTkFont(family=APP_FONT), text_color=COLOR_TEXT_MAIN).pack(anchor="w", pady=(5, 2))
        entry_pwd = ctk.CTkEntry(frame, height=38, corner_radius=8, show="*", font=ctk.CTkFont(family=APP_FONT), fg_color=COLOR_INPUT_BG, border_color=COLOR_BORDER); entry_pwd.pack(fill="x", pady=(0, 20)); bind_focus_effects(entry_pwd)
        def save_auth():
            u, p = entry_user.get().strip(), entry_pwd.get().strip()
            if not u or not p: messagebox.showwarning("提示", "账号和密码不能为空！", parent=self); return
            try:
                with open(self.app.auth_path, "r", encoding="utf-8") as f: auth_data = json.load(f)
                auth_data["username"] = u; auth_data["password"] = hash_pwd(p)
                if auth_data.get("remember_pwd"): auth_data["saved_user"] = u; auth_data["saved_pwd"] = _protect_secret(p)
                with open(self.app.auth_path + ".tmp", "w", encoding="utf-8") as f: json.dump(auth_data, f, ensure_ascii=False, indent=4)
                os.replace(self.app.auth_path + ".tmp", self.app.auth_path); messagebox.showinfo("成功", "账号密码已更新，下次启动生效！", parent=self); self.destroy()
            except Exception as e: messagebox.showerror("失败", str(e), parent=self)
        ctk.CTkButton(self, text="保存修改", font=ctk.CTkFont(family=APP_FONT, weight="bold"), fg_color=COLOR_BRAND, height=42, corner_radius=8, command=save_auth).pack(fill="x", padx=40)