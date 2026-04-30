from django.conf import settings
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render

from .models import AuditLog


def _is_admin(user):
    return user.is_authenticated and (
        user.is_superuser or user.groups.filter(name=settings.ROLE_ADMIN).exists()
    )


@login_required
@user_passes_test(_is_admin)
def audit_log(request):
    qs = AuditLog.objects.select_related("actor", "content_type")
    action = request.GET.get("action")
    if action in {"create", "update", "delete"}:
        qs = qs.filter(action=action)
    else:
        action = ""
    tabs = [("", "All"), ("create", "Created"), ("update", "Updated"), ("delete", "Deleted")]
    return render(request, "audit/list.html", {"entries": qs[:500], "action": action, "tabs": tabs})
