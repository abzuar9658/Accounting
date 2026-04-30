"""Template helpers for role-based UI hints."""
from django import template

register = template.Library()


@register.filter(name="in_group")
def in_group(user, group_name: str) -> bool:
    if not user or not user.is_authenticated:
        return False
    return user.groups.filter(name=group_name).exists()
