from django.db.models import QuerySet
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.utils.html import escape
from utilities.exceptions import AbortRequest

from .models import (
    CONTRACT_ON_POSTED_INVOICES_MESSAGE,
    POSTED_INVOICE_MESSAGE,
    Contract,
    ContractLine,
    InvoiceLine,
    _first_names,
)


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


@receiver(pre_delete, sender=InvoiceLine)
def protect_posted_invoice_line(sender, instance, origin=None, **kwargs):
    """Refuse deleting a line of a posted invoice, unless the invoice itself is deleted (FR-031)."""
    if isinstance(origin, QuerySet):
        direct = issubclass(origin.model, InvoiceLine)
    else:
        direct = isinstance(origin, InvoiceLine)
    if direct and instance.invoice_locked():
        raise AbortRequest(escape(POSTED_INVOICE_MESSAGE))


@receiver(pre_delete, sender=Contract)
def protect_contract_on_posted_invoices(sender, instance, origin=None, **kwargs):
    """Refuse a queryset deletion of a contract whose lines are on posted invoices (FR-031)."""
    if isinstance(origin, QuerySet) and issubclass(origin.model, Contract):
        numbers = instance.posted_invoice_numbers()
        if numbers:
            raise AbortRequest(escape(CONTRACT_ON_POSTED_INVOICES_MESSAGE.format(numbers=_first_names(numbers))))
