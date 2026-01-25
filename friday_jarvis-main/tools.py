import logging
import os
import requests
import smtplib
import subprocess
import datetime
import psutil
import socket
import json
import webbrowser
import platform
import pyautogui
import pyperclip

from typing import Optional
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from livekit.agents import function_tool, RunContext
from langchain_community.tools import DuckDuckGoSearchRun

# ------------------------------
# MEMORY (FRIDAY STYLE)
# ------------------------------

MEMORY_FILE = "jarvis_memory.json"

def _load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    return {}

def _save_memory(data):
    with open(MEMORY_FILE, "w") as f:
        json.dump(data, f, indent=2)

# ------------------------------
# WEATHER
# ------------------------------

@function_tool()
async def get_weather(context: RunContext, city: str) -> str:
    try:
        r = requests.get(f"https://wttr.in/{city}?format=3", timeout=5)
        return r.text.strip() if r.status_code == 200 else "Weather unavailable."
    except Exception:
        return "Weather service unavailable."

# ------------------------------
# WEB SEARCH
# ------------------------------

@function_tool()
async def search_web(context: RunContext, query: str) -> str:
    try:
        return DuckDuckGoSearchRun().run(tool_input=query)
    except Exception:
        return "Web search failed."

# ------------------------------
# EMAIL
# ------------------------------

@function_tool()
async def send_email(
    context: RunContext,
    to_email: str,
    subject: str,
    message: str,
    cc_email: Optional[str] = None
) -> str:

    gmail_user = os.getenv("GMAIL_USER")
    gmail_password = os.getenv("GMAIL_APP_PASSWORD")

    if not gmail_user or not gmail_password:
        return "Email credentials are not configured."

    try:
        msg = MIMEMultipart()
        msg["From"] = gmail_user
        msg["To"] = to_email
        msg["Subject"] = subject

        recipients = [to_email]
        if cc_email:
            msg["Cc"] = cc_email
            recipients.append(cc_email)

        msg.attach(MIMEText(message, "plain"))

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(gmail_user, gmail_password)
        server.sendmail(gmail_user, recipients, msg.as_string())
        server.quit()

        return "Email sent successfully."
    except Exception:
        return "Email sending failed."

# ------------------------------
# SYSTEM STATUS
# ------------------------------

@function_tool()
async def system_status(context: RunContext) -> str:
    return (
        f"CPU {psutil.cpu_percent()}%, "
        f"Memory {psutil.virtual_memory().percent}%, "
        f"Disk {psutil.disk_usage('/').percent}%."
    )

# ------------------------------
# INTERNET CHECK
# ------------------------------

@function_tool()
async def check_internet(context: RunContext) -> str:
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return "Internet connection is active."
    except OSError:
        return "No internet connection detected."

# ------------------------------
# TIME
# ------------------------------

@function_tool()
async def current_time(context: RunContext) -> str:
    return datetime.datetime.now().strftime(
        "It is %I:%M %p on %A, %d %B %Y."
    )

# ------------------------------
# MEMORY
# ------------------------------

@function_tool()
async def remember(context: RunContext, key: str, value: str) -> str:
    memory = _load_memory()
    memory[key.lower()] = value
    _save_memory(memory)
    return f"I will remember that {key} is {value}."

@function_tool()
async def recall(context: RunContext, key: str) -> str:
    return _load_memory().get(key.lower(), "I do not have that stored.")

# ------------------------------
# WEBSITE & APP OPENER
# ------------------------------

@function_tool()
async def open_website_or_app(context: RunContext, query: str) -> str:
    q = query.lower().strip()

    if "youtube" in q:
        webbrowser.open("https://www.youtube.com")
        return "Opening YouTube."
    if "google" in q:
        webbrowser.open("https://www.google.com")
        return "Opening Google."
    if "gmail" in q:
        webbrowser.open("https://mail.google.com")
        return "Opening Gmail."
    if "github" in q:
        webbrowser.open("https://github.com")
        return "Opening GitHub."
    if q.startswith("http") or q.startswith("www"):
        webbrowser.open(q if q.startswith("http") else f"https://{q}")
        return "Opening the website."

    if platform.system() == "Windows":
        if "command prompt" in q or "cmd" in q:
            subprocess.Popen("cmd.exe", shell=True)
            return "Opening Command Prompt."
        if "notepad" in q:
            subprocess.Popen("notepad.exe", shell=True)
            return "Opening Notepad."
        if "calculator" in q or "calc" in q:
            subprocess.Popen("calc.exe", shell=True)
            return "Opening Calculator."

    return "I could not identify what you want me to open."

# ------------------------------
# FILE / FOLDER OPENER
# ------------------------------

@function_tool()
async def open_file_or_folder(context: RunContext, path: str) -> str:
    try:
        path = os.path.expandvars(path)
        path = os.path.expanduser(path)

        if not os.path.exists(path):
            return "That file or folder does not exist."

        if platform.system() == "Windows":
            os.startfile(path)
            return "Opening the requested file."

        subprocess.Popen(["xdg-open", path])
        return "Opening the requested file."
    except Exception as e:
        logging.error(e)
        return "I was unable to open that file."

# ------------------------------
# MUSIC
# ------------------------------

@function_tool()
async def play_music(context: RunContext, song: Optional[str] = None) -> str:
    query = song or "music"
    webbrowser.open(
        f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
    )
    return f"Playing {query}."

# ------------------------------
# SAFE SYSTEM COMMANDS
# ------------------------------

ALLOWED_COMMANDS = {"ipconfig", "whoami", "dir", "ls"}

@function_tool()
async def run_command(context: RunContext, command: str) -> str:
    cmd = command.split()[0]
    if cmd not in ALLOWED_COMMANDS:
        return "That command is not permitted."
    try:
        return subprocess.check_output(command, shell=True, text=True)[:2000]
    except Exception:
        return "Command execution failed."

# ------------------------------
# BATTERY STATUS
# ------------------------------

@function_tool()
async def battery_status(context: RunContext) -> str:
    battery = psutil.sensors_battery()
    if not battery:
        return "Battery information is unavailable."
    return f"Battery at {battery.percent}%, {'charging' if battery.power_plugged else 'not charging'}."

# ------------------------------
# SYSTEM UPTIME
# ------------------------------

@function_tool()
async def system_uptime(context: RunContext) -> str:
    boot = datetime.datetime.fromtimestamp(psutil.boot_time())
    uptime = datetime.datetime.now() - boot
    return f"System uptime is {str(uptime).split('.')[0]}."

# ------------------------------
# CLIPBOARD
# ------------------------------

@function_tool()
async def read_clipboard(context: RunContext) -> str:
    try:
        return f"Clipboard contains: {pyperclip.paste()[:500]}"
    except Exception:
        return "Unable to read clipboard."

# ------------------------------
# RUNNING PROCESSES
# ------------------------------

@function_tool()
async def running_processes(context: RunContext) -> str:
    procs = [p.info["name"] for p in psutil.process_iter(["name"])]
    return "Running processes:\n" + ", ".join(procs[:15])

# ------------------------------
# TERMINATE PROCESS
# ------------------------------

@function_tool()
async def terminate_process(context: RunContext, name: str) -> str:
    for p in psutil.process_iter(["name"]):
        if p.info["name"] and name.lower() in p.info["name"].lower():
            p.terminate()
            return f"Process {name} terminated."
    return "Process not found."

# ------------------------------
# SCREENSHOT
# ------------------------------

@function_tool()
async def take_screenshot(context: RunContext) -> str:
    path = "jarvis_screenshot.png"
    pyautogui.screenshot(path)
    return f"Screenshot captured as {path}."

# ------------------------------
# VOLUME CONTROL
# ------------------------------

@function_tool()
async def volume_control(context: RunContext, action: str) -> str:
    if platform.system() != "Windows":
        return "Volume control not supported on this OS."

    try:
        if action == "mute":
            subprocess.call("nircmd.exe mutesysvolume 1", shell=True)
        elif action == "up":
            subprocess.call("nircmd.exe changesysvolume 5000", shell=True)
        elif action == "down":
            subprocess.call("nircmd.exe changesysvolume -5000", shell=True)
        else:
            return "Unknown volume action."

        return f"Volume {action} executed."
    except Exception:
        return "Volume control failed."

# ------------------------------
# LOCK SYSTEM
# ------------------------------

@function_tool()
async def lock_system(context: RunContext) -> str:
    if platform.system() == "Windows":
        subprocess.call("rundll32.exe user32.dll,LockWorkStation")
        return "System locked."
    return "Lock not supported."

# ------------------------------
# IP INFORMATION
# ------------------------------

@function_tool()
async def ip_information(context: RunContext) -> str:
    local_ip = socket.gethostbyname(socket.gethostname())
    try:
        public_ip = requests.get("https://api.ipify.org", timeout=5).text
    except Exception:
        public_ip = "Unavailable"
    return f"Local IP: {local_ip}, Public IP: {public_ip}"

# ------------------------------
# SYSTEM HEALTH REPORT
# ------------------------------

@function_tool()
async def system_health_report(context: RunContext) -> str:
    battery = psutil.sensors_battery()
    battery_pct = battery.percent if battery else "N/A"
    return (
        f"CPU {psutil.cpu_percent()}%, "
        f"Memory {psutil.virtual_memory().percent}%, "
        f"Disk {psutil.disk_usage('/').percent}%, "
        f"Battery: {battery_pct}%"
    )


