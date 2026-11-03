import os

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import sessionmaker

load_dotenv()

from app.main import app
from app.api.deps import get_db
from backend.models import User

TEST_DATABASE_URL = os.environ["TEST_DATABASE_URL"]

test_engine = create_engine(TEST_DATABASE_URL, pool_pre_ping=True)
TestingSessionLocal = sessionmaker(
    bind=test_engine,
    autoflush=False,
    autocommit=False,
)


def _override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session", autouse=True)
def _apply_migrations():
    """Накатываем миграции на тестовую БД один раз за сессию."""
    from alembic import command
    from alembic.config import Config

    old = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL
    try:
        cfg = Config("alembic.ini")
        command.upgrade(cfg, "head")
    finally:
        if old is not None:
            os.environ["DATABASE_URL"] = old
        else:
            os.environ.pop("DATABASE_URL", None)
    yield


@pytest.fixture(scope="session")
def client() -> TestClient:
    app.dependency_overrides[get_db] = _override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def clean_db():
    yield
    with test_engine.begin() as conn:
        conn.execute(
            text(
                "TRUNCATE email_verification_tokens, sessions, "
                "space_members, rag_spaces, users "
                "RESTART IDENTITY CASCADE"
            )
        )


@pytest.fixture
def make_user(client: TestClient):
    def _make(
        email: str = "t@g.nsu.ru",
        password: str = "strongpass123",
        role: str = "student",
        verified: bool = True,
        first_name: str = "Test",
        last_name: str = "User",
    ):
        r = client.post(
            "/auth/register",
            json={
                "email": email,
                "password": password,
                "first_name": first_name,
                "last_name": last_name,
            },
        )
        assert r.status_code == 201, r.text

        # Подтверждаем email ДО логина (иначе login вернёт 403).
        # user_id нужен для verified=False и для возврата ниже.
        # Роль пока НЕ трогаем — login перезапишет её через resolve_role.
        with TestingSessionLocal() as db:
            user = db.scalar(select(User).where(User.email == email.lower()))
            assert user is not None
            user.is_email_verified = verified
            db.commit()
            user_id = user.id

        if not verified:
            return {
                "user_id": user_id,
                "headers": None,
                "email": email,
                "password": password,
            }

        r = client.post(
            "/auth/login",
            json={"email": email, "password": password},
        )
        assert r.status_code == 200, r.text
        token = r.json()["access_token"]

        # Роль ставим ПОСЛЕ login, иначе resolve_role её сбросит.
        # get_current_user читает роль из БД на каждом запросе,
        # так что для последующих запросов роль уже будет нужной.
        with TestingSessionLocal() as db:
            user = db.scalar(select(User).where(User.email == email.lower()))
            user.role = role
            db.commit()

        return {
            "user_id": user_id,
            "headers": {"Authorization": f"Bearer {token}"},
            "email": email,
            "password": password,
        }

    return _make