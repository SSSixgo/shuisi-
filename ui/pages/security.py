import customtkinter as ctk
from tkinter import ttk, messagebox
import os, shutil, datetime, pandas as pd
from core.config import *
from core.data_io import atomic_excel_write

class SecurityPage(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent"); self.app = app
        card = ctk.CTkFrame(self, fg_color=COLOR_CARD, corner_radius=16, border_width=1, border_color=COLOR_BORDER); card.pack(fill="both", expand=True)
        record_frame = ctk.CTkFrame(card, fg_color="transparent"); record_frame.pack(padx=40, pady=40, fill="both", expand=True)
        ctk.CTkLabel(record_frame, text="操作记录 & 撤回", font=ctk.CTkFont(family=APP_FONT, size=22, weight="bold"), text_color=COLOR_TEXT_MAIN).pack(anchor="w")
        ctk.CTkLabel(record_frame, text="选中一条历史备份，点击右侧按钮即可将数据库恢复到那一刻的状态。", font=ctk.CTkFont(family=APP_FONT, size=14), text_color=COLOR_TEXT_SUB).pack(anchor="w", pady=(8, 20))
        list_frame = ctk.CTkFrame(record_frame, fg_color="transparent"); list_frame.pack(fill="both", expand=True)
        self.backup_tree = ttk.Treeview(list_frame, columns=("time", "size", "filename"), show="headings", style="Backup.Treeview")
        self.backup_tree.heading("time", text="操作时间"); self.backup_tree.heading("size", text="文件大小"); self.backup_tree.heading("filename", text="备份文件名 (内部标识)")
        self.backup_tree.column("time", width=200, anchor="w"); self.backup_tree.column("size", width=100, anchor="center"); self.backup_tree.column("filename", width=350, anchor="w")
        v_scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.backup_tree.yview); self.backup_tree.configure(yscrollcommand=v_scroll.set); self.backup_tree.pack(side="left", fill="both", expand=True); v_scroll.pack(side="right", fill="y")
        self.btn_rollback = ctk.CTkButton(record_frame, text="一键撤回并恢复到此时", width=200, height=44, corner_radius=8, font=ctk.CTkFont(family=APP_FONT, size=15, weight="bold"), fg_color="transparent", text_color=COLOR_DANGER, border_width=1, border_color=COLOR_DANGER, hover_color=("#FEE2E2", "#3F1D1D"), command=self.rollback_data); self.btn_rollback.pack(anchor="e", pady=(25, 0))
        self.refresh_theme()
        self.refresh_backup_list()

    def refresh_theme(self):
        idx = 1 if ctk.get_appearance_mode() == "Dark" else 0
        self.backup_tree.tag_configure("odd", background=COLOR_TABLE_ODD[idx])
        self.backup_tree.tag_configure("even", background=COLOR_CARD[idx])
        self.refresh_backup_list()

    def refresh_backup_list(self):
        try:
            for i in self.backup_tree.get_children(): self.backup_tree.delete(i)
        except Exception: return
        if not os.path.exists(self.app.backup_dir): return
        files = [f for f in os.listdir(self.app.backup_dir) if f.endswith(".xlsx")]; files.sort(reverse=True)
        
        for index, f in enumerate(files):
            path = os.path.join(self.app.backup_dir, f); m = _BACKUP_TIME_RE.search(f)
            display_time = "未知时间"
            if m:
                try: display_time = datetime.datetime.strptime(m.group(1)[:15], "%Y%m%d_%H%M%S").strftime("%Y-%m-%d %H:%M:%S")
                except Exception: pass
            try:
                self.backup_tree.insert("", "end", values=(display_time, f"{round(os.path.getsize(path) / 1024, 1)} KB", f), tags=("even" if index % 2 == 0 else "odd",))
            except Exception: pass
    
    def rollback_data(self):
        sel = self.backup_tree.selection()
        if not sel: messagebox.showwarning("提示", "请先在列表中选中一条要撤回的历史记录！"); return
        item_values = self.backup_tree.item(sel[0], "values"); backup_file, display_time = item_values[2], item_values[0]
        if not messagebox.askyesno("确认撤回", f"确定要将数据库恢复到【{display_time}】的状态吗？\n\n当前所有最新数据将被覆盖！"): return
        try:
            backup_path = os.path.join(self.app.backup_dir, backup_file)
            time_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S"); current_backup = os.path.join(self.app.backup_dir, f"{BACKUP_PREFIX}{time_str}_撤回前.xlsx"); shutil.copy2(self.app.lib_path, current_backup)
            restored = pd.read_excel(backup_path, dtype=object).fillna(""); atomic_excel_write(restored, self.app.lib_path)
            
            # ★ 核心修复：强制刷新缓存
            self.app._lib_mtime = None
            self.app.load_library_data()
            
            self.refresh_backup_list(); messagebox.showinfo("撤回成功", f"数据库已成功恢复到 {display_time} 版本。")
        except PermissionError: messagebox.showerror("错误", "撤回失败！无法覆盖【历史价格库.xlsx】。\n请确保没有用 Excel 打开它。")
        except Exception as e: messagebox.showerror("错误", f"发生异常：\n{e}")