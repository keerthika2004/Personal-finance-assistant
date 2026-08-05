import asyncio
from sqlalchemy.future import select
from backend.app.db.database import AsyncSessionLocal
from backend.app.db.models import Transaction

async def main():
    async with AsyncSessionLocal() as session:
        # Delete my 5.0 dummy transaction
        result = await session.execute(select(Transaction).where(Transaction.id == '19b74013-566c-43fb-8c12-47ea2daf3ed1'))
        dummy = result.scalar_one_or_none()
        if dummy:
            await session.delete(dummy)
            print("Deleted dummy transaction.")
            
        # Update all PENDING to APPROVED
        result = await session.execute(select(Transaction).where(Transaction.status == "PENDING"))
        pending = result.scalars().all()
        for t in pending:
            t.status = "APPROVED"
            print(f"Approved transaction {t.id} ({t.amount})")
            
        await session.commit()
        print("Database fixed successfully.")

asyncio.run(main())
