"""
Ultron Supercharged Action Tools Suite
Comprehensive, Resilient OS Actuators for Windows:
Web & YouTube, Audio, Windows, Filesystem, PDF/DOCX Docs, Productivity, Lag Diagnostics, Alerts
"""

import os
import sys
import time
import socket
import zipfile
import platform
import threading
import subprocess
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

import psutil
import pyautogui
import pyperclip
import re
from urllib.parse import quote

# Audio control via pycaw with dynamic initialization
try:
    import comtypes
    from pycaw.pycaw import AudioUtilities
    HAS_PYCAW = True
except Exception:
    HAS_PYCAW = False

# PDF reader
try:
    import pypdf
    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False

# Live Web Search
try:
    from ddgs import DDGS
    HAS_DDGS = True
except ImportError:
    try:
        from duckduckgo_search import DDGS
        HAS_DDGS = True
    except ImportError:
        HAS_DDGS = False

# Thread-safe Qt application handle for instant high-DPI screenshots
try:
    from PySide6.QtWidgets import QApplication
    _QT_APP = QApplication.instance() or QApplication(sys.argv)
except Exception:
    _QT_APP = None


# ==============================================================================
# 1. WEB & SEARCH ACTUATORS
# ==============================================================================

def open_url(url: str, browser: str = "default") -> str:
    """
    Opens a website or search query in Chrome, Edge, or default browser.
    Normalizes URLs and handles browser fallback gracefully.
    """
    url_clean = url.strip()
    domain_map = {
        "github": "https://github.com",
        "github.com": "https://github.com",
        "instagram": "https://instagram.com",
        "instagram.com": "https://instagram.com",
        "youtube": "https://youtube.com",
        "youtube.com": "https://youtube.com",
        "google": "https://google.com",
        "google.com": "https://google.com",
        "twitter": "https://x.com",
        "x": "https://x.com",
        "reddit": "https://reddit.com",
        "chatgpt": "https://chatgpt.com",
        "linkedin": "https://linkedin.com",
        "whatsapp": "https://web.whatsapp.com"
    }
    target_url = domain_map.get(url_clean.lower(), url_clean)
    
    # If not a full URL, add https or convert to google search
    if not (target_url.startswith("http://") or target_url.startswith("https://")):
        if "." in target_url and not target_url.endswith(".exe"):
            target_url = "https://" + target_url
        else:
            target_url = f"https://www.google.com/search?q={target_url.replace(' ', '+')}"

    browser_clean = browser.lower().strip()
    try:
        if "chrome" in browser_clean:
            proc = subprocess.run(["powershell.exe", "-NoProfile", "-Command", f"Start-Process chrome '{target_url}' -ErrorAction Stop"], capture_output=True, text=True, timeout=5)
            if proc.returncode == 0:
                return f"Successfully opened '{target_url}' in Google Chrome."
        elif "edge" in browser_clean:
            proc = subprocess.run(["powershell.exe", "-NoProfile", "-Command", f"Start-Process msedge '{target_url}' -ErrorAction Stop"], capture_output=True, text=True, timeout=5)
            if proc.returncode == 0:
                return f"Successfully opened '{target_url}' in Microsoft Edge."
    except Exception:
        pass  # Fall back to default browser

    # Default browser launch
    try:
        subprocess.Popen(["powershell.exe", "-NoProfile", "-Command", f"Start-Process '{target_url}'"])
        return f"Successfully opened '{target_url}' in default browser."
    except Exception as e:
        return f"Error opening URL: {str(e)}"

def web_search(query: str, max_results: int = 4) -> str:
    """
    Performs a live web search for real-time information (weather, news, scores, current facts).
    """
    if not HAS_DDGS:
        return "ERROR: Web search library (ddgs) is not available."
    try:
        results = list(DDGS().text(query, max_results=max_results))
        if not results:
            return f"No search results found for query: '{query}'."
        
        output = [f"Search Results for '{query}':"]
        for i, r in enumerate(results, 1):
            title = r.get("title", "No Title").strip()
            body = r.get("body", "No description").strip()
            url = r.get("href", "")
            output.append(f"{i}. {title}\n   {body}\n   Source: {url}")
        return "\n\n".join(output)
    except Exception as e:
        return f"Web search error: {str(e)}"

def play_youtube(query: str) -> str:
    """Searches YouTube and opens the video/results directly in your browser."""
    search_term = query.replace(" ", "+")
    yt_url = f"https://www.youtube.com/results?search_query={search_term}"
    try:
        subprocess.Popen(["powershell.exe", "-NoProfile", "-Command", f"Start-Process '{yt_url}'"])
        return f"Successfully opened YouTube results for '{query}' in browser."
    except Exception as e:
        return f"Failed to open YouTube: {str(e)}"


# ==============================================================================
# 2. AUDIO & MEDIA ACTUATORS
# ==============================================================================

def control_volume(action: str, level: int = None) -> str:
    """
    Controls Windows master speaker volume dynamically with COM safety.
    action options:
      - 'set': Sets exact volume (0 to 100).
      - 'increase': Bumps volume up by level (default 10%).
      - 'decrease': Lowers volume by level (default 10%).
      - 'mute': Mutes audio.
      - 'unmute': Unmutes audio.
      - 'get': Returns current volume percentage and mute status.
    """
    if not HAS_PYCAW:
        return "ERROR: Audio endpoint controller (pycaw) is unavailable."
    
    try:
        # Initialize COM in this thread
        comtypes.CoInitialize()
        device = AudioUtilities.GetSpeakers()
        if not device:
            return "ERROR: No active audio speaker device found."
        vol = device.EndpointVolume
        
        act = action.lower().strip()
        curr_scalar = vol.GetMasterVolumeLevelScalar()
        curr_percent = int(round(curr_scalar * 100))

        if act == "mute":
            vol.SetMute(1, None)
            return "Master volume muted."
        elif act == "unmute":
            vol.SetMute(0, None)
            return f"Master volume unmuted (currently at {curr_percent}%)."
        elif act == "set":
            if level is None:
                return "ERROR: Please provide a volume percentage level (0-100)."
            scalar = max(0.0, min(1.0, float(level) / 100.0))
            vol.SetMasterVolumeLevelScalar(scalar, None)
            return f"Master volume set to {int(round(scalar * 100))}%."
        elif act in ["increase", "up"]:
            delta = float(level if level is not None else 10) / 100.0
            new_scalar = min(1.0, curr_scalar + delta)
            vol.SetMasterVolumeLevelScalar(new_scalar, None)
            return f"Master volume increased to {int(round(new_scalar * 100))}%."
        elif act in ["decrease", "down"]:
            delta = float(level if level is not None else 10) / 100.0
            new_scalar = max(0.0, curr_scalar - delta)
            vol.SetMasterVolumeLevelScalar(new_scalar, None)
            return f"Master volume decreased to {int(round(new_scalar * 100))}%."
        elif act in ["get", "check", "status"]:
            muted_str = "Muted" if vol.GetMute() else "Unmuted"
            return f"Master volume is at {curr_percent}% [{muted_str}]."
        else:
            return f"Unknown volume action '{action}'. Use 'set', 'increase', 'decrease', 'mute', 'unmute', or 'get'."
    except Exception as e:
        return f"Volume control error: {str(e)}"

def control_media(action: str) -> str:
    """
    Controls media playback:
    action options: 'play_pause', 'next', 'previous', 'stop', 'volume_up', 'volume_down'.
    """
    key_map = {
        "play_pause": "playpause", "play": "playpause", "pause": "playpause",
        "next": "nexttrack", "previous": "prevtrack", "prev": "prevtrack",
        "stop": "stop", "volume_up": "volumeup", "volume_down": "volumedown"
    }
    k = key_map.get(action.lower().strip())
    if k:
        pyautogui.press(k)
        return f"Triggered media key: {action}"
    return f"Invalid media action '{action}'. Options: play_pause, next, previous, stop."


# ==============================================================================
# 3. WINDOW & PROCESS MANAGEMENT
# ==============================================================================

def open_app(app_name: str) -> str:
    """Opens a Windows desktop program or UWP app without opening File Explorer."""
    app_clean = app_name.lower().strip()
    direct_map = {
        "calculator": "calc", "calc": "calc", "notepad": "notepad",
        "chrome": "chrome", "edge": "msedge", "spotify": "spotify",
        "terminal": "wt", "cmd": "cmd", "powershell": "powershell",
        "task manager": "taskmgr", "taskmgr": "taskmgr", "code": "code",
        "vscode": "code", "paint": "mspaint", "settings": "ms-settings:"
    }
    alias = direct_map.get(app_clean, app_clean)
    try:
        res = subprocess.run(
            ["powershell.exe", "-NoProfile", "-Command", f"Start-Process '{alias}' -ErrorAction Stop"],
            capture_output=True, text=True, timeout=5
        )
        if res.returncode == 0:
            return f"Successfully launched application '{app_name}'."
    except Exception:
        pass

    try:
        ps_find = f"Get-StartApps | Where-Object {{ $_.Name -like '*{app_name}*' }} | Select-Object -First 1 Name, AppID | ConvertTo-Json -Compress"
        res = subprocess.run(["powershell.exe", "-NoProfile", "-Command", ps_find], capture_output=True, text=True, timeout=8)
        import json
        out = res.stdout.strip()
        if out:
            data = json.loads(out)
            app_id = data.get("AppID")
            if app_id:
                subprocess.Popen(["powershell.exe", "-NoProfile", "-Command", f"Start-Process 'shell:appsFolder\\{app_id}'"])
                return f"Successfully launched '{data.get('Name', app_name)}' (AppID: {app_id})."
    except Exception:
        pass

    return f"ERROR: Could not find or launch application '{app_name}'."

def manage_windows(action: str, window_name: str = None) -> str:
    """
    Controls desktop windows:
    action options:
      - 'minimize_all' / 'show_desktop': Minimizes all windows to reveal desktop.
      - 'maximize': Maximizes the current active window.
      - 'snap_left' / 'snap_right': Snaps active window to left or right half.
      - 'focus': Focuses window matching title (e.g. 'Chrome', 'Notepad').
      - 'close': Closes window matching title or current window.
    """
    act = action.lower().strip()
    try:
        if act in ["minimize_all", "show_desktop"]:
            pyautogui.hotkey('win', 'd')
            return "Toggled desktop (minimized all open windows)."
        elif act in ["maximize", "fullscreen"]:
            pyautogui.hotkey('win', 'up')
            return "Maximized active window."
        elif act == "snap_left":
            pyautogui.hotkey('win', 'left')
            return "Snapped window to the left."
        elif act == "snap_right":
            pyautogui.hotkey('win', 'right')
            return "Snapped window to the right."
        elif act == "focus" and window_name:
            ps_focus = f"(New-Object -ComObject WScript.Shell).AppActivate('{window_name}')"
            subprocess.run(["powershell.exe", "-NoProfile", "-Command", ps_focus], capture_output=True, text=True)
            return f"Brought window matching '{window_name}' to focus."
        elif act == "close":
            if window_name:
                return kill_process(window_name)
            else:
                pyautogui.hotkey('alt', 'f4')
                return "Closed active window."
        else:
            return f"Unknown window action '{action}'. Options: minimize_all, show_desktop, maximize, snap_left, snap_right, focus, close."
    except Exception as e:
        return f"Window management error: {str(e)}"

def kill_process(process_name: str) -> str:
    """Terminates running processes matching a given name (e.g. 'notepad.exe', 'chrome')."""
    target = process_name.lower().strip()
    if not target.endswith(".exe"):
        target_exe = target + ".exe"
    else:
        target_exe = target

    killed = 0
    for p in psutil.process_iter(['name']):
        try:
            name = p.info['name'].lower()
            if name == target or name == target_exe:
                p.kill()
                killed += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    if killed > 0:
        return f"Successfully terminated {killed} instance(s) of '{process_name}'."
    return f"No running process found matching '{process_name}'."

def get_top_resource_hogs(count: int = 5) -> str:
    """Lists top CPU and RAM consuming processes to diagnose PC lag."""
    try:
        procs = []
        for p in psutil.process_iter(['name', 'cpu_percent', 'memory_percent', 'pid']):
            try:
                name = p.info['name']
                if name and p.info['memory_percent'] > 0.5:
                    procs.append((name, p.info['pid'], p.info['cpu_percent'], p.info['memory_percent']))
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        procs.sort(key=lambda x: x[3], reverse=True)
        top = procs[:count]
        lines = ["Top Resource-Consuming Processes:"]
        for name, pid, cpu, mem in top:
            lines.append(f"• {name} (PID: {pid}): {mem:.1f}% RAM, {cpu:.1f}% CPU")
        return "\n".join(lines)
    except Exception as e:
        return f"Error gathering resource hogs: {str(e)}"


# ==============================================================================
# 4. FILESYSTEM & DOCUMENT ACTUATORS
# ==============================================================================

def create_folder(folder_path: str) -> str:
    """Creates a new folder safely handling spaces and nested paths."""
    try:
        p = Path(folder_path).resolve()
        p.mkdir(parents=True, exist_ok=True)
        return f"SUCCESS: Created directory '{p.name}' at: {p}"
    except Exception as e:
        return f"ERROR creating folder '{folder_path}': {str(e)}"

def read_file(file_path: str, max_lines: int = 200) -> str:
    """Reads lines from an existing text/code file with encoding fallbacks."""
    try:
        p = Path(file_path).resolve()
        if not p.exists():
            return f"ERROR: File '{file_path}' does not exist."
        if not p.is_file():
            return f"ERROR: Path '{file_path}' is a directory."
        
        # Try UTF-8 then fallback to latin-1
        try:
            text = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = p.read_text(encoding="latin-1", errors="replace")
            
        lines = text.splitlines()
        content = "\n".join(lines[:max_lines])
        return f"File '{p.name}' ({len(lines)} lines total):\n{content}"
    except Exception as e:
        return f"ERROR reading file '{file_path}': {str(e)}"

def write_file(file_path: str, content: str, mode: str = "overwrite") -> str:
    """Writes, prepends, or appends to a file on disk."""
    try:
        p = Path(file_path).resolve()
        mode_clean = mode.lower().strip()
        existing = ""
        if p.exists() and p.is_file():
            try:
                existing = p.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                existing = p.read_text(encoding="latin-1", errors="replace")
                
        if mode_clean == "prepend":
            new_content = content.rstrip("\n") + "\n" + existing
        elif mode_clean == "append":
            new_content = existing + "\n" + content.lstrip("\n")
        else:
            new_content = content
            
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(new_content, encoding="utf-8")
        return f"SUCCESS: File '{p.name}' updated in '{mode_clean}' mode ({len(new_content)} characters)."
    except Exception as e:
        return f"ERROR writing to file '{file_path}': {str(e)}"

def list_directory(dir_path: str = ".") -> str:
    """Lists files and folders in the target directory."""
    try:
        p = Path(dir_path).resolve()
        if not p.exists():
            return f"ERROR: Directory '{dir_path}' does not exist."
        items = list(p.iterdir())
        if not items:
            return f"Directory '{p.name}' is empty."
        lines = [f"Contents of {p}:"]
        for item in sorted(items, key=lambda x: (not x.is_dir(), x.name.lower())):
            kind = "[DIR] " if item.is_dir() else "[FILE]"
            lines.append(f"  {kind} {item.name}")
        return "\n".join(lines)
    except Exception as e:
        return f"ERROR listing directory: {str(e)}"

def organize_folder(folder_path: str = "Downloads") -> str:
    """
    Cleans up and organizes a folder by categorizing files into sorted subdirectories:
    Images, Documents, Installers, Archives, Code, Media.
    Safely ignores locked files and prevents name collisions.
    """
    user_home = Path.home()
    aliases = {
        "downloads": user_home / "Downloads",
        "desktop": user_home / "Desktop",
        "documents": user_home / "Documents"
    }
    target = aliases.get(folder_path.lower().strip(), Path(folder_path).resolve())
    if not target.exists():
        return f"ERROR: Folder '{target}' does not exist."

    category_map = {
        "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg", ".ico"],
        "Documents": [".pdf", ".docx", ".doc", ".txt", ".xlsx", ".xls", ".pptx", ".csv", ".epub"],
        "Installers": [".exe", ".msi", ".dmg", ".iso"],
        "Archives": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"],
        "Media": [".mp4", ".mkv", ".avi", ".mov", ".mp3", ".wav", ".flac", ".m4a"],
        "Code": [".py", ".js", ".html", ".css", ".json", ".cpp", ".java", ".ts", ".rs", ".go"]
    }

    moved_counts = {}
    for item in list(target.iterdir()):
        if item.is_file() and not item.name.startswith("."):
            ext = item.suffix.lower()
            dest_category = "Others"
            for cat, extensions in category_map.items():
                if ext in extensions:
                    dest_category = cat
                    break
                    
            dest_dir = target / dest_category
            dest_dir.mkdir(exist_ok=True)
            dest_file = dest_dir / item.name
            
            # Avoid name collisions
            if dest_file.exists():
                stem = item.stem
                timestamp = int(time.time())
                dest_file = dest_dir / f"{stem}_{timestamp}{ext}"

            try:
                item.rename(dest_file)
                moved_counts[dest_category] = moved_counts.get(dest_category, 0) + 1
            except PermissionError:
                continue  # File is open/locked by another app
            except Exception:
                continue

    if not moved_counts:
        return f"Folder '{target.name}' is already organized or contains no files to move."
    summary = ", ".join([f"{count} in {cat}" for cat, count in moved_counts.items()])
    return f"Successfully organized {target.name}: {summary}."

def read_document(file_path: str) -> str:
    """
    Extracts text from PDF (.pdf), Word (.docx), CSV, code, or text files for reading/summarization.
    Extracts DOCX text natively without external libraries.
    """
    p = Path(file_path).resolve()
    if not p.exists():
        return f"ERROR: Document '{file_path}' not found."
    ext = p.suffix.lower()

    if ext == ".pdf":
        if not HAS_PYPDF:
            return "ERROR: pypdf is not installed."
        try:
            reader = pypdf.PdfReader(str(p))
            total_pages = len(reader.pages)
            extracted = []
            for i, page in enumerate(reader.pages[:10]):
                text = page.extract_text() or ""
                extracted.append(f"--- Page {i+1} ---\n{text.strip()}")
            return f"Extracted text from PDF '{p.name}' ({total_pages} pages total):\n" + "\n\n".join(extracted)
        except Exception as e:
            return f"Error extracting PDF: {str(e)}"
            
    elif ext == ".docx":
        try:
            with zipfile.ZipFile(str(p)) as doc:
                xml_content = doc.read('word/document.xml')
                tree = ET.fromstring(xml_content)
                paragraphs = []
                for p_node in tree.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p'):
                    texts = [node.text for node in p_node.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t') if node.text]
                    if texts:
                        paragraphs.append("".join(texts))
                return f"Extracted text from Word document '{p.name}':\n" + "\n\n".join(paragraphs[:100])
        except Exception as e:
            return f"Error reading DOCX: {str(e)}"
    else:
        return read_file(file_path, max_lines=200)


# ==============================================================================
# 5. PRODUCTIVITY, CLIPBOARD & TIMERS
# ==============================================================================

def set_timer_reminder(minutes: float, message: str) -> str:
    """
    Sets a non-blocking background timer that chimes and triggers a desktop popup alert.
    """
    seconds = max(1.0, float(minutes) * 60.0)

    def timer_worker():
        time.sleep(seconds)
        # Audible sound chime
        try:
            import winsound
            for _ in range(3):
                winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
                time.sleep(0.4)
        except Exception:
            pass
        # Desktop Toast / Message Box popup (system modal so it pops up on top)
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, message, f"Ultron Timer Finished ({minutes}m)", 0x40 | 0x1000)
        except Exception:
            pass

    thread = threading.Thread(target=timer_worker, daemon=True)
    thread.start()
    return f"Timer scheduled: will alert you in {minutes} minute(s) with message: '{message}'."

def manage_clipboard(action: str = "read", text: str = None) -> str:
    """
    Interacts with the Windows clipboard:
    action: 'read' (gets current clipboard) or 'set' (copies text into clipboard).
    """
    act = action.lower().strip()
    try:
        if act == "read":
            content = pyperclip.paste()
            return f"Current Clipboard Content:\n{content}" if content else "Clipboard is currently empty."
        elif act in ["set", "copy"]:
            if text is None:
                return "ERROR: No text provided to copy to clipboard."
            pyperclip.copy(text)
            return f"Successfully copied {len(text)} characters to Windows clipboard."
        else:
            return f"Unknown clipboard action '{action}'. Options: read, set."
    except Exception as e:
        return f"Clipboard error: {str(e)}"

def manage_notes(action: str = "read", note_text: str = None) -> str:
    """
    Manages quick notes saved in 'notes.md' on your Desktop.
    action: 'add' or 'read'.
    """
    notes_file = Path.home() / "Desktop" / "notes.md"
    act = action.lower().strip()
    if act in ["add", "write", "note"]:
        if not note_text:
            return "ERROR: No note content provided."
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        entry = f"- [{stamp}] {note_text}\n"
        with open(notes_file, "a", encoding="utf-8") as f:
            f.write(entry)
        return f"Saved note to {notes_file.name}: '{note_text}'."
    else:
        if not notes_file.exists():
            return "You have no notes saved yet (notes.md on Desktop is empty)."
        return f"Notes from {notes_file.name}:\n" + notes_file.read_text(encoding="utf-8")


# ==============================================================================
# 6. SYSTEM SPECS, SCREENSHOT & NETWORK
# ==============================================================================

def take_screenshot(filename: str = "screenshot.png") -> str:
    """Captures a screenshot of the display and saves it to Desktop."""
    save_path = Path.home() / "Desktop" / filename
    global _QT_APP
    # 1. Try PySide6 high-resolution grab (bulletproof on Windows)
    try:
        if _QT_APP is not None:
            screen = _QT_APP.primaryScreen()
            if screen:
                pixmap = screen.grabWindow(0)
                if pixmap.save(str(save_path)):
                    return f"SUCCESS: Screenshot captured and saved to: {save_path}"
    except Exception:
        pass

    # 2. Fallback to PyAutoGUI / PIL
    try:
        shot = pyautogui.screenshot()
        shot.save(str(save_path))
        return f"SUCCESS: Screenshot captured and saved to: {save_path}"
    except Exception as e:
        return f"Failed to capture screenshot: {str(e)}"

def check_network_status() -> str:
    """Checks internet connectivity, ping, and local network IP."""
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        ping_res = subprocess.run(["ping", "-n", "1", "8.8.8.8"], capture_output=True, text=True, timeout=5)
        connected = "Online" if ping_res.returncode == 0 else "Offline / Restricted"
        
        wifi_ssid = "Ethernet / Disconnected"
        wifi_res = subprocess.run(["netsh", "wlan", "show", "interfaces"], capture_output=True, text=True, timeout=5)
        for line in wifi_res.stdout.splitlines():
            if "SSID" in line and "BSSID" not in line:
                parts = line.split(":")
                if len(parts) > 1:
                    wifi_ssid = parts[1].strip()
                    break

        return (
            f"Network Status:\n"
            f"• Internet State: {connected}\n"
            f"• Connected WiFi / Network: {wifi_ssid}\n"
            f"• Local IPv4: {local_ip}\n"
            f"• Device Hostname: {hostname}"
        )
    except Exception as e:
        return f"Network check error: {str(e)}"

def get_system_configuration() -> str:
    """Returns full PC hardware specifications and OS configuration."""
    try:
        os_info = f"{platform.system()} {platform.release()} (Build {platform.version()})"
        cpu_name = platform.processor() or "Intel/AMD Processor"
        physical_cores = psutil.cpu_count(logical=False) or 2
        logical_cores = psutil.cpu_count(logical=True) or 4
        mem = psutil.virtual_memory()
        disk_c = psutil.disk_usage("C:\\")
        battery = psutil.sensors_battery()
        bat_str = f"{battery.percent}% ({'Plugged in' if battery.power_plugged else 'On Battery'})" if battery else "Desktop PC"

        return (
            f"=== Windows System Configuration ===\n"
            f"• OS: {os_info} ({platform.machine()})\n"
            f"• CPU: {cpu_name} ({physical_cores} Physical / {logical_cores} Logical Cores)\n"
            f"• RAM: {round(mem.total / (1024**3), 1)} GB Total ({round(mem.available / (1024**3), 1)} GB Available, {mem.percent}% used)\n"
            f"• Disk C: {round(disk_c.total / (1024**3), 1)} GB Total ({round(disk_c.free / (1024**3), 1)} GB Free, {disk_c.percent}% used)\n"
            f"• Battery: {bat_str}"
        )
    except Exception as e:
        return f"Error gathering specs: {str(e)}"


# ==============================================================================
# 7. TERMINAL & PYTHON FALLBACKS
# ==============================================================================

def run_terminal_command(command: str) -> str:
    """Executes a Windows PowerShell or CMD terminal command."""
    try:
        res = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", command],
            capture_output=True, text=True, timeout=35
        )
        out = res.stdout.strip()
        err = res.stderr.strip()
        parts = []
        if out:
            parts.append(f"STDOUT:\n{out}")
        if err:
            parts.append(f"STDERR:\n{err}")
        parts.append(f"EXIT_CODE: {res.returncode}")
        return "\n\n".join(parts) if (out or err) else f"Command completed with EXIT_CODE: {res.returncode} (no output)."
    except subprocess.TimeoutExpired:
        return "ERROR: Terminal command timed out after 35 seconds."
    except Exception as e:
        return f"Terminal execution error: {str(e)}"

def execute_python_code(code: str) -> str:
    """Executes arbitrary Python 3 code in a separate process."""
    try:
        res = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True, text=True, timeout=35
        )
        out = res.stdout.strip()
        err = res.stderr.strip()
        parts = []
        if out:
            parts.append(f"STDOUT:\n{out}")
        if err:
            parts.append(f"STDERR:\n{err}")
        parts.append(f"EXIT_CODE: {res.returncode}")
        return "\n\n".join(parts) if (out or err) else f"Python script completed with EXIT_CODE: {res.returncode} (no output)."
    except subprocess.TimeoutExpired:
        return "ERROR: Python execution timed out after 35 seconds."
    except Exception as e:
        return f"Python execution error: {str(e)}"


# ==============================================================================
# 8. KEYBOARD & MOUSE ACTUATORS
# ==============================================================================

def keyboard_type(text: str, paste_mode: bool = False) -> str:
    """
    Types text into the active window.
    If text contains newlines, Unicode, or paste_mode is True, pastes via clipboard for reliability.
    """
    try:
        pyautogui.FAILSAFE = False
        text_str = str(text)
        needs_paste = paste_mode or "\n" in text_str or any(ord(c) > 127 for c in text_str) or len(text_str) > 50
        if needs_paste:
            pyperclip.copy(text_str)
            time.sleep(0.05)
            pyautogui.hotkey("ctrl", "v")
            return f"Typed text via instant paste ({len(text_str)} chars)."
        else:
            pyautogui.write(text_str, interval=0.01)
            return f"Typed text: '{text_str}'."
    except Exception as e:
        return f"Keyboard type error: {str(e)}"

def keyboard_press(key: str) -> str:
    """
    Presses a single key (e.g. 'enter', 'esc', 'tab', 'backspace', 'space', 'win', 'delete', 'up', 'down').
    """
    try:
        pyautogui.FAILSAFE = False
        k = key.lower().strip()
        key_aliases = {
            "return": "enter",
            "escape": "esc",
            "windows": "win",
            "del": "delete",
            "control": "ctrl"
        }
        k = key_aliases.get(k, k)
        pyautogui.press(k)
        return f"Pressed key '{k}'."
    except Exception as e:
        return f"Keyboard press error: {str(e)}"

def keyboard_hotkey(keys: str) -> str:
    """
    Presses a combination of keys simultaneously (e.g. 'ctrl+c', 'ctrl+v', 'alt+tab', 'win+d', 'ctrl+shift+esc').
    """
    try:
        pyautogui.FAILSAFE = False
        normalized = keys.replace(",", "+").replace(" ", "")
        parts = [p.lower().strip() for p in normalized.split("+") if p.strip()]
        key_aliases = {
            "control": "ctrl",
            "windows": "win",
            "command": "win",
            "escape": "esc",
            "return": "enter",
            "del": "delete"
        }
        clean_parts = [key_aliases.get(p, p) for p in parts]
        pyautogui.hotkey(*clean_parts)
        return f"Executed hotkey: {' + '.join(clean_parts)}."
    except Exception as e:
        return f"Keyboard hotkey error: {str(e)}"

def mouse_click(button: str = "left", clicks: int = 1, x: int = None, y: int = None) -> str:
    """
    Clicks the mouse at current cursor location or specified (x, y) coordinates.
    button="left", "right", or "middle". clicks=1 (single) or 2 (double click).
    """
    try:
        pyautogui.FAILSAFE = False
        btn = button.lower().strip()
        if btn not in ["left", "right", "middle"]:
            btn = "left"
        clk_count = max(1, min(int(clicks), 3))
        if x is not None and y is not None:
            pyautogui.click(x=int(x), y=int(y), button=btn, clicks=clk_count)
            return f"Clicked {btn} button ({clk_count}x) at ({x}, {y})."
        else:
            pyautogui.click(button=btn, clicks=clk_count)
            pos = pyautogui.position()
            return f"Clicked {btn} button ({clk_count}x) at ({pos.x}, {pos.y})."
    except Exception as e:
        return f"Mouse click error: {str(e)}"

def mouse_move(x: int, y: int, duration: float = 0.2) -> str:
    """
    Smoothly moves the mouse cursor to (x, y) screen coordinates.
    """
    try:
        pyautogui.FAILSAFE = False
        target_x = int(x)
        target_y = int(y)
        pyautogui.moveTo(target_x, target_y, duration=float(duration))
        return f"Moved cursor to ({target_x}, {target_y})."
    except Exception as e:
        return f"Mouse move error: {str(e)}"

def mouse_scroll(amount: int = 5, direction: str = "down") -> str:
    """
    Scrolls the mouse wheel up or down by a given amount of clicks.
    """
    try:
        pyautogui.FAILSAFE = False
        amt = int(amount)
        clicks = amt * 100
        if direction.lower().strip() == "down":
            pyautogui.scroll(-clicks)
            return f"Scrolled down {amt} units."
        else:
            pyautogui.scroll(clicks)
            return f"Scrolled up {amt} units."
    except Exception as e:
        return f"Mouse scroll error: {str(e)}"

def mouse_drag(start_x: int, start_y: int, end_x: int, end_y: int, duration: float = 0.5) -> str:
    """
    Drags the mouse from (start_x, start_y) to (end_x, end_y).
    """
    try:
        pyautogui.FAILSAFE = False
        pyautogui.moveTo(int(start_x), int(start_y))
        time.sleep(0.05)
        pyautogui.dragTo(int(end_x), int(end_y), duration=float(duration), button="left")
        return f"Dragged from ({start_x}, {start_y}) to ({end_x}, {end_y})."
    except Exception as e:
        return f"Mouse drag error: {str(e)}"

def get_cursor_position() -> str:
    """
    Returns current mouse cursor position and screen dimensions.
    """
    try:
        pyautogui.FAILSAFE = False
        pos = pyautogui.position()
        size = pyautogui.size()
        return f"Mouse Position: X={pos.x}, Y={pos.y} | Screen Resolution: {size.width}x{size.height}"
    except Exception as e:
        return f"Cursor position error: {str(e)}"


# ==============================================================================
# 9. WHATSAPP DESKTOP AUTOMATION TOOLS
# ==============================================================================

def whatsapp_status_check() -> str:
    """
    Checks if WhatsApp is installed on Windows (UWP / desktop) and whether its process is active.
    """
    try:
        proc_found = False
        pids = []
        for p in psutil.process_iter(['name', 'pid']):
            pname = (p.info['name'] or '').lower()
            if 'whatsapp' in pname:
                proc_found = True
                pids.append(f"{p.info['name']} (PID: {p.info['pid']})")

        ps_chk = "(Get-AppxPackage *WhatsApp*).PackageFullName"
        res = subprocess.run(["powershell.exe", "-NoProfile", "-Command", ps_chk], capture_output=True, text=True, timeout=5)
        pkg = res.stdout.strip()

        status_lines = []
        if pkg:
            status_lines.append(f"WhatsApp Package: {pkg}")
        else:
            status_lines.append("WhatsApp package detected via system registry protocol.")

        if proc_found:
            status_lines.append(f"Running Processes: {', '.join(pids)}")
        else:
            status_lines.append("Process Status: Not running (can be launched on demand).")

        return " | ".join(status_lines)
    except Exception as e:
        return f"WhatsApp status check error: {str(e)}"

def whatsapp_open_app() -> str:
    """
    Launches or focuses the WhatsApp desktop application on Windows.
    """
    try:
        try:
            os.startfile("whatsapp:")
        except Exception:
            subprocess.Popen(["powershell.exe", "-NoProfile", "-Command", "Start-Process 'whatsapp:'"])
        time.sleep(1.2)

        ps_focus = "(New-Object -ComObject WScript.Shell).AppActivate('WhatsApp')"
        subprocess.run(["powershell.exe", "-NoProfile", "-Command", ps_focus], capture_output=True, text=True, timeout=5)
        return "Successfully opened and focused WhatsApp."
    except Exception as e:
        return f"WhatsApp open error: {str(e)}"

def _is_phone_number(recipient: str) -> Tuple[bool, str]:
    """Helper to determine if recipient is a phone number and clean numeric characters."""
    clean = re.sub(r'[\s\-\(\)\+]', '', recipient.strip())
    if clean.isdigit() and len(clean) >= 7:
        return True, clean
    return False, recipient.strip()

def whatsapp_open_chat(recipient: str) -> str:
    """
    Navigates to a specific chat by contact name or phone number in WhatsApp.
    """
    try:
        is_phone, clean_target = _is_phone_number(recipient)
        if is_phone:
            uri = f"whatsapp://send?phone={clean_target}"
            try:
                os.startfile(uri)
            except Exception:
                subprocess.Popen(["powershell.exe", "-NoProfile", "-Command", f"Start-Process '{uri}'"])
            time.sleep(1.5)
            subprocess.run(["powershell.exe", "-NoProfile", "-Command", "(New-Object -ComObject WScript.Shell).AppActivate('WhatsApp')"], capture_output=True, text=True, timeout=5)
            return f"Opened WhatsApp chat with phone number '{clean_target}'."
        else:
            whatsapp_open_app()
            time.sleep(0.8)
            pyautogui.FAILSAFE = False
            pyautogui.hotkey('ctrl', 'f')
            time.sleep(0.3)
            pyperclip.copy(clean_target)
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(0.8)
            pyautogui.press('enter')
            time.sleep(0.5)
            return f"Navigated to WhatsApp chat for contact '{clean_target}'."
    except Exception as e:
        return f"WhatsApp open chat error: {str(e)}"

def whatsapp_send_message(recipient: str, message: str) -> str:
    """
    Sends a WhatsApp message to a contact name or phone number.
    """
    try:
        pyautogui.FAILSAFE = False
        is_phone, clean_target = _is_phone_number(recipient)

        if is_phone:
            encoded_msg = quote(message)
            uri = f"whatsapp://send?phone={clean_target}&text={encoded_msg}"
            try:
                os.startfile(uri)
            except Exception:
                subprocess.Popen(["powershell.exe", "-NoProfile", "-Command", f"Start-Process '{uri}'"])
            time.sleep(2.0)
            subprocess.run(["powershell.exe", "-NoProfile", "-Command", "(New-Object -ComObject WScript.Shell).AppActivate('WhatsApp')"], capture_output=True, text=True, timeout=5)
            time.sleep(0.3)
            pyautogui.press('enter')
            return f"Successfully sent WhatsApp message to {clean_target}: \"{message}\""
        else:
            open_res = whatsapp_open_chat(recipient)
            if "error" in open_res.lower():
                return open_res
            time.sleep(0.5)
            pyperclip.copy(message)
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(0.2)
            pyautogui.press('enter')
            return f"Successfully sent WhatsApp message to '{recipient}': \"{message}\""
    except Exception as e:
        return f"WhatsApp send message error: {str(e)}"

def whatsapp_send_file(recipient: str, file_path: str) -> str:
    """
    Attaches and sends a file (document, image, video, audio) to a WhatsApp recipient.
    """
    try:
        pyautogui.FAILSAFE = False
        abs_path = os.path.abspath(os.path.expanduser(file_path))
        if not os.path.exists(abs_path):
            return f"ERROR: File '{file_path}' does not exist on disk."

        open_res = whatsapp_open_chat(recipient)
        if "error" in open_res.lower():
            return open_res
        time.sleep(0.8)

        ps_clip = f"Set-Clipboard -Path '{abs_path}'"
        res = subprocess.run(["powershell.exe", "-NoProfile", "-Command", ps_clip], capture_output=True, text=True, timeout=5)
        if res.returncode != 0:
            return f"ERROR: Failed to copy file to clipboard: {res.stderr}"

        subprocess.run(["powershell.exe", "-NoProfile", "-Command", "(New-Object -ComObject WScript.Shell).AppActivate('WhatsApp')"], capture_output=True, text=True, timeout=5)
        time.sleep(0.3)

        pyautogui.hotkey('ctrl', 'v')
        time.sleep(1.2)
        pyautogui.press('enter')
        return f"Successfully sent file '{os.path.basename(abs_path)}' to '{recipient}' on WhatsApp."
    except Exception as e:
        return f"WhatsApp send file error: {str(e)}"

def whatsapp_call(recipient: str, call_type: str = "voice") -> str:
    """
    Initiates a voice or video call to a contact on WhatsApp.
    """
    try:
        pyautogui.FAILSAFE = False
        call_kind = "video" if "vid" in call_type.lower() else "voice"
        open_res = whatsapp_open_chat(recipient)
        if "error" in open_res.lower():
            return open_res
        time.sleep(1.0)

        subprocess.run(["powershell.exe", "-NoProfile", "-Command", "(New-Object -ComObject WScript.Shell).AppActivate('WhatsApp')"], capture_output=True, text=True, timeout=5)
        time.sleep(0.3)

        if call_kind == "voice":
            pyautogui.hotkey('ctrl', 'shift', 'c')
        else:
            pyautogui.hotkey('ctrl', 'shift', 'v')

        return f"Initiated WhatsApp {call_kind} call to '{recipient}'."
    except Exception as e:
        return f"WhatsApp call error: {str(e)}"


# ==============================================================================
# 10. TOOL DISPATCHER & OLLAMA SCHEMAS
# ==============================================================================

TOOL_DISPATCHER = {
    "open_url": open_url,
    "web_search": web_search,
    "play_youtube": play_youtube,
    "control_volume": control_volume,
    "control_media": control_media,
    "open_app": open_app,
    "manage_windows": manage_windows,
    "kill_process": kill_process,
    "get_top_resource_hogs": get_top_resource_hogs,
    "create_folder": create_folder,
    "read_file": read_file,
    "write_file": write_file,
    "list_directory": list_directory,
    "read_directory": list_directory,
    "organize_folder": organize_folder,
    "read_document": read_document,
    "set_timer_reminder": set_timer_reminder,
    "manage_clipboard": manage_clipboard,
    "manage_notes": manage_notes,
    "take_screenshot": take_screenshot,
    "check_network_status": check_network_status,
    "get_system_configuration": get_system_configuration,
    "run_terminal_command": run_terminal_command,
    "execute_python_code": execute_python_code,
    "keyboard_type": keyboard_type,
    "keyboard_press": keyboard_press,
    "keyboard_hotkey": keyboard_hotkey,
    "mouse_click": mouse_click,
    "mouse_move": mouse_move,
    "mouse_scroll": mouse_scroll,
    "mouse_drag": mouse_drag,
    "get_cursor_position": get_cursor_position,
    "whatsapp_status_check": whatsapp_status_check,
    "whatsapp_open_app": whatsapp_open_app,
    "whatsapp_open_chat": whatsapp_open_chat,
    "whatsapp_send_message": whatsapp_send_message,
    "whatsapp_send_file": whatsapp_send_file,
    "whatsapp_call": whatsapp_call
}

TOOL_SCHEMAS_DESCRIPTION = """
Available Ultron Tools:
- open_url(url, browser): Open website. browser="chrome", "edge", or "default".
- web_search(query): Real-time live web search for weather, news, facts, current events.
- play_youtube(query): Search and open video on YouTube.
- control_volume(action, level): action="set" (level 0-100), "increase", "decrease", "mute", "unmute", "get".
- control_media(action): action="play_pause", "next", "previous", "stop".
- open_app(app_name): Launch Windows program (calc, notepad, spotify, etc.).
- manage_windows(action, window_name): action="minimize_all", "show_desktop", "maximize", "snap_left", "snap_right", "focus", "close".
- kill_process(process_name): Terminate process by name (e.g. "notepad.exe").
- get_top_resource_hogs(count): Check what apps are hogging RAM/CPU.
- create_folder(folder_path): Create directory safely (handles spaces).
- read_file(file_path): Read text/code from a file.
- write_file(file_path, content, mode): mode="overwrite", "prepend" (top of file), "append".
- list_directory(dir_path): Check files and folders in directory.
- organize_folder(folder_path): Sort files in 'Downloads' or 'Desktop' into Images, Documents, etc.
- read_document(file_path): Read/summarize PDF (.pdf), Word (.docx), or text documents.
- set_timer_reminder(minutes, message): Set a countdown timer with audible chime and desktop popup.
- manage_clipboard(action, text): action="read" or "set".
- manage_notes(action, note_text): action="add" or "read" notes on Desktop.
- take_screenshot(filename): Capture screen image to Desktop.
- check_network_status(): Check WiFi, ping, and local IP.
- get_system_configuration(): Check PC specs (OS, CPU, RAM, Disk).
- run_terminal_command(command): Run custom PowerShell command.
- execute_python_code(code): Run custom Python script.
- keyboard_type(text, paste_mode): Type or paste text into currently focused window.
- keyboard_press(key): Press key like "enter", "esc", "tab", "backspace", "space", "win".
- keyboard_hotkey(keys): Execute shortcut like "ctrl+c", "ctrl+v", "ctrl+s", "alt+tab", "win+d", "win+r".
- mouse_click(button, clicks, x, y): Click mouse ("left", "right", "middle") at current or (x, y) coords.
- mouse_move(x, y, duration): Move cursor smoothly to (x, y) coordinates.
- mouse_scroll(amount, direction): Scroll mouse wheel direction="down" or "up".
- mouse_drag(start_x, start_y, end_x, end_y): Click and drag from start to end coordinates.
- get_cursor_position(): Get current mouse X, Y position and screen resolution.
- whatsapp_status_check(): Verify WhatsApp installation and runtime status.
- whatsapp_open_app(): Open and bring WhatsApp desktop window to front.
- whatsapp_open_chat(recipient): Open chat with contact name or phone number.
- whatsapp_send_message(recipient, message): Send text message to contact or phone number.
- whatsapp_send_file(recipient, file_path): Send image/document/media file to recipient.
- whatsapp_call(recipient, call_type): Initiate "voice" or "video" call to recipient.
"""
