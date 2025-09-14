# admin/base.py
from starlette.requests import Request
from starlette.responses import RedirectResponse
from starlette_admin.auth import AuthProvider
from starlette_admin import BaseModelView, BaseAdmin

from open_webui.utils.auth import (
    get_current_user,
    get_http_authorization_cred,
)


class LabyAdminAuth(AuthProvider):
    async def is_authenticated(self, request: Request) -> bool:
        # Try to resolve the current user using existing auth utilities
        # Supports Authorization header (Bearer/API key) and fallback cookie token
        auth_header = request.headers.get("Authorization")
        try:
            user = get_current_user(
                request,
                None,  # no background tasks in this context
                get_http_authorization_cred(auth_header),
            )
        except Exception:
            return False

        if not user:
            return False

        # Admin panel access: restrict to admin role
        if getattr(user, "role", None) != "admin":
            return False

        # Stash for downstream views
        request.state.admin_user = user
        return True

    async def render_login(self, request: Request, admin: BaseAdmin):
        """Override the default login behavior to implement custom logic."""
        return RedirectResponse(url="/", status_code=307, headers=request.headers)

    def get_admin_user(self, request: Request):
        u = getattr(request.state, "admin_user", None)
        return {"name": getattr(u, "email", "unknown")}

class RBACView(BaseModelView):
    """Per-view role gates; override as needed in domain views."""
    async def can_create(self, request):  # admin only
        return "admin" in getattr(request.state.admin_user, "roles", [])
    async def can_edit(self, request):    # admin or staff
        return bool({"admin","staff"} & set(getattr(request.state.admin_user, "roles", [])))
    async def can_delete(self, request):  # admin only
        return "admin" in getattr(request.state.admin_user, "roles", [])
