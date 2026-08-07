import asyncio
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

load_dotenv(dotenv_path="backend/.env")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgrespassword@localhost:5433/financial_ai_db")

async def inspect():
    engine = create_async_engine(DATABASE_URL)
    async with engine.begin() as conn:
        users = await conn.execute(text("SELECT id, email, name FROM users;"))
        print("\n--- USERS IN DATABASE ---")
        for u in users.fetchall():
            print(u)

        tx_counts = await conn.execute(text("SELECT user_id, COUNT(*), SUM(amount) FROM transactions GROUP BY user_id;"))
        print("\n--- TRANSACTIONS BY USER_ID ---")
        for row in tx_counts.fetchall():
            print(row)

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(inspect())
