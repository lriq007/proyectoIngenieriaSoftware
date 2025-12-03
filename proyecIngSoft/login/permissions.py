from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.shortcuts import redirect

ADMIN_GROUP = "ADMIN"
PROFESOR_GROUP = "PROFESOR"


def ensure_default_groups():
    """
    Crea los grupos base si aún no existen para evitar fallos
    en los flujos de login o filtros de queryset.
    """
    for name in (ADMIN_GROUP, PROFESOR_GROUP):
        Group.objects.get_or_create(name=name)


def user_has_role(user, role_name: str) -> bool:
    return user.is_authenticated and user.groups.filter(name=role_name).exists()


def is_admin(user) -> bool:
    # Permite superuser/staff como fallback además del grupo explícito.
    return user.is_superuser or user.is_staff or user_has_role(user, ADMIN_GROUP)


def is_profesor(user) -> bool:
    return user_has_role(user, PROFESOR_GROUP)


def _role_required(check_fn, error_message):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect("login:login")
            if not check_fn(request.user):
                messages.error(request, error_message)
                return redirect("login:login")
            return view_func(request, *args, **kwargs)

        return login_required(_wrapped)

    return decorator


def admin_required(view_func):
    return _role_required(is_admin, "No tienes permisos de administrador.")(view_func)


def profesor_required(view_func):
    # Un ADMIN también puede acceder a vistas de profesor para soporte.
    return _role_required(lambda u: is_profesor(u) or is_admin(u), "No tienes permisos de profesor.")(
        view_func
    )
