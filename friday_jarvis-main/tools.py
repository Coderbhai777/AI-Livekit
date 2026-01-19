import logging
import os
import platform
import webbrowser
from subprocess import Popen
from typing import Optional

import requests
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from dotenv import load_dotenv
from langchain_community.tools import DuckDuckGoSearchRun
from livekit.agents import function_tool, RunContext

load_dotenv()

from livekit.agents import function_tool, RunContext
import webbrowser
import platform
import logging
from subprocess import Popen


@function_tool()
async def open_anything(
    context: RunContext,   # REQUIRED
    query: str
) -> str:
    q = query.lower()

    if "youtube" in q:
        webbrowser.open("https://www.youtube.com")
        return "Opening YouTube"

    if "google" in q:
        webbrowser.open("https://www.google.com")
        return "Opening Google"

    try:
        system = platform.system().lower()
        if system == "windows":
            Popen(query, shell=True)
        elif system == "darwin":
            Popen(["open", "-a", query])
        else:
            Popen([query])

        return f"Opening {query}"
    except Exception as e:
        logging.error(e)
        return "Failed to open"


# --------------------------------------------------
# WEATHER TOOL
# --------------------------------------------------
@function_tool()
async def get_weather(
    context: RunContext,  # type: ignore
    city: str
) -> str:
    try:
        response = requests.get(f"https://wttr.in/{city}?format=3")
        if response.status_code == 200:
            return response.text.strip()
        return f"Could not retrieve weather for {city}"
    except Exception as e:
        logging.error(e)
        return f"Error retrieving weather for {city}"


# --------------------------------------------------
# WEB SEARCH TOOL
# --------------------------------------------------
@function_tool()
async def search_web(
    context: RunContext,  # type: ignore
    query: str
) -> str:
    try:
        return DuckDuckGoSearchRun().run(tool_input=query)
    except Exception as e:
        logging.error(e)
        return "An error occurred while searching the web"


# --------------------------------------------------
# EMAIL TOOL
# --------------------------------------------------
@function_tool()
async def send_email(
    context: RunContext,  # type: ignore
    to_email: str,
    subject: str,
    message: str,
    cc_email: Optional[str] = None
) -> str:
    try:
        gmail_user = os.getenv("GMAIL_USER")
        gmail_password = os.getenv("GMAIL_APP_PASSWORD")

        if not gmail_user or not gmail_password:
            return "Gmail credentials not configured"

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

        return f"Email sent to {to_email}"

    except Exception as e:
        logging.error(e)
        return "Failed to send email"
