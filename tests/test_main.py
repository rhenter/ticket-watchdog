import json
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from src import schemas
from src.main import app, get_db
from src.scheduler import evaluate_slas


@pytest.fixture(autouse=True)
def override_db(db_session):
    # Override dependency
    def _get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _get_db


client = TestClient(app)


def test_ingest_and_get_ticket():
    payload = {
        "id": "api-test",
        "priority": "low",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "status": "open",
        "customer_tier": "bronze"
    }
    # Ingest
    response = client.post("/tickets", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "api-test"
    # Retrieve
    get_resp = client.get(f"/tickets/{payload['id']}")
    assert get_resp.status_code == 200
    get_data = get_resp.json()
    assert get_data["id"] == "api-test"


def test_batch_ingestion_and_retrieval():
    # Prepare two ticket events
    now = datetime.now(timezone.utc).isoformat()
    event1 = {
        "id": "batch1",
        "priority": "high",
        "created_at": now,
        "updated_at": now,
        "status": "open",
        "customer_tier": "gold"
    }
    event2 = {
        "id": "batch2",
        "priority": "low",
        "created_at": now,
        "updated_at": now,
        "status": "open",
        "customer_tier": "silver"
    }
    # Ingest batch
    response = client.post("/tickets", json=[event1, event2])
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2
    ids = {t["id"] for t in data}
    assert ids == {"batch1", "batch2"}


def test_structured_logging_on_error(caplog):
    caplog.set_level("INFO")
    # Trigger 404 to log structured entry
    response = client.get("/tickets/notfound")
    assert response.status_code == 404
    # Last log record contains JSON
    record = caplog.records[-1]
    log_data = json.loads(record.getMessage())
    assert "correlation_id" in log_data
    assert log_data["path"] == "/tickets/notfound"
    assert log_data["status"] == 404
    assert "latency_ms" in log_data


def test_list_tickets_empty():
    response = client.get("/dashboard")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_dashboard_filter_by_state(monkeypatch):
    # Create one ticket that will generate an alert
    past = datetime.now(timezone.utc).replace(year=2000)
    event = schemas.TicketEvent(
        id="filter1",
        priority="high",
        created_at=past,
        updated_at=past,
        status="open",
        customer_tier="gold"
    )
    # Ingest
    client.post("/tickets", json=[event.dict()])
    # Force SLA config such that response threshold is 1 minute
    monkeypatch.setenv("SLA_CONFIG_PATH", "")
    monkeypatch.setattr("src.config.get_sla_config", lambda: {"gold": {"high": {"response": 1, "resolution": 1000}}})
    # Evaluate SLAs
    evaluate_slas()
    # Query dashboard for alerts
    response = client.get("/dashboard?state=alert")
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == "filter1"


def test_websocket_broadcast(monkeypatch):
    past = datetime.now(timezone.utc).replace(year=2000)
    event = schemas.TicketEvent(
        id="ws1",
        priority="high",
        created_at=past,
        updated_at=past,
        status="open",
        customer_tier="gold"
    )
    # Connect to WebSocket
    with client.websocket_connect("/ws/alerts") as ws:
        # Ingest and evaluate to trigger broadcast
        client.post("/tickets", json=[event.dict()])
        monkeypatch.setattr("src.config.get_sla_config",
                            lambda: {"gold": {"high": {"response": 1, "resolution": 1000}}})
        evaluate_slas()
        message = ws.receive_json(timeout=5)
        assert message["ticket_id"] == "ws1"
        assert message["state"] == "alert"
