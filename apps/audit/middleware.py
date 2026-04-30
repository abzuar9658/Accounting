"""Thread-local store for the request's authenticated user.

The audit signal handlers run inside ``post_save`` / ``post_delete`` and
have no access to ``request``. This middleware stashes the current user
in a thread-local so the handlers can attribute writes to whoever is
logged in. Outside of an HTTP request (management commands, shell, async
tasks) the actor is simply ``None``.
"""
from threading import local

_state = local()


def get_current_user():
    return getattr(_state, "user", None)


def set_current_user(user) -> None:
    _state.user = user


def clear_current_user() -> None:
    if hasattr(_state, "user"):
        del _state.user


class CurrentUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        set_current_user(user if user and user.is_authenticated else None)
        try:
            return self.get_response(request)
        finally:
            clear_current_user()
