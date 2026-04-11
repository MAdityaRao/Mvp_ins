import logging
from dotenv import load_dotenv

from livekit.agents import Agent, AgentServer, AgentSession, JobContext, cli, inference, room_io
from livekit.plugins import silero, noise_cancellation
from livekit.plugins.turn_detector.multilingual import MultilingualModel
from search import search_customer, get_regulation, _get_pool

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("insurance-agent")


def build_instructions() -> str:
    return (
        "You are Aria, a professional insurance assistant.\n"
        "Sound human, be empathetic, keep replies to 2-3 sentences.\n\n"
        "FLOW:\n"
        "1. Ask for policy number first.\n"
        "2. Use search_customer when policy number is given.\n"
        "3. Use get_regulation for claims, rules, or policy questions.\n"
        "4. If not found, ask again politely.\n"
        "5. Offer human help if needed.\n"
        "6. Never repeat the policy number back.\n"
    )


class InsuranceAssistant(Agent):
    def __init__(self):
        super().__init__(
            instructions=build_instructions(),
            tools=[search_customer, get_regulation],
            turn_detection=MultilingualModel(),
        )


server = AgentServer()


@server.rtc_session()
async def entrypoint(ctx: JobContext):
    logger.info(f"Incoming call — room: {ctx.room.name}")

    await ctx.connect()

    # warm pool now so first tool call has no connection overhead
    await _get_pool()

    session = AgentSession(
        stt=inference.STT("deepgram/nova-3", language="multi"),
        llm=inference.LLM("gpt-4o"),

        # deepgram aura-2 — fastest TTS, ~200ms ttfb vs cartesia's ~600ms
        tts=inference.TTS("deepgram/aura-2", voice="athena", language="en"),

        vad=silero.VAD.load(),
        preemptive_generation=True,
    )

    await session.start(
        room=ctx.room,
        agent=InsuranceAssistant(),
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=noise_cancellation.BVC()
            )
        )
    )

    await session.generate_reply(
        instructions="Greet the caller warmly and ask for their policy number.",
        allow_interruptions=False
    )


if __name__ == "__main__":
    cli.run_app(server)