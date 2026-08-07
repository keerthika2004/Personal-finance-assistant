import asyncio
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine
from backend.app.db.database import Base
from backend.app.db.models import User

load_dotenv(dotenv_path="backend/.env")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgrespassword@localhost:5433/financial_ai_db")

async def init():
    print(f"Connecting to database to create users table...")
    engine = create_async_engine(DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Users table created successfully!")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(init())
