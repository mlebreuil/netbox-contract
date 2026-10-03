"""
Amendment of the price or quantity of an invoiced contract line from a date (FR-030, decision I10).

The contract terms of an invoiced line are locked (FR-029). An amendment keeps them: the line ends the
day before the new terms apply, and a successor line with the new unit price or quantity starts that day.
Invoiced periods therefore keep their price, and the reason is recorded in the NetBox change log.
"""

from datetime import timedelta

from django.db import transaction
from django.db.models import Max, Q
from django.utils.translation import gettext as _

from ..models import BillingMethodChoices, ContractLine, Invoice, InvoiceStatusChoices


class AmendmentError(Exception):
    def __init__(self, errors):
        super().__init__(errors)
        self.errors = errors


def last_invoiced_date(line):
    """End of the last period invoiced for a line: invoices that reference it or that belong to its contract."""
    return (
        Invoice.objects.exclude(status=InvoiceStatusChoices.STATUS_CANCELED)
        .exclude(template=True)
        .filter(Q(invoicelines__contract_line=line) | Q(contracts=line.contract_id))
        .aggregate(last=Max('period_end'))['last']
    )


def check_amendment(line, effective_date, reason, unit_price, quantity):
    errors = {}
    if not (reason or '').strip():
        errors['reason'] = _('A reason is required; it is recorded in the change log.')
    if line.unit.billing_method == BillingMethodChoices.ONE_TIME:
        errors['__all__'] = _('A one-time line is invoiced once; its price or quantity cannot be amended.')
    elif line.replaced_by.exists():
        errors['__all__'] = _('This line was already amended; amend the line that replaces it.')
    new_price = line.unit_price if unit_price is None else unit_price
    new_quantity = line.quantity if quantity is None else quantity
    if (new_price, new_quantity) == (line.unit_price, line.quantity):
        errors['unit_price'] = _('Give a new unit price or a new quantity.')

    start, end = line.effective_start_date, line.effective_end_date
    if effective_date is None:
        errors['effective_date'] = _('This field is required.')
    elif start and effective_date <= start:
        errors['effective_date'] = _('The new terms must start after the start of the line ({date}).').format(
            date=start.isoformat()
        )
    elif end and effective_date > end:
        errors['effective_date'] = _('The new terms must start before the end of the line ({date}).').format(
            date=end.isoformat()
        )
    else:
        last = last_invoiced_date(line)
        if last and effective_date <= last:
            errors['effective_date'] = _(
                'The new terms must start after the last invoiced period, which ends on {date}.'
            ).format(date=last.isoformat())
    return errors, new_price, new_quantity


def amend_contract_line(line, effective_date, reason, unit_price=None, quantity=None):
    """
    End `line` the day before `effective_date` and create the line that replaces it with the new unit price
    and/or quantity. Returns the new line; raises AmendmentError with errors per field.
    """
    errors, new_price, new_quantity = check_amendment(line, effective_date, reason, unit_price, quantity)
    if errors:
        raise AmendmentError(errors)
    reason = reason.strip()

    with transaction.atomic():
        original_end = line.end_date
        if hasattr(line, 'snapshot'):
            line.snapshot()
        line.end_date = effective_date - timedelta(days=1)
        line._changelog_message = reason
        line.save()

        note = _('Amended from {date}: {reason}').format(date=effective_date.isoformat(), reason=reason)
        new = ContractLine(
            contract=line.contract,
            description=line.description,
            quantity=new_quantity,
            unit_price=new_price,
            unit=line.unit,
            currency=line.currency,
            start_date=effective_date,
            end_date=original_end,
            comments=f'{note}\n\n{line.comments}' if line.comments else note,
            custom_field_data=dict(line.custom_field_data),
            replaces=line,
        )
        new._changelog_message = reason
        new.save()
        new.accounting_dimensions.set(line.accounting_dimensions.all())
        new.tags.set(line.tags.all())
    return new
