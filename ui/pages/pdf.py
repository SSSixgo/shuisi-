import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import threading, datetime, base64, os, shutil
import pandas as pd
try: import pymupdf as fitz
except ImportError: import fitz
from core.config import *
from core.ai_parser import AIParser, _split_text_chunks, _dedupe_extracted_rows
from core.data_io import validate_import_frame, atomic_excel_write
from utils.helpers import _open_folder, _safe_str
from ui.dialogs.preview import PreviewWindow

class PDFPage(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent"); self.app = app; self.parser = AIParser(app); self._pdf_running = False
        card = ctk.CTkFrame(self, fg_color=COLOR_CARD, corner_radius=16, border_width=1, border_color=COLOR_BORDER); card.pack(fill="both", expand=True, padx=20, pady=20)
        header_frame = ctk.CTkFrame(card, fg_color="transparent"); header_frame.pack(fill="x", padx=40, pady=(40, 20))
        ctk.CTkLabel(header_frame, text="🤖 AI 视觉大模型 · 智能提取", font=ctk.CTkFont(family=APP_FONT, size=24, weight="bold"), text_color=COLOR_TEXT_MAIN).pack(anchor="w")
        ctk.CTkLabel(header_frame, text="基于最新多模态大模型技术，无论是原生电子版还是低质量扫描件，皆能精准理解版式结构，一键提取结构化合同明细。", font=ctk.CTkFont(family=APP_FONT, size=14), text_color=COLOR_TEXT_SUB, justify="left").pack(anchor="w", pady=(8, 0))
        btn_frame = ctk.CTkFrame(card, fg_color="transparent"); btn_frame.pack(fill="x", padx=40, pady=(30, 10))
        self.btn_import_pdf = ctk.CTkButton(btn_frame, text="📄 上传 PDF 并启动 AI 解析", width=220, height=48, corner_radius=8, font=ctk.CTkFont(family=APP_FONT, size=15, weight="bold"), fg_color=COLOR_BRAND, hover_color=("#005A9E", "#339BDB"), command=self.import_pdf_data); self.btn_import_pdf.pack(side="left", padx=(0, 15))
        self.btn_cancel_pdf = ctk.CTkButton(btn_frame, text="停止分析", width=120, height=48, corner_radius=8, font=ctk.CTkFont(family=APP_FONT, size=15, weight="bold"), fg_color="transparent", text_color=COLOR_DANGER, border_width=1, border_color=COLOR_DANGER, hover_color=("#FEE2E2", "#3F1D1D"), command=self.cancel_pdf); self.btn_cancel_pdf.pack(side="left"); self.btn_cancel_pdf.configure(state="disabled", text_color=("#D1D5DB", "#4B5563"), border_color=COLOR_BORDER)
        status_panel = ctk.CTkFrame(card, fg_color=COLOR_INPUT_BG, corner_radius=12, border_width=1, border_color=COLOR_BORDER); status_panel.pack(fill="both", expand=True, padx=40, pady=(30, 40))
        self.manage_status = ctk.CTkLabel(status_panel, text="🟢 引擎就绪，等待上传合同文件...", font=ctk.CTkFont(family=APP_FONT, size=15, weight="bold"), text_color=COLOR_TEXT_MAIN); self.manage_status.pack(padx=25, pady=25, anchor="w")
        ctk.CTkLabel(status_panel, text="Powered by 多模态 AI Vision Engine", font=ctk.CTkFont(family=APP_FONT, size=12), text_color=COLOR_TEXT_SUB).pack(side="bottom", padx=25, pady=10, anchor="w")
    
    def import_pdf_data(self):
        if self._pdf_running: return
        if not self.app.ai_config.get("api_key"): messagebox.showwarning("提示", "请先在【系统设置】中配置 AI 接口密钥。"); return
        file_path = filedialog.askopenfilename(title="选择合同 PDF", filetypes=[("PDF 文件", "*.pdf")])
        if not file_path or not messagebox.askyesno("确认开始分析", f"您已选择文件：\n{os.path.basename(file_path)}\n\n即将调用 AI 视觉大模型进行深度解析，这可能会消耗 Token 额度。\n是否确认开始？"):
            self._update_pdf_progress("已取消分析操作。", COLOR_TEXT_SUB); return
        self._pdf_running = True; self.app.cancel_event.clear(); self.btn_import_pdf.configure(state="disabled", text="AI 解析中..."); self.btn_cancel_pdf.configure(state="normal", text_color=COLOR_DANGER, border_color=COLOR_DANGER); self._update_pdf_progress("正在初始化视觉解析引擎...", COLOR_BRAND)
        threading.Thread(target=self.run_pdf_extract_logic, args=(file_path,), daemon=True).start()
    
    def cancel_pdf(self):
        if not self.app.cancel_event.is_set(): self.app.cancel_event.set(); self.btn_cancel_pdf.configure(text="正在终止...", state="disabled"); self._update_pdf_progress("正在请求终止分析，请稍候...", COLOR_DANGER)
    
    def _update_pdf_progress(self, text, color=COLOR_TEXT_SUB):
        try: self.manage_status.configure(text=f"{('🔵' if color==COLOR_BRAND else ('🟢' if color==COLOR_SEARCH else ('🔴' if color==COLOR_DANGER else '⚪')))} {text}", text_color=color)
        except Exception: pass
    
    def run_pdf_extract_logic(self, file_path):
        try: self._run_pdf_extract(file_path)
        except Exception as e: self.after(0, self.import_pdf_finish, False, f"系统发生未捕获的异常：\n{e}")
    
    def _run_pdf_extract(self, file_path):
        try: doc = fitz.open(file_path); total_pages = len(doc)
        except Exception as e: self.after(0, self.import_pdf_finish, False, f"PDF 打开失败：\n{e}"); return
        if total_pages == 0: self.after(0, self.import_pdf_finish, False, "PDF 中没有任何可读取的页面。"); return
        max_pages = min(total_pages, PDF_MAX_PAGES); today = datetime.datetime.now().strftime("%Y-%m-%d")
        self.after(0, self._update_pdf_progress, "正在提取 PDF 原生文本...", COLOR_BRAND); full_text = "".join([p.get_text() + "\n" for p in doc])
        all_data, failed_pages = [], []
        if len(full_text.strip()) > 500:
            doc.close(); chunks = _split_text_chunks(full_text); self.after(0, self._update_pdf_progress, f"识别为原生电子版，AI 正在分段提取数据 ({len(chunks)} 段)...", COLOR_BRAND)
            for ci, chunk in enumerate(chunks, 1):
                if self.app.cancel_event.is_set(): break
                self.after(0, self._update_pdf_progress, f"大模型推理中：正在处理第 {ci}/{len(chunks)} 段...", COLOR_BRAND)
                page_data = self.parser.call_text_ai(chunk)
                if isinstance(page_data, str): failed_pages.append((ci, page_data))
                elif page_data: all_data.extend(page_data)
        else:
            self.after(0, self._update_pdf_progress, "识别为图像扫描件，启动视觉大模型并发提取...", COLOR_BRAND)
            b64_images = []
            for page_idx in range(max_pages):
                try: pix = doc[page_idx].get_pixmap(dpi=120); b64_images.append(base64.b64encode(pix.tobytes("jpeg", jpg_quality=75) if hasattr(pix, 'tobytes') else pix.tobytes("jpeg")).decode("utf-8"))
                except Exception: b64_images.append(None)
            doc.close()
            def process_page(idx):
                if self.app.cancel_event.is_set() or b64_images[idx] is None: return idx, []
                self.after(0, self._update_pdf_progress, f"视觉大模型推理中：正在解析第 {idx+1}/{max_pages} 页图像...", COLOR_BRAND)
                return idx, self.parser.call_vl_ai_for_page(b64_images[idx], idx+1, max_pages)
            
            from concurrent.futures import ThreadPoolExecutor, as_completed
            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = {executor.submit(process_page, i): i for i in range(max_pages)}
                for future in as_completed(futures):
                    if self.app.cancel_event.is_set(): 
                        executor.shutdown(wait=False, cancel_futures=True); break
                    try:
                        idx, page_data = future.result()
                        if isinstance(page_data, str): failed_pages.append((idx+1, page_data))
                        elif page_data: all_data.extend(page_data)
                    except Exception: pass # ★ 修复：忽略被取消的线程抛出的异常
        if self.app.cancel_event.is_set() and not all_data: self.after(0, self.import_pdf_finish, False, "已终止分析。"); return
        elif self.app.cancel_event.is_set(): self.after(0, self._update_pdf_progress, "已终止分析，正在整理已提取的数据...", COLOR_DANGER)
        if not all_data:
            msg = "AI 提取完成，但未找到任何有效的物资明细。"
            if failed_pages: msg += f"\n\n错误原因：\n" + "\n".join(f"第 {p} 段/页：{str(e)[:60]}" for p, e in failed_pages[:5])
            self.after(0, self.import_pdf_finish, False, msg); return
        all_data = _dedupe_extracted_rows(all_data); global_contract_no = ""; global_supplier = ""; valid_data = []
        for item in all_data:
            c_no, s_comp = _safe_str(item.get("contract_no")), _safe_str(item.get("supply_company"))
            if not global_contract_no and c_no: global_contract_no = c_no
            if not global_supplier and s_comp: global_supplier = s_comp
            if _safe_str(item.get("material_name")) or _safe_str(item.get("spec_feature")): valid_data.append(item)
        if not valid_data: self.after(0, self.import_pdf_finish, False, "AI 提取完成，但未找到任何物资明细。"); return
        pdf_name = os.path.basename(file_path)
        for item in valid_data:
            for c in self.app.df_lib.columns:
                if c not in item: item[c] = ""
            if "contract_no" in self.app.df_lib.columns and not item.get("contract_no"): item["contract_no"] = global_contract_no
            if "supply_company" in self.app.df_lib.columns and not item.get("supply_company"): item["supply_company"] = global_supplier
            if "source_file" in self.app.df_lib.columns and not item.get("source_file"): item["source_file"] = pdf_name
            if "record_date" in item and not item["record_date"]: item["record_date"] = today
        self.after(0, self._on_pdf_all_done, valid_data, failed_pages, max_pages)
    
    def _on_pdf_all_done(self, data_list, failed_pages, total_pages):
        try:
            self._pdf_running = False; self.btn_import_pdf.configure(state="normal", text="📄 上传 PDF 并启动 AI 解析"); self.btn_cancel_pdf.configure(state="disabled", text="停止分析", text_color=("#D1D5DB", "#4B5563"), border_color=COLOR_BORDER)
            self._update_pdf_progress(f"解析完成！共处理 {total_pages} 页，提取到 {len(data_list)} 条数据，请在弹窗中核对。", COLOR_SEARCH)
            if failed_pages: messagebox.showwarning("部分内容提取失败", f"以下内容提取失败：\n\n" + "\n".join(f"第 {p} 页/段：{str(e)[:80]}" for p, e in failed_pages[:10]))
            PreviewWindow(self, data_list, self.app.df_lib.columns.tolist(), self.confirm_pdf_import)
        except Exception as e: self.import_pdf_finish(False, f"收尾处理异常：\n{e}")
    
    def import_pdf_finish(self, success, msg):
        self._pdf_running = False
        try: self.btn_import_pdf.configure(state="normal", text="📄 上传 PDF 并启动 AI 解析"); self.btn_cancel_pdf.configure(state="disabled", text="停止分析", text_color=("#D1D5DB", "#4B5563"), border_color=COLOR_BORDER)
        except Exception: pass
        if not success: self._update_pdf_progress("提取失败（详见弹窗）", COLOR_DANGER); messagebox.showwarning("AI 提取失败", msg)
    
    def confirm_pdf_import(self, df_new):
        self._update_pdf_progress("正在写入数据库...", COLOR_BRAND)
        try:
            df_new = validate_import_frame(df_new)
            with self.app.db_lock:
                existing_cols = self.app.df_lib.columns.tolist(); new_cols = [c for c in df_new.columns if c not in existing_cols]
                merged = pd.concat([self.app.df_lib, df_new.reindex(columns=existing_cols + new_cols)], ignore_index=True)
                time_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f"); backup_path = os.path.join(self.app.backup_dir, f"{BACKUP_PREFIX}{time_str}.xlsx")
                os.makedirs(self.app.backup_dir, exist_ok=True); shutil.copy2(self.app.lib_path, backup_path)
                atomic_excel_write(merged, self.app.lib_path)
                
                # ★ 核心修复：强制刷新缓存
                self.app._lib_mtime = None 
                self.app.load_library_data()
                
            msg = f"入库成功！本次新增 {len(df_new)} 条记录，当前库总记录数为 {len(merged)} 条。"; self._update_pdf_progress(msg, COLOR_SEARCH); messagebox.showinfo("成功", msg)
        except PermissionError: self._update_pdf_progress("入库失败", COLOR_DANGER); messagebox.showerror("错误", "写入失败！无法覆盖【历史价格库.xlsx】。\n请确保没有用 Excel 打开它。")
        except Exception as e: self._update_pdf_progress("入库失败", COLOR_DANGER); messagebox.showerror("错误", f"写入发生异常：\n{e}")