from api.routes.permissions import router as permissions_router
from api.routes.roles import router as roles_router
from api.routes.users import router as users_router

__all__ = ["permissions_router", "roles_router", "users_router"]
