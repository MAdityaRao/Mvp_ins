# ========================= search.py =========================
from pydantic import BaseModel, Field
from typing import List, Optional
import asyncpg
import os


# -------- Pydantic Models --------
class SearchRequest(BaseModel):
    phone: Optional[str] = Field(None, description="Customer phone number")
    policy_number: Optional[str] = Field(None, description="Policy number")


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


# -------- DB Connection --------
async def connect_db():
    return await asyncpg.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
    )


# -------- Fetch Function (Tool) --------
async def fetch_customer_data(req: SearchRequest) -> Optional[CustomerResponse]:
    conn = await connect_db()
    try:
        query = """
        SELECT c.id AS customer_id, c.full_name,
               p.policy_number, p.policy_type, p.status,
               p.premium_amount, p.premium_frequency,
               p.sum_insured, p.start_date, p.end_date,
               cl.claim_number, cl.status AS claim_status,
               cl.claimed_amount, cl.approved_amount, cl.description
        FROM customers c
        JOIN policies p ON p.customer_id = c.id
        LEFT JOIN claims cl ON cl.policy_id = p.id
        WHERE c.phone = $1 OR p.policy_number = $2
        ORDER BY p.id DESC
        """

        rows = await conn.fetch(query, req.phone, req.policy_number)
        if not rows:
            return None

        policies = []
        for row in rows:
            claim = None
            if row["claim_number"]:
                claim = ClaimInfo(
                    claim_number=row["claim_number"],
                    claim_status=row["claim_status"],
                    claimed_amount=row["claimed_amount"],
                    approved_amount=row["approved_amount"],
                    description=row["description"],
                )

            policies.append(
                PolicyInfo(
                    policy_number=row["policy_number"],
                    policy_type=row["policy_type"],
                    status=row["status"],
                    premium_amount=row["premium_amount"],
                    premium_frequency=row["premium_frequency"],
                    sum_insured=row["sum_insured"],
                    start_date=str(row["start_date"]) if row["start_date"] else None,
                    end_date=str(row["end_date"]) if row["end_date"] else None,
                    claim=claim,
                )
            )

        return CustomerResponse(
            customer_id=rows[0]["customer_id"],
            full_name=rows[0]["full_name"],
            policies=policies,
        )

    finally:
        await conn.close()


