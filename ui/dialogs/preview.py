import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
from core.config import *
from utils.win32_effects import apply_win11_effects

class PreviewWindow(ctk.CTkToplevel):
    def __init__(self, master, data_list, columns, confirm_callback):
        super().__init__(master)
        self.title("AI 提取数据核对"); self.geometry("1150x680"); self.configure(fg_color=COLOR_BG)
        self.confirm_callback = confirm_callback; self.columns = list(columns); self.transient(master); self.grab_set()
        apply_win11_effects(self)
        header_frame = ctk.CTkFrame(self, fg_color="transparent"); header_frame.pack(fill="x", padx=30, pady=(25, 10))
        ctk.CTkLabel(header_frame, text="核对 AI 提取到的数据", font=ctk.CTkFont(family=APP_FONT, size=22, weight="bold"), text_color=COLOR_TEXT_MAIN).pack(anchor="w")
        ctk.CTkLabel(header_frame, text="提示：双击任意单元格可直接修改内容；“选用”列可勾选/取消勾选。", font=ctk.CTkFont(family=APP_FONT, size=13), text_color=COLOR_TEXT_SUB).pack(anchor="w", pady=(5, 0))
        toolbar = ctk.CTkFrame(self, fg_color="transparent"); toolbar.pack(fill="x", padx=30, pady=(15, 5))
        ctk.CTkButton(toolbar, text="全选", width=60, height=32, corner_radius=6, fg_color=COLOR_BRAND_LIGHT, text_color=COLOR_BRAND, hover_color=("#D6E9F8", "#1C4058"), command=self.select_all).pack(side="left", padx=(0, 10))
        ctk.CTkButton(toolbar, text="取消全选", width=80, height=32, corner_radius=6, fg_color=COLOR_BRAND_LIGHT, text_color=COLOR_BRAND, hover_color=("#D6E9F8", "#1C4058"), command=self.deselect_all).pack(side="left")
        mode_idx = 1 if ctk.get_appearance_mode() == "Dark" else 0
        table_frame = tk.Frame(self, bg=COLOR_CARD[mode_idx], highlightbackground=COLOR_BORDER[mode_idx], highlightthickness=1); table_frame.pack(fill="both", expand=True, padx=30, pady=10)
        self.display_cols = ["_selected"] + self.columns
        self.tree = ttk.Treeview(table_frame, columns=self.display_cols, show="headings", style="Preview.Treeview")
        self.tree.heading("_selected", text="选用"); self.tree.column("_selected", width=50, anchor="center")
        for col in self.columns: self.tree.heading(col, text=col); self.tree.column(col, width=120, anchor="w")
        v_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview); h_scroll = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set); self.tree.grid(row=0, column=0, sticky="nsew"); v_scroll.grid(row=0, column=1, sticky="ns"); h_scroll.grid(row=1, column=0, sticky="ew")
        table_frame.grid_rowconfigure(0, weight=1); table_frame.grid_columnconfigure(0, weight=1)
        self.data_list = data_list
        for item in self.data_list: item["_selected"] = True
        self.refresh_tree(); self.tree.bind("<ButtonRelease-1>", self.on_single_click); self.tree.bind("<Double-1>", self.on_double_click)
        btn_frame = ctk.CTkFrame(self, fg_color="transparent"); btn_frame.pack(fill="x", padx=30, pady=(10, 25))
        ctk.CTkButton(btn_frame, text="删除选中行", fg_color="transparent", text_color=COLOR_DANGER, border_width=1, border_color=COLOR_DANGER, hover_color=("#FEE2E2", "#3F1D1D"), width=100, height=38, corner_radius=8, command=self.delete_selected).pack(side="left")
        ctk.CTkButton(btn_frame, text="确认勾选数据，一键入库", fg_color=COLOR_BRAND, hover_color=("#005A9E", "#339BDB"), width=200, height=38, corner_radius=8, font=ctk.CTkFont(family=APP_FONT, weight="bold"), command=self.confirm_import).pack(side="right")
        ctk.CTkButton(btn_frame, text="取消导入", fg_color=COLOR_INPUT_BG, text_color=COLOR_TEXT_MAIN, hover_color=COLOR_NAV_HOVER, width=100, height=38, corner_radius=8, command=self.destroy).pack(side="right", padx=(0, 15))
    def refresh_tree(self):
        for item in self.tree.get_children(): self.tree.delete(item)
        for i, row in enumerate(self.data_list):
            sel_val = "☑" if row.get("_selected", True) else "☐"; values = [sel_val] + [str(row.get(col, "")) for col in self.columns]
            self.tree.insert("", "end", iid=str(i), values=values)
    def select_all(self):
        for i, row in enumerate(self.data_list): row["_selected"] = True; self.tree.set(str(i), "#1", "☑")
    def deselect_all(self):
        for i, row in enumerate(self.data_list): row["_selected"] = False; self.tree.set(str(i), "#1", "☐")
    def on_single_click(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell": return
        col = self.tree.identify_column(event.x)
        if col == "#1":
            item = self.tree.identify_row(event.y)
            if item:
                idx = int(item); self.data_list[idx]["_selected"] = not self.data_list[idx]["_selected"]; self.tree.set(item, "#1", "☑" if self.data_list[idx]["_selected"] else "☐")
    def on_double_click(self, event):
        item = self.tree.identify_row(event.y); col_id = self.tree.identify_column(event.x)
        if not item or not col_id: return
        try: col_idx = int(col_id.replace("#", "")) - 1
        except ValueError: return
        if col_idx == 0: return
        try: key = self.columns[col_idx - 1]
        except IndexError: return
        bbox = self.tree.bbox(item, col_id)
        if not bbox: return
        x, y, width, height = bbox; mode_idx = 1 if ctk.get_appearance_mode() == "Dark" else 0
        entry = tk.Entry(self.tree, font=(APP_FONT, 11), bg=COLOR_CARD[mode_idx], fg=COLOR_TEXT_MAIN[mode_idx], insertbackground=COLOR_TEXT_MAIN[mode_idx])
        entry.place(x=x, y=y, width=width, height=height); entry.insert(0, self.tree.set(item, col_id)); entry.focus(); entry.select_range(0, "end"); saved = [False]
        def save_edit(_event=None):
            if saved[0]: return
            saved[0] = True; new_val = entry.get()
            try:
                idx = int(item)
                if 0 <= idx < len(self.data_list): self.data_list[idx][key] = new_val; self.tree.set(item, col_id, new_val)
            finally: entry.destroy()
        entry.bind("<Return>", save_edit); entry.bind("<FocusOut>", save_edit); entry.bind("<Escape>", lambda _e: entry.destroy())
    def delete_selected(self):
        selected = self.tree.selection()
        if not selected: return
        for idx in sorted((int(i) for i in selected), reverse=True):
            if 0 <= idx < len(self.data_list): self.data_list.pop(idx)
        self.refresh_tree()
    def confirm_import(self):
        final_data = [{k: v for k, v in row.items() if k != "_selected"} for row in self.data_list if row.get("_selected", True)]
        if not final_data: messagebox.showwarning("提示", "您没有勾选任何数据，请先勾选！", parent=self); return
        self.confirm_callback(pd.DataFrame(final_data)); self.destroy()