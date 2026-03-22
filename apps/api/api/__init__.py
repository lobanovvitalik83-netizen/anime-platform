from api.routes.auth import router as auth_router
from api.routes.permissions import router as permissions_router
from api.routes.roles import router as roles_router
from api.routes.users import router as users_router

__all__ = ["auth_router", "permissions_router", "roles_router", "users_router"]
