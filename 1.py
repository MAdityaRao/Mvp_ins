import asyncio
import asyncpg

async def main():
    conn = await asyncpg.connect(
        host="localhost", port=5432,
        database="insurance_mvp",
        user="adityarao", password="The_sunday",
    )

    rows = await conn.fetch("SELECT id, policy_number, policy_type, status, customer_id FROM policies ORDER BY id")

    print(f"\n{'ID':<5} {'Policy Number':<15} {'Type':<10} {'Status':<12} {'Customer ID'}")
    print("-" * 55)
    for r in rows:
        print(f"{r['id']:<5} {r['policy_number']:<15} {r['policy_type']:<10} {r['status']:<12} {r['customer_id']}")

    await conn.close()

asyncio.run(main())