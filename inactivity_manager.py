import ctypes
import time
import threading
import os

class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]

def get_idle_duration():
    lii = LASTINPUTINFO()
    lii.cbSize = ctypes.sizeof(lii)
    ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii))
    millis = ctypes.windll.kernel32.GetTickCount() - lii.dwTime
    return millis / 1000.0

def get_log_file_path():
    log_dir = os.path.join(os.getenv("APPDATA"), "MyAppLogs")
    os.makedirs(log_dir, exist_ok=True)
    return os.path.join(log_dir, "inactivity.log")

def log(text):
    try:
        log_file = get_log_file_path()
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(text + "\n")
    except Exception as e:
        print(f"[Logging Error] {e}")

# === Global State ===
_inactivity_thread = None
_stop_flag = threading.Event()
_reset_flag = threading.Event()
_lock_after_min = False
_locked_time_start = None  # When inactivity was marked

def start_inactivity_timer(min_minutes: float, max_minutes: float, on_warn=None, on_exit=None):
    global _inactivity_thread, _stop_flag, _reset_flag, _lock_after_min, _locked_time_start

    _stop_flag.clear()
    _reset_flag.clear()
    _lock_after_min = False
    _locked_time_start = None

    min_seconds = min_minutes * 60
    max_seconds = max_minutes * 60

    log(f"Inactivity monitor started: min={min_minutes}min, max={max_minutes}min")

    def monitor():
        global _lock_after_min, _locked_time_start

        while not _stop_flag.is_set():
            idle_time = get_idle_duration()
            log(f"Idle for {int(idle_time)}s | Locked: {_lock_after_min}")

            # ✅ Once locked (after min), count time until max is hit
            if _lock_after_min:
                if _locked_time_start is None:
                    _locked_time_start = time.time()
                    log("Inactivity marked. Tracking max time from now.")

                elapsed_since_lock = time.time() - _locked_time_start

                if elapsed_since_lock >= (max_seconds - min_seconds):
                    log("Maximum inactivity time reached. Exiting.")
                    if on_exit:
                        try: on_exit()
                        except Exception as e: log(f"Error in on_exit callback: {e}")
                    time.sleep(1)
                    os._exit(0)

            # ✅ First time reaching min — lock inactivity state
            if idle_time >= min_seconds and not _lock_after_min:
                log(f"Minimum inactivity reached ({min_minutes}m). Locking timer.")
                _lock_after_min = True
                _locked_time_start = time.time()
                if on_warn:
                    try: on_warn()
                    except Exception as e: log(f"Error in on_warn callback: {e}")

            # ✅ Manual reset
            if _reset_flag.is_set():
                log("Manual reset called. Unlocking inactivity state.")
                _reset_flag.clear()
                _lock_after_min = False
                _locked_time_start = None

            # ✅ If not yet locked and user active, reset inactivity clock (implicitly via OS idle time)
            if not _lock_after_min and idle_time < min_seconds:
                log("User activity detected before min. Timer stays fresh.")

            time.sleep(1)

    _inactivity_thread = threading.Thread(target=monitor, daemon=True)
    _inactivity_thread.start()

def stop_inactivity_timer():
    _stop_flag.set()
    log("Inactivity monitor stopped.")

def reset_idle_timer():
    """
    Reset the locked inactivity state, only works after min is exceeded.
    """
    global _reset_flag
    _reset_flag.set()
