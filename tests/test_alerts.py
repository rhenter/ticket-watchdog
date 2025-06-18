from datetime import datetime

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
    monkeypatch.setattr("requests.post", lambda *args, **kwargs: DummyResponse(200))
    send_slack_notification("Test", [])
    # No exception means success


def test_process_alert_creates_and_notifies(monkeypatch, db_session):
    # Prepare ticket in DB
    ticket = models.Ticket(
        id="palert",
        priority="high",
        customer_tier="gold",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(ticket)
    db_session.commit()

    monkeypatch.setattr("requests.post", lambda *args, **kwargs: DummyResponse(200))
    # Process alert
    process_alert("palert", "response", models.SLAState.ALERT, {"a": 1})
    # Check alert persisted
    alert = db_session.query(models.Alert).filter_by(ticket_id="palert").first()
    assert alert is not None
