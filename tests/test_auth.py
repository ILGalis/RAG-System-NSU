import hashlib
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy import select

from backend.db.connection import SessionLocal
from backend.models import User
from backend.models.email_token import EmailVerificationToken


def _sha(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def test_register_wrong_domain(client: TestClient):
    r = client.post("/auth/register", json={"email": "x@gmail.com", "password": "strongpass123"})
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "invalid_domain"


def test_register_duplicate(client: TestClient):
    body = {"email": "t@g.nsu.ru", "password": "strongpass123"}
    assert client.post("/auth/register", json=body).status_code == 201
    r = client.post("/auth/register", json=body)
    assert r.status_code == 409


def test_register_short_password(client: TestClient):
    r = client.post("/auth/register", json={"email": "t@g.nsu.ru", "password": "123"})
    assert r.status_code == 422


def test_login_before_verify(client: TestClient):
    body = {"email": "t@g.nsu.ru", "password": "strongpass123"}
    client.post("/auth/register", json=body)
    r = client.post("/auth/login", json=body)
    assert r.status_code == 403
    assert r.json()["error"]["code"] == "email_not_verified"


def test_verify_flow(client: TestClient):
    body = {"email": "t@g.nsu.ru", "password": "strongpass123"}
    client.post("/auth/register", json=body)

    # руками кладём известный токен
    raw = "known-token"
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == "t@g.nsu.ru"))
        db.add(EmailVerificationToken(
            user_id=user.id,
            token_hash=_sha(raw),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        ))
        db.commit()

    assert client.post("/auth/verify-email", json={"token": raw}).status_code == 200
    # одноразовый
    assert client.post("/auth/verify-email", json={"token": raw}).status_code == 400
    # логин теперь работает
    assert client.post("/auth/login", json=body).status_code == 200


def test_verify_bad_token(client: TestClient):
    r = client.post("/auth/verify-email", json={"token": "garbage"})
    assert r.status_code == 400


def test_login_wrong_password(client: TestClient, make_user):
    u = make_user()
    r = client.post("/auth/login", json={"email": u["email"], "password": "wrong"})
    assert r.status_code == 401


def test_login_unknown_user(client: TestClient):
    r = client.post("/auth/login", json={"email": "nobody@g.nsu.ru", "password": "strongpass123"})
    assert r.status_code == 401


def test_spaces_unauthorized(client: TestClient):
    assert client.get("/spaces").status_code == 401


def test_spaces_invalid_token(client: TestClient):
    r = client.get("/spaces", headers={"Authorization": "Bearer garbage"})
    assert r.status_code == 401