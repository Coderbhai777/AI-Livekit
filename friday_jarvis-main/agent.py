from dotenv import load_dotenv
load_dotenv()

from livekit import agents
from livekit.agents import Agent, AgentSession, RoomInputOptions, RunContext
from livekit.plugins import google, noise_cancellation

from prompts import AGENT_INSTRUCTION, SESSION_INSTRUCTION

# ==============================
# IMPORT ALL TOOLS
# ==============================

from tools import (
    # Core
    get_weather,
    search_web,
    send_email,
    play_music,

    # System & Time
    system_status,
    system_uptime,
    battery_status,
    current_time,
    check_internet,
    system_health_report,

    # Memory
    remember,
    recall,

    # OS / Automation
    open_website_or_app,
    open_file_or_folder,
    run_command,
    lock_system,
    volume_control,
    take_screenshot,
    read_clipboard,

    # Processes
    running_processes,
    terminate_process,

    # Network / IP
    ip_information,
)

# ==============================
# TOOL REGISTRY
# ==============================

ALL_TOOLS = [
    get_weather,
    search_web,
    send_email,
    play_music,

    system_status,
    system_uptime,
    battery_status,
    current_time,
    check_internet,
    system_health_report,

    remember,
    recall,

    open_website_or_app,
    open_file_or_folder,
    run_command,
    lock_system,
    volume_control,
    take_screenshot,
    read_clipboard,

    running_processes,
    terminate_process,

    ip_information,
]

# ==============================
# INTENT → TOOL ROUTER (CRITICAL)
# ==============================

def route_intent(user_input: str):
    q = user_input.lower()

    if "weather" in q:
        return get_weather, {"city": q.split()[-1]}

    if "time" in q:
        return current_time, {}

    if "internet" in q:
        return check_internet, {}

    if "status" in q or "health" in q:
        return system_health_report, {}

    if "open" in q:
        return open_website_or_app, {"query": q}

    if "file" in q or "folder" in q:
        return open_file_or_folder, {"path": q}

    if "music" in q or "play" in q:
        return play_music, {"song": q.replace("play", "").strip()}

    if "ip" in q:
        return ip_information, {}

    if "process" in q:
        return running_processes, {}

    if "shutdown" in q or "lock" in q:
        return lock_system, {}

    return None, None


# ==============================
# ASSISTANT
# ==============================

class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=AGENT_INSTRUCTION,
            llm=google.beta.realtime.RealtimeModel(
                voice="Aoede",
                temperature=0.6,
            ),
            tools=ALL_TOOLS,
        )

    async def on_user_message(self, context: RunContext, message: str):
        """
        HARD ROUTER:
        - Detect intent
        - Execute tool
        - Then respond
        """
        tool, args = route_intent(message)

        if tool:
            result = await tool(context, **args)
            return f"Roger, Boss. {result}"

        return await super().on_user_message(context, message)


# ==============================
# ENTRYPOINT
# ==============================

async def entrypoint(ctx: agents.JobContext):
    session = AgentSession()

    await session.start(
        room=ctx.room,
        agent=Assistant(),
        room_input_options=RoomInputOptions(
            video_enabled=True,
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    await ctx.connect()

    await session.generate_reply(
        instructions=SESSION_INSTRUCTION
    )


# ==============================
# RUN
# ==============================

if __name__ == "__main__":
    agents.cli.run_app(
        agents.WorkerOptions(entrypoint_fnc=entrypoint)
    )


