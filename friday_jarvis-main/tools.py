# ==============================
# STANDARD LIBRARY IMPORTS
# ==============================
import os
import platform
import subprocess
import webbrowser
import socket
import json
import logging
import time
import base64
from typing import Optional
from collections import defaultdict
from datetime import datetime, timedelta

# ==============================
# THIRD-PARTY IMPORTS
# ==============================
import psutil
import requests
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from livekit.agents import function_tool, RunContext
from langchain_community.tools import DuckDuckGoSearchRun

# ==============================
# WINDOWS-SPECIFIC IMPORTS
# ==============================
import win32gui
import win32process

# ==============================
# LG WEBOS TV
# ==============================
from pywebostv.connection import WebOSClient
import asyncio

# ==============================
# APP USAGE TRACKING
# ==============================
APP_LOG_FILE = "app_usage_log.json"

def _load_app_log():
    if os.path.exists(APP_LOG_FILE):
        with open(APP_LOG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def _save_app_log(data):
    with open(APP_LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

@function_tool()
async def track_active_application(context: RunContext) -> str:
    hwnd = win32gui.GetForegroundWindow()
    _, pid = win32process.GetWindowThreadProcessId(hwnd)
    app = psutil.Process(pid).name()

    log = _load_app_log()
    today = datetime.today().date().isoformat()
    log.setdefault(today, {})
    log[today][app] = log[today].get(app, 0) + 1
    _save_app_log(log)
    return f"Tracked usage for {app}"

@function_tool()
async def weekly_app_usage_report(context: RunContext) -> str:
    log = _load_app_log()
    cutoff = datetime.today().date() - timedelta(days=7)
    summary = defaultdict(int)

    for day, apps in log.items():
        if datetime.fromisoformat(day).date() >= cutoff:
            for app, mins in apps.items():
                summary[app] += mins

    if not summary:
        return "No usage data available."

    report = ["📊 Weekly Application Usage:"]
    for app, mins in sorted(summary.items(), key=lambda x: -x[1]):
        report.append(f"{app}: {mins} min")
    return "\n".join(report)

# ==============================
# MEMORY
# ==============================
MEMORY_FILE = "jarvis_memory.json"

def _load_memory():
    return json.load(open(MEMORY_FILE)) if os.path.exists(MEMORY_FILE) else {}

def _save_memory(data):
    json.dump(data, open(MEMORY_FILE, "w"), indent=2)

@function_tool()
async def remember(context: RunContext, key: str, value: str) -> str:
    mem = _load_memory()
    mem[key.lower()] = value
    _save_memory(mem)
    return f"Saved: {key}"

@function_tool()
async def recall(context: RunContext, key: str) -> str:
    return _load_memory().get(key.lower(), "Not found")

# ==============================
# WEATHER
# ==============================
@function_tool()
async def get_weather(context: RunContext, city: str) -> str:
    try:
        return requests.get(f"https://wttr.in/{city}?format=3", timeout=5).text
    except:
        return "Weather unavailable"

# ==============================
# WEB SEARCH
# ==============================
@function_tool()
async def search_web(context: RunContext, query: str) -> str:
    return DuckDuckGoSearchRun().run(query)

# ==============================
# EMAIL
# ==============================
@function_tool()
async def send_email(context: RunContext, to_email: str, subject: str, message: str) -> str:
    user = os.getenv("GMAIL_USER")
    pwd = os.getenv("GMAIL_APP_PASSWORD")

    msg = MIMEMultipart()
    msg["From"] = user
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(message))

    with smtplib.SMTP("smtp.gmail.com", 587) as s:
        s.starttls()
        s.login(user, pwd)
        s.send_message(msg)

    return "Email sent"

# ==============================
# SYSTEM & TIME
# ==============================
@function_tool()
async def current_time(context: RunContext) -> str:
    return datetime.now().strftime("%H:%M:%S")

@function_tool()
async def system_status(context: RunContext) -> str:
    return platform.platform()

@function_tool()
async def system_uptime(context: RunContext) -> str:
    return str(timedelta(seconds=int(time.time() - psutil.boot_time())))

@function_tool()
async def battery_status(context: RunContext) -> str:
    b = psutil.sensors_battery()
    return f"{b.percent}% {'Charging' if b.power_plugged else 'Not Charging'}"

@function_tool()
async def check_internet(context: RunContext) -> str:
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return "Internet Connected"
    except:
        return "No Internet"

@function_tool()
async def system_health_report(context: RunContext) -> str:
    return f"CPU: {psutil.cpu_percent()}% | RAM: {psutil.virtual_memory().percent}%"

# ==============================
# OS AUTOMATION
# ==============================
@function_tool()
async def open_website_or_app(context: RunContext, query: str) -> str:
    webbrowser.open(query.replace("open", "").strip())
    return "Opened"

@function_tool()
async def open_file_or_folder(context: RunContext, path: str) -> str:
    os.startfile(path)
    return "Opened"

@function_tool()
async def run_command(context: RunContext, command: str) -> str:
    subprocess.Popen(command, shell=True)
    return "Command executed"

@function_tool()
async def lock_system(context: RunContext) -> str:
    os.system("rundll32.exe user32.dll,LockWorkStation")
    return "System locked"

@function_tool()
async def volume_control(context: RunContext, level: int) -> str:
    return f"Volume set to {level}"

@function_tool()
async def take_screenshot(context: RunContext) -> str:
    import pyautogui
    pyautogui.screenshot("screenshot.png")
    return "Screenshot saved"

@function_tool()
async def read_clipboard(context: RunContext) -> str:
    import pyperclip
    return pyperclip.paste()

# ==============================
# PROCESSES
# ==============================
@function_tool()
async def running_processes(context: RunContext) -> str:
    return ", ".join(p.name() for p in psutil.process_iter())

@function_tool()
async def terminate_process(context: RunContext, name: str) -> str:
    for p in psutil.process_iter():
        if p.name().lower() == name.lower():
            p.kill()
            return "Process terminated"
    return "Not found"

# ==============================
# NETWORK
# ==============================
@function_tool()
async def ip_information(context: RunContext) -> str:
    return requests.get("https://api.ipify.org").text

# ==============================
# ADVANCED
# ==============================
# ==============================
# REAL MOUSE & KEYBOARD CONTROL
# ==============================
import pyautogui

@function_tool()
async def keyboard_mouse_control(
    context: RunContext,
    action: str,
    value: Optional[str] = None
) -> str:
    """
    Actions:
    - move x,y
    - click
    - double_click
    - right_click
    - type text
    - press key
    - scroll amount
    """

    try:
        if action == "move":
            x, y = map(int, value.split(","))
            pyautogui.moveTo(x, y, duration=0.5)

        elif action == "click":
            pyautogui.click()

        elif action == "double_click":
            pyautogui.doubleClick()

        elif action == "right_click":
            pyautogui.rightClick()

        elif action == "type":
            pyautogui.write(value, interval=0.05)

        elif action == "press":
            pyautogui.press(value)

        elif action == "scroll":
            pyautogui.scroll(int(value))

        else:
            return "Unknown mouse/keyboard action."

        return f"Action executed: {action}"

    except Exception as e:
        return f"Mouse/Keyboard error: {e}"


@function_tool()
async def login_with_gmail(context: RunContext, website: str) -> str:
    webbrowser.open(f"https://{website}.com")
    return f"Opening {website}"

@function_tool()
async def restart_system(context: RunContext) -> str:
    os.system("shutdown /r /t 5")
    return "Restarting"

@function_tool()
async def shutdown_system(context: RunContext) -> str:
    os.system("shutdown /s /t 5")
    return "Shutting down"

# ==============================
# LG TV
# ==============================
TV_IP = "192.168.1.100"
tv = WebOSClient(TV_IP)
_registered = False

async def _register_tv():
    global _registered
    if not _registered:
        for _ in tv.register():
            pass
        _registered = True

@function_tool()
async def tv_play_video(context: RunContext, query: str) -> str:
    await _register_tv()
    tv.launch_app("com.webos.app.youtube")
    tv.send_text(query)
    tv.enter()
    return f"Playing {query} on TV"

@function_tool()
async def play_music(context: RunContext, song: str) -> str:
    """
    Plays music on YouTube using Google Chrome explicitly.
    """
    if not song:
        song = "music"

    query = song.replace(" ", "+")
    url = f"https://www.youtube.com/results?search_query={query}"

    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
    ]

    for chrome in chrome_paths:
        if os.path.exists(chrome):
            subprocess.Popen([chrome, url])
            return f"Playing '{song}' on YouTube (Chrome)."

    return "Google Chrome not found on this system."


# ==============================
# IMAGE GENERATION
# ==============================
# ==============================
# GEMINI IMAGE GENERATION
# ==============================
import google.genai as genai
from PIL import Image
import io

@function_tool()
async def generate_image(context: RunContext, prompt: str) -> str:
    if not prompt:
        return "Prompt is required."

    try:
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

        model = genai.GenerativeModel("imagen-3.0-generate-001")

        result = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "image/png"}
        )

        image_bytes = result.candidates[0].content.parts[0].data
        image = Image.open(io.BytesIO(image_bytes))

        file_name = f"gemini_image_{int(time.time())}.png"
        image.save(file_name)

        return f"Image generated successfully: {file_name}"

    except Exception as e:
        return f"Gemini image generation failed: {e}"


# ==============================
# WHATSAPP AUTOMATION
# ==============================
@function_tool()
async def send_whatsapp_message(context: RunContext, phone: str, message: str) -> str:
    """
    Sends a text message using WhatsApp Web.
    Phone format: countrycode+number (example: 919876543210)
    """
    try:
        url = f"https://web.whatsapp.com/send?phone={phone}&text={message}"
        webbrowser.open(url)
        time.sleep(15)  # Wait for load
        
        import pyautogui
        pyautogui.press("enter") # Send message
        
        return "Message sent via WhatsApp"
    except Exception as e:
        return f"WhatsApp send failed: {e}"

@function_tool()
async def send_whatsapp_image(context: RunContext, phone: str, image_path: str, message: str = "") -> str:
    """
    Sends an image using WhatsApp Web.
    Phone format: countrycode+number (example: 919876543210)
    """

    if not os.path.exists(image_path):
        return "Image file not found."

    try:
        url = f"https://web.whatsapp.com/send?phone={phone}&text={message}"
        webbrowser.open(url)

        time.sleep(15)  # Wait for WhatsApp Web to load

        import pyautogui

        # Click attach button (paperclip)
        pyautogui.click(1350, 680)
        time.sleep(1)

        # Click image option
        pyautogui.click(1350, 610)
        time.sleep(1)

        # Type image path
        pyautogui.write(os.path.abspath(image_path))
        pyautogui.press("enter")

        time.sleep(3)
        pyautogui.press("enter")  # Send

        return "Image sent via WhatsApp successfully."

    except Exception as e:
        return f"WhatsApp send failed: {e}"

# ==============================
# PHONE AUTOMATION
# ==============================
@function_tool()
async def unlock_phone(context: RunContext, password: str = "072016") -> str:
    """
    Unlocks an Android phone connected via USB (Type-C) using ADB.
    Default password is '072016'.
    Requires ADB to be installed and in the system PATH.
    """
    try:
        # Check for connected devices
        result = subprocess.run(["adb", "devices"], capture_output=True, text=True)
        if "device" not in result.stdout.replace("List of devices attached", ""):
            return "No device connected via ADB. Please ensure USB Debugging is enabled."

        # Wake up the screen (KEYCODE_WAKEUP)
        subprocess.run(["adb", "shell", "input", "keyevent", "224"])
        time.sleep(1)

        # Swipe up to dismiss lock screen overlay
        subprocess.run(["adb", "shell", "input", "swipe", "500", "1500", "500", "500"])
        time.sleep(1)

        # Enter the password
        subprocess.run(["adb", "shell", "input", "text", password])
        time.sleep(0.5)

        # Press Enter to confirm (KEYCODE_ENTER)
        subprocess.run(["adb", "shell", "input", "keyevent", "66"])

        return f"Unlock command sent with password {password}"

    except FileNotFoundError:
        return "ADB executable not found. Please install Android Platform Tools."
    except Exception as e:
        return f"Error unlocking phone: {e}"


# ==============================
# FILE SYSTEM CONTROL
# ==============================
@function_tool()
async def create_file(context: RunContext, path: str, content: str = "") -> str:
    """
    Creates a new file with optional content.
    """
    try:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"File created: {path}"
    except Exception as e:
        return f"Failed to create file: {e}"

@function_tool()
async def read_file(context: RunContext, path: str) -> str:
    """
    Reads and returns the content of a file.
    """
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content[:500] + ("..." if len(content) > 500 else "")  # Limit output
    except Exception as e:
        return f"Failed to read file: {e}"

@function_tool()
async def delete_file(context: RunContext, path: str) -> str:
    """
    Deletes a file or folder.
    """
    try:
        if os.path.isfile(path):
            os.remove(path)
            return f"File deleted: {path}"
        elif os.path.isdir(path):
            import shutil
            shutil.rmtree(path)
            return f"Folder deleted: {path}"
        else:
            return "Path not found"
    except Exception as e:
        return f"Delete failed: {e}"

@function_tool()
async def rename_file(context: RunContext, old_path: str, new_path: str) -> str:
    """
    Renames or moves a file/folder.
    """
    try:
        os.rename(old_path, new_path)
        return f"Renamed: {old_path} -> {new_path}"
    except Exception as e:
        return f"Rename failed: {e}"

@function_tool()
async def list_directory(context: RunContext, path: str = ".") -> str:
    """
    Lists all files and folders in a directory.
    """
    try:
        items = os.listdir(path)
        if len(items) > 50:
            return f"Found {len(items)} items. First 50: " + ", ".join(items[:50])
        return ", ".join(items)
    except Exception as e:
        return f"Failed to list directory: {e}"

@function_tool()
async def create_folder(context: RunContext, path: str) -> str:
    """
    Creates a new folder.
    """
    try:
        os.makedirs(path, exist_ok=True)
        return f"Folder created: {path}"
    except Exception as e:
        return f"Failed to create folder: {e}"


# ==============================
# WINDOW MANAGEMENT
# ==============================
@function_tool()
async def get_active_window(context: RunContext) -> str:
    """
    Returns the title of the currently active window.
    """
    try:
        hwnd = win32gui.GetForegroundWindow()
        return win32gui.GetWindowText(hwnd)
    except Exception as e:
        return f"Failed to get active window: {e}"

@function_tool()
async def minimize_window(context: RunContext) -> str:
    """
    Minimizes the currently active window.
    """
    try:
        import pyautogui
        pyautogui.hotkey('win', 'down')
        return "Window minimized"
    except Exception as e:
        return f"Failed to minimize: {e}"

@function_tool()
async def maximize_window(context: RunContext) -> str:
    """
    Maximizes the currently active window.
    """
    try:
        import pyautogui
        pyautogui.hotkey('win', 'up')
        return "Window maximized"
    except Exception as e:
        return f"Failed to maximize: {e}"

@function_tool()
async def close_active_window(context: RunContext) -> str:
    """
    Closes the currently active window.
    """
    try:
        import pyautogui
        pyautogui.hotkey('alt', 'f4')
        return "Window closed"
    except Exception as e:
        return f"Failed to close window: {e}"

@function_tool()
async def switch_window(context: RunContext) -> str:
    """
    Switches to the next window (Alt+Tab).
    """
    try:
        import pyautogui
        pyautogui.hotkey('alt', 'tab')
        return "Switched window"
    except Exception as e:
        return f"Failed to switch window: {e}"


# ==============================
# CLIPBOARD CONTROL
# ==============================
@function_tool()
async def copy_to_clipboard(context: RunContext, text: str) -> str:
    """
    Copies text to the clipboard.
    """
    try:
        import pyperclip
        pyperclip.copy(text)
        return f"Copied to clipboard: {text[:50]}..."
    except Exception as e:
        return f"Failed to copy: {e}"


# ==============================
# POWER MANAGEMENT
# ==============================
@function_tool()
async def sleep_system(context: RunContext) -> str:
    """
    Puts the system to sleep.
    """
    try:
        os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
        return "System going to sleep"
    except Exception as e:
        return f"Failed to sleep: {e}"

@function_tool()
async def hibernate_system(context: RunContext) -> str:
    """
    Hibernates the system.
    """
    try:
        os.system("shutdown /h")
        return "System hibernating"
    except Exception as e:
        return f"Failed to hibernate: {e}"


# ==============================
# BRIGHTNESS CONTROL
# ==============================
@function_tool()
async def set_brightness(context: RunContext, level: int) -> str:
    """
    Sets screen brightness (0-100).
    """
    try:
        if not (0 <= level <= 100):
            return "Brightness must be between 0 and 100"
        
        import screen_brightness_control as sbc
        sbc.set_brightness(level)
        return f"Brightness set to {level}%"
    except Exception as e:
        return f"Brightness control failed: {e}"


# ==============================
# WIFI CONTROL
# ==============================
@function_tool()
async def list_wifi_networks(context: RunContext) -> str:
    """
    Lists available Wi-Fi networks.
    """
    try:
        result = subprocess.run(
            ["netsh", "wlan", "show", "networks"],
            capture_output=True,
            text=True
        )
        networks = []
        for line in result.stdout.split('\n'):
            if "SSID" in line and "BSSID" not in line:
                ssid = line.split(":")[-1].strip()
                if ssid:
                    networks.append(ssid)
        return "Available networks: " + ", ".join(networks[:10])
    except Exception as e:
        return f"Failed to list Wi-Fi networks: {e}"

@function_tool()
async def connect_wifi(context: RunContext, ssid: str) -> str:
    """
    Connects to a Wi-Fi network by name.
    """
    try:
        subprocess.run(["netsh", "wlan", "connect", f"name={ssid}"])
        return f"Connecting to {ssid}"
    except Exception as e:
        return f"Failed to connect to Wi-Fi: {e}"

@function_tool()
async def disconnect_wifi(context: RunContext) -> str:
    """
    Disconnects from current Wi-Fi network.
    """
    try:
        subprocess.run(["netsh", "wlan", "disconnect"])
        return "Disconnected from Wi-Fi"
    except Exception as e:
        return f"Failed to disconnect: {e}"


# ==============================
# DISK & STORAGE INFO
# ==============================
@function_tool()
async def disk_usage(context: RunContext, path: str = "C:\\") -> str:
    """
    Shows disk usage for a given drive.
    """
    try:
        usage = psutil.disk_usage(path)
        total_gb = usage.total / (1024**3)
        used_gb = usage.used / (1024**3)
        free_gb = usage.free / (1024**3)
        return f"{path} - Total: {total_gb:.1f}GB | Used: {used_gb:.1f}GB | Free: {free_gb:.1f}GB ({usage.percent}% used)"
    except Exception as e:
        return f"Failed to get disk usage: {e}"


# ==============================
# NOTIFICATION CONTROL
# ==============================
@function_tool()
async def show_notification(context: RunContext, title: str, message: str) -> str:
    """
    Shows a Windows notification.
    """
    try:
        from win10toast import ToastNotifier
        toaster = ToastNotifier()
        toaster.show_toast(title, message, duration=5, threaded=True)
        return "Notification displayed"
    except Exception as e:
        return f"Notification failed: {e}"


# ==============================
# CLIPBOARD HISTORY
# ==============================
@function_tool()
async def open_clipboard_history(context: RunContext) -> str:
    """
    Opens Windows clipboard history (Win+V).
    """
    try:
        import pyautogui
        pyautogui.hotkey('win', 'v')
        return "Clipboard history opened"
    except Exception as e:
        return f"Failed to open clipboard history: {e}"


# ==============================
# TASK SCHEDULER
# ==============================
@function_tool()
async def schedule_task(context: RunContext, task_name: str, command: str, time: str) -> str:
    """
    Schedules a task using Windows Task Scheduler.
    Time format: HH:MM (24-hour format)
    """
    try:
        cmd = f'schtasks /create /sc once /tn "{task_name}" /tr "{command}" /st {time} /f'
        subprocess.run(cmd, shell=True)
        return f"Task '{task_name}' scheduled for {time}"
    except Exception as e:
        return f"Failed to schedule task: {e}"


# ==============================
# ENHANCED CMD/POWERSHELL CONTROL
# ==============================
@function_tool()
async def execute_powershell(context: RunContext, command: str) -> str:
    """
    Executes a PowerShell command and returns the output.
    Full access to PowerShell capabilities.
    """
    try:
        result = subprocess.run(
            ["powershell", "-Command", command],
            capture_output=True,
            text=True,
            timeout=30
        )
        output = result.stdout.strip()
        if result.stderr:
            output += f"\nError: {result.stderr.strip()}"
        return output[:1000] if output else "Command executed successfully (no output)"
    except subprocess.TimeoutExpired:
        return "Command timed out after 30 seconds"
    except Exception as e:
        return f"PowerShell execution failed: {e}"

@function_tool()
async def execute_cmd(context: RunContext, command: str) -> str:
    """
    Executes a CMD command and returns the output.
    Full access to Windows Command Prompt.
    """
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        output = result.stdout.strip()
        if result.stderr:
            output += f"\nError: {result.stderr.strip()}"
        return output[:1000] if output else "Command executed successfully (no output)"
    except subprocess.TimeoutExpired:
        return "Command timed out after 30 seconds"
    except Exception as e:
        return f"CMD execution failed: {e}"


# ==============================
# NETWORK SCANNING & CONTROL
# ==============================
@function_tool()
async def scan_network_devices(context: RunContext) -> str:
    """
    Scans the local network to find all connected devices.
    Shows IP addresses, MAC addresses, and hostnames.
    """
    try:
        # Get the local network IP range
        result = subprocess.run(
            ["arp", "-a"],
            capture_output=True,
            text=True
        )
        
        devices = []
        lines = result.stdout.split('\n')
        
        for line in lines:
            # Parse ARP table entries
            if 'dynamic' in line.lower() or 'static' in line.lower():
                parts = line.split()
                if len(parts) >= 2:
                    ip = parts[0]
                    mac = parts[1] if len(parts) > 1 else "Unknown"
                    devices.append(f"IP: {ip} | MAC: {mac}")
        
        if not devices:
            return "No devices found on network"
        
        device_count = len(devices)
        device_list = "\n".join(devices[:20])  # Limit to 20 devices
        
        return f"Found {device_count} devices on network:\n{device_list}"
    
    except Exception as e:
        return f"Network scan failed: {e}"

@function_tool()
async def get_detailed_network_info(context: RunContext) -> str:
    """
    Gets detailed information about network connections, adapters, and routing.
    """
    try:
        # Get network adapter info
        result = subprocess.run(
            ["ipconfig", "/all"],
            capture_output=True,
            text=True
        )
        
        output = result.stdout[:1500]  # Limit output
        return f"Network Configuration:\n{output}"
    
    except Exception as e:
        return f"Failed to get network info: {e}"

@function_tool()
async def get_active_connections(context: RunContext) -> str:
    """
    Lists all active network connections (TCP/UDP).
    Shows which applications are connected to the internet.
    """
    try:
        result = subprocess.run(
            ["netstat", "-ano"],
            capture_output=True,
            text=True
        )
        
        lines = result.stdout.split('\n')
        connections = []
        
        for line in lines[4:30]:  # Get first 26 connections (skip header)
            if line.strip():
                connections.append(line.strip())
        
        return "Active Network Connections:\n" + "\n".join(connections)
    
    except Exception as e:
        return f"Failed to get connections: {e}"

@function_tool()
async def block_device_on_network(context: RunContext, ip_address: str) -> str:
    """
    Blocks a device from accessing the internet via Windows Firewall.
    Requires administrator privileges.
    """
    try:
        # Create firewall rule to block IP
        rule_name = f"BlockDevice_{ip_address.replace('.', '_')}"
        cmd = f'netsh advfirewall firewall add rule name="{rule_name}" dir=out action=block remoteip={ip_address}'
        
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if "Ok." in result.stdout or "successfully" in result.stdout.lower():
            return f"Device {ip_address} blocked via firewall"
        else:
            return f"Failed to block device: {result.stdout}"
    
    except Exception as e:
        return f"Block failed: {e}"

@function_tool()
async def unblock_device_on_network(context: RunContext, ip_address: str) -> str:
    """
    Unblocks a previously blocked device.
    """
    try:
        rule_name = f"BlockDevice_{ip_address.replace('.', '_')}"
        cmd = f'netsh advfirewall firewall delete rule name="{rule_name}"'
        
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if "Ok." in result.stdout or "successfully" in result.stdout.lower():
            return f"Device {ip_address} unblocked"
        else:
            return f"Failed to unblock: {result.stdout}"
    
    except Exception as e:
        return f"Unblock failed: {e}"

@function_tool()
async def port_scan(context: RunContext, ip_address: str, ports: str = "80,443,22,21,3389") -> str:
    """
    Scans specific ports on a target IP address.
    Default ports: 80 (HTTP), 443 (HTTPS), 22 (SSH), 21 (FTP), 3389 (RDP)
    """
    try:
        import socket
        
        port_list = [int(p.strip()) for p in ports.split(',')]
        results = []
        
        for port in port_list:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            
            result = sock.connect_ex((ip_address, port))
            
            if result == 0:
                results.append(f"Port {port}: OPEN")
            else:
                results.append(f"Port {port}: CLOSED")
            
            sock.close()
        
        return f"Port scan for {ip_address}:\n" + "\n".join(results)
    
    except Exception as e:
        return f"Port scan failed: {e}"

@function_tool()
async def get_router_info(context: RunContext) -> str:
    """
    Gets information about the router/gateway.
    """
    try:
        # Get default gateway
        result = subprocess.run(
            ["ipconfig"],
            capture_output=True,
            text=True
        )
        
        gateway = "Unknown"
        for line in result.stdout.split('\n'):
            if "Default Gateway" in line or "gateway" in line.lower():
                parts = line.split(':')
                if len(parts) > 1:
                    gateway = parts[1].strip()
                    if gateway:
                        break
        
        return f"Router/Gateway: {gateway}"
    
    except Exception as e:
        return f"Failed to get router info: {e}"

@function_tool()
async def network_bandwidth_usage(context: RunContext) -> str:
    """
    Shows network bandwidth usage statistics.
    """
    try:
        net_io = psutil.net_io_counters()
        
        bytes_sent = net_io.bytes_sent / (1024**2)  # Convert to MB
        bytes_recv = net_io.bytes_recv / (1024**2)
        
        return f"Network Usage:\nSent: {bytes_sent:.2f} MB\nReceived: {bytes_recv:.2f} MB"
    
    except Exception as e:
        return f"Failed to get bandwidth usage: {e}"

@function_tool()
async def flush_dns(context: RunContext) -> str:
    """
    Flushes the DNS cache.
    """
    try:
        result = subprocess.run(
            ["ipconfig", "/flushdns"],
            capture_output=True,
            text=True
        )
        return "DNS cache flushed successfully"
    except Exception as e:
        return f"Failed to flush DNS: {e}"

@function_tool()
async def renew_ip_address(context: RunContext) -> str:
    """
    Releases and renews the IP address (ipconfig /release & /renew).
    """
    try:
        subprocess.run(["ipconfig", "/release"], capture_output=True)
        time.sleep(2)
        subprocess.run(["ipconfig", "/renew"], capture_output=True)
        return "IP address renewed successfully"
    except Exception as e:
        return f"Failed to renew IP: {e}"

@function_tool()
async def ping_device(context: RunContext, target: str) -> str:
    """
    Pings a device or website to check connectivity.
    """
    try:
        result = subprocess.run(
            ["ping", "-n", "4", target],
            capture_output=True,
            text=True
        )
        
        # Extract key info
        lines = result.stdout.split('\n')
        relevant = [l for l in lines if 'Reply' in l or 'Lost' in l or 'Average' in l]
        
        return "\n".join(relevant[:10])
    except Exception as e:
        return f"Ping failed: {e}"

@function_tool()
async def trace_route(context: RunContext, target: str) -> str:
    """
    Traces the network route to a target (traceroute).
    """
    try:
        result = subprocess.run(
            ["tracert", "-h", "15", target],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        return result.stdout[:1500]  # Limit output
    except subprocess.TimeoutExpired:
        return "Trace route timed out"
    except Exception as e:
        return f"Trace route failed: {e}"

@function_tool()
async def get_network_speed(context: RunContext) -> str:
    """
    Gets current network adapter speed/link speed.
    """
    try:
        result = subprocess.run(
            ["powershell", "-Command", "Get-NetAdapter | Select-Object Name, Status, LinkSpeed"],
            capture_output=True,
            text=True
        )
        
        return result.stdout[:500]
    except Exception as e:
        return f"Failed to get network speed: {e}"

@function_tool()
async def control_network_adapter(context: RunContext, action: str) -> str:
    """
    Enables or disables network adapter.
    Actions: 'enable' or 'disable'
    """
    try:
        if action.lower() == 'disable':
            cmd = 'netsh interface set interface "Wi-Fi" disable'
        elif action.lower() == 'enable':
            cmd = 'netsh interface set interface "Wi-Fi" enable'
        else:
            return "Invalid action. Use 'enable' or 'disable'"
        
        subprocess.run(cmd, shell=True)
        return f"Network adapter {action}d"
    except Exception as e:
        return f"Failed to {action} adapter: {e}"



