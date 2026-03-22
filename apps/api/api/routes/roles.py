from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from crud.role import create_role, get_role_by_slug, list_roles, update_role
from deps import get_db
from schemas import RoleCreate, RoleRead, RoleUpdate

router = APIRouter(prefix="/roles", tags=["roles"])


@router.get("", response_model=list[RoleRead])
def roles_list(db: Session = Depends(get_db)):
    return list_roles(db)


@router.post("", response_model=RoleRead, status_code=status.HTTP_201_CREATED)
def roles_create(payload: RoleCreate, db: Session = Depends(get_db)):
    return create_role(
        db,
        name=payload.name,
        slug=payload.slug,
        description=payload.description,
        permission_keys=payload.permission_keys,
    )


@router.patch("/{slug}", response_model=RoleRead)
def roles_update(slug: str, payload: RoleUpdate, db: Session = Depends(get_db)):
    role = get_role_by_slug(db, slug)
    if role is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")

    return update_role(
        db,
        role=role,
        name=payload.name,
        slug=payload.slug,
        description=payload.description,
        permission_keys=payload.permission_keys,
    )
