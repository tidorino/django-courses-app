from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def instructor_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        profile = getattr(request.user, "profile", None)
        if not profile or not profile.is_instructor:
            raise PermissionDenied("You need an instructor account to access this page.")
        return view_func(request, *args, **kwargs)
    return wrapper
