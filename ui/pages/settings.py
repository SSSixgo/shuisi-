import customtkinter as ctk
import os, json
from core.config import *
from ui.dialogs.auth_config import AuthConfigWindow
from ui.dialogs.ai_config import AIConfigWindow
import sys
from utils.win32_effects import apply_win11_effects
from tkinter import ttk

class SettingsPage(ctk.CTkFrame):
    def __init__(self, master, app):	
        super().__init__(master, fg_color="transparent"); self.app = app
        card = ctk.CTkFrame(self, fg_color=COLOR_CARD, corner_radius=16, border_width=1, border_color=COLOR_BORDER); card.pack(fill="both", expand=True)
        inner = ctk.CTkFrame(card, fg_color="transparent"); inner.pack(padx=40, pady=40, fill="x")
        ctk.CTkLabel(inner, text="系统设置", font=ctk.CTkFont(family=APP_FONT, size=22, weight="bold"), text_color=COLOR_TEXT_MAIN).pack(anchor="w")
        ctk.CTkLabel(inner, text="配置 AI 接口密钥、修改系统管理员凭证。", font=ctk.CTkFont(family=APP_FONT, size=14), text_color=COLOR_TEXT_SUB).pack(anchor="w", pady=(8, 30))
        btn_row = ctk.CTkFrame(inner, fg_color="transparent"); btn_row.pack(anchor="w")
        self.btn_ai_config = ctk.CTkButton(btn_row, text="配置 AI 接口", width=170, height=46, corner_radius=8, font=ctk.CTkFont(family=APP_FONT, size=15), fg_color=COLOR_INPUT_BG, text_color=COLOR_TEXT_MAIN, hover_color=COLOR_NAV_HOVER, border_width=1, border_color=COLOR_BORDER, command=self.open_ai_config); self.btn_ai_config.pack(side="left", padx=(0, 15))
        self.btn_auth_config = ctk.CTkButton(btn_row, text="修改登录密码", width=170, height=46, corner_radius=8, font=ctk.CTkFont(family=APP_FONT, size=15), fg_color=COLOR_INPUT_BG, text_color=COLOR_TEXT_MAIN, hover_color=COLOR_NAV_HOVER, border_width=1, border_color=COLOR_BORDER, command=self.open_auth_config); self.btn_auth_config.pack(side="left")
        theme_frame = ctk.CTkFrame(inner, fg_color="transparent"); theme_frame.pack(anchor="w", pady=(40, 0))
        ctk.CTkLabel(theme_frame, text="界面主题：", font=ctk.CTkFont(family=APP_FONT, size=15), text_color=COLOR_TEXT_MAIN).pack(side="left", padx=(0, 15))
        self.theme_switch = ctk.CTkButton(theme_frame, text=f"当前: {ctk.get_appearance_mode()}", width=120, height=40, corner_radius=8, font=ctk.CTkFont(family=APP_FONT, size=14), fg_color=COLOR_BRAND_LIGHT, text_color=COLOR_BRAND, hover_color=("#D6E9F8", "#1C4058"), command=self._toggle_theme); self.theme_switch.pack(side="left")
    
    def _toggle_theme(self):
        current = ctk.get_appearance_mode()
        new_mode = "Dark" if current == "Light" else "Light"
        ctk.set_appearance_mode(new_mode)
        try: self.theme_switch.configure(text=f"当前: {new_mode}")
        except Exception: pass
   # ★ 新增：将选择保存到本地配置
        try:
            os.makedirs(os.path.dirname(self.app.theme_config_path), exist_ok=True)
            with open(self.app.theme_config_path, "w", encoding="utf-8") as f:
                json.dump({"appearance_mode": new_mode}, f)
        except Exception: 
            pass
        self.app._on_theme_changed() # 通知全局刷新
            
    def open_auth_config(self): AuthConfigWindow(self, self.app)
    def open_ai_config(self): AIConfigWindow(self, self.app)