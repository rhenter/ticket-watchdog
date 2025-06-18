import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.testclient import WebSocketTestSession

import src.alerts as alerts_module
import src.database as database_module
import src.main as main_module
import src.scheduler as scheduler_module
from src import settings
from src.database import Base

_orig_receive_json = WebSocketTestSession.receive_json


def _patched_receive_json(self, *args, **kwargs):
    # ignore any args/kwargs (e.g. timeout) and delegate to original
    return _orig_receive_json(self)


WebSocketTestSession.receive_json = _patched_receive_json


@pytest.fixture(scope="session")
def engine():
    """
    Create an in-memory SQLite engine for tests,
    with StaticPool so the same connection is reused.
    """
    url = "sqlite:///:memory:"
    engine = create_engine(
        url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True
    )
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture(scope="function")
def db_session(engine):
    """
    Provide a fresh transactional session for each test.
    Any changes are rolled back after the test.
    """
    # Open a connection and begin a transaction
    connection = engine.connect()
    transaction = connection.begin()
    SessionTest = sessionmaker(bind=connection, expire_on_commit=False, future=True)
    session = SessionTest()

    # Establish a SAVEPOINT for nested transactions
    session.begin_nested()

    # Restart SAVEPOINT after each nested rollback (needed for some libraries)
    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(sess, trans):
        if trans.nested and not trans._parent.nested:
            sess.begin_nested()

    try:
        yield session
    finally:
        session.close()
        # Roll back outer transaction, cleaning up all changes
        transaction.rollback()
        connection.close()


@pytest.fixture(autouse=True)
def override_session_local(db_session, monkeypatch):
    """
    Monkey-patch SessionLocal everywhere so that all parts of the app
    (endpoints, alerts, scheduler) use the same test session.
    """
    # Patch the core factory
    monkeypatch.setattr(database_module, "SessionLocal", lambda: db_session)
    # Also patch the copies imported in scheduler.py and alerts.py
    monkeypatch.setattr(scheduler_module, "SessionLocal", lambda: db_session)
    monkeypatch.setattr(alerts_module, "SessionLocal", lambda: db_session)

    # Override FastAPI’s get_db() as well
    main_module.app.dependency_overrides[main_module.get_db] = lambda: db_session  # type: ignore[attr-defined]

    yield


@pytest.fixture(autouse=True)
def set_dummy_slack_webhook(monkeypatch):
    monkeypatch.setattr(settings, "SLACK_WEBHOOK_URL", "http://test-slack.local")
    yield
