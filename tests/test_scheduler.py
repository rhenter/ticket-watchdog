from datetime import datetime, timedelta, timezone

from src import scheduler, models


def test_evaluate_slas_triggers_alert(monkeypatch, db_session):
    # Fake config: target 1 minute so breach immediately
    monkeypatch.setattr(scheduler, "get_sla_config", lambda: {"gold": {"high": {"response": 1, "resolution": 2}}})
    # Chunk SessionLocal
    monkeypatch.setattr(scheduler, "SessionLocal", lambda: db_session)
    # Capture created alerts
    created = []
    monkeypatch.setattr(scheduler.crud, "create_alert",
                        lambda db, tid, sla_type, state, details: created.append((tid, sla_type, state)))
    # Create ticket older than 2 minutes
    old_time = datetime.now(timezone.utc) - timedelta(minutes=2)
    ticket = models.Ticket(
        id="sched-test",
        priority="high",
        customer_tier="gold",
        created_at=old_time,
        updated_at=old_time
    )
    db_session.add(ticket)
    db_session.commit()
    scheduler.evaluate_slas()
    assert created, "Expected at least one alert"
