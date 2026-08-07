import asyncio
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

load_dotenv(dotenv_path="backend/.env")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/finance_db")


async def migrate():
    print(f"Connecting to database: {DATABASE_URL}")
    engine = create_async_engine(DATABASE_URL)
    
    async with engine.begin() as conn:
        print("Adding missing 'user_id' columns to existing PostgreSQL tables...")
        await conn.execute(text("ALTER TABLE transactions ADD COLUMN IF NOT EXISTS user_id VARCHAR(100) DEFAULT 'demo_user';"))
        await conn.execute(text("ALTER TABLE statements ADD COLUMN IF NOT EXISTS user_id VARCHAR(100) DEFAULT 'demo_user';"))
        await conn.execute(text("ALTER TABLE user_goals ADD COLUMN IF NOT EXISTS user_id VARCHAR(100) DEFAULT 'demo_user';"))
        print("Successfully added 'user_id' column to transactions, statements, and user_goals tables!")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(migrate())
