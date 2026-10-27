from fastapi.testclient import TestClient

from backend.db.connection import SessionLocal
from backend.models import User


def _create_user() -> int:
    with SessionLocal() as db:
        user = User(
            email="teacher@nsu.ru",
            password_hash="fake",
            role="teacher",
            is_email_verified=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user.id


def test_create_space(
    client: TestClient,
) -> None:
    user_id = _create_user()

    response = client.post(
        "/spaces",
        json={
            "name": "Test Course",
            "owner_id": user_id,
            "access_mode": "private",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Course"
    assert data["owner_id"] == user_id
    assert data["id"] > 0


def test_list_spaces(
    client: TestClient,
) -> None:
    user_id = _create_user()

    client.post(
        "/spaces",
        json={
            "name": "A",
            "owner_id": user_id,
            "access_mode": "private",
        },
    )
    client.post(
        "/spaces",
        json={
            "name": "B",
            "owner_id": user_id,
            "access_mode": "public",
        },
    )

    response = client.get(
        f"/spaces?user_id={user_id}",
    )

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_space_not_found(
    client: TestClient,
) -> None:
    response = client.get("/spaces/9999")

    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "space_not_found"


def test_update_space(
    client: TestClient,
) -> None:
    user_id = _create_user()

    created = client.post(
        "/spaces",
        json={
            "name": "Old",
            "owner_id": user_id,
            "access_mode": "private",
        },
    ).json()

    response = client.patch(
        f"/spaces/{created['id']}",
        json={"name": "New"},
    )

    assert response.status_code == 200
    assert response.json()["name"] == "New"


def test_delete_space(
    client: TestClient,
) -> None:
    user_id = _create_user()

    created = client.post(
        "/spaces",
        json={
            "name": "To delete",
            "owner_id": user_id,
            "access_mode": "private",
        },
    ).json()

    response = client.delete(
        f"/spaces/{created['id']}",
    )
    assert response.status_code == 204

    response = client.get(
        f"/spaces/{created['id']}",
    )
    assert response.status_code == 404