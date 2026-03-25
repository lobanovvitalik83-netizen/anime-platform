from pathlib import Path
from uuid import uuid4
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.api.deps import require_permission
from app.db.session import get_db
from app.models.content import ContentItem
from app.models.user import User
from app.schemas.content import ContentUpdate
from app.core.config import BASE_DIR

router = APIRouter(prefix="/content", tags=["content"])
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

def serialize_content(item: ContentItem) -> dict:
    return {
        "id": item.id,
        "title": item.title,
        "description": item.description,
        "tags": item.tags,
        "media_type": item.media_type,
        "media_path": item.media_path,
        "status": item.status,
        "visibility": item.visibility,
        "is_archived": item.is_archived,
        "created_at": item.created_at.isoformat() + "Z" if item.created_at else None,
        "updated_at": item.updated_at.isoformat() + "Z" if item.updated_at else None,
    }

@router.get("")
def list_content(db: Session = Depends(get_db), _: User = Depends(require_permission("content.view"))):
    return [serialize_content(item) for item in db.query(ContentItem).order_by(ContentItem.id.desc()).all()]

@router.get("/public")
def list_public_content(db: Session = Depends(get_db)):
    items = db.query(ContentItem).filter(ContentItem.status == "published", ContentItem.visibility == "public", ContentItem.is_archived == False).order_by(ContentItem.id.desc()).all()
    return [serialize_content(item) for item in items]

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_content(
    title: str = Form(...),
    description: str = Form(...),
    tags: str = Form(""),
    media_type: str = Form("image"),
    status_value: str = Form("draft", alias="status"),
    visibility: str = Form("public"),
    media_file: UploadFile | None = File(default=None),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("content.create")),
):
    media_path = None
    if media_file and media_file.filename:
        suffix = Path(media_file.filename).suffix
        filename = f"{uuid4().hex}{suffix}"
        file_path = UPLOAD_DIR / filename
        with file_path.open("wb") as fh:
            fh.write(await media_file.read())
        media_path = f"/api/v1/content/media/{filename}"
    item = ContentItem(
        title=title,
        description=description,
        tags=tags,
        media_type=media_type,
        media_path=media_path,
        status=status_value,
        visibility=visibility,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return serialize_content(item)

@router.patch("/{content_id}")
def update_content(content_id: int, payload: ContentUpdate, db: Session = Depends(get_db), _: User = Depends(require_permission("content.update"))):
    item = db.query(ContentItem).filter(ContentItem.id == content_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content not found")
    for field in ["title", "description", "tags", "status", "visibility", "is_archived"]:
        value = getattr(payload, field)
        if value is not None:
            setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return serialize_content(item)

@router.delete("/{content_id}")
def delete_content(content_id: int, db: Session = Depends(get_db), _: User = Depends(require_permission("content.delete"))):
    item = db.query(ContentItem).filter(ContentItem.id == content_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content not found")
    db.delete(item)
    db.commit()
    return {"status": "ok"}

@router.get("/media/{filename}")
def serve_media(filename: str):
    file_path = UPLOAD_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    return FileResponse(file_path)
