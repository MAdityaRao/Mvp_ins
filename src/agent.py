import logging
from dotenv import load_dotenv

from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    cli,
    inference,
)

from livekit.plugins import silero
from search import search_customer, get_regulation

#Load env
load_dotenv()

#Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("insurance-agent")


#PROMPT
def build_instructions() -> str:
    return (
        "You are Aria, a professional insurance assistant.\n"
        "keep replies short (2-3 sentences).\n\n"
        "FLOW:\n"
        "1. Ask for policy number first.\n"
        "2. Use search_customer tool when policy number is given.\n"
        "3. Use get_regulation tool for claims, rules, or policy questions.\n"
        "4. Explain clearly.\n"
        "5. If not found, ask again politely.\n"
        "6. Offer human help if needed.\n"
    )


#AGENT
class InsuranceAssistant(Agent):
    def __init__(self):
        super().__init__(
            instructions=build_instructions(),
            tools=[search_customer, get_regulation],
        )


#SERVER
server = AgentServer()


#ENTRYPOINT
@server.rtc_session()
async def entrypoint(ctx: JobContext):
    logger.info(f"Incoming call — room: {ctx.room.name}")

    await ctx.connect()

    session = AgentSession(
        stt=inference.STT("deepgram/nova-3", language="multi"),
        llm=inference.LLM("openai/gpt-4o-mini"),
        tts=inference.TTS("cartesia/sonic-2"),
        vad=silero.VAD.load(),
    )

    await session.start(
        room=ctx.room,
        agent=InsuranceAssistant(),
    )

    #Initial greeting
    await session.generate_reply(
        instructions="Greet the caller and ask for their policy number.",
        allow_interruptions=False
    )


#MAIN
if __name__ == "__main__":
    cli.run_app(server)