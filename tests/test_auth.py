import hashlib
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from backend.models import User
from backend.models.email_token import EmailVerificationToken
from tests.conftest import TestingSessionLocal


def _sha(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


BASE_USER = {
    "email": "t@g.nsu.ru",
    "password": "strongpass123",
    "first_name": "Иван",
    "last_name": "Иванов",
}


# ---------- register ----------

def test_register_ok(client: TestClient):
    r = client.post("/auth/register", json=BASE_USER)
    assert r.status_code == 201, r.text
    assert r.json()["status"] == "pending_verification"


@pytest.mark.parametrize(
    "email",
    [
        "user@nsu.ru",
        "user@g.nsu.ru",
        "user@alembic.nsu.ru",
        "user@sub.alembic.nsu.ru",
    ],
)
def test_register_ok_domains(client: TestClient, email):
    r = client.post(
        "/auth/register",
        json={**BASE_USER, "email": email},
    )
    assert r.status_code == 201, r.text


@pytest.mark.parametrize(
    "email",
    [
        "user@gmail.com",
        "user@fake-nsu.ru",
        "user@nsu.ru.evil.com",
        "user@nsu.rux",
    ],
)
def test_register_bad_domains(client: TestClient, email):
    r = client.post(
        "/auth/register",
        json={**BASE_USER, "email": email},
    )
    assert r.status_code == 400, r.text
    assert r.json()["error"]["code"] == "invalid_domain"


def test_register_duplicate(client: TestClient):
    assert client.post("/auth/register", json=BASE_USER).status_code == 201
    r = client.post("/auth/register", json=BASE_USER)
    assert r.status_code == 409, r.text


def test_register_case_insensitive_duplicate(client: TestClient):
    r1 = client.post(
        "/auth/register",
        json={**BASE_USER, "email": "User@G.NSU.RU"},
    )
    assert r1.status_code == 201, r1.text

    r2 = client.post(
        "/auth/register",
        json={**BASE_USER, "email": "user@g.nsu.ru"},
    )
    assert r2.status_code == 409, r2.text


def test_register_short_password(client: TestClient):
    r = client.post(
        "/auth/register",
        json={**BASE_USER, "password": "123"},
    )
    assert r.status_code == 422


def test_register_missing_name(client: TestClient):
    r = client.post(
        "/auth/register",
        json={"email": "t@g.nsu.ru", "password": "strongpass123"},
    )
    assert r.status_code == 422


# ---------- login / verify ----------

def test_login_before_verify(client: TestClient):
    client.post("/auth/register", json=BASE_USER)
    r = client.post(
        "/auth/login",
        json={"email": BASE_USER["email"], "password": BASE_USER["password"]},
    )
    assert r.status_code == 403, r.text
    assert r.json()["error"]["code"] == "email_not_verified"


def test_verify_flow(client: TestClient):
    client.post("/auth/register", json=BASE_USER)

    raw = "known-token"
    with TestingSessionLocal() as db:
        user = db.scalar(
            select(User).where(User.email == BASE_USER["email"].lower())
        )
        assert user is not None
        db.add(
            EmailVerificationToken(
                user_id=user.id,
                token_hash=_sha(raw),
                expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            )
        )
        db.commit()

    assert client.post("/auth/verify-email", json={"token": raw}).status_code == 200
    # одноразовый
    assert client.post("/auth/verify-email", json={"token": raw}).status_code == 400
    # логин работает
    assert client.post(
        "/auth/login",
        json={"email": BASE_USER["email"], "password": BASE_USER["password"]},
    ).status_code == 200


def test_verify_bad_token(client: TestClient):
    r = client.post("/auth/verify-email", json={"token": "garbage"})
    assert r.status_code == 400


def test_login_wrong_password(client: TestClient, make_user):
    u = make_user()
    r = client.post(
        "/auth/login",
        json={"email": u["email"], "password": "wrong"},
    )
    assert r.status_code == 401


def test_login_unknown_user(client: TestClient):
    r = client.post(
        "/auth/login",
        json={"email": "nobody@g.nsu.ru", "password": "strongpass123"},
    )
    assert r.status_code == 401


def test_login_returns_user_fields(client: TestClient, make_user):
    u = make_user(first_name="Пётр", last_name="Петров", role="student")
    r = client.post(
        "/auth/login",
        json={"email": u["email"], "password": u["password"]},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert "access_token" in body
    assert body["user"]["first_name"] == "Пётр"
    assert body["user"]["last_name"] == "Петров"
    assert body["user"]["role"] == "student"


def test_me_endpoint(client: TestClient, make_user):
    u = make_user(first_name="Анна", last_name="Сидорова")
    r = client.get("/auth/me", headers=u["headers"])
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["first_name"] == "Анна"
    assert body["last_name"] == "Сидорова"


# ---------- spaces ----------

def test_spaces_unauthorized(client: TestClient):
    assert client.get("/spaces").status_code == 401


def test_spaces_invalid_token(client: TestClient):
    r = client.get("/spaces", headers={"Authorization": "Bearer garbage"})
    assert r.status_code == 401

def test_login_downgrades_role_when_not_in_teachers(client: TestClient, monkeypatch):
    from backend.core import roles

    email = "ex-teacher@g.nsu.ru"
    payload = {
        "email": email,
        "password": "strongpass123",
        "first_name": "Ex",
        "last_name": "Teacher",
    }
    assert client.post("/auth/register", json=payload).status_code == 201

    # подтверждаем email руками и ставим teacher
    with TestingSessionLocal() as db:
        user = db.scalar(select(User).where(User.email == email))
        user.is_email_verified = True
        user.role = "teacher"
        db.commit()

    # в списке преподавателей его нет → login должен понизить
    monkeypatch.setattr(roles, "TEACHER_EMAILS", set())

    r = client.post("/auth/login", json={"email": email, "password": "strongpass123"})
    assert r.status_code == 200, r.text
    assert r.json()["user"]["role"] == "student"


def test_login_promotes_role_when_in_teachers(client: TestClient, monkeypatch):
    from backend.core import roles

    email = "new-teacher@g.nsu.ru"
    payload = {
        "email": email,
        "password": "strongpass123",
        "first_name": "New",
        "last_name": "Teacher",
    }
    assert client.post("/auth/register", json=payload).status_code == 201

    with TestingSessionLocal() as db:
        user = db.scalar(select(User).where(User.email == email))
        user.is_email_verified = True
        db.commit()

    monkeypatch.setattr(roles, "TEACHER_EMAILS", {email})

    r = client.post("/auth/login", json={"email": email, "password": "strongpass123"})
    assert r.status_code == 200, r.text
    assert r.json()["user"]["role"] == "teacher"