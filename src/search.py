import asyncpg
import os
import logging
import re
import json
from typing import List, Optional
from pydantic import BaseModel, Field
from livekit.agents import function_tool
from dotenv import load_dotenv

load_dotenv(".env")
logger = logging.getLogger("search-tool")

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
            ssl="require",
            min_size=2,
            max_size=5,
        )
        logger.info("DB pool ready")
    return _pool


# ── models ────────────────────────────────────────────────────────────────

class SearchRequest(BaseModel):
    phone: Optional[str] = Field(default=None)
    policy_number: Optional[str] = Field(default=None)

# FIX 1 — new model
class NomineeInfo(BaseModel):
    id: Optional[int]
    name: Optional[str]
    relationship: Optional[str]
    percentage: Optional[float]

class ClaimInfo(BaseModel):
    claim_number: Optional[str]
    claim_status: Optional[str]
    claimed_amount: Optional[float]
    approved_amount: Optional[float]
    description: Optional[str]

# FIX 2 — nominees field added
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
    nominees: List[NomineeInfo] = []

class CustomerResponse(BaseModel):
    customer_id: int
    full_name: str
    policies: List[PolicyInfo]


# ── query ─────────────────────────────────────────────────────────────────

_QUERY = """
    SELECT
        c.id                AS customer_id,
        c.full_name,
        c.phone,
        p.id                AS policy_id,
        p.policy_number,
        p.policy_type,
        p.status,
        p.premium_amount,
        p.premium_frequency,
        p.sum_insured,
        p.start_date,
        p.end_date,
        cl.claim_number,
        cl.status           AS claim_status,
        cl.claimed_amount,
        cl.approved_amount,
        cl.description      AS claim_description,
        nominee_data.list   AS nominees
    FROM policies p
    JOIN customers c ON c.id = p.customer_id
    LEFT JOIN claims cl ON cl.policy_id = p.id
    LEFT JOIN LATERAL (
        SELECT jsonb_agg(jsonb_build_object(
            'id',           n.id,
            'name',         n.name,
            'relationship', n.relationship,
            'percentage',   n.percentage
        )) AS list
        FROM nominees n
        WHERE n.customer_id = c.id
    ) nominee_data ON true
    WHERE p.policy_number = $1
    ORDER BY p.id DESC
    LIMIT 1;
"""


# ── fetch ─────────────────────────────────────────────────────────────────

async def fetch_customer_data(req: SearchRequest) -> Optional[CustomerResponse]:
    pool = await _get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(_QUERY, req.policy_number)
        if not rows:
            return None

        policy_map = {}
        for row in rows:
            pid = row["policy_id"]
            if pid not in policy_map:

                # FIX 3 — parse nominees from the jsonb column
                raw_nominees = row["nominees"]
                if raw_nominees:
                    if isinstance(raw_nominees, str):
                        raw_nominees = json.loads(raw_nominees)
                    parsed_nominees = [NomineeInfo(**n) for n in raw_nominees]
                else:
                    parsed_nominees = []

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
                    "nominees":          parsed_nominees,
                }

            if row["claim_number"]:
                policy_map[pid]["claim"] = ClaimInfo(
                    claim_number    = row["claim_number"],
                    claim_status    = row["claim_status"],
                    claimed_amount  = float(row["claimed_amount"]),
                    approved_amount = float(row["approved_amount"]) if row["approved_amount"] else None,
                    # FIX 4 — was row["description"], query alias is claim_description
                    description     = row["claim_description"],
                )

        return CustomerResponse(
            customer_id = rows[0]["customer_id"],
            full_name   = rows[0]["full_name"],
            policies    = [PolicyInfo(**p) for p in policy_map.values()],
        )


# ── normalizer ────────────────────────────────────────────────────────────

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
