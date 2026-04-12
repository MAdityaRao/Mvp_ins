import asyncpg
import os
import logging
import re
from typing import List, Optional
from pydantic import BaseModel, Field
from livekit.agents import function_tool
from dotenv import load_dotenv

load_dotenv(".env")

logger = logging.getLogger("search-tool")

# ── pool ──────────────────────────────────────────────────────────────────
# lazy — created on first call inside the job's event loop, never in __main__

_pool: Optional[asyncpg.Pool] = None


async def _get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None or _pool._closed:
        _pool = await asyncpg.create_pool(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", 5432)),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASS"),
            ssl="require",   #THIS LINE IS IMPORTANT FOR NEON
            min_size=2,
            max_size=5,
        )
        logger.info("DB pool ready")
    return _pool

# run these once in psql to fix slow queries:
#   CREATE INDEX IF NOT EXISTS idx_policies_policy_number ON policies(policy_number);
#   CREATE INDEX IF NOT EXISTS idx_policies_customer_id  ON policies(customer_id);
#   CREATE INDEX IF NOT EXISTS idx_claims_policy_id      ON claims(policy_id);
#   CREATE INDEX IF NOT EXISTS idx_customers_phone       ON customers(phone);

# ── models ────────────────────────────────────────────────────────────────

class SearchRequest(BaseModel):
    phone: Optional[str] = Field(default=None)
    policy_number: Optional[str] = Field(default=None)


class ClaimInfo(BaseModel):
    claim_number: Optional[str]
    claim_status: Optional[str]
    claimed_amount: Optional[float]
    approved_amount: Optional[float]
    description: Optional[str]


class PolicyInfo(BaseModel):
    policy_number: str
    policy_type: str
    status: str
    premium_amount: float
    premium_frequency: str
    sum_insured: float
    start_date: Optional[str]
    end_date: Optional[str]
    claim: Optional[ClaimInfo]


class CustomerResponse(BaseModel):
    customer_id: int
    full_name: str
    policies: List[PolicyInfo]


# ── db fetch ──────────────────────────────────────────────────────────────

_QUERY = """
    SELECT
        c.id              AS customer_id,
        c.full_name,
        p.id              AS policy_id,
        p.policy_number,
        p.policy_type,
        p.status,
        p.premium_amount,
        p.premium_frequency,
        p.sum_insured,
        p.start_date,
        p.end_date,
        cl.claim_number,
        cl.status         AS claim_status,
        cl.claimed_amount,
        cl.approved_amount,
        cl.description
    FROM customers c
    JOIN policies p ON p.customer_id = c.id
    LEFT JOIN claims cl ON cl.policy_id = p.id
    WHERE ($1::TEXT IS NOT NULL AND c.phone = $1)
       OR ($2::TEXT IS NOT NULL AND p.policy_number = $2)
    ORDER BY p.id DESC
"""


async def fetch_customer_data(req: SearchRequest) -> Optional[CustomerResponse]:
    pool = await _get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(_QUERY, req.phone, req.policy_number)

    if not rows:
        return None

    policy_map = {}
    for row in rows:
        pid = row["policy_id"]
        if pid not in policy_map:
            policy_map[pid] = {
                "policy_number":     row["policy_number"],
                "policy_type":       row["policy_type"],
                "status":            row["status"],
                "premium_amount":    float(row["premium_amount"]),
                "premium_frequency": row["premium_frequency"],
                "sum_insured":       float(row["sum_insured"]),
                "start_date":        str(row["start_date"]) if row["start_date"] else None,
                "end_date":          str(row["end_date"])   if row["end_date"]   else None,
                "claim":             None,
            }
        if row["claim_number"]:
            policy_map[pid]["claim"] = ClaimInfo(
                claim_number    = row["claim_number"],
                claim_status    = row["claim_status"],
                claimed_amount  = float(row["claimed_amount"]),
                approved_amount = float(row["approved_amount"]) if row["approved_amount"] else None,
                description     = row["description"],
            )

    return CustomerResponse(
        customer_id = rows[0]["customer_id"],
        full_name   = rows[0]["full_name"],
        policies    = [PolicyInfo(**p) for p in policy_map.values()],
    )


# ── normalizer ────────────────────────────────────────────────────────────
# STT splits "POL" into letters or mishears it entirely.
# strip all leading letters, convert spoken words to digits, parse year+serial.

_WORDS = {
    "twenty twenty five": "2025",
    "twenty twenty four": "2024",
    "twenty twenty three": "2023",
    "twenty twenty":      "2020",
    "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4",
    "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9",
}


def normalize_policy_number(raw: str) -> str:
    if re.match(r'^POL-\d{4}-\d{3,}$', raw.strip().upper()):
        return raw.strip().upper()

    lowered = raw.lower().strip()
    for word, digit in _WORDS.items():
        lowered = lowered.replace(word, digit)

    cleaned = re.sub(r'[\s\-_]+', '', lowered)
    cleaned = re.sub(r'^[a-z]+', '', cleaned)   # strip any letter prefix

    match = re.match(r'^(\d{4})(\d+)$', cleaned)
    if match:
        serial = match.group(2).lstrip('0') or '0'
        return f"POL-{match.group(1)}-{serial.zfill(3)}"

    logger.warning(f"Could not normalize: '{raw}' → '{cleaned}'")
    return raw.upper()


# ── regulations ───────────────────────────────────────────────────────────

_REGULATIONS = {
    "storm":   "Storm damage is covered. File within 30 days with photos and a damage report.",
    "flood":   "Flood damage is covered. Notify within 48 hours and document before cleanup.",
    "fire":    "Fire claims need a fire department report. Emergency stay up to $5,000 covered.",
    "theft":   "Theft claims need a police FIR within 24 hours plus a list of stolen items.",
    "claim":   "Submit documents within 30 days. Claims reviewed within 7 working days.",
    "premium": "15-day grace period after due date before the policy lapses.",
    "renewal": "Policies can be renewed up to 30 days before expiry.",
    "policy":  "Policy must be active for benefits or claims to apply.",
    "general": "Please provide your policy number for verification.",
}


def _match_regulation(topic: str) -> str:
    t = topic.lower()
    for key, text in _REGULATIONS.items():
        if key in t:
            return text
    return "No specific regulation found. A human agent can help with detailed queries."


# ── tools ─────────────────────────────────────────────────────────────────

@function_tool
async def search_customer(policy_number: str) -> dict:
    """Fetch customer and policy details from the database."""
    try:
        normalized = normalize_policy_number(policy_number)
        logger.info(f"Looking up: '{policy_number}' → '{normalized}'")
        result = await fetch_customer_data(SearchRequest(policy_number=normalized))
        if not result:
            return {"error": "Customer not found"}
        return result.model_dump()
    except Exception as e:
        logger.error(f"search_customer failed: {e}")
        return {"error": "Internal error"}


@function_tool
async def get_regulation(topic: str) -> str:
    """Return insurance regulation for the given topic."""
    return _match_regulation(topic)