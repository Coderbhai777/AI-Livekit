from dotenv import load_dotenv
load_dotenv()

from livekit import agents
from livekit.agents import Agent, AgentSession, RoomInputOptions
from livekit.plugins import google, noise_cancellation

# ---- IMPORT ALL TOOLS EXPLICITLY ----
from tools import (
    get_weather,
    search_web,
    send_email,
    system_status,
    check_internet,
    current_time,
    remember,
    recall,
    open_website_or_app,
    open_file_or_folder,
    play_music,
    run_command,

    # Ethical Network Tools
    network_info,
    active_connections,
    listening_ports,
    suspicious_connections,
    local_port_awareness,
    explain_network_risk,
)

from prompts import AGENT_INSTRUCTION, SESSION_INSTRUCTION


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=AGENT_INSTRUCTION,

            # ✅ GOOGLE REALTIME MODEL (STABLE)
            llm=google.beta.realtime.RealtimeModel(
                voice="Aoede",
                temperature=0.7,
            ),

            # ✅ ALL TOOLS MUST BE LISTED HERE OR THEY WILL NEVER RUN
            tools=[
                get_weather,
                search_web,
                send_email,
                play_music,
                system_status,
                check_internet,
                current_time,
                remember,
                recall,
                open_website_or_app,
                open_file_or_folder,
                run_command,
                network_info,
                active_connections,
                listening_ports,
                suspicious_connections,
                local_port_awareness,
                explain_network_risk,
            ],
        )


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

    # ✅ INITIAL GREETING
    await session.generate_reply(
        instructions=SESSION_INSTRUCTION
    )


if __name__ == "__main__":
    agents.cli.run_app(
        agents.WorkerOptions(entrypoint_fnc=entrypoint)
    )

