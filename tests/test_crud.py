from datetime import datetime, timezone

from src import crud, schemas, models


def test_create_and_get_ticket(db_session):
    event = schemas.TicketEvent(
        id="test-id",
        priority="high",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        status="open",
        customer_tier="gold"
    )
    # Create
    ticket = crud.create_ticket(db_session, event)
    assert ticket.id == "test-id"
    # Retrieve
    fetched = crud.get_ticket(db_session, "test-id")
    assert fetched.id == ticket.id
    # List
    all_tickets = crud.list_tickets(db_session)
    assert any(t.id == "test-id" for t in all_tickets)


def test_update_ticket_idempotency(db_session):
    now = datetime.now(timezone.utc)
    event_old = schemas.TicketEvent(
        id="idempotent",
        priority="low",
        created_at=now,
        updated_at=now,
        status="open",
        customer_tier="silver"
    )
    ticket = crud.create_ticket(db_session, event_old)
    # Update with older timestamp: no change
    event_older = schemas.TicketEvent(
        id="idempotent",
        priority="medium",
        created_at=now,
        updated_at=now,
        status="closed",
        customer_tier="silver"
    )
    updated = crud.update_ticket(db_session, event_older)
    assert updated.priority == "low"
    # Update with newer timestamp
    later = now.replace(year=now.year + 1)
    event_new = schemas.TicketEvent(
        id="idempotent",
        priority="medium",
        created_at=now,
        updated_at=later,
        status="closed",
        customer_tier="silver"
    )
    updated_new = crud.update_ticket(db_session, event_new)
    assert updated_new.priority == "medium"
    assert any(h.status == "closed" for h in updated_new.status_history)


def test_create_alert_increments_escalation(db_session):
    # Setup ticket
    ticket = models.Ticket(
        id="alert-test",
        priority="high",
        customer_tier="gold",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db_session.add(ticket)
    db_session.commit()
    # Create alert
    alert = crud.create_alert(db_session, "alert-test", "response", models.SLAState.ALERT, {"foo": "bar"})
    assert alert.ticket_id == "alert-test"
    # Check escalation increment
    updated_ticket = crud.get_ticket(db_session, "alert-test")
    assert updated_ticket.escalation_level == 1
