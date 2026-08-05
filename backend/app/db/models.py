import enum
import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Float, Boolean, DateTime, ForeignKey, Enum as SQLEnum, Text, Integer, Index
)
from sqlalchemy.orm import relationship
from backend.app.db.database import Base


class TransactionStatus(enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    FLAGGED = "FLAGGED"


class Account(Base):
    __tablename__ = "accounts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    institution_name = Column(String(100), nullable=False)
    account_number_last4 = Column(String(4), nullable=True)
    account_type = Column(String(50), nullable=False, default="Checking")  # Checking, Savings, Credit
    currency = Column(String(10), nullable=False, default="USD")
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    transactions = relationship("Transaction", back_populates="account", cascade="all, delete-orphan")


class Statement(Base):
    __tablename__ = "statements"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    file_name = Column(String(255), nullable=False)
    file_hash = Column(String(64), nullable=False, unique=True)
    file_type = Column(String(10), nullable=False, default="pdf")
    status = Column(String(50), nullable=False, default="INGESTED")  # INGESTED, RECONCILING, COMPLETED, ERROR
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    transactions = relationship("Transaction", back_populates="statement", cascade="all, delete-orphan")


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    account_id = Column(String(36), ForeignKey("accounts.id"), nullable=True)
    statement_id = Column(String(36), ForeignKey("statements.id"), nullable=True)
    
    date = Column(DateTime, nullable=False)
    amount = Column(Float, nullable=False)  # Positive for Income, Negative for Expense
    raw_description = Column(Text, nullable=False)
    normalized_merchant = Column(String(150), nullable=True)
    category = Column(String(100), nullable=False, default="Uncategorized")
    
    # Anomaly & Deduplication Flags
    is_duplicate = Column(Boolean, default=False)
    duplicate_of_id = Column(String(36), ForeignKey("transactions.id"), nullable=True)
    is_suspicious = Column(Boolean, default=False)
    anomaly_score = Column(Float, default=0.0)  # 0 to 100 risk score
    anomaly_reason = Column(Text, nullable=True)
    
    from sqlalchemy.dialects.postgresql import ENUM as PGEnum
    status = Column(PGEnum("PENDING", "APPROVED", "REJECTED", "FLAGGED", name="transactionstatus", create_type=False), default="PENDING", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    account = relationship("Account", back_populates="transactions")
    statement = relationship("Statement", back_populates="transactions")
    audit_logs = relationship("AuditLog", back_populates="transaction", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_tx_date", "date"),
        Index("idx_tx_category", "category"),
        Index("idx_tx_status", "status"),
    )


class UserGoal(Base):
    __tablename__ = "user_goals"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    goal_name = Column(String(150), nullable=False)
    target_amount = Column(Float, nullable=False)
    current_amount = Column(Float, default=0.0)
    category_target = Column(String(100), nullable=True)  # e.g., Dining, Travel, Savings
    target_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    transaction_id = Column(String(36), ForeignKey("transactions.id"), nullable=False)
    action = Column(String(50), nullable=False)  # APPROVE, REJECT, MANUAL_EDIT
    reason = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Relationship
    transaction = relationship("Transaction", back_populates="audit_logs")
