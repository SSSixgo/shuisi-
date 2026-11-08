import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading, pandas as pd
from rapidfuzz import fuzz
from core.config import *
from core.matcher import calculate_match_score
from utils.helpers import bind_focus_effects

class SearchPage(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent"); self.app = app; self._searching = False
        search_card = ctk.CTkFrame(self, fg_color=COLOR_CARD, corner_radius=16, border_width=1, border_color=COLOR_BORDER); search_card.pack(fill="x", pady=(0, 15), side="top")
        inner_card = ctk.CTkFrame(search_card, fg_color="transparent"); inner_card.pack(fill="x", padx=30, pady=25)
        row1 = ctk.CTkFrame(inner_card, fg_color="transparent"); row1.pack(fill="x", pady=(0, 15))
        self.entry_proj = ctk.CTkEntry(row1, placeholder_text=" 项目名称 (支持关键字)", placeholder_text_color=COLOR_PLACEHOLDER, text_color=COLOR_TEXT_MAIN, font=ctk.CTkFont(family=APP_FONT, size=15), height=46, corner_radius=10, border_width=1, border_color=COLOR_BORDER, fg_color=COLOR_INPUT_BG)
        self.entry_proj.pack(side="left", fill="x", expand=True, padx=(0, 15)); bind_focus_effects(self.entry_proj)
        self.time_filter = ctk.CTkComboBox(row1, values=["全部时间", "近半年", "近一年", "近三年"], font=ctk.CTkFont(family=APP_FONT, size=14), width=130, height=46, corner_radius=10, fg_color=COLOR_INPUT_BG, border_width=1, border_color=COLOR_BORDER, button_color=COLOR_INPUT_BG, button_hover_color=COLOR_NAV_HOVER, dropdown_fg_color=COLOR_CARD, dropdown_hover_color=COLOR_NAV_HOVER, dropdown_text_color=COLOR_TEXT_MAIN, text_color=COLOR_TEXT_MAIN, state="readonly")
        self.time_filter.pack(side="right")
        row2 = ctk.CTkFrame(inner_card, fg_color="transparent"); row2.pack(fill="x", pady=(0, 20))
        self.entry_mat = ctk.CTkEntry(row2, placeholder_text=" 物资名称", placeholder_text_color=COLOR_PLACEHOLDER, text_color=COLOR_TEXT_MAIN, font=ctk.CTkFont(family=APP_FONT, size=15), height=46, corner_radius=10, border_width=1, border_color=COLOR_BORDER, fg_color=COLOR_INPUT_BG)
        self.entry_mat.pack(side="left", fill="x", expand=True, padx=(0, 15)); bind_focus_effects(self.entry_mat)
        self.entry_spec = ctk.CTkEntry(row2, placeholder_text=" 规格特征", placeholder_text_color=COLOR_PLACEHOLDER, text_color=COLOR_TEXT_MAIN, font=ctk.CTkFont(family=APP_FONT, size=15), height=46, corner_radius=10, border_width=1, border_color=COLOR_BORDER, fg_color=COLOR_INPUT_BG)
        self.entry_spec.pack(side="left", fill="x", expand=True, padx=(0, 0)); bind_focus_effects(self.entry_spec)
        for w in (self.entry_proj, self.entry_mat, self.entry_spec): w.bind("<Return>", lambda _e: self.single_search())
        btn_frame = ctk.CTkFrame(inner_card, fg_color="transparent"); btn_frame.pack(fill="x")
        self.btn_export = ctk.CTkButton(btn_frame, text="导出当前列表", width=110, height=38, corner_radius=8, font=ctk.CTkFont(family=APP_FONT, size=13), fg_color="transparent", text_color=COLOR_TEXT_SUB, hover_color=COLOR_NAV_HOVER, command=self.export_single_result); self.btn_export.pack(side="left"); self.btn_export.configure(state="disabled")
        self.btn_search = ctk.CTkButton(btn_frame, text="开始检索", width=130, height=38, corner_radius=8, font=ctk.CTkFont(family=APP_FONT, size=14, weight="bold"), fg_color=COLOR_SEARCH, hover_color=("#0D6B5E", "#1E9B88"), command=self.single_search); self.btn_search.pack(side="right")
        self.btn_reset = ctk.CTkButton(btn_frame, text="重置条件", width=90, height=38, corner_radius=8, font=ctk.CTkFont(family=APP_FONT, size=13), fg_color="transparent", text_color=COLOR_TEXT_SUB, hover_color=COLOR_NAV_HOVER, command=self.reset_search); self.btn_reset.pack(side="right", padx=(15, 0))
        self.single_status = ctk.CTkLabel(self, text="提示：输入的条件需全部满足才会显示结果；点击表头可排序，双击数据行可快速复制。", font=ctk.CTkFont(family=APP_FONT, size=12), text_color=COLOR_TEXT_SUB); self.single_status.pack(anchor="w", padx=10, pady=(0, 8))
        
        mode_idx = 1 if ctk.get_appearance_mode() == "Dark" else 0
        self.table_frame = tk.Frame(self, bg=COLOR_CARD[mode_idx], highlightbackground=COLOR_BORDER[mode_idx], highlightthickness=1); self.table_frame.pack(fill="both", expand=True, padx=5, pady=(0, 10))
        
        columns = ("proj", "mat", "spec", "score", "reason", "price", "unit", "contract", "supplier", "date")
        self.tree = ttk.Treeview(self.table_frame, columns=columns, show="headings", style="Treeview")
        headers = {"proj": "项目名称", "mat": "物资名称", "spec": "规格特征", "score": "综合得分", "reason": "命中理由", "price": "含税单价", "unit": "单位", "contract": "合同编号", "supplier": "供应商", "date": "发生日期"}
        for col, text in headers.items(): self.tree.heading(col, text=text, command=lambda c=col: self.sort_treeview(c, False))
        for col, width in {"proj": 160, "mat": 140, "spec": 220, "score": 90, "reason": 110, "price": 100, "unit": 60, "contract": 150, "supplier": 150, "date": 100}.items():
            anchor = "center" if col in ("score", "unit", "date") else ("e" if col == "price" else "w"); self.tree.column(col, width=width, anchor=anchor)
        
        v_scroll = ttk.Scrollbar(self.table_frame, orient="vertical", command=self.tree.yview); h_scroll = ttk.Scrollbar(self.table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        self.tree.grid(row=0, column=0, sticky="nsew", padx=(10, 0), pady=(10, 0)); v_scroll.grid(row=0, column=1, sticky="ns", pady=(10, 0), padx=(0, 10)); h_scroll.grid(row=1, column=0, sticky="ew", padx=(10, 0), pady=(0, 10))
        self.table_frame.grid_rowconfigure(0, weight=1); self.table_frame.grid_columnconfigure(0, weight=1)
        self.tree.bind("<Double-1>", self.copy_row_to_clipboard)
        self.refresh_theme()

    def refresh_theme(self):
        idx = 1 if ctk.get_appearance_mode() == "Dark" else 0
        try:
            self.table_frame.configure(bg=COLOR_CARD[idx], highlightbackground=COLOR_BORDER[idx])
            self.tree.tag_configure("odd", background=COLOR_TABLE_ODD[idx])
            self.tree.tag_configure("even", background=COLOR_CARD[idx])
        except Exception: pass

    def sort_treeview(self, col, reverse):
        items = [(self.tree.set(k, col), k) for k in self.tree.get_children("")]
        if col in ("score", "price"):
            def parse_num(val):
                try: return float(str(val).replace("¥", "").replace(",", "").strip())
                except ValueError: return -1e18
            items.sort(key=lambda t: parse_num(t[0]), reverse=reverse)
        else: items.sort(key=lambda t: str(t[0]), reverse=reverse)
        for index, (_, k) in enumerate(items): self.tree.move(k, "", index); self.tree.item(k, tags=("even" if index % 2 == 0 else "odd",))
        for c in self.tree["columns"]: self.tree.heading(c, command=(lambda cc=c, r=reverse: self.sort_treeview(cc, not r)) if c == col else (lambda cc=c: self.sort_treeview(cc, False)))
    def reset_search(self):
        self.entry_proj.delete(0, "end"); self.entry_mat.delete(0, "end"); self.entry_spec.delete(0, "end"); self.time_filter.set("全部时间"); self.tree.delete(*self.tree.get_children()); self.btn_export.configure(state="disabled"); self.single_status.configure(text="已重置，请输入新的搜索条件", text_color=COLOR_TEXT_SUB); self.entry_proj.focus_set()
    def copy_row_to_clipboard(self, _event):
        sel = self.tree.selection()
        if not sel: return
        values = self.tree.item(sel[0], "values"); self.clipboard_clear(); self.clipboard_append("\t".join(str(v) for v in values)); self.single_status.configure(text="已复制该行内容到剪贴板", text_color=COLOR_SEARCH)
    def export_single_result(self):
        if not self.tree.get_children(): return
        out_file = filedialog.asksaveasfilename(title="导出搜索结果", defaultextension=".xlsx", initialfile="单条搜索导出.xlsx", filetypes=[("Excel 文件", "*.xlsx")])
        if not out_file: return
        data = [self.tree.item(i, "values") for i in self.tree.get_children()]; cols = ["项目名称", "物资名称", "规格特征", "综合得分", "命中理由", "含税单价", "单位", "合同编号", "供应商", "发生日期"]
        try: pd.DataFrame(data, columns=cols).to_excel(out_file, index=False); messagebox.showinfo("成功", f"已导出到：{out_file}")
        except Exception as e: messagebox.showerror("失败", f"导出失败：{e}")
    def single_search(self):
        if self._searching or not self.app.load_library_data(): return
        proj, mat, spec, time_val = self.entry_proj.get().strip(), self.entry_mat.get().strip(), self.entry_spec.get().strip(), self.time_filter.get()
        if not proj and not mat and not spec: messagebox.showwarning("提示", "请至少输入一项搜索条件！"); return
        self._searching = True; self.tree.delete(*self.tree.get_children()); self.btn_search.configure(state="disabled", text="检索中..."); self.btn_export.configure(state="disabled"); self.single_status.configure(text="正在检索历史数据，请稍候...", text_color=COLOR_TEXT_SUB)
        threading.Thread(target=self.run_single_logic, args=(proj, mat, spec, time_val), daemon=True).start()
    def run_single_logic(self, new_proj, new_mat, new_spec, time_val):
        try:
            df = self.app.df_lib
            if df is None or df.empty: self.after(0, self.finish_single_error, "库里暂无数据"); return
            days = {"近半年": 180, "近一年": 365, "近三年": 365 * 3}.get(time_val)
            if days and self.app._lib_dates is not None:
                df = df[self.app._lib_dates >= pd.Timestamp.now() - pd.Timedelta(days=days)]
                if df.empty: self.after(0, self.finish_single_error, "所选时间范围内没有数据。"); return
            if new_mat and COL_MATERIAL in df.columns: df = df[df[COL_MATERIAL].str.contains(new_mat, case=False, regex=False)]
            if new_spec and COL_SPEC in df.columns: df = df[df[COL_SPEC].str.contains(new_spec, case=False, regex=False)]
            if new_proj and COL_PROJECT in df.columns: df = df[df[COL_PROJECT].str.contains(new_proj, case=False, regex=False)]
            if df.empty:
                if new_mat and COL_MATERIAL in self.app.df_lib.columns: df = self.app.df_lib[self.app.df_lib[COL_MATERIAL].map(lambda v: fuzz.partial_ratio(new_mat, v)) >= 80]
                if df.empty: self.after(0, self.finish_single_error, "没有找到符合条件的历史记录。"); return
            scores = [calculate_match_score(new_proj, new_mat, new_spec, row[COL_PROJECT], row[COL_MATERIAL], row[COL_SPEC]) for _, row in df.iterrows()]
            df = df.assign(_score=scores).sort_values("_score", ascending=False).head(SINGLE_RESULT_LIMIT)
            self.after(0, self.display_single_results, df)
        except Exception: self.after(0, self.finish_single_error, "检索异常，详见日志。")
    def display_single_results(self, df_result):
        reason_str = " 且 ".join([r for c, r in [(self.entry_proj, "项目匹配"), (self.entry_mat, "名称匹配"), (self.entry_spec, "规格匹配")] if c.get().strip()]) or "综合相似"
        for index, row in enumerate(df_result.to_dict("records")):
            self.tree.insert("", "end", values=(row.get(COL_PROJECT, ""), row.get(COL_MATERIAL, ""), row.get(COL_SPEC, ""), row.get("_score", ""), reason_str, row.get(COL_PRICE, ""), row.get(COL_UNIT, ""), row.get(COL_CONTRACT, ""), row.get(COL_SUPPLIER, ""), row.get(COL_DATE, "")), tags=("even" if index % 2 == 0 else "odd",))
        self.btn_search.configure(state="normal", text="开始检索"); self.btn_export.configure(state="normal"); self.single_status.configure(text=f"检索完成，共找到 {len(df_result)} 条记录", text_color=COLOR_SEARCH); self._searching = False
    def finish_single_error(self, msg):
        self.btn_search.configure(state="normal", text="开始检索"); self.single_status.configure(text=msg, text_color=COLOR_DANGER); self._searching = False