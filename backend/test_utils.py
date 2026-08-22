import logging
import sys

class CriticalFallbackHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.fallback_occurred = False
        self.fallback_logs = []

    def emit(self, record):
        log_entry = self.format(record)
        if "CRITICAL" in record.levelname or "fell back to _LOCAL_STORE" in record.getMessage():
            self.fallback_occurred = True
            self.fallback_logs.append(record.getMessage())

_fallback_handler = None

def setup_strict_fallback_listener():
    global _fallback_handler
    _fallback_handler = CriticalFallbackHandler()
    logger = logging.getLogger("hospital_app.supabase")
    logger.addHandler(_fallback_handler)

def assert_no_local_fallback():
    global _fallback_handler
    if _fallback_handler and _fallback_handler.fallback_occurred:
        print("\n" + "!" * 75)
        print("FAIL: Detected Local Store Fallback in Test Run!")
        for log in _fallback_handler.fallback_logs:
            print(f" -> {log}")
        print("!" * 75)
        raise AssertionError(f"Test run failed due to {len(_fallback_handler.fallback_logs)} _LOCAL_STORE fallback events!")
