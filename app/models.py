from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False
    )

    email_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    verification_code: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True
    )

    verification_expires: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    subscription_status: Mapped[str] = mapped_column(
        String(20),
        default="PENDING",
        nullable=False
    )

    subscription_started: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )

    subscription_expires: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )

    alerts_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )

    is_admin: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    reference: Mapped[str] = mapped_column(
        String(8),
        unique=True,
        index=True,
        nullable=False
    )

    user_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True
    )

    plan_id: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    amount: Mapped[float] = mapped_column(
        Numeric(12, 2),
        nullable=False
    )

    currency: Mapped[str] = mapped_column(
        String(10),
        default="USDT",
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="PENDING",
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )

    paid_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )

    user_reported_paid: Mapped[bool] = mapped_column(
        Boolean, default=False,
        nullable=False
    )
    user_reported_paid_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )

    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )