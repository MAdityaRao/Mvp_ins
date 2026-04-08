import json
import logging
from dotenv import load_dotenv

from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    cli,
    inference,
    function_tool,
)
from livekit.plugins import silero

from search import fetch_customer_data, SearchRequest

load_dotenv(".env")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("insurance-agent")


# ------------------ TOOL (Context7 structured) ------------------
@function_tool
async def search_customer(policy_number: str) -> dict:
    """
    Fetch customer details using policy number
    """
    try:
        req = SearchRequest(
        phone=None,
        policy_number=policy_number.strip()
        )
        result = await fetch_customer_data(req)

        if not result:
            return {"error": "Customer not found"}

        return result.dict()

    except Exception as e:
        logger.error(f"Search error: {e}")
        return {"error": "Internal error"}


# ------------------ PROMPT ------------------
def build_instructions() -> str:
    return (
        "You are Aria, a professional insurance assistant for InsureCo.\n"
        "You are on a live voice call — keep every reply to 2-3 sentences.\n"
        "Speak naturally. Do not use bullet points or symbols.\n\n"

        "FLOW:\n"
        "1. First ask for policy number.\n"
        "2. When user provides policy number, call the search_customer tool.\n"
        "3. After receiving data, explain policy, premium, and claim status clearly.\n"
        "4. If not found, politely ask again.\n"
        "5. If unsure, transfer to human agent.\n"
    )


# ------------------ AGENT ------------------
class InsuranceAssistant(Agent):
    def __init__(self):
        super().__init__(
            instructions=build_instructions(),
            tools=[search_customer],  # 🔥 tool added
        )


server = AgentServer()


# ------------------ ENTRYPOINT ------------------
@server.rtc_session()
async def entrypoint(ctx: JobContext):
    logger.info(f"Incoming call — room: {ctx.room.name}")

    # Just connect (no DB fetch here)
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

    # -------- FORCE FIRST QUESTION --------
    await session.generate_reply(
        instructions="Greet the caller and ask for their policy number to proceed."
    )


# ------------------ MAIN ------------------
if __name__ == "__main__":
    cli.run_app(server)