import asyncpg
import os
import logging
import requests
from typing import List, Optional
from pydantic import BaseModel, Field
from livekit.agents import function_tool
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("search-tool")

BACKEND_URL = os.getenv("BACKEND_URL")

# LOGGER FUNCTION
def log_to_backend(query, response, category="general"):
    try:
        if BACKEND_URL:
            requests.post(BACKEND_URL, json={
                "query": query,
                "response": response,
                "category": category
            })
    except Exception as e:
        logger.error(f"Logging failed: {e}")

#MODELS
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

#DB CONNECTION
async def connect_db():
    return await asyncpg.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", 5432)),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
    )

#FETCH FUNCTION
async def fetch_customer_data(req: SearchRequest) -> Optional[CustomerResponse]:
    conn = await connect_db()
    try:
        query = """
        SELECT c.id AS customer_id, c.full_name,
               p.id AS policy_id,
               p.policy_number, p.policy_type, p.status,
               p.premium_amount, p.premium_frequency,
               p.sum_insured, p.start_date, p.end_date,
               cl.claim_number, cl.status AS claim_status,
               cl.claimed_amount, cl.approved_amount, cl.description
        FROM customers c
        JOIN policies p ON p.customer_id = c.id
        LEFT JOIN claims cl ON cl.policy_id = p.id
        WHERE 
            ($1::TEXT IS NOT NULL AND c.phone = $1)
            OR
            ($2::TEXT IS NOT NULL AND p.policy_number = $2)
        ORDER BY p.id DESC
        """

        rows = await conn.fetch(query, req.phone, req.policy_number)

        if not rows:
            return None

        policy_map = {}

        for row in rows:
            policy_id = row["policy_id"]

            if policy_id not in policy_map:
                policy_map[policy_id] = {
                    "policy_number": row["policy_number"],
                    "policy_type": row["policy_type"],
                    "status": row["status"],
                    "premium_amount": float(row["premium_amount"]),
                    "premium_frequency": row["premium_frequency"],
                    "sum_insured": float(row["sum_insured"]),
                    "start_date": str(row["start_date"]) if row["start_date"] else None,
                    "end_date": str(row["end_date"]) if row["end_date"] else None,
                    "claim": None
                }

            if row["claim_number"]:
                policy_map[policy_id]["claim"] = ClaimInfo(
                    claim_number=row["claim_number"],
                    claim_status=row["claim_status"],
                    claimed_amount=float(row["claimed_amount"]),
                    approved_amount=float(row["approved_amount"]) if row["approved_amount"] else None,
                    description=row["description"],
                )

        policies = [PolicyInfo(**p) for p in policy_map.values()]

        return CustomerResponse(
            customer_id=rows[0]["customer_id"],
            full_name=rows[0]["full_name"],
            policies=policies,
        )

    finally:
        await conn.close()

#CUSTOMER SEARCH

@function_tool
async def search_customer(policy_number: str) -> dict:
    try:
        policy_number = policy_number.strip().upper()

        req = SearchRequest(policy_number=policy_number)

        result = await fetch_customer_data(req)

        if not result:
            response = {"error": "Customer not found"}
            log_to_backend(policy_number, str(response), "policy")
            return response

        response = result.model_dump()

        #LOG SUCCESS
        log_to_backend(policy_number, "Customer data fetched", "policy")

        return response

    except Exception as e:
        logger.error(f"Search error: {e}")

        response = {"error": "Internal error"}
        log_to_backend(policy_number, str(response), "error")

        return response

#REGULATIONS
@function_tool
async def get_regulation(topic: str) -> str:
    topic = topic.lower()

    regulations = {
        "claim": (
            "To file a claim, valid documents must be submitted. "
            "Claims are reviewed and may be approved or rejected."
        ),
        "premium": (
            "Premium must be paid on time. Missing payments may lead to policy lapse."
        ),
        "policy": (
            "Policy must be active for benefits. Expired policies are not eligible."
        ),
        "general": (
            "Customer must provide policy number for verification."
        )
    }

    response = regulations.get(topic, "No regulation found for this topic.")

    #LOG
    log_to_backend(topic, response, "regulation")
    return response