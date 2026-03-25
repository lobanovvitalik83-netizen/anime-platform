import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.deps import require_permission
from app.models import ContentCard
from app.schemas import ContentCreate, ContentOut, ContentUpdate

router = APIRouter()


def content_to_out(item: ContentCard) -> ContentOut:
    tags = [tag for tag in item.tags.split(",") if tag] if item.tags else []
    return ContentOut.model_validate(
        {
            "id": item.id,
            "title": item.title,
            "description": item.description,
            "tags": tags,
            "media_type": item.media_type,
            "media_path": item.media_path,
            "status": item.status,
            "visibility": item.visibility,
            "created_at": item.created_at,
            "updated_at": item.updated_at,
        }
    )


@router.get("", response_model=list[ContentOut])
def list_content(db: Session = Depends(get_db), _=Depends(require_permission("content.view"))):
    items = list(db.scalars(select(ContentCard).order_by(ContentCard.id.desc())).all())
    return [content_to_out(item) for item in items]


@router.post("", response_model=ContentOut)
def create_content(payload: ContentCreate, db: Session = Depends(get_db), _=Depends(require_permission("content.create"))):
    item = ContentCard(
        title=payload.title,
        description=payload.description,
        tags=",".join(payload.tags),
        status=payload.status,
        visibility=payload.visibility,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return content_to_out(item)


@router.get("/{content_id}", response_model=ContentOut)
def get_content(content_id: int, db: Session = Depends(get_db), _=Depends(require_permission("content.view"))):
    item = db.get(ContentCard, content_id)
    if not item:
        raise HTTPException(status_code=404, detail="Content not found")
    return content_to_out(item)


@router.patch("/{content_id}", response_model=ContentOut)
def update_content(content_id: int, payload: ContentUpdate, db: Session = Depends(get_db), _=Depends(require_permission("content.update"))):
    item = db.get(ContentCard, content_id)
    if not item:
        raise HTTPException(status_code=404, detail="Content not found")

    if payload.title is not None:
        item.title = payload.title
    if payload.description is not None:
        item.description = payload.description
    if payload.tags is not None:
        item.tags = ",".join(payload.tags)
    if payload.status is not None:
        item.status = payload.status
    if payload.visibility is not None:
        item.visibility = payload.visibility

    db.add(item)
    db.commit()
    db.refresh(item)
    return content_to_out(item)


@router.delete("/{content_id}")
def delete_content(content_id: int, db: Session = Depends(get_db), _=Depends(require_permission("content.delete"))):
    item = db.get(ContentCard, content_id)
    if not item:
        raise HTTPException(status_code=404, detail="Content not found")
    db.delete(item)
    db.commit()
    return {"status": "deleted"}


@router.post("/{content_id}/upload-media", response_model=ContentOut)
def upload_media(
    content_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _=Depends(require_permission("media.upload")),
):
    item = db.get(ContentCard, content_id)
    if not item:
        raise HTTPException(status_code=404, detail="Content not found")

    extension = Path(file.filename or "").suffix
    unique_name = f"{uuid.uuid4().hex}{extension}"
    media_root = Path(settings.media_root)
    media_root.mkdir(parents=True, exist_ok=True)
    destination = media_root / unique_name

    with destination.open("wb") as output:
        output.write(file.file.read())

    item.media_path = str(destination)
    item.media_type = file.content_type or "application/octet-stream"
    db.add(item)
    db.commit()
    db.refresh(item)
    return content_to_out(item)
