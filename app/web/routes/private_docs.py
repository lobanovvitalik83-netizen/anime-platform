from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.database import get_db_session
from app.web.auth import get_current_admin_from_request

router = APIRouter(include_in_schema=False)

@router.get("/admin/api-docs")
def private_docs(request: Request, db: Session = Depends(get_db_session)):
    admin = get_current_admin_from_request(request, db)
    if not admin or admin.role != "superadmin":
        raise HTTPException(status_code=403, detail="Недостаточно прав.")
    return get_swagger_ui_html(openapi_url="/admin/private-openapi.json", title="Private API docs")

@router.get("/admin/private-openapi.json")
def private_openapi(request: Request, db: Session = Depends(get_db_session)):
    admin = get_current_admin_from_request(request, db)
    if not admin or admin.role != "superadmin":
        raise HTTPException(status_code=403, detail="Недостаточно прав.")
    schema = request.app.openapi()
    return JSONResponse(schema)
