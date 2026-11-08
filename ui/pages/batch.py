import customtkinter as ctk
from tkinter import messagebox, filedialog
import threading, time, pandas as pd, os
from rapidfuzz import fuzz, process
from core.config import *
from core.matcher import calculate_match_score
from utils.helpers import _open_folder

class BatchPage(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent"); self.app = app; self.new_file_path = ""; self.out_file_path = ""
        card = ctk.CTkFrame(self, fg_color=COLOR_CARD, corner_radius=16, border_width=1, border_color=COLOR_BORDER); card.pack(fill="both", expand=True)
        center_frame = ctk.CTkFrame(card, fg_color="transparent"); center_frame.place(relx=0.5, rely=0.4, anchor="center")
        self.file_label = ctk.CTkLabel(center_frame, text="尚未选择新需求清单文件", font=ctk.CTkFont(family=APP_FONT, size=20, weight="bold"), text_color=COLOR_TEXT_MAIN); self.file_label.pack(pady=(0, 25))
        btn_row = ctk.CTkFrame(center_frame, fg_color="transparent"); btn_row.pack()
        self.browse_btn = ctk.CTkButton(btn_row, text="选择本地文件", width=170, height=46, corner_radius=8, font=ctk.CTkFont(family=APP_FONT, size=15), fg_color=COLOR_BRAND_LIGHT, text_color=COLOR_BRAND, hover_color=("#D6E9F8", "#1C4058"), command=self.select_file); self.browse_btn.pack(side="left", padx=(0, 15))
        self.reset_batch_btn = ctk.CTkButton(btn_row, text="重置", width=110, height=46, corner_radius=8, font=ctk.CTkFont(family=APP_FONT, size=15), fg_color="transparent", text_color=COLOR_TEXT_SUB, hover_color=COLOR_NAV_HOVER, command=self.reset_batch_state); self.reset_batch_btn.pack(side="left")
        self.batch_status = ctk.CTkLabel(card, text="等待导入数据 (将生成：首选匹配、回填表、询价单、全部明细)", font=ctk.CTkFont(family=APP_FONT, size=13), text_color=COLOR_TEXT_SUB); self.batch_status.pack(side="bottom", pady=(0, 80))
        action_frame = ctk.CTkFrame(card, fg_color="transparent"); action_frame.pack(side="bottom", fill="x", padx=60, pady=40)
        self.start_btn = ctk.CTkButton(action_frame, text="开始批量匹配并生成报表", height=48, corner_radius=8, font=ctk.CTkFont(family=APP_FONT, size=16, weight="bold"), fg_color=COLOR_BRAND, hover_color=("#005A9E", "#339BDB"), command=self.start_matching); self.start_btn.pack(side="left", fill="x", expand=True, padx=(0, 15))
        self.cancel_batch_btn = ctk.CTkButton(action_frame, text="停止处理", width=140, height=48, corner_radius=8, font=ctk.CTkFont(family=APP_FONT, size=15, weight="bold"), fg_color="transparent", text_color=COLOR_DANGER, border_width=1, border_color=COLOR_DANGER, hover_color=("#FEE2E2", "#3F1D1D"), command=self.cancel_batch); self.cancel_batch_btn.pack(side="right"); self.cancel_batch_btn.configure(state="disabled")
    def select_file(self):
        fp = filedialog.askopenfilename(title="选择新需求清单", filetypes=[("Excel", "*.xlsx *.xls")])
        if fp: self.new_file_path = fp; self.file_label.configure(text=os.path.basename(fp), text_color=COLOR_TEXT_MAIN); self.batch_status.configure(text="文件已就绪", text_color=COLOR_SEARCH)
    def reset_batch_state(self):
        self.new_file_path = ""; self.file_label.configure(text="尚未选择新需求清单文件", text_color=COLOR_TEXT_MAIN); self.batch_status.configure(text="等待导入数据 (将生成：首选匹配、回填表、询价单、全部明细)", text_color=COLOR_TEXT_SUB)
    def start_matching(self):
        if not self.new_file_path or not os.path.exists(self.new_file_path): messagebox.showwarning("提示", "请先选择新需求清单文件！"); return
        if not self.app.load_library_data(): return
        self.out_file_path = filedialog.asksaveasfilename(title="保存批量匹配报表", defaultextension=".xlsx", initialfile="批量匹配综合报表.xlsx", filetypes=[("Excel 文件", "*.xlsx")])
        if not self.out_file_path: return
        self.app.cancel_event.clear(); self.start_btn.configure(state="disabled", text="处理中..."); self.browse_btn.configure(state="disabled"); self.cancel_batch_btn.configure(state="normal", text="停止处理", fg_color="transparent", text_color=COLOR_DANGER); self.batch_status.configure(text="正在计算相似度，请稍候...", text_color=COLOR_TEXT_SUB)
        threading.Thread(target=self.run_batch_logic, daemon=True).start()
    def cancel_batch(self):
        if not self.app.cancel_event.is_set(): self.app.cancel_event.set(); self.cancel_batch_btn.configure(text="正在停止...", state="disabled"); self.batch_status.configure(text="正在请求停止，请稍候...", text_color=COLOR_DANGER)
    def _restore_batch_buttons(self):
        self.start_btn.configure(state="normal", text="开始批量匹配并生成报表", fg_color=COLOR_BRAND); self.browse_btn.configure(state="normal"); self.cancel_batch_btn.configure(state="disabled", text="停止处理", fg_color="transparent")
    def run_batch_logic(self):
        try: df_new = pd.read_excel(self.new_file_path)
        except Exception as e: self.after(0, self.finish_batch_error, f"读取新清单失败：{e}"); return
        for col in IMPORT_REQUIRED_COLS:
            if col not in df_new.columns: self.after(0, self.finish_batch_error, f"表格错误：缺少必要列名 '{col}'！"); return
        if df_new.empty: self.after(0, self.finish_batch_error, "新清单为空，无可处理数据。"); return
        lib_df = self.app.df_lib
        lib_mats = lib_df[COL_MATERIAL].tolist() if COL_MATERIAL in lib_df.columns else [""] * len(lib_df)
        lib_specs = lib_df[COL_SPEC].tolist() if COL_SPEC in lib_df.columns else [""] * len(lib_df)
        lib_projs = lib_df[COL_PROJECT].tolist() if COL_PROJECT in lib_df.columns else [""] * len(lib_df)
        result_list, top1_list, inquiry_list, backfill_data = [], [], [], []
        total_new = len(df_new); last_ui = 0.0; cancelled = False; processed_count = 0
        for idx_new, row_new in df_new.iterrows():
            if self.app.cancel_event.is_set(): cancelled = True; break
            now_ts = time.time()
            if now_ts - last_ui > UI_THROTTLE_SEC or idx_new == total_new - 1:
                last_ui = now_ts
                self.after(0, lambda i=idx_new, n=total_new: self.batch_status.configure(text=f"正在处理第 {i+1} / {n} 条数据..."))
            new_mat = str(row_new.get(COL_MATERIAL, "")).strip(); new_spec = str(row_new.get(COL_SPEC, "")).strip(); base_bf = row_new.to_dict()
            if not new_mat and not new_spec:
                inquiry_list.append({**base_bf, "询价状态": "未匹配到历史价"}); base_bf.update({"匹配相似度": "无匹配", "匹配_历史物资名称": "", "匹配_含税单价": "", "匹配_供应商": "", "匹配_合同编号": ""}); backfill_data.append(base_bf); processed_count = idx_new + 1; continue
            candidates_idx = set()
            if new_mat:
                for match in process.extract(new_mat, lib_mats, scorer=fuzz.token_set_ratio, limit=50): candidates_idx.add(match[2])
            if new_spec:
                for match in process.extract(new_spec, lib_specs, scorer=fuzz.token_set_ratio, limit=50): candidates_idx.add(match[2])
            best = None
            for i in candidates_idx:
                lib_proj, lib_mat, lib_spec = lib_projs[i], lib_mats[i], lib_specs[i]
                sim = calculate_match_score("", new_mat, new_spec, lib_proj, lib_mat, lib_spec)
                if sim < BATCH_FUZZ_THRESHOLD: continue
                if best is None or sim > best[0]: best = (sim, i)
                result_list.append({"新需求序号": idx_new + 1, "新需求_物资名称": new_mat, "新需求_项目特征": new_spec, "库内_物资名称": lib_mat, "库内_规格特征": lib_spec, "相似度得分": sim, "库内_含税单价": lib_df.iloc[i].get(COL_PRICE, ""), "供应商": lib_df.iloc[i].get(COL_SUPPLIER, ""), "合同编号": lib_df.iloc[i].get(COL_CONTRACT, "")})
            if best is not None:
                score, best_i = best; best_row = lib_df.iloc[best_i]
                base_bf.update({"匹配相似度": score, "匹配_历史物资名称": best_row.get(COL_MATERIAL, ""), "匹配_含税单价": best_row.get(COL_PRICE, ""), "匹配_供应商": best_row.get(COL_SUPPLIER, ""), "匹配_合同编号": best_row.get(COL_CONTRACT, "")}); backfill_data.append(base_bf)
                top1_list.append({"序号": idx_new + 1, "物资名称": new_mat, "项目特征": new_spec, "匹配物资": best_row.get(COL_MATERIAL, ""), "匹配特征": best_row.get(COL_SPEC, ""), "相似度": score, "含税单价": best_row.get(COL_PRICE, ""), "供应商": best_row.get(COL_SUPPLIER, ""), "合同编号": best_row.get(COL_CONTRACT, "")})
            else:
                inquiry_list.append({**base_bf, "询价状态": "未匹配到历史价"}); base_bf.update({"匹配相似度": "无匹配", "匹配_历史物资名称": "", "匹配_含税单价": "", "匹配_供应商": "", "匹配_合同编号": ""}); backfill_data.append(base_bf)
            processed_count = idx_new + 1
        df_result_all, df_top1, df_inquiry, df_backfill = pd.DataFrame(result_list), pd.DataFrame(top1_list), pd.DataFrame(inquiry_list), pd.DataFrame(backfill_data)
        try:
            with pd.ExcelWriter(self.out_file_path, engine="openpyxl") as writer:
                if not df_backfill.empty: df_backfill.to_excel(writer, sheet_name="一键回填表", index=False)
                if not df_top1.empty: df_top1.to_excel(writer, sheet_name="首选最佳匹配", index=False)
                if not df_inquiry.empty: df_inquiry.to_excel(writer, sheet_name="待询价清单", index=False)
                if not df_result_all.empty: df_result_all.to_excel(writer, sheet_name="全部候选明细", index=False)
            if cancelled: self.after(0, self.finish_batch_cancelled, processed_count, total_new, len(inquiry_list))
            else: self.after(0, self.finish_batch_success, len(inquiry_list))
        except PermissionError: self.after(0, self.finish_batch_error, "保存失败：请先关闭正在打开的输出文件。")
        except Exception as e: self.after(0, self.finish_batch_error, f"生成报表异常：{e}")
    def finish_batch_success(self, inquiry_count):
        self.reset_batch_state(); self._restore_batch_buttons(); self.batch_status.configure(text="批量匹配完成", text_color=COLOR_SEARCH)
        msg = f"批量匹配成功！\n结果已保存至：\n{self.out_file_path}\n\n" + (f"注意：有 {inquiry_count} 条物资未匹配到历史价，\n已自动为您生成了《待询价清单》Sheet。" if inquiry_count > 0 else "所有物资均成功匹配到历史价格。")
        messagebox.showinfo("完成", msg); _open_folder(os.path.dirname(self.out_file_path))
    def finish_batch_cancelled(self, processed_count, total_count, inquiry_count):
        self.reset_batch_state(); self._restore_batch_buttons(); self.batch_status.configure(text=f"已停止（完成 {processed_count} / {total_count}）", text_color=COLOR_DANGER)
        if processed_count == 0: messagebox.showinfo("已停止", "已停止处理，尚无任何结果可保存。"); return
        msg = f"已停止处理。\n\n已完成 {processed_count} / {total_count} 条，已保存至：\n{self.out_file_path}\n\n其中未匹配物资 {inquiry_count} 条。\n如需完整结果请重新运行。"
        messagebox.showinfo("已停止", msg); _open_folder(os.path.dirname(self.out_file_path))
    def finish_batch_error(self, msg):
        self.reset_batch_state(); self._restore_batch_buttons(); self.batch_status.configure(text="发生错误", text_color=COLOR_DANGER); messagebox.showerror("错误", msg)