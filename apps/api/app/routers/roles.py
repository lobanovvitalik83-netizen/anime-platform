from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import require_permission
from app.models import Permission, Role
from app.schemas import RoleCreate, RoleOut, RoleUpdate

router = APIRouter()


@router.get("", response_model=list[RoleOut])
def list_roles(db: Session = Depends(get_db), _=Depends(require_permission("roles.view"))):
    return list(db.scalars(select(Role).order_by(Role.id)).unique().all())


@router.post("", response_model=RoleOut)
def create_role(payload: RoleCreate, db: Session = Depends(get_db), _=Depends(require_permission("roles.create"))):
    existing = db.scalar(select(Role).where((Role.name == payload.name) | (Role.slug == payload.slug)))
    if existing:
        raise HTTPException(status_code=400, detail="Role already exists")

    permissions = list(db.scalars(select(Permission).where(Permission.id.in_(payload.permission_ids))).all()) if payload.permission_ids else []
    role = Role(name=payload.name, slug=payload.slug, description=payload.description)
    role.permissions = permissions
    db.add(role)
    db.commit()
    db.refresh(role)
    return role


@router.patch("/{role_id}", response_model=RoleOut)
def update_role(role_id: int, payload: RoleUpdate, db: Session = Depends(get_db), _=Depends(require_permission("roles.update"))):
    role = db.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    if payload.name is not None:
        role.name = payload.name
    if payload.slug is not None:
        role.slug = payload.slug
    if payload.description is not None:
        role.description = payload.description
    if payload.permission_ids is not None:
        role.permissions = list(db.scalars(select(Permission).where(Permission.id.in_(payload.permission_ids))).all())

    db.add(role)
    db.commit()
    db.refresh(role)
    return role
