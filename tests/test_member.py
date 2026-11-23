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
    assert r.status_code == 403  # Требуется членство

def test_remove_member_and_lose_access(client, make_user):
    owner = make_user("o@g.nsu.ru")
    member = make_user("m@g.nsu.ru")
    sid = client.post(
        "/spaces", headers=owner["headers"],
        json={"name": "S", "owner_id": 1, "access_mode": "private"}
    ).json()["id"]

    # Принудительно добавляем member в БД (имитация принятия инвайта)
    from tests.conftest import TestingSessionLocal
    from backend.models import SpaceMember
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