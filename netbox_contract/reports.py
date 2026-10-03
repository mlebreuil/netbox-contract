"""
Detection of records whose currency does not match the record they belong to (FR-012).

Read-only: nothing is changed. Used by the "Report currency mismatches" custom script
(scripts/netbox-contract.py) and by the tests; the logic is kept here so that it can move
with the replacement of NetBox custom scripts (NetBox 4.7 work).
"""

from dataclasses import dataclass

from .models import Contract, ContractLine, Invoice, InvoiceLine


@dataclass
class CurrencyMismatch:
    kind: str
    object: object
    expected: str
    found: str
    url: str

    def __str__(self):
        return f'{self.kind} "{self.object}": currency {self.found.upper()}, expected {self.expected.upper()}'


def _mismatch(kind, obj, expected, found):
    return CurrencyMismatch(kind=kind, object=obj, expected=expected, found=found, url=obj.get_absolute_url())


def find_currency_mismatches():
    """List contract lines, invoices, invoice lines and non-billable child contracts with a mismatched currency."""
    mismatches = []

    for line in ContractLine.objects.select_related('contract').order_by('pk'):
        if line.currency != line.contract.currency:
            mismatches.append(_mismatch('contract line', line, line.contract.currency, line.currency))

    for invoice in Invoice.objects.prefetch_related('contracts').order_by('pk'):
        for contract in invoice.contracts.all():
            if invoice.currency != contract.currency:
                mismatches.append(_mismatch('invoice', invoice, contract.currency, invoice.currency))

    for line in InvoiceLine.objects.select_related('invoice').order_by('pk'):
        if line.currency != line.invoice.currency:
            mismatches.append(_mismatch('invoice line', line, line.invoice.currency, line.currency))

    children = Contract.objects.filter(parent__isnull=False, billable=False).select_related('parent').order_by('pk')
    for child in children:
        if child.currency != child.parent.currency:
            mismatches.append(_mismatch('non-billable child contract', child, child.parent.currency, child.currency))

    return mismatches
