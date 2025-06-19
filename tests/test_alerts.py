from datetime import datetime, timezone

import pytest

from src import models
from src.alerts import process_alert
from src.utils.slack import send_slack_notification


class DummyResponse:
    def __init__(self, status_code=200):
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code != 200:
            raise Exception("HTTP error")


@pytest.fixture(autouse=True)
def dummy_env(monkeypatch):
    monkeypatch.setenv("SLACK_WEBHOOK_URL", "http://example.com/webhook")


def test_send_slack_notification_success(monkeypatch):
    # Simulate successful post
    monkeypatch.setattr("httpx.post", lambda *args, **kwargs: DummyResponse(200))
    send_slack_notification("Test", [])
    # No exception means success


def test_process_alert_creates_and_notifies(monkeypatch, db_session):
    # Prepare ticket in DB
    ticket = models.Ticket(
        id="palert",
        priority="high",
        customer_tier="gold",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        escalation_level=0
    )
    db_session.add(ticket)
    db_session.commit()

    monkeypatch.setattr("httpx.post", lambda *args, **kwargs: DummyResponse(200))
    # Monkeypatch alert creation to simulate DB insert
    created = []
    monkeypatch.setattr("src.crud.create_alert", lambda db, tid, sla_type, state, details: created.append((tid, sla_type, state)))
    # Process alert
    process_alert("palert", "response", models.SLAState.ALERT, {"a": 1})
    # Check alert persisted (simulated)
    assert created, "Alert was not created"


def test_send_slack_notification_http_error(monkeypatch):
    class DummyResponse:
        def __init__(self, status_code=500):
            self.status_code = status_code
        def raise_for_status(self):
            if self.status_code != 200:
                raise Exception("HTTP error")
    monkeypatch.setattr("httpx.post", lambda *args, **kwargs: DummyResponse(500))
    # Should not raise, just log error
    send_slack_notification("Test", [])


def test_send_slack_notification_no_webhook(monkeypatch):
    monkeypatch.setenv("SLACK_WEBHOOK_URL", "")
    send_slack_notification("Test", [])


def test_process_alert_ticket_not_found(monkeypatch, db_session):
    # Simulate missing ticket in DB
    monkeypatch.setattr("src.crud.create_alert", lambda db, tid, sla_type, state, details: (_ for _ in ()).throw(ValueError("Ticket not found")))
    # Should not raise, just log error
    process_alert("notfound", "response", models.SLAState.ALERT, {"a": 1})


def test_process_alert_slack_failure(monkeypatch, db_session):
    # Prepare ticket in DB
    ticket = models.Ticket(
        id="failalert",
        priority="high",
        customer_tier="gold",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        escalation_level=0
    )
    db_session.add(ticket)
    db_session.commit()
    # Simulate Slack failure
    class DummyResponse:
        def __init__(self, status_code=500):
            self.status_code = status_code
        def raise_for_status(self):
            if self.status_code != 200:
                raise Exception("HTTP error")
    monkeypatch.setattr("httpx.post", lambda *args, **kwargs: DummyResponse(500))
    # Should not raise, just log error
    process_alert("failalert", "response", models.SLAState.ALERT, {"a": 1})
