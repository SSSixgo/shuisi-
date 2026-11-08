import sys
import traceback
from utils.logger import _log_crash, global_exception_handler
from ui.main_window import ModernMatcherApp

sys.excepthook = global_exception_handler

if __name__ == "__main__":
    app = None
    try:
        app = ModernMatcherApp()
        app.mainloop()
    except Exception:
        _log_crash(traceback.format_exc())
        try:
            if app is not None and app.winfo_exists(): app.destroy()
        except Exception: pass
        sys.exit(1)