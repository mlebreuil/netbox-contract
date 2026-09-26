"""
Invoice amounts from contract lines: the pre-fill of a new invoice (FR-017..FR-020) and the lines
generated when an invoice is created (FR-021..FR-025). Both use the rules of calculations.py.
"""

from dataclasses import dataclass, field
from decimal import Decimal

from django.db.models import Sum
from django.utils.translation import gettext as _

from .. import calculations
from ..models import BillingMethodChoices, ContractLine, InvoiceLine, InvoiceStatusChoices


class InvoicingError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message


def not_billable_message(contract):
    return _(
        'The contract {contract} is not billable: its lines are invoiced through its closest billable parent.'
    ).format(contract=contract)


@dataclass
class ProposedLine:
    contract_line: ContractLine
    quantity: Decimal | None
    amount: Decimal


@dataclass
class Proposal:
    lines: list = field(default_factory=list)

    @property
    def total(self):
        return calculations.round_amount(sum((line.amount for line in self.lines), Decimal(0)))


def scope_lines(contract):
    """The contract lines invoiced under a billable contract: its own and those of its non-billable descendants."""
    return (
        ContractLine.objects.filter(contract__in=contract.billing_scope())
        .select_related('unit', 'contract')
        .prefetch_related('accounting_dimensions')
        .order_by('contract__pk', 'start_date', 'pk')
    )


def posted_totals(lines):
    """Quantity and amount already on Posted invoices, per contract line (Draft, Canceled and templates ignored)."""
    rows = (
        InvoiceLine.objects.filter(contract_line__in=lines, invoice__status=InvoiceStatusChoices.STATUS_POSTED)
        .exclude(invoice__template=True)
        .values('contract_line')
        .annotate(quantity=Sum('quantity'), amount=Sum('amount'))
    )
    return {row['contract_line']: (row['quantity'] or Decimal(0), row['amount'] or Decimal(0)) for row in rows}


def _plan(contract, period_start, period_end, for_generation):
    if not contract.billable:
        raise InvoicingError(not_billable_message(contract))
    lines = list(scope_lines(contract))
    posted = posted_totals(lines)
    proposal = Proposal()

    for line in lines:
        start, end = line.effective_start_date, line.effective_end_date
        if not calculations.ranges_overlap(period_start, period_end, start, end):
            continue
        method = line.unit.billing_method

        if method == BillingMethodChoices.USAGE:
            if for_generation:
                proposal.lines.append(ProposedLine(line, None, calculations.usage_amount(None, line.unit_price)))

        elif method == BillingMethodChoices.ONE_TIME:
            if line.invoiced_at_conversion:
                continue
            invoiced_quantity, invoiced_amount = posted.get(line.pk, (Decimal(0), Decimal(0)))
            quantity = calculations.remaining(line.quantity, invoiced_quantity)
            if for_generation:
                # The generated line gets the quantity still to invoice; its amount is calculated from it
                amount = calculations.usage_amount(quantity, line.unit_price)
            else:
                # FR-019: quantity x unit price minus the amounts already on Posted invoices
                total = calculations.round_amount(line.quantity * line.unit_price)
                amount = calculations.remaining(total, invoiced_amount)
            if not quantity or not amount:
                continue
            proposal.lines.append(ProposedLine(line, quantity, amount))

        else:
            # Without an invoice period, the line counts for one invoice frequency of the invoiced contract
            amount = calculations.invoice_line_amount(
                method, line.quantity, line.unit_price, line.unit.months, period_start, period_end, start, end,
                default_months=contract.invoice_frequency or 1,
            )
            proposal.lines.append(ProposedLine(line, line.quantity, amount))

    return proposal


def propose_invoice(contract, period_start, period_end):
    """
    Amounts proposed for a new invoice of a billable contract (FR-017..FR-019): recurring lines for the period,
    one-time lines for what remains to invoice, usage-based lines never (FR-017a). Without a period, recurring
    lines count for one invoice frequency. Raises InvoicingError for a non-billable contract (FR-008).
    """
    return _plan(contract, period_start, period_end, for_generation=False)


def lines_to_generate(contract, period_start, period_end):
    """The invoice lines a new invoice of this contract gets (FR-021, FR-022, FR-025)."""
    return _plan(contract, period_start, period_end, for_generation=True).lines


def check_new_invoice(contract, amount, period_start, period_end):
    """
    Errors refusing the creation of a new invoice for a contract: a non-billable contract (FR-023) or an
    amount lower than the total of the lines to generate (FR-021).
    """
    try:
        planned = lines_to_generate(contract, period_start, period_end)
    except InvoicingError as e:
        return [e.message]
    total = calculations.round_amount(sum((line.amount for line in planned), Decimal(0)))
    if amount is not None and amount < total:
        return [
            _(
                'The invoice amount {amount} is lower than the total {total} of the invoice lines generated from '
                'the contract lines.'
            ).format(amount=amount, total=total)
        ]
    return []


def generate_invoice_lines(invoice):
    """
    Create the invoice lines of a new invoice linked to one billable contract: one line per applicable contract
    line, referencing it and carrying its accounting dimensions. Called only at invoice creation.
    """
    contracts = list(invoice.contracts.all())
    if len(contracts) != 1 or invoice.template:
        return []
    created = []
    for planned in lines_to_generate(contracts[0], invoice.period_start, invoice.period_end):
        invoice_line = InvoiceLine(
            invoice=invoice,
            contract_line=planned.contract_line,
            quantity=planned.quantity,
            amount=planned.amount,
            currency=invoice.currency,
            comments=planned.contract_line.description,
        )
        invoice_line.save()
        invoice_line.accounting_dimensions.set(planned.contract_line.accounting_dimensions.all())
        created.append(invoice_line)
    return created
