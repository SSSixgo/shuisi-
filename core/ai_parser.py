import base64, json, time, requests
from core.config import *
from utils.helpers import _safe_str

def _split_text_chunks(text, chunk_size=PDF_TEXT_CHUNK_CHARS, overlap=PDF_TEXT_CHUNK_OVERLAP):
    text = (text or "").strip()
    if not text: return []
    chunks, start = [], 0
    while start < len(text):
        end = min(len(text), start + chunk_size)
        if end < len(text):
            boundary = max(text.rfind("\n", start, end), text.rfind("。", start, end), text.rfind("；", start, end))
            if boundary > start + chunk_size // 2: end = boundary + 1
        chunks.append(text[start:end])
        if end >= len(text): break
        start = max(start + 1, end - overlap)
    return chunks

def _dedupe_extracted_rows(rows):
    seen, result = set(), []
    for row in rows:
        key = tuple(_safe_str(row.get(k)) for k in ("contract_no", "supply_company", "material_name", "spec_feature", "unit", "price_tax"))
        if not any(key[2:4]) and not any(key[:2]): continue
        if key not in seen:
            seen.add(key); result.append(row)
    return result

class AIParser:
    def __init__(self, app):
        self.app = app
        self.cancel_event = app.cancel_event

    def _ai_call(self, model, messages):
        payload = {"model": model, "messages": messages, "temperature": 0.1}
        headers = {"Authorization": f"Bearer {self.app.ai_config['api_key']}", "Content-Type": "application/json"}
        last_err = None
        for attempt in range(3):
            try:
                resp = requests.post(self.app.ai_config["api_url"], headers=headers, json=payload, timeout=API_TIMEOUT, verify=False)
                data = resp.json()
                if "choices" not in data: return None, f"API 返回错误: {data.get('message') or data.get('error', {}).get('message', '未知错误')}"
                return data["choices"][0]["message"]["content"], None
            except requests.exceptions.Timeout: last_err = "请求超时"
            except requests.exceptions.ConnectionError as e: last_err = f"网络异常: {e}"
            except Exception as e: last_err = f"请求异常: {e}"
            time.sleep(1.5 * (2 ** attempt))
        return None, last_err

    def call_text_ai(self, full_text):
        target_cols = [c for c in self.app.df_lib.columns if c.lower() not in ("id", "序号")]
        sample_data = self.app.df_lib.head(3).to_dict(orient="records")
        clean_samples = [{k: _safe_str(v) for k, v in row.items() if k in target_cols} for row in sample_data]
        prompt = f"这是一份工程造价合同文本。请从中提取所有的物资采购明细。\n## 目标字段：\n{json.dumps(target_cols, ensure_ascii=False)}\n## 样例：\n{json.dumps(clean_samples, ensure_ascii=False)}\n## 规则：\n1. 只输出 JSON 数组。\n2. 寻找“合同编号”和“乙方/供方/供应商”自动填入。\n3. 忽略汇总行。\n4. 金额转为纯数字。\n文本如下：\n{full_text[:12000]}"
        content, err = self._ai_call(self.app.ai_config["text_model"], [{"role": "user", "content": prompt}])
        if err: return err
        cleaned = content.replace("```json", "").replace("```", "").strip()
        m = _JSON_ARRAY_RE.search(cleaned)
        if not m: return f"未找到 JSON。回复: {cleaned[:100]}..."
        try: return [it for it in json.loads(m.group(0)) if isinstance(it, dict)]
        except Exception as e: return f"JSON 解析失败: {e}"

    def call_vl_ai_for_page(self, b64_image, page_num, total_pages):
        target_cols = [c for c in self.app.df_lib.columns if c.lower() not in ("id", "序号")]
        sample_data = self.app.df_lib.head(3).to_dict(orient="records")
        clean_samples = [{k: _safe_str(v) for k, v in row.items() if k in target_cols} for row in sample_data]
        prompt = f"这是合同扫描件第 {page_num} 页。提取明细。\n## 目标字段：\n{json.dumps(target_cols, ensure_ascii=False)}\n## 样例：\n{json.dumps(clean_samples, ensure_ascii=False)}\n## 规则：只输出 JSON 数组。寻找合同编号和乙方。如果有表则提取；如果有编号没表，返回占位记录。找不到返回 []。"
        messages = [{"role": "user", "content": [{"type": "text", "text": prompt}, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_image}"}}]}]
        content, err = self._ai_call(self.app.ai_config["vl_model"], messages)
        if err: return err
        cleaned = content.replace("```json", "").replace("```", "").strip()
        m = _JSON_ARRAY_RE.search(cleaned)
        if not m: return "未找到 JSON。"
        try: return [it for it in json.loads(m.group(0)) if isinstance(it, dict)]
        except Exception as e: return f"JSON 解析失败: {e}"