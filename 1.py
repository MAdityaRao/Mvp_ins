import asyncio
import asyncpg

async def main():
    conn = await asyncpg.connect(
        host="localhost", port=5432,
        database="insurance_mvp",
        user="adityarao", password="The_sunday",
    )

    rows = await conn.fetch("SELECT * from policies")
    for row in rows:
        print(dict(row),"\n")
    await conn.close()

asyncio.run(main())