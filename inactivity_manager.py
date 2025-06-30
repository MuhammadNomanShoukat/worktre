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

def show_message_box(title, message):
    def _show():
        ctypes.windll.user32.MessageBoxW(0, message, title, 0x40 | 0x1)
    threading.Thread(target=_show, daemon=True).start()

def log(text):
    with open("inactivity.log", "a", encoding="utf-8") as f:
        f.write(text + "\n")

# === Inactivity Timer State ===
_inactivity_thread = None
_stop_flag = threading.Event()

def start_inactivity_timer(min_minutes: float, max_minutes: float, on_warn=None, on_exit=None):
    """
    Starts the inactivity monitor.
    - min_minutes: Minutes after which to show alert (0 = disable)
    - max_minutes: Minutes after which to exit app (0 = disable)
    - on_warn: Callback function for warning
    - on_exit: Callback function before exit
    """
    global _inactivity_thread, _stop_flag

    if min_minutes <= 0 and max_minutes <= 0:
        log("🚫 Inactivity monitor disabled (min=0, max=0).")
        return

    _stop_flag.clear()
    log(f"🟢 Inactivity monitor started: min={min_minutes}min, max={max_minutes}min")

    min_seconds = min_minutes * 60
    max_seconds = max_minutes * 60

    def monitor():
        warning_shown = False

        while not _stop_flag.is_set():
            idle_time = int(get_idle_duration())
            log(f"Idle for {idle_time} second(s)...")

            if max_seconds > 0 and idle_time >= max_seconds:
                log(f"⛔ Inactive for {max_minutes} minutes. Exiting.")
                if on_exit:
                    try:
                        on_exit()
                    except Exception as e:
                        log(f"Error in on_exit callback: {e}")
                show_message_box("Inactivity Timeout", f"You were inactive for {max_minutes} minutes. Exiting.")
                time.sleep(2)
                os._exit(0)

            if min_seconds > 0 and idle_time >= min_seconds and not warning_shown:
                log(f"⚠️ Warning: Inactive for {min_minutes} minutes.")
                if on_warn:
                    try:
                        on_warn()
                    except Exception as e:
                        log(f"Error in on_warn callback: {e}")
                show_message_box("Inactivity Warning", f"You have been inactive for {min_minutes} minutes.")
                warning_shown = True

            if idle_time < min_seconds:
                warning_shown = False

            time.sleep(1)

    _inactivity_thread = threading.Thread(target=monitor, daemon=True)
    _inactivity_thread.start()

def stop_inactivity_timer():
    global _stop_flag
    _stop_flag.set()
    log("🛑 Inactivity monitor stopped.")
