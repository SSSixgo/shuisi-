import customtkinter as ctk
from core.config import *
class AnalysisPage(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        card = ctk.CTkFrame(self, fg_color=COLOR_CARD, corner_radius=16, border_width=1, border_color=COLOR_BORDER); card.pack(fill="both", expand=True)
        inner = ctk.CTkFrame(card, fg_color="transparent"); inner.place(relx=0.5, rely=0.5, anchor="center")
        ctk.CTkLabel(inner, text="价格分析模块开发中", font=ctk.CTkFont(family=APP_FONT, size=26, weight="bold"), text_color=COLOR_TEXT_MAIN).pack()
        ctk.CTkLabel(inner, text="未来将提供：材料价格趋势、供应商价格对比、价格波动预警等功能。", font=ctk.CTkFont(family=APP_FONT, size=15), text_color=COLOR_TEXT_SUB).pack(pady=(15, 0))