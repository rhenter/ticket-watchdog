from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from src import models, schemas


def get_ticket(db: Session, ticket_id: str) -> Optional[models.Ticket]:
    """
    Retrieve a ticket by its ID.
    """
    return db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()


def create_ticket(db: Session, ticket_event: schemas.TicketEvent) -> models.Ticket:
    """
    Create a new ticket and its initial status history.
    """
    ticket = models.Ticket(
        id=ticket_event.id,
        priority=ticket_event.priority,
        customer_tier=ticket_event.customer_tier,
        created_at=ticket_event.created_at,
        updated_at=ticket_event.updated_at
    )
    db.add(ticket)
    # Add initial status history
    status_history = models.TicketStatusHistory(
        ticket_id=ticket.id,
        status=ticket_event.status,
        timestamp=ticket_event.updated_at or datetime.utcnow()
    )
    db.add(status_history)
    db.commit()
    db.refresh(ticket)
    return ticket


def update_ticket(db: Session, ticket_event: schemas.TicketEvent) -> models.Ticket:
    """
    Update an existing ticket if the event is newer, or create it if not present.
    Maintains idempotency based on updated_at.
    """
    existing = get_ticket(db, ticket_event.id)
    if existing is None:
        return create_ticket(db, ticket_event)

    # Check event freshness (idempotency)
    if ticket_event.updated_at <= existing.updated_at:
        return existing

    # Update fields
    existing.priority = ticket_event.priority
    existing.customer_tier = ticket_event.customer_tier
    existing.updated_at = ticket_event.updated_at
    db.add(existing)

    # Add status history entry
    status_history = models.TicketStatusHistory(
        ticket_id=existing.id,
        status=ticket_event.status,
        timestamp=ticket_event.updated_at
    )
    db.add(status_history)

    db.commit()
    db.refresh(existing)
    return existing


def list_tickets(db: Session, skip: int = 0, limit: int = 100) -> List[models.Ticket]:
    """
    List tickets with pagination.
    """
    return db.query(models.Ticket).offset(skip).limit(limit).all()


def create_alert(
        db: Session,
        ticket_id: str,
        sla_type: str,
        state: models.SLAState,
        details: dict
) -> models.Alert:
    """
    Create an alert for a ticket and increment its escalation level.
    """
    alert = models.Alert(
        ticket_id=ticket_id,
        sla_type=sla_type,
        state=state,
        created_at=datetime.utcnow(),
        details=details
    )
    db.add(alert)

    # Update ticket's escalation level
    ticket = get_ticket(db, ticket_id)
    ticket.escalation_level += 1
    db.add(ticket)

    db.commit()
    db.refresh(alert)
    return alert
