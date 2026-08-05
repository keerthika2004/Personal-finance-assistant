import asyncio
from sqlalchemy.future import select
from backend.app.db.database import AsyncSessionLocal
from backend.app.db.models import Transaction

async def main():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Transaction))
        txs = result.scalars().all()
        for t in txs:
            print(f"ID: {t.id}, Date: {t.date}, Amount: {t.amount}, Desc: {t.raw_description}, Status: {t.status}")

asyncio.run(main())
