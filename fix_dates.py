import asyncio
from datetime import datetime
from sqlalchemy.future import select
from backend.app.db.database import AsyncSessionLocal
from backend.app.db.models import Transaction

async def main():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Transaction))
        txs = result.scalars().all()
        for t in txs:
            old_date = t.date
            try:
                new_date = old_date.replace(month=old_date.day, day=old_date.month)
                t.date = new_date
                print(f"Updated {t.id} from {old_date} to {new_date}")
            except ValueError as e:
                print(f"Could not swap date for {t.id} ({old_date}): {e}")
        
        await session.commit()
        print("All dates fixed successfully.")

asyncio.run(main())
