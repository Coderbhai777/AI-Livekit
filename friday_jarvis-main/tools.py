# ==============================
# FRIDAY / JARVIS TOOLS MODULE
# Windows • Python 3.12
# ==============================

import os
import json
import psutil
import socket
import platform
import subprocess
import datetime
import webbrowser
import logging
import requests
import smtplib

from typing import Optional
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from livekit.agents import function_tool, RunContext
from langchain_community.tools import DuckDuckGoSearchRun

logging.basicConfig(level=logging.INFO)

# ==============================
# MEMORY
# ==============================

MEMORY_FILE = "jarvis_memory.json"

def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_memory(data):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

# ==============================
# BASIC ASSISTANT TOOLS
# ==============================

@function_tool()
async def current_time(context: RunContext) -> str:
    return datetime.datetime.now().strftime(
        "It is %I:%M %p on %A, %d %B %Y."
    )

@function_tool()
async def check_internet(context: RunContext) -> str:
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return "Internet connection is active."
    except OSError:
        return "No internet connection detected."

@function_tool()
async def system_status(context: RunContext) -> str:
    return (
        f"CPU: {psutil.cpu_percent()}%, "
        f"Memory: {psutil.virtual_memory().percent}%, "
        f"Disk: {psutil.disk_usage('C:\\').percent}%"
    )

# ==============================
# WEATHER & SEARCH
# ==============================

@function_tool()
async def get_weather(context: RunContext, city: str) -> str:
    try:
        r = requests.get(f"https://wttr.in/{city}?format=3", timeout=5)
        return r.text if r.status_code == 200 else "Weather unavailable."
    except Exception:
        return "Weather service unavailable."

@function_tool()
async def search_web(context: RunContext, query: str) -> str:
    try:
        return DuckDuckGoSearchRun().run(query)
    except Exception:
        return "Search failed."

# ==============================
# EMAIL
# ==============================

@function_tool()
async def send_email(
    context: RunContext,
    to_email: str,
    subject: str,
    message: str
) -> str:

    user = os.getenv("GMAIL_USER")
    password = os.getenv("GMAIL_APP_PASSWORD")

    if not user or not password:
        return "Email credentials not configured."

    try:
        msg = MIMEMultipart()
        msg["From"] = user
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(message, "plain"))

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(user, password)
        server.send_message(msg)
        server.quit()

        return "Email sent successfully."
    except Exception as e:
        logging.error(e)
        return "Failed to send email."

# ==============================
# WEBSITE & APP OPENER
# ==============================

@function_tool()
async def open_website_or_app(context: RunContext, query: str) -> str:
    q = query.lower()

    websites = {
        "youtube": "https://www.youtube.com",
        "google": "https://www.google.com",
        "gmail": "https://mail.google.com",
        "github": "https://github.com",
        "chatgpt": "https://chat.openai.com",
    }

    for key, url in websites.items():
        if key in q:
            webbrowser.open(url)
            return f"Opening {key}."

    if q.startswith("http") or q.startswith("www"):
        webbrowser.open(q if q.startswith("http") else f"https://{q}")
        return "Opening website."

    if platform.system() == "Windows":
        apps = {
            "command prompt": "cmd.exe",
            "cmd": "cmd.exe",
            "notepad": "notepad.exe",
            "calculator": "calc.exe",
            "calc": "calc.exe",
        }
        for key, exe in apps.items():
            if key in q:
                subprocess.Popen(exe, shell=True)
                return f"Opening {key}."

    return "Unable to open the requested item."

# ==============================
# FILE / FOLDER OPENER
# ==============================

@function_tool()
async def open_file_or_folder(context: RunContext, path: str) -> str:
    try:
        path = os.path.expandvars(os.path.expanduser(path))

        if not os.path.exists(path):
            return "File or folder does not exist."

        if platform.system() == "Windows":
            os.startfile(path)
        else:
            subprocess.Popen(["xdg-open", path])

        return "Opening file or folder."
    except Exception as e:
        logging.error(e)
        return "Failed to open file or folder."

# ==============================
# MUSIC
# ==============================

@function_tool()
async def play_music(context: RunContext, song: Optional[str] = None) -> str:
    q = song or "music"
    webbrowser.open(
        f"https://www.youtube.com/results?search_query={q.replace(' ', '+')}"
    )
    return f"Playing {q}."

# ==============================
# ETHICAL CYBERSECURITY TOOLS
# ==============================

@function_tool()
async def security_audit(context: RunContext) -> str:
    suspicious = []
    for proc in psutil.process_iter(['name']):
        name = (proc.info['name'] or "").lower()
        if any(x in name for x in ["rat", "miner", "keylog", "hack"]):
            suspicious.append(name)

    return (
        "Security audit completed. "
        f"Suspicious processes found: {len(suspicious)}."
    )

@function_tool()
async def check_open_ports(context: RunContext) -> str:
    ports = sorted(
        {c.laddr.port for c in psutil.net_connections() if c.laddr}
    )
    return f"Open local ports: {ports[:15]}"

@function_tool()
async def password_strength(context: RunContext, password: str) -> str:
    score = sum([
        len(password) >= 12,
        any(c.isupper() for c in password),
        any(c.islower() for c in password),
        any(c.isdigit() for c in password),
        any(c in "!@#$%^&*" for c in password),
    ])
    levels = ["Very Weak", "Weak", "Moderate", "Strong", "Very Strong"]
    return f"Password strength: {levels[min(score, 4)]}"

@function_tool()
async def explain_attack(context: RunContext, topic: str) -> str:
    knowledge = {
        "sql injection": "SQL Injection manipulates unsanitized database queries.",
        "xss": "XSS injects malicious scripts into trusted websites.",
        "phishing": "Phishing tricks users into revealing credentials.",
        "brute force": "Brute force repeatedly guesses passwords."
    }
    return knowledge.get(topic.lower(), "Topic not available.")

# ==============================
# MEMORY TOOLS
# ==============================

@function_tool()
async def remember(context: RunContext, key: str, value: str) -> str:
    mem = load_memory()
    mem[key.lower()] = value
    save_memory(mem)
    return f"I will remember that {key} is {value}."

@function_tool()
async def recall(context: RunContext, key: str) -> str:
    return load_memory().get(key.lower(), "No memory found.")

# ==============================
# ETHICAL NETWORK SECURITY TOOLS
# ==============================

@function_tool()
async def network_info(context: RunContext) -> str:
    """Shows basic network configuration"""
    info = []
    for iface, addrs in psutil.net_if_addrs().items():
        for addr in addrs:
            if addr.family == socket.AF_INET:
                info.append(f"{iface}: {addr.address}")
    return "Network Interfaces:\n" + "\n".join(info[:10])


@function_tool()
async def active_connections(context: RunContext) -> str:
    """Lists active TCP connections (local only)"""
    connections = psutil.net_connections(kind="tcp")
    results = []

    for c in connections:
        if c.raddr:
            results.append(
                f"Local {c.laddr.ip}:{c.laddr.port} → "
                f"Remote {c.raddr.ip}:{c.raddr.port} [{c.status}]"
            )

    return (
        "Active network connections:\n"
        + "\n".join(results[:10])
        if results else
        "No active outbound connections detected."
    )


@function_tool()
async def listening_ports(context: RunContext) -> str:
    """Shows locally listening services"""
    ports = set()
    for c in psutil.net_connections(kind="inet"):
        if c.status == "LISTEN":
            ports.add(c.laddr.port)

    return f"Listening ports on this system: {sorted(list(ports))[:20]}"


@function_tool()
async def suspicious_connections(context: RunContext) -> str:
    """Detects unusual outbound traffic heuristically"""
    suspicious = []

    for c in psutil.net_connections(kind="tcp"):
        if c.raddr and c.raddr.port not in {80, 443, 53}:
            suspicious.append(
                f"{c.laddr.ip}:{c.laddr.port} → {c.raddr.ip}:{c.raddr.port}"
            )

    return (
        "Potentially unusual outbound connections:\n"
        + "\n".join(suspicious[:10])
        if suspicious else
        "No suspicious outbound connections detected."
    )


@function_tool()
async def local_port_awareness(context: RunContext) -> str:
    """Awareness-level port review (not scanning)"""
    ports = sorted(
        {c.laddr.port for c in psutil.net_connections() if c.laddr}
    )
    common = [p for p in ports if p in (21, 22, 23, 25, 80, 443, 3389)]

    return (
        f"Total local ports observed: {len(ports)}. "
        f"Common service ports in use: {common}"
    )


@function_tool()
async def explain_network_risk(context: RunContext, topic: str) -> str:
    knowledge = {
        "open ports": "Open ports expose services that can be targeted if misconfigured.",
        "dns spoofing": "DNS spoofing redirects traffic by falsifying DNS responses.",
        "man in the middle": "MITM intercepts communication between two endpoints.",
        "port scanning": "Port scanning maps exposed services for security analysis.",
        "firewall": "Firewalls control inbound and outbound network traffic."
    }
    return knowledge.get(topic.lower(), "Network topic not found.")

