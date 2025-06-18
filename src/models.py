import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import (
    String,
    DateTime,
    Integer,
    ForeignKey,
    Enum,
    JSON,
)
from sqlalchemy.orm import relationship, mapped_column, Mapped

from src.database import Base


class SLAState(PyEnum):
    OK = "ok"
    ALERT = "alert"
    BREACH = "breach"


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    priority: Mapped[str] = mapped_column(String, nullable=False)
    customer_tier: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc),
                                                 nullable=False)
    escalation_level: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # relationships
    status_history: Mapped[list["TicketStatusHistory"]] = relationship("TicketStatusHistory", back_populates="ticket",
                                                                       cascade="all, delete-orphan")
    alerts: Mapped[list["Alert"]] = relationship("Alert", back_populates="ticket", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Ticket id={self.id} state={self.escalation_level}>"


class TicketStatusHistory(Base):
    __tablename__ = "ticket_status_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticket_id: Mapped[str] = mapped_column(String, ForeignKey("tickets.id"), nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    ticket: Mapped[Ticket] = relationship("Ticket", back_populates="status_history")

    def __repr__(self) -> str:
        return f"<StatusHistory ticket_id={self.ticket_id} status={self.status}>"


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticket_id: Mapped[str] = mapped_column(String, ForeignKey("tickets.id"), nullable=False)
    sla_type: Mapped[str] = mapped_column(String, nullable=False)  # e.g. "response" or "resolution"
    state: Mapped[SLAState] = mapped_column(Enum(SLAState), default=SLAState.ALERT, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    details: Mapped[dict] = mapped_column(JSON, default={})

    ticket: Mapped[Ticket] = relationship("Ticket", back_populates="alerts")

    def __repr__(self) -> str:
        return f"<Alert ticket_id={self.ticket_id} sla_type={self.sla_type} state={self.state}>"
