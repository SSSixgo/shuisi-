import customtkinter as ctk
import datetime
from core.config import *

class DashboardPage(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent"); self.app = app
        stats_frame = ctk.CTkFrame(self, fg_color="transparent"); stats_frame.pack(fill="x", pady=(10, 25)); stats_frame.grid_columnconfigure((0, 1), weight=1)
        self.card1 = ctk.CTkFrame(stats_frame, fg_color=COLOR_CARD, corner_radius=16, border_width=1, border_color=COLOR_BORDER); self.card1.grid(row=0, column=0, padx=(0, 12), sticky="nsew")
        ctk.CTkLabel(self.card1, text="历史价格库", font=ctk.CTkFont(family=APP_FONT, size=15, weight="bold"), text_color=COLOR_TEXT_SUB).pack(anchor="w", padx=30, pady=(30, 5))
        self.lbl_total_records = ctk.CTkLabel(self.card1, text="0", font=ctk.CTkFont(family=NUM_FONT, size=44, weight="bold"), text_color=COLOR_TEXT_MAIN); self.lbl_total_records.pack(anchor="w", padx=30)
        ctk.CTkLabel(self.card1, text="材料价格数据总量", font=ctk.CTkFont(family=APP_FONT, size=13), text_color=COLOR_TEXT_SUB).pack(anchor="w", padx=30, pady=(5, 30))
        self.card2 = ctk.CTkFrame(stats_frame, fg_color=COLOR_CARD, corner_radius=16, border_width=1, border_color=COLOR_BORDER); self.card2.grid(row=0, column=1, padx=(12, 0), sticky="nsew")
        ctk.CTkLabel(self.card2, text="本月新增", font=ctk.CTkFont(family=APP_FONT, size=15, weight="bold"), text_color=COLOR_TEXT_SUB).pack(anchor="w", padx=30, pady=(30, 5))
        self.lbl_month_new = ctk.CTkLabel(self.card2, text="0", font=ctk.CTkFont(family=NUM_FONT, size=44, weight="bold"), text_color=COLOR_TEXT_MAIN); self.lbl_month_new.pack(anchor="w", padx=30)
        ctk.CTkLabel(self.card2, text="新增入库记录", font=ctk.CTkFont(family=APP_FONT, size=13), text_color=COLOR_TEXT_SUB).pack(anchor="w", padx=30, pady=(5, 30))
        quick_card = ctk.CTkFrame(self, fg_color=COLOR_CARD, corner_radius=16, border_width=1, border_color=COLOR_BORDER); quick_card.pack(fill="x", pady=(0, 25))
        ctk.CTkLabel(quick_card, text="常用功能", font=ctk.CTkFont(family=APP_FONT, size=16, weight="bold"), text_color=COLOR_TEXT_MAIN).pack(anchor="w", padx=30, pady=(25, 20))
        btn_row = ctk.CTkFrame(quick_card, fg_color="transparent"); btn_row.pack(fill="x", padx=30, pady=(0, 25))
        def make_quick(text, page): return ctk.CTkButton(btn_row, text=text, font=ctk.CTkFont(family=APP_FONT, size=14), fg_color=COLOR_BRAND_LIGHT, text_color=COLOR_BRAND, hover_color=("#D6E9F8", "#1C4058"), corner_radius=8, height=40, command=lambda: self.app.switch_page(page))
        make_quick("单条价格快搜", "search").pack(side="left", padx=(0, 15)); make_quick("批量清单匹配", "batch").pack(side="left", padx=(0, 15)); make_quick("AI 合同解析", "pdf").pack(side="left")
        recent_card = ctk.CTkFrame(self, fg_color=COLOR_CARD, corner_radius=16, border_width=1, border_color=COLOR_BORDER); recent_card.pack(fill="both", expand=True)
        ctk.CTkLabel(recent_card, text="最近操作", font=ctk.CTkFont(family=APP_FONT, size=16, weight="bold"), text_color=COLOR_TEXT_MAIN).pack(anchor="w", padx=30, pady=(25, 15))
        ctk.CTkLabel(recent_card, text="最近导入、检索和数据维护记录将在这里展示。", font=ctk.CTkFont(family=APP_FONT, size=14), text_color=COLOR_TEXT_SUB).pack(anchor="w", padx=30)
        self.update_stats()

    def update_stats(self):
        if self.app.df_lib is None: return
        try:
            total = len(self.app.df_lib); self.lbl_total_records.configure(text=f"{total:,}")
            month_new = int(self.app.df_lib[COL_DATE].str.startswith(datetime.datetime.now().strftime("%Y-%m")).sum()) if COL_DATE in self.app.df_lib.columns else 0
            self.lbl_month_new.configure(text=f"{month_new:,}")
        except Exception: pass