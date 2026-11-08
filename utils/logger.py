import logging, datetime, traceback, os, sys
from logging.handlers import RotatingFileHandler
from core.config import BASE_DIR

_LOG_PATH = None
def _setup_logging() -> logging.Logger:
    global _LOG_PATH
    logger = logging.getLogger("shuisi")
    if _LOG_PATH is not None: return logger
    try:
        _LOG_PATH = BASE_DIR / "app.log"
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            fh = RotatingFileHandler(_LOG_PATH, maxBytes=5*1024*1024, backupCount=3, encoding="utf-8")
            fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
            logger.addHandler(fh)
    except Exception: pass
    return logger
logger = _setup_logging()

def _log_crash(exc_text):
    try:
        with open(BASE_DIR / "crash.log", "a", encoding="utf-8") as f:
            f.write(f"\n===== {datetime.datetime.now()} =====\n{exc_text}\n")
    except Exception: pass
    try: logger.error(exc_text)
    except Exception: pass

def global_exception_handler(exc_type, exc_value, exc_traceback):
    from tkinter import messagebox
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback); return
    tb = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    _log_crash(tb)
    try: messagebox.showerror("程序崩溃", f"捕获到未处理异常：\n{exc_value}\n\n详情已写入 crash.log")
    except Exception: pass