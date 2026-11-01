import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, text


from app.main import app
from backend.db.connection import SessionLocal,engine
from backend.models import User

@pytest.fixture(scope="session")
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture(autouse=True)
def clean_db() -> None:
    yield
    with engine.begin() as conn:
        conn.execute(
            text(
                "TRUNCATE email_verification_tokens, sessions, "
                "space_members, rag_spaces, users "
                "RESTART IDENTITY CASCADE"
            )
        )
@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def make_user(client: TestClient):
    def _make(
        email: str = "t@g.nsu.ru",
        password: str = "strongpass123",
        role: str = "student",
        verified: bool = True,
    ):
        r = client.post("/auth/register", json={"email": email, "password": password})
        assert r.status_code == 201, r.text

        with SessionLocal() as db:
            user = db.scalar(select(User).where(User.email == email))
            user.is_email_verified = verified
            user.role = role
            db.commit()
            user_id = user.id

        if not verified:
            return {"user_id": user_id, "headers": None, "email": email, "password": password}

        r = client.post("/auth/login", json={"email": email, "password": password})
        assert r.status_code == 200, r.text
        token = r.json()["access_token"]
        return {
            "user_id": user_id,
            "headers": {"Authorization": f"Bearer {token}"},
            "email": email,
            "password": password,
        }

    return _make