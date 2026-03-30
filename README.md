# k3y-Iogger

An advanced keylogger built in Python, designed for educational and ethical purposes. It captures keystrokes globally across your system, logs them with millisecond-precision timestamps, and generates a clean report with both individual keystroke data and combined readable text output.

## Features

- **User Consent**: A formatted disclaimer is displayed, and the user must accept the terms (`y/Y`) before the keylogger starts.
- **Flexible Duration Input**: Supports multiple time formats:
  | Input | Duration |
  |-------|----------|
  | `30` | 30 seconds |
  | `5m` or `5 m` | 5 minutes |
  | `3.5m` | 3 minutes 30 seconds |
  | `1h` or `1 h` | 1 hour |
  | `1.5h` | 1 hour 30 minutes |
- **Live Countdown Timer**: A real-time progress bar displayed in the terminal showing:
  - Time remaining (`MM:SS` or `HH:MM:SS`)
  - Visual progress bar
  - Completion percentage
  - Live keystroke count
- **Millisecond-Precision Timestamps**: Each keystroke is logged with timestamps accurate to the millisecond.
- **Smart Key Handling**:
  - Printable characters logged as-is
  - Special keys labeled clearly: `[SPACE]`, `[ENTER]`, `[TAB]`, `[BACKSPACE]`
  - Backspace actually removes previous character from the combined text
  - Shift and modifier keys silently ignored
- **Dual-Section Log Report**:
  - **Section 1**: Individual keystroke log with precise timestamps
  - **Section 2**: Combined readable text output showing actual words and sentences
- **Global Capture**: Captures keystrokes from any application across your system — not limited to the terminal.

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/zzzastro/k3y-Iogger.git
   cd k3y-Iogger
   ```

2. Install the required Python library:
   ```bash
   pip install pynput
   ```

## Usage

1. Run the Python script:

   ```bash
   python Keylogger.py
   ```

2. Accept the disclaimer by typing `y` when prompted.

3. Enter the logging duration:

   ```
   Duration: 1m        # logs for 1 minute
   Duration: 30        # logs for 30 seconds
   Duration: 1.5h      # logs for 1 hour 30 minutes
   ```

4. Switch to any application (Notepad, browser, etc.) and start typing.

5. Watch the live countdown in the terminal:

   ```
   ⏱  01:27  │████████████░░░░░░░░░░░░░░░░░░│  52.3%  │  Keys: 47
   ```

6. Once the timer ends, the keystrokes are saved to `key_log.txt`.

## Log File Example
