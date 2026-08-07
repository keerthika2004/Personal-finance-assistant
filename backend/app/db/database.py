import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgrespassword@localhost:5432/financial_ai_db"
)

# Async Engine for PostgreSQL
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

# Async Session Factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

Base = declarative_base()


async def get_db():
    """Dependency for obtaining async DB sessions in FastAPI endpoints."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Initialize database tables asynchronously."""
    from sqlalchemy import text
    
    # Migrate existing ENUM columns to VARCHAR if needed (fixes asyncpg compatibility)
    async with engine.begin() as conn:
        try:
            await conn.execute(text(
                "ALTER TABLE transactions ALTER COLUMN status TYPE VARCHAR(50) USING status::text"
            ))
        except Exception:
            pass  # Table doesn't exist yet or column is already VARCHAR
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    import json
    from datetime import datetime
    from sqlalchemy import select
    from backend.app.db.models import Transaction, UserGoal, User
    
    async with AsyncSessionLocal() as session:
        user_query = await session.execute(select(User).where(User.id == "demo_user"))
        if not user_query.scalar_one_or_none():
            session.add(User(id="demo_user", email="demo@example.com", name="Demo User", password_hash="dummy"))
            await session.commit()
            
        tx_query = await session.execute(select(Transaction).where(Transaction.user_id == "demo_user"))
        if not tx_query.scalars().first():
            try:
                seed_path = os.path.join(os.path.dirname(__file__), "seed_data.json")
                if os.path.exists(seed_path):
                    with open(seed_path, 'r') as f:
                        seed_data = json.load(f)
                    for tx in seed_data.get('transactions', []):
                        session.add(Transaction(
                            id=tx['id'], user_id="demo_user", 
                            date=datetime.fromisoformat(tx['date']), amount=tx['amount'], 
                            category=tx['category'], normalized_merchant=tx['normalized_merchant'], 
                            raw_description=tx['normalized_merchant'], status="APPROVED"
                        ))
                    for goal in seed_data.get('goals', []):
                        session.add(UserGoal(
                            id=goal['id'], user_id="demo_user", goal_name=goal['goal_name'], 
                            target_amount=goal['target_amount'], current_amount=goal['current_amount'], 
                            category_target=goal['category_target']
                        ))
                    await session.commit()
            except Exception as e:
                print(f"Error seeding data: {e}")
