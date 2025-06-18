import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import src.alerts as alerts_module
from src.database import Base


@pytest.fixture(scope="session")
def engine():
    """Create an in-memory SQLite engine with StaticPool for tests."""
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
    """Provide a database session and ensure it is closed after each test."""
    SessionTest = sessionmaker(bind=engine, expire_on_commit=False, future=True)
    session = SessionTest()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(autouse=True)
def override_session_local(db_session, monkeypatch):
    """
    Monkey-patch alerts_module.SessionLocal so that
    process_alert() uses the test session instead of a new one.
    """
    monkeypatch.setattr(alerts_module, "SessionLocal", lambda: db_session)
