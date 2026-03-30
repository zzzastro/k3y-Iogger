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

<br>
<br>

## Prerequisites (Fresh PC Setup)

If you're on a fresh Windows machine, follow these steps to get everything ready.

### 1. Install winget (Windows Package Manager)

> Most Windows 10 (1709+) and Windows 11 machines already have winget installed.

Check if you have it:

```powershell
winget --version
```

If it's not installed, run this in PowerShell as Administrator:

```powershell
Invoke-WebRequest -Uri "https://aka.ms/getwinget" -OutFile "$env:TEMP\winget.msixbundle"
Add-AppxPackage -Path "$env:TEMP\winget.msixbundle"
```

Or install it manually from the Microsoft Store — App Installer.

### 2. Install Python & pip

Python includes pip by default. Install it via winget:

```bash
winget install Python.Python.3.12
```

Close and reopen your terminal, then verify:

```bash
python --version
pip --version
```

<br>
<br>

⚠️ Important: After installing Python, you must close and reopen your terminal for the python and pip commands to be recognized.

<br>
<br>

Optional: Install via Chocolatey
If you prefer Chocolatey as your package manager:

### 1. Install Chocolatey (run in PowerShell as Administrator):

```powershell
Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
```

### 2. Install Python via Chocolatey:

```bash
choco install python -y
```

### 3. Close and reopen your terminal, then verify:

```bash
python --version
pip --version
```

<br>
<br>

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

## Disclaimer

This keylogger is intended for **ethical and educational purposes only**. You must have explicit permission to use this software on any device or system. Unauthorized use can violate laws and privacy regulations. The author is not responsible for any misuse of this software.
