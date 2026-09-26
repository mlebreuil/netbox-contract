from django.db.models import QuerySet
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.utils.html import escape
from utilities.exceptions import AbortRequest

from .models import ContractLine


def _deleted_directly(origin):
    """Whether a deletion was started on contract lines themselves, not cascaded from their contract."""
    if isinstance(origin, QuerySet):
        return issubclass(origin.model, ContractLine)
    return isinstance(origin, ContractLine)


@receiver(pre_delete, sender=ContractLine)
def protect_invoiced_contract_line(sender, instance, origin=None, **kwargs):
    """Refuse deleting a contract line once its contract is invoiced or an invoice line uses it (FR-029)."""
    if not _deleted_directly(origin):
        return
    message = instance.lock_message()
    if message:
        raise AbortRequest(escape(message))
