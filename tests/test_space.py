import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, text

from app.main import app
from backend.db.connection import SessionLocal, engine
from backend.models import User

def test_create_space_uses_current_user(client: TestClient, make_user):
    u = make_user()
    r = client.post(
        "/spaces",
        headers=u["headers"],
        json={"name": "Test Course", "owner_id": 999, "access_mode": "private"},
    )
    assert r.status_code == 201
    body = r.json()
    assert body["name"] == "Test Course"
    assert body["owner_id"] == u["user_id"]  # owner перезаписан на текущего
    assert body["id"] > 0


def test_list_spaces_requires_auth(client: TestClient):
    r = client.get("/spaces")
    assert r.status_code == 401


def test_list_spaces_only_own_and_public(client: TestClient, make_user):
    a = make_user("a@g.nsu.ru",role = "teacher")
    b = make_user("b@g.nsu.ru")

    client.post("/spaces", headers=a["headers"],
                json={"name": "A private", "owner_id": 1, "access_mode": "private"})
    client.post("/spaces", headers=a["headers"],
                json={"name": "A public", "owner_id": 1, "access_mode": "public"})

    r = client.get("/spaces", headers=b["headers"])
    assert r.status_code == 200
    names = [s["name"] for s in r.json()]
    assert "A public" in names
    assert "A private" not in names


def test_other_user_cannot_read_private(client: TestClient, make_user):
    a = make_user("a@g.nsu.ru")
    b = make_user("b@g.nsu.ru")
    sid = client.post("/spaces", headers=a["headers"],
                      json={"name": "A", "owner_id": 1, "access_mode": "private"}).json()["id"]

    r = client.get(f"/spaces/{sid}", headers=b["headers"])
    assert r.status_code == 403


def test_other_user_cannot_update_or_delete(client: TestClient, make_user):
    a = make_user("a@g.nsu.ru")
    b = make_user("b@g.nsu.ru")
    sid = client.post("/spaces", headers=a["headers"],
                      json={"name": "A", "owner_id": 1, "access_mode": "private"}).json()["id"]

    assert client.patch(f"/spaces/{sid}", headers=b["headers"],
                        json={"name": "Hacked"}).status_code == 403
    assert client.delete(f"/spaces/{sid}", headers=b["headers"]).status_code == 403

    # пространство живо
    assert client.get(f"/spaces/{sid}", headers=a["headers"]).status_code == 200


def test_get_space_not_found(client: TestClient, make_user):
    u = make_user()
    r = client.get("/spaces/9999", headers=u["headers"])
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "space_not_found"


def test_update_space_by_owner(client: TestClient, make_user):
    u = make_user()
    sid = client.post("/spaces", headers=u["headers"],
                      json={"name": "Old", "owner_id": 1, "access_mode": "private"}).json()["id"]
    r = client.patch(f"/spaces/{sid}", headers=u["headers"], json={"name": "New"})
    assert r.status_code == 200
    assert r.json()["name"] == "New"


def test_delete_space_by_owner(client: TestClient, make_user):
    u = make_user()
    sid = client.post("/spaces", headers=u["headers"],#faculty = "str",
                      json={"name": "To delete", "owner_id": 1, "access_mode": "private"}).json()["id"]
    assert client.delete(f"/spaces/{sid}", headers=u["headers"]).status_code == 204
    assert client.get(f"/spaces/{sid}", headers=u["headers"]).status_code == 404

def test_create_space_with_faculty_and_owner(client, make_user):
    u = make_user(
        "a@g.nsu.ru",
        first_name="Иван",
        last_name="Иванов",
        role="teacher",
        #faculty = "something",
    )
    r = client.post(
        "/spaces",
        headers=u["headers"],
        json={
            "name": "матанчик 1 курс",
            "faculty": "ММФ",
            "owner_id": 1,
            "access_mode": "private",
        },
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["faculty"] == "ММФ"
    assert body["owner"]["first_name"] == "Иван"
    assert body["owner"]["last_name"] == "Иванов"
    assert body["owner"]["email"] == "a@g.nsu.ru"


def test_create_space_faculty_defaults_to_empty(client, make_user):
    u = make_user()
    r = client.post(
        "/spaces",
        headers=u["headers"],
        json={"name": "Space", "owner_id": 1, "access_mode": "private"},
    )
    assert r.status_code == 201, r.text
    assert r.json()["faculty"] == ""


def test_list_spaces_includes_owner_info(client, make_user):
    u = make_user(first_name="Пётр", last_name="Петров",role = "teacher")
    client.post(
        "/spaces",
        headers=u["headers"],
        json={
            "name": "X",
            "faculty": "ФФ",
            "owner_id": 1,
            "access_mode": "public",
        },
    )
    # учитель, чтобы создать public
    r = client.get("/spaces", headers=u["headers"])
    assert r.status_code == 200, r.text
    spaces = r.json()
    assert spaces[0]["owner"]["first_name"] == "Пётр"
    assert spaces[0]["faculty"] == "ФФ"