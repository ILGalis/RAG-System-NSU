import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.main import app
from backend.db.connection import engine


@pytest.fixture(scope="session")
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture(autouse=True)
def clean_db() -> None:
    yield
    with engine.begin() as conn:
        conn.execute(
            text(
                "TRUNCATE space_members, rag_spaces, users "
                "RESTART IDENTITY CASCADE"
            )
        )