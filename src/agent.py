import json
import logging
import os

import asyncpg
from dotenv import load_dotenv
from livekit.agents import Agent, AgentServer, AgentSession, JobContext, cli, inference
from livekit.plugins import silero

load_dotenv(".env")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("insurance-agent")


# ── Database ──────────────────────────────────────────────────────────────────

async def _connect():
    return await asyncpg.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", 5432)),
        database=os.getenv("DB_NAME", "insurance_mvp"),
        user=os.getenv("DB_USER", "adityarao"),
        password=os.getenv("DB_PASS", "The_sunday"),
    )


async def get_customer(phone: str) -> dict | None:
    conn = await _connect()
    try:
        row = await conn.fetchrow(
            """
            SELECT c.id AS customer_id, c.full_name,
                   p.policy_number, p.policy_type, p.status AS policy_status,
                   p.premium_amount, p.premium_frequency,
                   p.sum_insured, p.start_date, p.end_date,
                   cl.claim_number, cl.status AS claim_status,
                   cl.claimed_amount, cl.approved_amount, cl.description AS claim_desc
            FROM customers c
            JOIN policies p ON p.customer_id = c.id
            LEFT JOIN claims cl ON cl.policy_id = p.id
            WHERE c.phone = $1
            ORDER BY p.id DESC, cl.filed_at DESC
            LIMIT 1
            """,
            phone,
        )
        return dict(row) if row else None
    finally:
        await conn.close()


async def log_call(customer_id: int | None, room_id: str):
    conn = await _connect()
    try:
        await conn.execute(
            "INSERT INTO call_logs (customer_id, livekit_room_id, intent, resolved) VALUES ($1, $2, $3, TRUE)",
            customer_id, room_id, "inbound_call",
        )
    finally:
        await conn.close()


# ── System Prompt ─────────────────────────────────────────────────────────────

def build_instructions(customer: dict | None) -> str:
    base = (
        "You are Aria, a professional insurance assistant for InsureCo. "
        "You are on a live voice call — keep every reply to 2-3 sentences max. "
        "Never use bullet points, asterisks, or emojis. Speak naturally. "
        "Round large numbers when speaking them aloud."
        "If you cannot help, offer to transfer to a human agent.\n\n"
    )

    if not customer:
        return base + (
            "This caller is not in our system. "
            "Ask for their phone number to verify identity."
        )

    fmt = lambda n: f"Rs.{int(n):,}"
    end = customer["end_date"].strftime("%d %B %Y") if customer["end_date"] else "N/A"

    info = (
        f"CALLER (verified by phone — do NOT ask them to re-verify):\n"
        f"Name: {customer['full_name']}\n"
        f"Policy: {customer['policy_number']} | {customer['policy_type'].capitalize()} Insurance\n"
        f"Status: {customer['policy_status'].upper()}\n"
        f"Coverage: {fmt(customer['sum_insured'])} | "
        f"Premium: {fmt(customer['premium_amount'])} {customer['premium_frequency']}\n"
        f"Valid until: {end}\n"
    )

    if customer.get("claim_number"):
        approved = fmt(customer["approved_amount"]) if customer.get("approved_amount") else "pending"
        info += (
            f"\nLATEST CLAIM: {customer['claim_number']} | "
            f"Status: {customer['claim_status'].replace('_', ' ').title()} | "
            f"Claimed: {fmt(customer['claimed_amount'])} | Approved: {approved}\n"
            f"Reason: {customer['claim_desc']}\n"
        )
    else:
        info += "\nNo claims on file.\n"

    return base + info


# ── Agent ─────────────────────────────────────────────────────────────────────

class InsuranceAssistant(Agent):
    def __init__(self, instructions: str):
        super().__init__(instructions=instructions)


server = AgentServer()


@server.rtc_session()
async def entrypoint(ctx: JobContext):
    logger.info(f"Incoming call — room: {ctx.room.name}")

    # Get caller phone from SIP metadata
    caller_phone = None
    try:
        caller_phone = json.loads(ctx.room.metadata or "{}").get("caller_phone")
    except Exception:
        pass

    # Fallback: check SIP participant attributes
    if not caller_phone:
        await ctx.connect()
        for p in ctx.room.remote_participants.values():
            caller_phone = (p.attributes or {}).get("sip.phoneNumber")
            if caller_phone:
                break

    logger.info(f"Caller phone: {caller_phone}")

    # DB lookup
    customer = None
    if caller_phone:
        try:
            customer = await get_customer(caller_phone)
            logger.info(f"Customer: {customer['full_name'] if customer else 'not found'}")
        except Exception as e:
            logger.error(f"DB error: {e}")

    # Start session — VAD only, no external model files needed
    session = AgentSession(
        stt=inference.STT("deepgram/nova-3", language="multi"),
        llm=inference.LLM("openai/gpt-4o-mini"),
        tts=inference.TTS("cartesia/sonic-2"),
        vad=silero.VAD.load(),  # handles turn detection, no download needed
    )

    await session.start(
        room=ctx.room,
        agent=InsuranceAssistant(instructions=build_instructions(customer)),
    )

    # Greet caller
    if customer:
        await session.generate_reply(
            instructions=f"Greet {customer['full_name']} by name and ask how you can help with their {customer['policy_type']} policy."
        )
    else:
        await session.generate_reply(
            instructions="Greet the caller and ask for their policy number to get started."
        )

    # Log call
    try:
        await log_call(
            customer_id=customer["customer_id"] if customer else None,
            room_id=ctx.room.name,
        )
    except Exception as e:
        logger.error(f"Call log failed: {e}")


if __name__ == "__main__":
    cli.run_app(server)