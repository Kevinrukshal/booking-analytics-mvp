from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Integer, JSON, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Upload(Base):
    __tablename__ = "uploads"
    id: Mapped[int] = mapped_column(primary_key=True)
    filename: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    booking_count: Mapped[int] = mapped_column(Integer, default=0)
    error_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(32), default="processing")
    summary: Mapped[dict] = mapped_column(JSON, default=dict)
    bookings: Mapped[list["Booking"]] = relationship(cascade="all, delete-orphan")
    errors: Mapped[list["ErrorRecord"]] = relationship(cascade="all, delete-orphan")


class Booking(Base):
    __tablename__ = "bookings"
    __table_args__ = (UniqueConstraint("upload_id", "booking_reference", name="uq_booking_upload_reference"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    upload_id: Mapped[int] = mapped_column(ForeignKey("uploads.id", ondelete="CASCADE"), index=True)
    booking_reference: Mapped[str] = mapped_column(String(64), index=True)
    booking_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    travel_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    agent: Mapped[str | None] = mapped_column(String(128), index=True)
    team: Mapped[str | None] = mapped_column(String(128), index=True)
    source: Mapped[str | None] = mapped_column(String(128))
    selling_cost: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    profit: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    booking_type: Mapped[str | None] = mapped_column(String(128))
    booking_status: Mapped[str | None] = mapped_column(String(64))
    payment_status: Mapped[str | None] = mapped_column(String(128))
    product_status: Mapped[str | None] = mapped_column(String(128), index=True)
    pending_products: Mapped[str | None] = mapped_column(Text)
    special_requests: Mapped[str | None] = mapped_column(Text)
    attachments_status: Mapped[str | None] = mapped_column(Text)
    quality_checks: Mapped[dict] = mapped_column(JSON, default=dict)
    raw_data: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ErrorRecord(Base):
    __tablename__ = "errors"
    id: Mapped[int] = mapped_column(primary_key=True)
    upload_id: Mapped[int] = mapped_column(ForeignKey("uploads.id", ondelete="CASCADE"), index=True)
    booking_reference: Mapped[str] = mapped_column(String(64), index=True)
    department: Mapped[str | None] = mapped_column(String(128))
    issue_date: Mapped[date | None] = mapped_column(Date, index=True)
    issue_text: Mapped[str] = mapped_column(Text)
    normalized_issue: Mapped[str] = mapped_column(Text)
    issue_hash: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    raw_status: Mapped[str | None] = mapped_column(String(128))
    responsible_agent: Mapped[str | None] = mapped_column(String(128), index=True)
    handled_agent: Mapped[str | None] = mapped_column(String(128), index=True)
    reported_to: Mapped[str | None] = mapped_column(String(128))
    remarks: Mapped[str | None] = mapped_column(Text)
    action_taken: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(128), index=True)
    severity: Mapped[str] = mapped_column(String(32), index=True)
    ai_category: Mapped[str | None] = mapped_column(String(128))
    ai_subcategory: Mapped[str | None] = mapped_column(String(128))
    ai_severity: Mapped[str | None] = mapped_column(String(32))
    ai_summary: Mapped[str | None] = mapped_column(Text)
    ai_recommended_action: Mapped[str | None] = mapped_column(Text)
    raw_data: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ErrorClassification(Base):
    __tablename__ = "error_classifications"
    id: Mapped[int] = mapped_column(primary_key=True)
    issue_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    payload: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

