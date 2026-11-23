from datetime import datetime, timezone, timedelta
from sqlalchemy import select
from backend.models import Invitation
from tests.conftest import TestingSessionLocal

def test_invitation_flow(client, make_user):
    owner = make_user("o@g.nsu.ru")
    student = make_user("s@g.nsu.ru")
    
    sid = client.post(
        "/spaces", headers=owner["headers"],
        json={"name": "S", "owner_id": 1, "access_mode": "private"}
    ).json()["id"]

    # 1. Создаем инвайт
    r = client.post(f"/spaces/{sid}/invitations", headers=owner["headers"], json={})
    assert r.status_code == 201
    code = r.json()["code"]
    inv_id = r.json()["id"]

    # 2. Студент принимает
    r = client.post("/invitations/accept", headers=student["headers"], json={"code": code})
    assert r.status_code == 200
    
    # 3. Студент теперь в пространстве
    r = client.get(f"/spaces/{sid}/members", headers=student["headers"])
    assert len(r.json()) == 2

    # 4. Повторное принятие тем же кодом - ошибка used
    r = client.post("/invitations/accept", headers=student["headers"], json={"code": code})
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "invalid_invitation"

def test_invitation_expired(client, make_user):
    owner = make_user("o@g.nsu.ru")
    student = make_user("s@g.nsu.ru")
    sid = client.post("/spaces", headers=owner["headers"], json={"name": "S", "owner_id": 1, "access_mode": "private"}).json()["id"]

    r = client.post(f"/spaces/{sid}/invitations", headers=owner["headers"], json={})
    code = r.json()["code"]

    # Искусственно сдвигаем время в БД
    with TestingSessionLocal() as db:
        inv = db.scalar(select(Invitation))
        inv.expires_at = datetime.now(timezone.utc) - timedelta(days=1)
        db.commit()

    r = client.post("/invitations/accept", headers=student["headers"], json={"code": code})
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "invalid_invitation"

def test_invitation_revoked(client, make_user):
    owner = make_user("o@g.nsu.ru")
    student = make_user("s@g.nsu.ru")
    sid = client.post("/spaces", headers=owner["headers"], json={"name": "S", "owner_id": 1, "access_mode": "private"}).json()["id"]

    r = client.post(f"/spaces/{sid}/invitations", headers=owner["headers"], json={})
    code, inv_id = r.json()["code"], r.json()["id"]

    # Отзываем
    assert client.delete(f"/spaces/{sid}/invitations/{inv_id}", headers=owner["headers"]).status_code == 204

    # Нельзя принять
    r = client.post("/invitations/accept", headers=student["headers"], json={"code": code})
    assert r.status_code == 400

def test_non_owner_cannot_manage_invites(client, make_user):
    owner = make_user("o@g.nsu.ru")
    student = make_user("s@g.nsu.ru")
    sid = client.post("/spaces", headers=owner["headers"], json={"name": "S", "owner_id": 1, "access_mode": "private"}).json()["id"]

    # Студент не может создать инвайт
    r = client.post(f"/spaces/{sid}/invitations", headers=student["headers"], json={})
    assert r.status_code == 403