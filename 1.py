import asyncio
import asyncpg
import json
from dotenv import load_dotenv
import os
load_dotenv(".env")

async def main():
    conn = await asyncpg.connect(
        host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", 5432)),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASS"),
            ssl="require",   #THIS LINE IS IMPORTANT FOR NEON
           
    )

    rows = await conn.fetch("SELECT * FROM  customers")

    structured_output = []

    for row in rows:
        structured_output.append(dict(row))

    # Pretty JSON output
    print(json.dumps(structured_output, indent=4, default=str))

    await conn.close()


asyncio.run(main())