from django import template

from ..object_actions import can_amend as _can_amend

register = template.Library()


@register.filter
def can_amend(line, user):
    """`{% if object|can_amend:request.user %}`: the rule of the Amend button (research D6)."""
    return _can_amend(line, user)
