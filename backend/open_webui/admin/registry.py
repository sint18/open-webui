# admin/registry.py
import importlib
import pkgutil
from starlette_admin.contrib.sqla import Admin
from open_webui.admin.base import LabyAdminAuth
from open_webui.internal.db import engine

from open_webui.admin.views.users import UserAdmin, User
from open_webui.admin.views.plans import PlanAdmin, Plan
from open_webui.admin.views.payment_orders import PaymentOrderAdmin, PaymentOrder
from open_webui.admin.views.user_credits import UserCreditAdmin, UserCredit
from open_webui.admin.views.quota_policies import QuotaPolicyAdmin, QuotaPolicy


def iter_modules(package_name: str):
    pkg = importlib.import_module(package_name)
    for m in pkgutil.walk_packages(pkg.__path__, prefix=pkg.__name__ + "."):
        if m.ispkg:
            continue
        yield m.name

def build_admin() -> Admin:
    admin = Admin(engine, title="Laby AI Admin", auth_provider=LabyAdminAuth())

    # Auto-discover all modules under admin.views.*
    # for module_name in iter_modules("open_webui.admin.views"):
    #     mod = importlib.import_module(module_name)
    #     views = getattr(mod, "VIEWS", None)
    #     if views:
    #         for v in views:
    #             admin.add_view(v)
    admin.add_view(UserAdmin(User))
    admin.add_view(PlanAdmin(Plan))
    admin.add_view(PaymentOrderAdmin(PaymentOrder))
    admin.add_view(UserCreditAdmin(UserCredit))
    admin.add_view(QuotaPolicyAdmin(QuotaPolicy))

    return admin
