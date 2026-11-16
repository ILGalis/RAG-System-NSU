from pathlib import Path
import pytest
from sqlalchemy import select

from backend.models import Document
from tests.conftest import TestingSessionLocal


PDF_BYTES = b"%PDF-1.4\nfake\n"
TXT_BYTES = b"hello\n"
@pytest.fixture(autouse=True)
def _no_ingest(monkeypatch):
    """BackgroundTasks не должны ходить в БД во время тестов."""
    monkeypatch.setattr(
        "app.api.routes.document",
        lambda *a, **kw: None,
    )

def _upload(client, headers, space_id, filename, content, mime="text/plain"):
    return client.post(
        f"/spaces/{space_id}/documents",
        headers=headers,
        files={"file": (filename, content, mime)},
    )


def _create_space(client, headers, *, name="S", access_mode="private"):
    return client.post(
        "/spaces",
        headers=headers,
        json={"name": name, "faculty": "", "owner_id": 1, "access_mode": access_mode},
    ).json()["id"]


def test_upload_txt_by_owner(client, make_user):
    u = make_user()
    sid = _create_space(client, u["headers"])
    r = _upload(client, u["headers"], sid, "notes.txt", TXT_BYTES)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["status"] == "pending"
    assert body["file_type"] == "txt"
    assert body["source_name"] == "notes.txt"
    assert isinstance(body["id"], str)
    assert isinstance(body["space_id"], str)
    assert body["space_id"] == str(sid)


def test_upload_rejects_non_owner(client, make_user):
    owner = make_user("o@g.nsu.ru")
    other = make_user("x@g.nsu.ru")
    sid = _create_space(client, owner["headers"])
    r = _upload(client, other["headers"], sid, "a.txt", TXT_BYTES)
    assert r.status_code == 403


def test_upload_rejects_bad_extension(client, make_user):
    u = make_user()
    sid = _create_space(client, u["headers"])
    r = _upload(client, u["headers"], sid, "virus.exe", b"x")
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "invalid_file_type"


def test_upload_rejects_empty_file(client, make_user):
    u = make_user()
    sid = _create_space(client, u["headers"])
    r = _upload(client, u["headers"], sid, "empty.txt", b"")
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "empty_file"


def test_list_documents_filters_by_space(client, make_user):
    u = make_user()
    sid1 = _create_space(client, u["headers"], name="one")
    sid2 = _create_space(client, u["headers"], name="two")
    _upload(client, u["headers"], sid1, "a.txt", TXT_BYTES)
    _upload(client, u["headers"], sid2, "b.txt", TXT_BYTES)

    r = client.get(f"/spaces/{sid1}/documents", headers=u["headers"])
    assert r.status_code == 200
    names = [d["source_name"] for d in r.json()]
    assert names == ["a.txt"]


def test_delete_document_removes_file(client, make_user):
    u = make_user()
    sid = _create_space(client, u["headers"])
    doc = _upload(client, u["headers"], sid, "gone.txt", TXT_BYTES).json()
    file_path = None
    with TestingSessionLocal() as db:
        row = db.scalar(select(Document).where(Document.id == int(doc["id"])))
        file_path = Path(row.file_path)
        assert file_path.exists()

    r = client.delete(f"/spaces/{sid}/documents/{doc['id']}", headers=u["headers"])
    assert r.status_code == 204
    assert not file_path.exists()


def test_document_not_found(client, make_user):
    u = make_user()
    sid = _create_space(client, u["headers"])
    r = client.get(f"/spaces/{sid}/documents/9999", headers=u["headers"])
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "document_not_found"