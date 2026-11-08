import pandas as pd
import os, tempfile, shutil, datetime
from pathlib import Path
from core.config import *

def atomic_excel_write(df, target_path):
    target = Path(target_path).resolve(); target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".water_tmp_", suffix=".xlsx", dir=str(target.parent)); os.close(fd)
    try:
        df.to_excel(tmp, index=False, engine="openpyxl")
        check = pd.read_excel(tmp)
        if list(check.columns) != list(df.columns) or len(check) != len(df): raise ValueError("临时 Excel 校验失败")
        os.replace(tmp, target)
    finally:
        try: Path(tmp).unlink(missing_ok=True)
        except OSError: pass

def validate_import_frame(df):
    missing = [c for c in IMPORT_REQUIRED_COLS if c not in df.columns]
    if missing: raise ValueError("缺少必要字段：" + "、".join(missing))
    if df.empty: raise ValueError("文件没有可导入的数据")
    df = df.copy().fillna("")
    for col in df.columns: df[col] = df[col].astype(str).str.strip().replace(["nan", "None", "NaN"], "")
    if (df[COL_MATERIAL] == "").all() and (df[COL_SPEC] == "").all(): raise ValueError("物资名称和规格特征均为空")
    if COL_PRICE in df.columns:
        raw = df[COL_PRICE].str.replace(",", "", regex=False); nonempty = raw.ne("")
        numeric = pd.to_numeric(raw.where(nonempty), errors="coerce")
        if (nonempty & numeric.isna()).any(): raise ValueError("含税单价存在非数字内容")
        df[COL_PRICE] = numeric.where(nonempty, "")
    return df