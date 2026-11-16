from pathlib import Path
from uuid import uuid4
#ЭТУ ручку проверить прям надо, я честно не понял как её реализовать нормально
# пока придумал только вынести в разные ручки мб чето
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    UploadFile,
    status,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import (
    get_current_user,
    get_db,
    get_space_or_404,
    require_space_access,
    require_space_owner,
)
from app.core.error import AppError
from app.services.ingest import ingest_document
from backend.models import Document, User
from backend.schemas.document import DocumentResponse

router = APIRouter(tags=["documents"])

STORAGE_ROOT = Path("storage")
ALLOWED_EXTENSIONS = {"pdf", "docx", "txt"}
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB


@router.post(
    "/spaces/{space_id}/documents",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    space_id: int,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentResponse:
    space = get_space_or_404(db, space_id)
    require_space_owner(space, current_user)

    raw_name = file.filename or ""
    safe_name = Path(raw_name).name
    if "." not in safe_name:
        raise AppError(400, "invalid_file_type", "Файл без расширения")

    ext = safe_name.rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise AppError(
            400,
            "invalid_file_type",
            f"Разрешены только: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    content = await file.read()
    if not content:
        raise AppError(400, "empty_file", "Файл пустой")
    if len(content) > MAX_FILE_SIZE:
        raise AppError(
            400,
            "file_too_large",
            f"Максимум {MAX_FILE_SIZE // (1024 * 1024)} MB",
        )

    storage_name = f"{uuid4().hex}_{safe_name}"
    file_dir = STORAGE_ROOT / "spaces" / str(space_id) / "documents"
    file_dir.mkdir(parents=True, exist_ok=True)
    file_path = file_dir / storage_name
    file_path.write_bytes(content)

    doc = Document(
        space_id=space_id,
        uploaded_by=current_user.id,
        source_name=safe_name,
        file_path=str(file_path),
        file_type=ext,
        file_size=len(content),
        status="pending",
    )
    try:
        db.add(doc)
        db.commit()
        db.refresh(doc)
    except Exception:
        file_path.unlink(missing_ok=True)
        raise

    background_tasks.add_task(ingest_document, doc.id)
    return DocumentResponse.model_validate(doc)


@router.get(
    "/spaces/{space_id}/documents",
    response_model=list[DocumentResponse],
)
def list_documents(
    space_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[DocumentResponse]:
    space = get_space_or_404(db, space_id)
    require_space_access(db, space, current_user)

    rows = db.scalars(
        select(Document)
        .where(Document.space_id == space_id)
        .order_by(Document.created_at.desc())
    ).all()
    return [DocumentResponse.model_validate(d) for d in rows]


@router.get(
    "/spaces/{space_id}/documents/{document_id}",
    response_model=DocumentResponse,
)
def get_document(
    space_id: int,
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentResponse:
    space = get_space_or_404(db, space_id)
    require_space_access(db, space, current_user)

    doc = db.get(Document, document_id)
    if doc is None or doc.space_id != space_id:
        raise AppError(404, "document_not_found", "Документ не найден")
    return DocumentResponse.model_validate(doc)


@router.delete(
    "/spaces/{space_id}/documents/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_document(
    space_id: int,
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    space = get_space_or_404(db, space_id)
    require_space_owner(space, current_user)

    doc = db.get(Document, document_id)
    if doc is None or doc.space_id != space_id:
        raise AppError(404, "document_not_found", "Документ не найден")

    file_path = Path(doc.file_path)
    db.delete(doc)
    db.commit()

    try:
        file_path.unlink(missing_ok=True)
    except OSError:
        pass  # файл удалить не удалось — не ломаем ответ