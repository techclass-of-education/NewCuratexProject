from functools import wraps
from django.shortcuts import redirect
from django.http import HttpResponseForbidden


def role_required(*allowed_roles):

    def decorator(view_func):

        @wraps(view_func)
        def wrapper(request, *args, **kwargs):

            user = request.session.get("user")

            if not user:
                return redirect("login")

            role = user.get("role")

            if role not in allowed_roles:
                return redirect("access_denied")

            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator