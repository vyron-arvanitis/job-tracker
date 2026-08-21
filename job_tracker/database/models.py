from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class ApplicationStatus(str, Enum):
    APPLIED = "applied"
    NO_RESPONSE = "no_response"
    HR_INTERVIEW = "hr_interview"
    TECHNICAL_INTERVIEW = "technical_interview"
    ASSESSMENT = "assessment"
    FINAL_INTERVIEW = "final_interview"
    REJECTED = "rejected"
    OFFER = "offer"
    WITHDRAWN = "withdrawn"
    UNKNOWN = "unknown"


class Application(Base):
    __tablename__ = "applications"
    __table_args__ = (UniqueConstraint("company_key", "position_key", name="uq_application_role"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company: Mapped[str] = mapped_column(String(255))
    position: Mapped[str] = mapped_column(String(500))
    company_key: Mapped[str] = mapped_column(String(255), index=True)
    position_key: Mapped[str] = mapped_column(String(500), index=True)
    applied_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_contact_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(50), default=ApplicationStatus.UNKNOWN.value)
    status_override: Mapped[str | None] = mapped_column(String(50))
    contact_email: Mapped[str | None] = mapped_column(String(320))
    next_action: Mapped[str | None] = mapped_column(String(500))
    source: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    emails: Mapped[list["Email"]] = relationship(back_populates="application")


class Email(Base):
    __tablename__ = "emails"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    gmail_message_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    gmail_thread_id: Mapped[str | None] = mapped_column(String(255), index=True)
    application_id: Mapped[int | None] = mapped_column(ForeignKey("applications.id"))
    sender: Mapped[str] = mapped_column(String(500))
    recipients: Mapped[str | None] = mapped_column(String(1000))
    subject: Mapped[str] = mapped_column(String(1000), default="")
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    body_text: Mapped[str | None] = mapped_column(Text)
    classification: Mapped[str | None] = mapped_column(String(100))
    company: Mapped[str | None] = mapped_column(String(255))
    position: Mapped[str | None] = mapped_column(String(500))
    is_sent: Mapped[bool] = mapped_column(default=False)
    application: Mapped[Application | None] = relationship(back_populates="emails")
