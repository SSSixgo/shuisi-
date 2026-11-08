import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox
import threading, traceback, sys, json, os
import pandas as pd
from core.config import *
from utils.logger import _log_crash
from utils.win32_effects import apply_win11_effects, set_taskbar_icon
from ui.login_window import LoginWindow
from ui.pages.dashboard import DashboardPage
from ui.pages.search import SearchPage
from ui.pages.batch import BatchPage
from ui.pages.pdf import PDFPage
from ui.pages.database import DatabasePage
from ui.pages.analysis import AnalysisPage
from ui.pages.security import SecurityPage
from ui.pages.settings import SettingsPage

class ModernMatcherApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # ★ 1. 先定义配置路径，并读取历史主题
        self.theme_config_path = str(BASE_DIR / "life" / "theme.json")
        saved_theme = "light"
        if os.path.exists(self.theme_config_path):
            try:
                with open(self.theme_config_path, "r", encoding="utf-8") as f:
                    saved_theme = json.load(f).get("appearance_mode", "light")
            except Exception:
                pass
        ctk.set_appearance_mode(saved_theme) # 强制应用

        # ★ 2. 窗口基础设置
        self.title("水司智搜 · Smart Workspace")
        self.geometry("1366x820")
        self.minsize(1100, 700)
        self.configure(fg_color=COLOR_BG)
        
        if sys.platform == "win32": 
            apply_win11_effects(self)
            set_taskbar_icon(self)

        # ★ 3. 路径初始化（去除了重复代码）
        self.lib_path = str(BASE_DIR / "life" / LIB_FILE_NAME)
        self.backup_dir = str(BASE_DIR / "life" / "backups")
        self.ai_config_path = str(BASE_DIR / "life" / "ai_config.json")
        self.auth_path = str(BASE_DIR / "life" / "auth.json")

        # ★ 4. 状态变量
        self.df_lib = None; self._lib_mtime = None; self._lib_dates = None
        self.ai_config = self.load_ai_config()
        self.cancel_event = threading.Event(); self.db_lock = threading.RLock()
        self.current_page = ""; self.nav_buttons = {}; self.pages = {}

        try: 
            style = ttk.Style()
            style.theme_use("default")
            self._apply_treeview_style(style)
        except Exception: 
            pass

        if not os.path.exists(self.lib_path):
            messagebox.showerror("错误", "找不到核心数据库！\n请确保在程序同级目录下有【life】文件夹且包含Excel文件。")
            self.destroy()
            return
            
        os.makedirs(self.backup_dir, exist_ok=True)
        self.withdraw(); self.after(100, self._show_login)

    def _show_login(self):
        if self.winfo_exists() == 0: return
        try: LoginWindow(self, self.auth_path, self.on_login_success)
        except Exception: _log_crash(traceback.format_exc()); self.on_login_success()

    def on_login_success(self):
        global NUM_FONT
        try:
            from tkinter import font as tkfont
            for c in ("Segoe UI Variable Display", "Segoe UI Variable", "Segoe UI"):
                if c in tkfont.families(): 
                    NUM_FONT = c
                    break
        except Exception: pass
        self.deiconify(); self.setup_ui(); self.protocol("WM_DELETE_WINDOW", self._on_app_close)

    def _on_app_close(self):
        try: self.cancel_event.set()
        finally: self.destroy()

    def load_ai_config(self):
        default_cfg = {"api_url": DEFAULT_AI_URL_CN, "api_key": "", "text_model": DEFAULT_TEXT_MODEL, "vl_model": DEFAULT_VL_MODEL}
        if not os.path.exists(self.ai_config_path): return default_cfg
        try:
            with open(self.ai_config_path, "r", encoding="utf-8") as f: cfg = json.load(f)
        except Exception: return default_cfg
        for k, v in default_cfg.items(): cfg.setdefault(k, v)
        return cfg

    def load_library_data(self):
        try:
            mtime = os.path.getmtime(self.lib_path)
            with self.db_lock:
                if self.df_lib is not None and self._lib_mtime == mtime: return True
                self.df_lib = pd.read_excel(self.lib_path, dtype=object).fillna("")
                for col in self.df_lib.columns:
                    self.df_lib[col] = self.df_lib[col].astype(str).str.strip().replace(["nan", "None", "NaN"], "")
                if COL_DATE in self.df_lib.columns:
                    self._lib_dates = pd.to_datetime(self.df_lib[COL_DATE].str.replace("/", "-"), errors="coerce")
                self._lib_mtime = mtime
            return True
        except Exception as e:
            messagebox.showerror("加载失败", f"读取历史库失败：\n{e}"); self.df_lib = None; return False

    def setup_ui(self):
        self.grid_rowconfigure(0, weight=1); self.grid_columnconfigure(1, weight=1)
        self.sidebar = ctk.CTkFrame(self, fg_color=COLOR_SIDEBAR_BG, width=250, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="ns"); self.sidebar.grid_propagate(False)
        
        footer_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent", height=80); footer_frame.pack(side="bottom", fill="x", pady=20)
        ctk.CTkLabel(footer_frame, text="中正信咨询 | 提供技术支持\n©2026 雄安", font=ctk.CTkFont(family=APP_FONT, size=11), text_color=COLOR_TEXT_SUB, justify="center").pack(pady=5)
        
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent"); logo_frame.pack(fill="x", pady=(32, 28), padx=24)
        try:
            from PIL import Image
            from utils.helpers import get_resource_path
            pil_img = Image.open(get_resource_path("app1.ico"))
            ctk.CTkLabel(logo_frame, image=ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(42, 42)), text="").pack(side="left")
        except Exception: pass
        ctk.CTkLabel(logo_frame, text="水司智搜", font=ctk.CTkFont(family=APP_FONT, size=22, weight="bold"), text_color=COLOR_TEXT_MAIN).pack(side="left", padx=(12, 0))

        icon_font = "Segoe UI Symbol"
        try:
            import tkinter.font as tkfont
            for c in ("Segoe Fluent Icons", "Segoe MDL2 Assets", "Segoe UI Symbol"):
                if c in tkfont.families(): icon_font = c; break
        except: pass
        nav_items = [("工作台","\uE80F" if icon_font!="Segoe UI Symbol" else "⊞","dashboard"), ("历史价格检索","\uE721" if icon_font!="Segoe UI Symbol" else "⌕","search"), ("批量智能匹配","\uE8A9" if icon_font!="Segoe UI Symbol" else "⛁","batch"), ("AI 合同解析","\uE8A5" if icon_font!="Segoe UI Symbol" else "⌑","pdf"), ("价格数据库","\uE8B7" if icon_font!="Segoe UI Symbol" else "▤","database"), ("价格分析","\uE9D9" if icon_font!="Segoe UI Symbol" else "⌁","analysis"), ("数据备份与回滚","\uE81C" if icon_font!="Segoe UI Symbol" else "↺","security"), ("系统设置","\uE713" if icon_font!="Segoe UI Symbol" else "⚙","settings")]

        for label, icon, name in nav_items:
            item_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent", height=44); item_frame.pack(fill="x", padx=12, pady=2); item_frame.pack_propagate(False)
            btn_bg = ctk.CTkFrame(item_frame, fg_color="transparent", corner_radius=6); btn_bg.pack(fill="both", expand=True)
            indicator = ctk.CTkFrame(btn_bg, width=3, corner_radius=2, fg_color="transparent"); indicator.place(x=0, rely=0.5, anchor="w", relheight=0.55)
            content = ctk.CTkFrame(btn_bg, fg_color="transparent"); content.pack(fill="both", expand=True, padx=(16, 0)); content.grid_columnconfigure(1, weight=1)
            icon_lbl = ctk.CTkLabel(content, text=icon, font=ctk.CTkFont(family=icon_font, size=18), width=24, anchor="center"); icon_lbl.grid(row=0, column=0, pady=12)
            text_lbl = ctk.CTkLabel(content, text=label, font=ctk.CTkFont(family=APP_FONT, size=14), anchor="w"); text_lbl.grid(row=0, column=1, sticky="w", padx=(12, 0))

            def _apply_hover(e=None, p=name, bg=btn_bg, i=icon_lbl, t=text_lbl):
                if self.current_page == p: return
                bg.configure(fg_color=COLOR_NAV_HOVER); i.configure(text_color=COLOR_TEXT_MAIN); t.configure(text_color=COLOR_TEXT_MAIN)
            def _apply_idle(e=None, p=name, bg=btn_bg, i=icon_lbl, t=text_lbl):
                if self.current_page == p: return
                bg.configure(fg_color="transparent"); i.configure(text_color=COLOR_TEXT_SUB); t.configure(text_color=COLOR_TEXT_SUB)
            def on_leave(e, bg=btn_bg, apply_idle=_apply_idle):
                def _check():
                    try:
                        px, py = bg.winfo_pointerxy(); under = bg.winfo_containing(px, py); w = under
                        while w is not None:
                            if w == bg: return
                            w = w.master
                    except Exception: pass
                    apply_idle()
                self.after_idle(_check)

            for w in (btn_bg, content, icon_lbl, text_lbl):
                w.bind("<Button-1>", lambda e, p=name: self.switch_page(p)); w.bind("<Enter>", _apply_hover); w.bind("<Leave>", on_leave); w.configure(cursor="hand2")
            self.nav_buttons[name] = (btn_bg, icon_lbl, text_lbl, indicator)

        self.main_content = ctk.CTkFrame(self, fg_color=COLOR_BG, corner_radius=0); self.main_content.grid(row=0, column=1, sticky="nsew")
        header = ctk.CTkFrame(self.main_content, fg_color="transparent", height=70); header.pack(fill="x", padx=40, pady=(10, 0))
        self.page_title = ctk.CTkLabel(header, text="工作台总览", font=ctk.CTkFont(family=APP_FONT, size=26, weight="bold"), text_color=COLOR_TEXT_MAIN); self.page_title.pack(side="left", pady=15)
        self.page_container = ctk.CTkFrame(self.main_content, fg_color="transparent"); self.page_container.pack(fill="both", expand=True, padx=40, pady=(10, 40))
        
        self.page_classes = {"dashboard": DashboardPage, "search": SearchPage, "batch": BatchPage, "pdf": PDFPage, "database": DatabasePage, "analysis": AnalysisPage, "security": SecurityPage, "settings": SettingsPage}
        self.switch_page("dashboard")

    def switch_page(self, page_name):
        if page_name not in self.page_classes or page_name not in self.nav_buttons: return
        if self.current_page == page_name: return
        self.current_page = page_name
        for name, (btn_bg, icon_lbl, text_lbl, indicator) in self.nav_buttons.items():
            btn_bg.configure(fg_color="transparent"); icon_lbl.configure(text_color=COLOR_TEXT_SUB); text_lbl.configure(text_color=COLOR_TEXT_SUB); indicator.configure(fg_color="transparent")
        btn_bg, icon_lbl, text_lbl, indicator = self.nav_buttons[page_name]
        btn_bg.configure(fg_color=COLOR_BRAND_LIGHT); icon_lbl.configure(text_color=COLOR_BRAND); text_lbl.configure(text_color=COLOR_BRAND); indicator.configure(fg_color=COLOR_BRAND)
        titles = {"dashboard": "工作台总览", "search": "历史价格检索", "batch": "批量智能匹配", "pdf": "AI 视觉大模型 · 合同解析", "database": "价格数据库", "analysis": "价格分析", "security": "数据备份与回滚", "settings": "系统设置"}
        self.page_title.configure(text=titles.get(page_name, "水司智搜"))
        for w in self.page_container.winfo_children(): w.pack_forget()
        if page_name not in self.pages: self.pages[page_name] = self.page_classes[page_name](self.page_container, self)
        self.pages[page_name].pack(fill="both", expand=True)

    def _apply_treeview_style(self, style):
        idx = 1 if ctk.get_appearance_mode() == "Dark" else 0
        style.configure("Treeview", background=COLOR_CARD[idx], foreground=COLOR_TEXT_MAIN[idx], rowheight=42, fieldbackground=COLOR_CARD[idx], borderwidth=0, font=(APP_FONT, 11))
        style.map("Treeview", background=[("selected", COLOR_BRAND[idx])], foreground=[("selected", "#FFFFFF")])
        style.configure("Treeview.Heading", background=COLOR_TABLE_ODD[idx], foreground=COLOR_TEXT_MAIN[idx], relief="flat", font=(APP_FONT, 12, "bold"), padding=(0, 12))
        
        style.configure("Preview.Treeview", background=COLOR_CARD[idx], foreground=COLOR_TEXT_MAIN[idx], rowheight=36, fieldbackground=COLOR_CARD[idx], borderwidth=0, font=(APP_FONT, 11))
        style.map("Preview.Treeview", background=[("selected", COLOR_BRAND[idx])], foreground=[("selected", "#FFFFFF")])
        style.configure("Preview.Treeview.Heading", background=COLOR_INPUT_BG[idx], foreground=COLOR_TEXT_MAIN[idx], relief="flat", font=(APP_FONT, 11, "bold"), padding=(0, 8))
        
        style.configure("Backup.Treeview", background=COLOR_TABLE_ODD[idx], foreground=COLOR_TEXT_MAIN[idx], rowheight=40, fieldbackground=COLOR_TABLE_ODD[idx], borderwidth=0, font=(APP_FONT, 11))
        style.map("Backup.Treeview", background=[("selected", COLOR_BRAND[idx])], foreground=[("selected", "#FFFFFF")])
        style.configure("Backup.Treeview.Heading", background=COLOR_INPUT_BG[idx], foreground=COLOR_TEXT_MAIN[idx], relief="flat", font=(APP_FONT, 11, "bold"), padding=(0, 10))

    def _on_theme_changed(self):
        try:
            style = ttk.Style(); style.theme_use("default"); self._apply_treeview_style(style)
        except Exception: pass
        for page in self.pages.values():
            if hasattr(page, "refresh_theme"):
                try: page.refresh_theme()
                except Exception: pass