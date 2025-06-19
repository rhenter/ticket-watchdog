from datetime import datetime, timedelta, timezone

from src import scheduler, models, crud


def test_evaluate_slas_triggers_alert(monkeypatch, db_session):
    # Fake config: target 1 minute so breach immediately
    monkeypatch.setattr(scheduler, "get_sla_config", lambda: {"gold": {"high": {"response": 1, "resolution": 2}}})
    # Chunk SessionLocal
    monkeypatch.setattr(scheduler, "SessionLocal", lambda: db_session)
    monkeypatch.setattr("src.scheduler.db", db_session)
    # Capture created alerts
    created = []
    monkeypatch.setattr("src.crud.create_alert", lambda db, tid, sla_type, state, details: created.append((tid, sla_type, state)))
    # Create ticket older than 2 minutes
    old_time = datetime.now(timezone.utc) - timedelta(minutes=2)
    ticket = models.Ticket(
        id="sched-test",
        priority="high",
        customer_tier="gold",
        created_at=old_time,
        updated_at=old_time,
        escalation_level=0
    )
    db_session.add(ticket)
    db_session.commit()
    scheduler.evaluate_slas()
    assert created, "Expected at least one alert"


def test_evaluate_slas_config_error(monkeypatch, db_session):
    # Simulate config error
    def bad_config():
        raise Exception("Config error!")
    monkeypatch.setattr(scheduler, "get_sla_config", bad_config)
    monkeypatch.setattr(scheduler, "SessionLocal", lambda: db_session)
    monkeypatch.setattr("src.scheduler.db", db_session)
    # Should not raise, just log error
    scheduler.evaluate_slas()


def test_evaluate_slas_db_error(monkeypatch, db_session):
    # Simulate DB error
    monkeypatch.setattr(scheduler, "get_sla_config", lambda: {"gold": {"high": {"response": 1, "resolution": 2}}})
    def bad_query(*args, **kwargs):
        raise Exception("DB error!")
    monkeypatch.setattr(db_session, "query", bad_query)
    monkeypatch.setattr(scheduler, "SessionLocal", lambda: db_session)
    monkeypatch.setattr("src.scheduler.db", db_session)
    # Should not raise, just log error
    scheduler.evaluate_slas()


def test_start_scheduler(monkeypatch):
    # Patch BackgroundScheduler to test start_scheduler
    started = {}
    class DummyScheduler:
        def add_job(self, *args, **kwargs):
            started["job"] = True
        def start(self):
            started["started"] = True
        def add_listener(self, *args, **kwargs):
            pass
    dummy_scheduler = DummyScheduler()
    monkeypatch.setattr("apscheduler.schedulers.background.BackgroundScheduler", lambda: dummy_scheduler)
    monkeypatch.setattr("src.scheduler.BackgroundScheduler", lambda: dummy_scheduler)
    scheduler.start_scheduler()
    assert started.get("job") and started.get("started")
