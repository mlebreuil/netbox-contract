"""
Amount calculations for contract lines and invoice lines.

Pure functions with no database access, shared by the models, the invoice pre-fill,
the generation of invoice lines, the API and the tests. Intermediate values are kept
as exact fractions and rounded once, at the end, to two decimals (ROUND_HALF_UP).
"""

import calendar
from datetime import timedelta
from decimal import ROUND_HALF_UP, Decimal
from fractions import Fraction

from dateutil.relativedelta import relativedelta

# Values of BillingMethodChoices (models.py), repeated here to keep this module free of model imports
ONE_TIME = 'one_time'
RECURRING = 'recurring'
USAGE = 'usage'

TWO_PLACES = Decimal('0.01')


def round_amount(value):
    """Round an exact value (Fraction, Decimal or int) to two decimals, half away from zero."""
    value = Fraction(value)
    scaled = abs(value) * 100
    cents = int(scaled)
    if scaled - cents >= Fraction(1, 2):
        cents += 1
    if value < 0:
        cents = -cents
    return (Decimal(cents) / 100).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def _fraction(value):
    return Fraction(0) if value is None else Fraction(value)


def months_between(start, end):
    """
    Number of months covered by the range start..end (both days included): whole calendar months
    from the start date, plus the leftover days divided by the number of days of the month in which
    the range ends. 1 January to 20 March is 2 + 20/31.
    """
    after_end = end + timedelta(days=1)
    if after_end <= start:
        return Fraction(0)
    months = (after_end.year - start.year) * 12 + after_end.month - start.month
    while months > 0 and start + relativedelta(months=months) > after_end:
        months -= 1
    leftover = (after_end - (start + relativedelta(months=months))).days
    days_in_end_month = calendar.monthrange(end.year, end.month)[1]
    return months + Fraction(leftover, days_in_end_month)


def overlap_days(period_start, period_end, line_start, line_end):
    """Days (both ends included) of the period covered by a line; a missing line date is open-ended."""
    start = max(period_start, line_start) if line_start else period_start
    end = min(period_end, line_end) if line_end else period_end
    return max((end - start).days + 1, 0)


def recurring_invoice_amount(quantity, unit_price, unit_months, period_start, period_end, line_start, line_end):
    """
    Amount of a recurring line for an invoice period (FR-018): quantity x unit price x (months of the
    period) / (months of the unit), multiplied by (days covered by the line) / (days of the period)
    when the line only partly covers the period.
    """
    if period_start is None or period_end is None:
        raise ValueError('An invoice period is needed to calculate a recurring amount')
    period_days = (period_end - period_start).days + 1
    if period_days <= 0:
        return round_amount(0)
    covered = Fraction(overlap_days(period_start, period_end, line_start, line_end), period_days)
    value = (
        _fraction(quantity) * _fraction(unit_price) * months_between(period_start, period_end)
        / Fraction(unit_months) * covered
    )
    return round_amount(value)


def recurring_months_amount(quantity, unit_price, unit_months, months):
    """Amount of a recurring line for a number of months, used when an invoice has no period."""
    return round_amount(_fraction(quantity) * _fraction(unit_price) * Fraction(months) / Fraction(unit_months))


def usage_amount(quantity, unit_price):
    """Amount of a usage-based line: quantity x unit price; no quantity yet gives 0."""
    return round_amount(_fraction(quantity) * _fraction(unit_price))


def line_total_value(billing_method, quantity, unit_price, unit_months, start, end):
    """
    Total value of a contract line over its dates: recurring lines over their dates, one-time lines once,
    usage-based lines at their stated quantity. None (not available) for a recurring line without start
    or end date.
    """
    if billing_method == RECURRING:
        if start is None or end is None:
            return None
        return round_amount(
            _fraction(quantity) * _fraction(unit_price) * months_between(start, end) / Fraction(unit_months)
        )
    return round_amount(_fraction(quantity) * _fraction(unit_price))


def line_yearly_value(billing_method, quantity, unit_price, unit_months):
    """Twelve-month equivalent of a recurring line; 0 for other lines."""
    if billing_method != RECURRING:
        return round_amount(0)
    return round_amount(_fraction(quantity) * _fraction(unit_price) * 12 / Fraction(unit_months))


def invoice_line_amount(
    billing_method, quantity, unit_price, unit_months, period_start, period_end, line_start, line_end,
    default_months=None,
):
    """
    Calculated amount of an invoice line that references a contract line (research D7). Without an invoice
    period, a recurring line counts for `default_months` (the contract's invoice frequency) when it is given.
    """
    if billing_method == RECURRING:
        if (period_start is None or period_end is None) and default_months:
            return recurring_months_amount(quantity, unit_price, unit_months, default_months)
        return recurring_invoice_amount(
            quantity, unit_price, unit_months, period_start, period_end, line_start, line_end
        )
    return usage_amount(quantity, unit_price)


def remaining(total, invoiced):
    """What remains to invoice of a total, never past zero (a credit stays a credit)."""
    rest = total - invoiced
    if total >= 0:
        return max(rest, Decimal(0))
    return min(rest, Decimal(0))


def ranges_overlap(period_start, period_end, line_start, line_end):
    """Whether a line (missing dates are open-ended) overlaps a period (missing dates are open-ended)."""
    if period_end and line_start and line_start > period_end:
        return False
    return not (period_start and line_end and line_end < period_start)
