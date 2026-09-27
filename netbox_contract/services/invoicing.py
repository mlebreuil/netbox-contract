"""
Invoice amounts from contract lines: the pre-fill of a new invoice (FR-017..FR-020) and the lines
generated when an invoice is created (FR-021..FR-025). Both use the rules of calculations.py.
"""

import re
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation

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
    unit_price: Decimal | None = None
    accounting_dimensions: list | None = None

    def __post_init__(self):
        if self.unit_price is None:
            self.unit_price = self.contract_line.unit_price


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


def _get_list(data, key):
    if hasattr(data, 'getlist'):
        return data.getlist(key)
    value = data.get(key)
    if value is None:
        return []
    return list(value) if isinstance(value, (list, tuple)) else [value]


def _dimensions(data, prefix):
    """Accounting dimensions chosen in the preview for a row, or None when the row has no dimension field."""
    from ..models import AccountingDimension

    if not data.get(f'{prefix}-dimensions'):
        return None
    ids = [value for value in _get_list(data, f'{prefix}-accounting_dimensions') if str(value).isdigit()]
    return list(AccountingDimension.objects.filter(pk__in=ids).order_by('name', 'value'))


def check_dimensions(label, dimensions):
    """The rules of the invoice line form: no two dimensions of the same name, mandatory dimensions present."""
    from django.conf import settings

    names = [dimension.name for dimension in dimensions]
    errors = []
    if len(names) != len(set(names)):
        errors.append(_('{line}: two accounting dimensions have the same name.').format(line=label))
    for name in settings.PLUGINS_CONFIG['netbox_contract'].get('mandatory_dimensions') or []:
        if name not in names:
            errors.append(_('{line}: the accounting dimension {name} is missing.').format(line=label, name=name))
    return errors


def parse_line_overrides(data):
    """
    Quantities and unit prices typed in the preview of a new invoice (FR-032), from fields named
    `line-<contract line id>-quantity` and `line-<contract line id>-unit_price`. An empty quantity means
    no quantity; an empty unit price keeps the price of the contract line. Returns (overrides, errors).
    """
    overrides, errors = {}, []
    for key in data:
        match = re.fullmatch(r'line-(\d+)-(quantity|unit_price)', key)
        if not match:
            continue
        pk, field = int(match.group(1)), match.group(2)
        value = (data.get(key) or '').strip()
        if not value:
            if field == 'quantity':
                overrides.setdefault(pk, {})['quantity'] = None
            continue
        try:
            overrides.setdefault(pk, {})[field] = Decimal(value)
        except InvalidOperation:
            errors.append(_('"{value}" is not a valid number.').format(value=value))
    for key in data:
        match = re.fullmatch(r'line-(\d+)-dimensions', key)
        if match:
            overrides.setdefault(int(match.group(1)), {})['accounting_dimensions'] = _dimensions(
                data, f'line-{match.group(1)}'
            )
    return overrides, errors


@dataclass
class ExtraLine:
    """A line added to a new invoice in the preview, without contract line (FR-032)."""

    index: int
    description: str = ''
    unit: object = None
    unit_price: Decimal | None = None
    quantity: Decimal | None = None
    amount: Decimal | None = None
    accounting_dimensions: list = field(default_factory=list)
    raw: dict = field(default_factory=dict)

    @property
    def blank(self):
        return not any(self.raw.get(name) for name in ('description', 'unit', 'unit_price', 'quantity'))


def parse_extra_lines(data):
    """
    Lines added in the preview of a new invoice, from fields named `extra-<n>-description`, `extra-<n>-unit`,
    `extra-<n>-unit_price` and `extra-<n>-quantity`. A line left empty is ignored when the invoice is saved; a
    line partly filled needs a unit price and a quantity. Returns (lines, errors).
    """
    from ..models import Unit

    raw = {}
    for key in data:
        match = re.fullmatch(r'extra-(\d+)-(description|unit|unit_price|quantity)', key)
        if match:
            raw.setdefault(int(match.group(1)), {})[match.group(2)] = (data.get(key) or '').strip()
    lines, errors = [], []
    for index in sorted(raw):
        values = raw[index]
        line = ExtraLine(
            index=index,
            description=values.get('description', ''),
            accounting_dimensions=_dimensions(data, f'extra-{index}') or [],
            raw=values,
        )
        lines.append(line)
        if line.blank:
            continue
        label = line.description or _('added line {number}').format(number=index + 1)
        if values.get('unit'):
            line.unit = Unit.objects.filter(pk=values['unit']).first() if values['unit'].isdigit() else None
            if line.unit is None:
                errors.append(_('Unknown unit for {line}.').format(line=label))
        try:
            line.unit_price = Decimal(values['unit_price']) if values.get('unit_price') else None
            line.quantity = Decimal(values['quantity']) if values.get('quantity') else None
        except InvalidOperation:
            errors.append(_('The unit price and the quantity of {line} must be numbers.').format(line=label))
            continue
        if line.unit_price is None or line.quantity is None:
            errors.append(_('{line} needs a unit price and a quantity.').format(line=label))
    return lines, errors


def price_extra_lines(contract, period_start, period_end, extra_lines):
    """Calculate the amount of the complete added lines, as for any invoice line with a unit price."""
    for line in extra_lines:
        if line.blank or line.unit_price is None or line.quantity is None:
            line.amount = None
            continue
        line.amount = calculations.invoice_line_amount(
            line.unit.billing_method if line.unit else calculations.USAGE,
            line.quantity, line.unit_price, line.unit.months if line.unit else None,
            period_start, period_end, None, None, default_months=contract.invoice_frequency or 1,
        )
    return [line for line in extra_lines if line.amount is not None]


def lines_to_generate(contract, period_start, period_end, overrides=None):
    """
    The invoice lines a new invoice of this contract gets (FR-021, FR-022, FR-025), with the quantities and
    unit prices typed in the preview of the new invoice, if any (FR-032).
    """
    lines = _plan(contract, period_start, period_end, for_generation=True).lines
    for planned in lines:
        override = (overrides or {}).get(planned.contract_line.pk) or {}
        dimensions = override.get('accounting_dimensions')
        planned.accounting_dimensions = (
            list(planned.contract_line.accounting_dimensions.all()) if dimensions is None else dimensions
        )
        if not override.keys() - {'accounting_dimensions'}:
            continue
        line = planned.contract_line
        planned.quantity = override.get('quantity', planned.quantity)
        planned.unit_price = override.get('unit_price') or planned.unit_price
        planned.amount = calculations.invoice_line_amount(
            line.unit.billing_method, planned.quantity, planned.unit_price, line.unit.months, period_start,
            period_end, line.effective_start_date, line.effective_end_date,
            default_months=contract.invoice_frequency or 1,
        )
    return lines


def check_new_invoice(
    contract, amount, period_start, period_end, overrides=None, extra_lines=(), check_line_dimensions=False
):
    """
    Errors refusing the creation of a new invoice for a contract: a non-billable contract (FR-023) or an
    amount lower than the total of the lines to generate (FR-021).
    """
    try:
        planned = lines_to_generate(contract, period_start, period_end, overrides)
    except InvoicingError as e:
        return [e.message]
    added = price_extra_lines(contract, period_start, period_end, list(extra_lines))
    if check_line_dimensions:
        errors = [
            error
            for label, dimensions in (
                *((str(line.contract_line), line.accounting_dimensions) for line in planned),
                *((line.description or _('added line'), line.accounting_dimensions) for line in added),
            )
            for error in check_dimensions(label, dimensions)
        ]
        if errors:
            return errors
    total = calculations.round_amount(sum((line.amount for line in [*planned, *added]), Decimal(0)))
    if amount is not None and amount < total:
        return [
            _(
                'The invoice amount {amount} is lower than the total {total} of the invoice lines generated from '
                'the contract lines.'
            ).format(amount=amount, total=total)
        ]
    return []


def generate_invoice_lines(invoice, overrides=None, extra_lines=()):
    """
    Create the invoice lines of a new invoice linked to one billable contract: one line per applicable contract
    line, referencing it and carrying its accounting dimensions. Called only at invoice creation.
    """
    contracts = list(invoice.contracts.all())
    if len(contracts) != 1 or invoice.template:
        return []
    created = []
    for planned in lines_to_generate(contracts[0], invoice.period_start, invoice.period_end, overrides):
        invoice_line = InvoiceLine(
            invoice=invoice,
            contract_line=planned.contract_line,
            unit=planned.contract_line.unit,
            unit_price=planned.unit_price,
            quantity=planned.quantity,
            amount=planned.amount,
            currency=invoice.currency,
            comments=planned.contract_line.description,
        )
        invoice_line.save()
        invoice_line.accounting_dimensions.set(planned.accounting_dimensions)
        created.append(invoice_line)
    for added in price_extra_lines(contracts[0], invoice.period_start, invoice.period_end, list(extra_lines)):
        invoice_line = InvoiceLine(
            invoice=invoice,
            unit=added.unit,
            unit_price=added.unit_price,
            quantity=added.quantity,
            amount=added.amount,
            currency=invoice.currency,
            comments=added.description,
        )
        invoice_line.save()
        invoice_line.accounting_dimensions.set(added.accounting_dimensions)
        created.append(invoice_line)
    return created
