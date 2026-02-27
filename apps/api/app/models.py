from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    String, Integer, DateTime, ForeignKey, Numeric, Text, UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    scopes: Mapped[str] = mapped_column(
        Text,
        default="accounts:read transfers:write",
        nullable=False,
    )  # space-separated

    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)

    currency: Mapped[str] = mapped_column(String(3), default="GBP", nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="open", nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    user: Mapped[User] = relationship("User")


class LedgerEntry(Base):
    __tablename__ = "ledger_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), index=True, nullable=False)

    entry_type: Mapped[str] = mapped_column(String(16), nullable=False)  # credit/debit
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)

    ref: Mapped[str] = mapped_column(String(64), index=True, nullable=False)  # transfer/payment id

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class Transfer(Base):
    __tablename__ = "transfers"
    __table_args__ = (
        UniqueConstraint("user_id", "idempotency_key", name="uq_transfer_idem"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)

    from_account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False)
    to_account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False)

    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="succeeded", nullable=False)

    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class Merchant(Base):
    __tablename__ = "merchants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class MerchantKey(Base):
    __tablename__ = "merchant_keys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    merchant_id: Mapped[int] = mapped_column(ForeignKey("merchants.id"), index=True, nullable=False)

    key_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)  # public id
    key_secret_hash: Mapped[str] = mapped_column(String(255), nullable=False)  # hash of secret

    scopes: Mapped[str] = mapped_column(Text, default="payments:write", nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    merchant: Mapped[Merchant] = relationship("Merchant")
