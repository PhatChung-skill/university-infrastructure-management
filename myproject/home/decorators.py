from functools import wraps
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from .models import AppUser


def admin_required(view_func):
    """Chỉ cho phép user có role 'Admin' (trong AppUser) truy cập."""

    @login_required
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        app_user = AppUser.objects.select_related("role").filter(
            username=request.user.username
        ).first()

        is_django_admin = getattr(request.user, "is_superuser", False) or getattr(request.user, "is_staff", False)
        is_app_admin = app_user and app_user.role and app_user.role.name.lower() == "admin"
        if not (is_django_admin or is_app_admin):
            return redirect("map_view")

        return view_func(request, *args, **kwargs)

    return _wrapped
