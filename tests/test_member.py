from backend.models import SpaceMember
from tests.conftest import TestingSessionLocal


def test_list_members(client, make_user):
    owner = make_user("o@g.nsu.ru")
    member = make_user("m@g.nsu.ru")
    
    # Создаем пространство владельцем
    sid = client.post(
        "/spaces", headers=owner["headers"],
        json={"name": "S", "owner_id": 1, "access_mode": "private"}
    ).json()["id"]

    # Владелец видит только себя
    r = client.get(f"/spaces/{sid}/members", headers=owner["headers"])
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["user_id"] == owner["user_id"]

    # Чужой не видит
    r = client.get(f"/spaces/{sid}/members", headers=member["headers"])
    assert r.status_code == 403
    assert r.json()["error"]["code"] == "access_denied"


def test_remove_member_and_lose_access(client, make_user):
    owner = make_user("o@g.nsu.ru")
    member = make_user("m@g.nsu.ru")
    sid = client.post(
        "/spaces", headers=owner["headers"],
        json={"name": "S", "owner_id": 1, "access_mode": "private"}
    ).json()["id"]

    # Принудительно добавляем member в БД (имитация принятия инвайта)
    with TestingSessionLocal() as db:
        db.add(SpaceMember(space_id=sid, user_id=member["user_id"], role="student"))
        db.commit()

    # Теперь он видит
    assert client.get(f"/spaces/{sid}/members", headers=member["headers"]).status_code == 200

    # Владелец удаляет его
    r = client.delete(f"/spaces/{sid}/members/{member['user_id']}", headers=owner["headers"])
    assert r.status_code == 204

    # Он теряет доступ
    assert client.get(f"/spaces/{sid}/members", headers=member["headers"]).status_code == 403
    assert client.get(f"/spaces/{sid}", headers=member["headers"]).status_code == 403


def test_cannot_remove_owner(client, make_user):
    owner = make_user("o@g.nsu.ru")
    sid = client.post(
        "/spaces", headers=owner["headers"],
        json={"name": "S", "owner_id": 1, "access_mode": "private"}
    ).json()["id"]

    r = client.delete(f"/spaces/{sid}/members/{owner['user_id']}", headers=owner["headers"])
    assert r.status_code == 403
    assert r.json()["error"]["code"] == "cannot_remove_owner"


def test_non_owner_cannot_remove_member(client, make_user):
    owner = make_user("o@g.nsu.ru")
    member1 = make_user("m1@g.nsu.ru")
    member2 = make_user("m2@g.nsu.ru")
    
    # 1. Создаем пространство
    sid = client.post(
        "/spaces", headers=owner["headers"],
        json={"name": "S", "owner_id": 1, "access_mode": "private"}
    ).json()["id"]

    # 2. Добавляем member1 и member2 в БД
    with TestingSessionLocal() as db:
        db.add(SpaceMember(space_id=sid, user_id=member1["user_id"], role="student"))
        db.add(SpaceMember(space_id=sid, user_id=member2["user_id"], role="student"))
        db.commit()

    # 3. member1 пытается удалить member2
    r = client.delete(f"/spaces/{sid}/members/{member2['user_id']}", headers=member1["headers"])
    assert r.status_code == 403
    assert r.json()["error"]["code"] == "not_owner"

def test_duplicate_membership_with_another_code(client, make_user):
    owner = make_user("o@g.nsu.ru")
    student = make_user("s@g.nsu.ru")
    sid = client.post(
        "/spaces", headers=owner["headers"],
        json={"name": "S", "owner_id": 1, "access_mode": "private"}
    ).json()["id"]
    
    # Создаем 2 разных кода
    code1 = client.post(f"/spaces/{sid}/invitations", headers=owner["headers"], json={}).json()["code"]
    code2 = client.post(f"/spaces/{sid}/invitations", headers=owner["headers"], json={}).json()["code"]
    
    # Принимаем первый
    assert client.post("/invitations/accept", headers=student["headers"], json={"code": code1}).status_code == 200
    
    # Пытаемся принять второй
    r = client.post("/invitations/accept", headers=student["headers"], json={"code": code2})
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "already_member"
def test_invalid_ttl(client, make_user):
    owner = make_user("o@g.nsu.ru")
    sid = client.post(
        "/spaces", headers=owner["headers"],
        json={"name": "S", "owner_id": 1, "access_mode": "private"}
    ).json()["id"]

    # Отрицательный TTL
    r = client.post(f"/spaces/{sid}/invitations", headers=owner["headers"], json={"ttl_hours": -1})
    assert r.status_code == 422 # Pydantic вернет 422 на ошибку валидации поля

    # Слишком большой TTL
    r = client.post(f"/spaces/{sid}/invitations", headers=owner["headers"], json={"ttl_hours": 10**30})
    assert r.status_code == 422