import asyncio
import asyncpg
import json


async def main():
    conn = await asyncpg.connect(
        host="localhost",
        port=5432,
        database="insurance_mvp",
        user="adityarao",
        password="The_sunday",
    )

    rows = await conn.fetch("SELECT * FROM policies")

    structured_output = []

    for row in rows:
        structured_output.append(dict(row))

    # Pretty JSON output
    print(json.dumps(structured_output, indent=4, default=str))

    await conn.close()


asyncio.run(main())