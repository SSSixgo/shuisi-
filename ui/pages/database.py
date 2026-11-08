import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading, pandas as pd, os, shutil, datetime
from core.config import *
from core.data_io import atomic_excel_write, validate_import_frame

class DatabasePage(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent"); self.app = app
        card = ctk.CTkFrame(self, fg_color=COLOR_CARD, corner_radius=16, border_width=1, border_color=COLOR_BORDER); card.pack(fill="both", expand=True)
        inner = ctk.CTkFrame(card, fg_color="transparent"); inner.pack(padx=40, pady=40, fill="x")
        ctk.CTkLabel(inner, text="数据导入与导出", font=ctk.CTkFont(family=APP_FONT, size=22, weight="bold"), text_color=COLOR_TEXT_MAIN).pack(anchor="w")
        ctk.CTkLabel(inner, text="您可以在此处导出全量数据用于本地查看。或者上传新的 Excel 进行追加/覆盖入库。", font=ctk.CTkFont(family=APP_FONT, size=14), text_color=COLOR_TEXT_SUB).pack(anchor="w", pady=(8, 30))
        btn_row = ctk.CTkFrame(inner, fg_color="transparent"); btn_row.pack(anchor="w", fill="x")
        self.btn_export_db = ctk.CTkButton(btn_row, text="导出当前数据库", width=170, height=46, corner_radius=8, font=ctk.CTkFont(family=APP_FONT, size=15), fg_color=COLOR_INPUT_BG, text_color=COLOR_TEXT_MAIN, hover_color=COLOR_NAV_HOVER, border_width=1, border_color=COLOR_BORDER, command=self.export_db); self.btn_export_db.pack(side="left", padx=(0, 15))
        self.btn_import_data = ctk.CTkButton(btn_row, text="上传 Excel 追加入库", width=170, height=46, corner_radius=8, font=ctk.CTkFont(family=APP_FONT, size=15, weight="bold"), fg_color=COLOR_BRAND, hover_color=("#005A9E", "#339BDB"), command=self.import_new_data); self.btn_import_data.pack(side="left", padx=(0, 15))
        self.btn_overwrite_data = ctk.CTkButton(btn_row, text="上传 Excel 覆盖数据库", width=170, height=46, corner_radius=8, font=ctk.CTkFont(family=APP_FONT, size=15, weight="bold"), fg_color="transparent", text_color=COLOR_DANGER, border_width=1, border_color=COLOR_DANGER, hover_color=("#FEE2E2", "#3F1D1D"), command=self.overwrite_data); self.btn_overwrite_data.pack(side="left")
    def export_db(self):
        out_file = filedialog.asksaveasfilename(title="导出当前数据库", defaultextension=".xlsx", initialfile="历史价格库_导出.xlsx", filetypes=[("Excel 文件", "*.xlsx")])
        if not out_file: return
        try:
            with self.app.db_lock:
                if self.app.df_lib is not None: self.app.df_lib.to_excel(out_file, index=False)
            messagebox.showinfo("成功", f"数据库已成功导出至：\n{out_file}")
        except Exception as e: messagebox.showerror("失败", f"导出失败：\n{e}")
    def import_new_data(self):
        fp = filedialog.askopenfilename(title="选择要投喂的新数据文件 (追加入库)", filetypes=[("Excel", "*.xlsx *.xls")])
        if not fp: return
        self.btn_import_data.configure(state="disabled", text="正在合并..."); threading.Thread(target=self._run_import, args=(fp,), daemon=True).start()
    def _run_import(self, fp):
        try:
            df = validate_import_frame(pd.read_excel(fp))
            with self.app.db_lock:
                existing_cols = self.app.df_lib.columns.tolist(); new_cols = [c for c in df.columns if c not in existing_cols]
                merged = pd.concat([self.app.df_lib, df.reindex(columns=existing_cols + new_cols)], ignore_index=True)
                time_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f"); backup_path = os.path.join(self.app.backup_dir, f"{BACKUP_PREFIX}{time_str}.xlsx")
                os.makedirs(self.app.backup_dir, exist_ok=True); shutil.copy2(self.app.lib_path, backup_path)
                atomic_excel_write(merged, self.app.lib_path)
                
                # ★ 核心修复：强制刷新缓存
                self.app._lib_mtime = None
                self.app.load_library_data()
                
            self.after(0, self._on_import_done, True, f"追加成功！\n本次新增 {len(df)} 条记录。\n当前总数据量：{len(merged)} 条。")
        except PermissionError: self.after(0, self._on_import_done, False, "写入失败！无法覆盖【历史价格库.xlsx】。\n请检查是否用 Excel 打开了该文件。")
        except Exception as e: self.after(0, self._on_import_done, False, f"导入发生错误：\n{e}")
    def _on_import_done(self, ok, msg):
        self.btn_import_data.configure(state="normal", text="上传 Excel 追加入库")
        if ok: messagebox.showinfo("操作成功", msg)
        else: messagebox.showerror("操作失败", msg)
    def overwrite_data(self):
        fp = filedialog.askopenfilename(title="选择要覆盖的新数据文件", filetypes=[("Excel", "*.xlsx *.xls")])
        if not fp: return
        if not messagebox.askyesno("高危操作确认", "您确定要用该文件【完全覆盖】现有数据库吗？\n\n原有数据将丢失（系统会自动生成备份以防万一）！"): return
        self.btn_overwrite_data.configure(state="disabled", text="正在覆盖..."); threading.Thread(target=self._run_overwrite, args=(fp,), daemon=True).start()
    def _run_overwrite(self, fp):
        try:
            df = validate_import_frame(pd.read_excel(fp))
            with self.app.db_lock:
                if self.app.df_lib is not None:
                    for c in self.app.df_lib.columns:
                        if c not in df.columns: df[c] = ""
                time_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S"); backup_path = os.path.join(self.app.backup_dir, f"{BACKUP_PREFIX}{time_str}_覆盖前.xlsx"); shutil.copy2(self.app.lib_path, backup_path)
                atomic_excel_write(df, self.app.lib_path)
                
                # ★ 核心修复：强制刷新缓存
                self.app._lib_mtime = None
                self.app.load_library_data()
                
            self.after(0, self._on_overwrite_done, True, f"覆盖成功！当前总数据量：{len(df)} 条。")
        except PermissionError: self.after(0, self._on_overwrite_done, False, "写入失败！无法覆盖【历史价格库.xlsx】。\n请确保没有用 Excel 打开它。")
        except Exception as e: self.after(0, self._on_overwrite_done, False, f"覆盖失败：\n{e}")
    def _on_overwrite_done(self, ok, msg):
        self.btn_overwrite_data.configure(state="normal", text="上传 Excel 覆盖数据库")
        if ok: messagebox.showinfo("操作成功", msg)
        else: messagebox.showerror("操作失败", msg)