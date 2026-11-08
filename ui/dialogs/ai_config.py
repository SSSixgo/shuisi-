import customtkinter as ctk
from tkinter import messagebox
import json
from core.config import *
from utils.helpers import bind_focus_effects
from utils.win32_effects import apply_win11_effects

class AIConfigWindow(ctk.CTkToplevel):
    def __init__(self, master, app):
        super().__init__(master); self.app = app
        self.title("AI 接口配置"); self.geometry("540x620"); self.configure(fg_color=COLOR_BG); self.transient(master); self.grab_set(); apply_win11_effects(self)
        ctk.CTkLabel(self, text="配置 AI 接口 (支持双模型)", font=ctk.CTkFont(family=APP_FONT, size=20, weight="bold"), text_color=COLOR_TEXT_MAIN).pack(pady=(25, 8))
        ctk.CTkLabel(self, text="推荐使用 通义千问 DashScope", font=ctk.CTkFont(family=APP_FONT, size=13), text_color=COLOR_SEARCH).pack(pady=(0, 4))
        ctk.CTkLabel(self, text="国内推荐地址：\nhttps://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions", font=ctk.CTkFont(family=APP_FONT, size=12), text_color=COLOR_TEXT_SUB, justify="left").pack(pady=(0, 15))
        frame = ctk.CTkFrame(self, fg_color="transparent"); frame.pack(padx=40, fill="x")
        def labeled_entry(parent, label_text, default="", show=None):
            ctk.CTkLabel(parent, text=label_text, font=ctk.CTkFont(family=APP_FONT, size=14), text_color=COLOR_TEXT_MAIN).pack(anchor="w", pady=(5, 2))
            e = ctk.CTkEntry(parent, font=ctk.CTkFont(family=APP_FONT, size=13), height=38, fg_color=COLOR_INPUT_BG, border_color=COLOR_BORDER, **({"show": show} if show else {})); e.insert(0, default); e.pack(fill="x", pady=(0, 12)); bind_focus_effects(e)
            return e
        entry_url = labeled_entry(frame, "API 接口地址 (URL):", self.app.ai_config.get("api_url", DEFAULT_AI_URL_CN))
        entry_key = labeled_entry(frame, "API 密钥 (Key):", self.app.ai_config.get("api_key", ""), show="*")
        entry_text = labeled_entry(frame, "文本模型 (电子版):", self.app.ai_config.get("text_model", DEFAULT_TEXT_MODEL))
        entry_vl = labeled_entry(frame, "视觉模型 (扫描件):", self.app.ai_config.get("vl_model", DEFAULT_VL_MODEL))
        def save():
            cfg = {"api_url": entry_url.get().strip(), "api_key": entry_key.get().strip(), "text_model": entry_text.get().strip(), "vl_model": entry_vl.get().strip()}
            if not all(cfg.values()): messagebox.showwarning("提示", "请填写完整所有信息！", parent=self); return
            self.app.ai_config = cfg
            try:
                with open(self.app.ai_config_path, "w", encoding="utf-8") as f: json.dump(cfg, f, ensure_ascii=False, indent=4)
                messagebox.showinfo("成功", "AI 接口配置已保存！", parent=self); self.destroy()
            except Exception as e: messagebox.showerror("失败", str(e), parent=self)
        ctk.CTkButton(self, text="保存配置", font=ctk.CTkFont(family=APP_FONT, weight="bold"), fg_color=COLOR_BRAND, height=42, corner_radius=8, command=save).pack(fill="x", padx=40, pady=(10, 0))