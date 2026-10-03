from datetime import date
from decimal import Decimal
from fractions import Fraction

from django.test import SimpleTestCase

from netbox_contract import calculations as calc
from netbox_contract.models import BillingMethodChoices


class MonthsBetweenTestCase(SimpleTestCase):
    def test_one_full_month(self):
        self.assertEqual(calc.months_between(date(2025, 1, 1), date(2025, 1, 31)), 1)

    def test_whole_months_plus_leftover_days(self):
        # 1 January to 20 March = 2 + 20/31
        self.assertEqual(calc.months_between(date(2025, 1, 1), date(2025, 3, 20)), 2 + Fraction(20, 31))

    def test_full_year(self):
        self.assertEqual(calc.months_between(date(2025, 1, 1), date(2025, 12, 31)), 12)

    def test_range_ending_in_february(self):
        self.assertEqual(calc.months_between(date(2025, 1, 1), date(2025, 2, 14)), 1 + Fraction(14, 28))

    def test_range_ending_in_february_of_leap_year(self):
        self.assertEqual(calc.months_between(date(2024, 1, 1), date(2024, 2, 14)), 1 + Fraction(14, 29))
        self.assertEqual(calc.months_between(date(2024, 2, 1), date(2024, 2, 29)), 1)

    def test_month_starting_mid_month(self):
        self.assertEqual(calc.months_between(date(2025, 1, 15), date(2025, 2, 14)), 1)

    def test_less_than_one_month(self):
        self.assertEqual(calc.months_between(date(2025, 4, 11), date(2025, 4, 30)), Fraction(20, 30))

    def test_single_day(self):
        self.assertEqual(calc.months_between(date(2025, 3, 5), date(2025, 3, 5)), Fraction(1, 31))

    def test_end_before_start(self):
        self.assertEqual(calc.months_between(date(2025, 3, 5), date(2025, 3, 1)), 0)


class RoundingTestCase(SimpleTestCase):
    def test_round_half_up(self):
        self.assertEqual(calc.round_amount(Fraction(1, 200)), Decimal('0.01'))
        self.assertEqual(calc.round_amount(Fraction(-1, 200)), Decimal('-0.01'))
        self.assertEqual(calc.round_amount(Fraction(1, 300)), Decimal('0.00'))
        self.assertEqual(calc.round_amount(Decimal('2.345')), Decimal('2.35'))

    def test_rounded_once_at_the_end(self):
        # 100 x 1/3 months each computed separately would give 33.33 x 3 = 99.99
        amount = calc.recurring_invoice_amount(
            Decimal(1), Decimal(100), 3, date(2025, 1, 1), date(2025, 1, 31), None, None
        )
        self.assertEqual(amount, Decimal('33.33'))
        amount = calc.recurring_invoice_amount(
            Decimal(1), Decimal(100), 3, date(2025, 1, 1), date(2025, 3, 31), None, None
        )
        self.assertEqual(amount, Decimal('100.00'))


class RecurringInvoiceAmountTestCase(SimpleTestCase):
    """Spec user story 5, scenarios 1 to 3, and partial periods."""

    def test_monthly_line_three_full_months(self):
        amount = calc.recurring_invoice_amount(
            Decimal(1), Decimal(100), 1, date(2025, 1, 1), date(2025, 3, 31), date(2025, 1, 1), date(2025, 12, 31)
        )
        self.assertEqual(amount, Decimal('300.00'))

    def test_yearly_unit_three_full_months(self):
        amount = calc.recurring_invoice_amount(
            Decimal(1), Decimal(120), 12, date(2025, 1, 1), date(2025, 3, 31), date(2025, 1, 1), date(2025, 12, 31)
        )
        self.assertEqual(amount, Decimal('30.00'))

    def test_line_starting_after_period_start(self):
        # 30-day period, line starts 10 days after the period start: 20 days out of 30
        amount = calc.recurring_invoice_amount(
            Decimal(1), Decimal(90), 1, date(2025, 4, 1), date(2025, 4, 30), date(2025, 4, 11), date(2025, 12, 31)
        )
        self.assertEqual(amount, Decimal('60.00'))

    def test_line_ending_before_period_end(self):
        amount = calc.recurring_invoice_amount(
            Decimal(1), Decimal(90), 1, date(2025, 4, 1), date(2025, 4, 30), date(2025, 1, 1), date(2025, 4, 20)
        )
        self.assertEqual(amount, Decimal('60.00'))

    def test_quarterly_unit(self):
        amount = calc.recurring_invoice_amount(
            Decimal(2), Decimal(300), 3, date(2025, 1, 1), date(2025, 1, 31), None, None
        )
        self.assertEqual(amount, Decimal('200.00'))

    def test_open_ended_line(self):
        amount = calc.recurring_invoice_amount(
            Decimal(1), Decimal(100), 1, date(2025, 1, 1), date(2025, 1, 31), None, None
        )
        self.assertEqual(amount, Decimal('100.00'))

    def test_no_overlap(self):
        amount = calc.recurring_invoice_amount(
            Decimal(1), Decimal(100), 1, date(2025, 1, 1), date(2025, 1, 31), date(2025, 2, 1), None
        )
        self.assertEqual(amount, Decimal('0.00'))

    def test_quantity(self):
        amount = calc.recurring_invoice_amount(
            Decimal('2.5'), Decimal(100), 1, date(2025, 1, 1), date(2025, 1, 31), None, None
        )
        self.assertEqual(amount, Decimal('250.00'))

    def test_zero_and_negative(self):
        args = (1, date(2025, 1, 1), date(2025, 1, 31), None, None)
        self.assertEqual(calc.recurring_invoice_amount(Decimal(0), Decimal(100), *args), Decimal('0.00'))
        self.assertEqual(calc.recurring_invoice_amount(Decimal(1), Decimal(0), *args), Decimal('0.00'))
        self.assertEqual(calc.recurring_invoice_amount(Decimal(-1), Decimal(100), *args), Decimal('-100.00'))
        self.assertEqual(calc.recurring_invoice_amount(Decimal(1), Decimal(-50), *args), Decimal('-50.00'))

    def test_without_period_counts_the_default_months(self):
        amount = calc.invoice_line_amount(
            calc.RECURRING, Decimal(2), Decimal(100), 3, None, None, None, None, default_months=6
        )
        self.assertEqual(amount, Decimal('400.00'))
        self.assertEqual(calc.recurring_months_amount(Decimal(1), Decimal(120), 12, 1), Decimal('10.00'))

    def test_period_required(self):
        with self.assertRaises(ValueError):
            calc.recurring_invoice_amount(Decimal(1), Decimal(100), 1, None, date(2025, 1, 31), None, None)


class LineValuesTestCase(SimpleTestCase):
    """Spec user story 3, scenario 1: total 1,900 and yearly 1,200."""

    start = date(2025, 1, 1)
    end = date(2025, 12, 31)

    def test_recurring_total_and_yearly(self):
        args = (BillingMethodChoices.RECURRING, Decimal(1), Decimal(100), 1, self.start, self.end)
        self.assertEqual(calc.line_total_value(*args), Decimal('1200.00'))
        self.assertEqual(calc.line_yearly_value(*args[:4]), Decimal('1200.00'))

    def test_one_time_total(self):
        args = (BillingMethodChoices.ONE_TIME, Decimal(1), Decimal(500), None, self.start, self.end)
        self.assertEqual(calc.line_total_value(*args), Decimal('500.00'))
        self.assertEqual(calc.line_yearly_value(*args[:4]), Decimal('0.00'))

    def test_usage_total(self):
        args = (BillingMethodChoices.USAGE, Decimal(10), Decimal(20), None, self.start, self.end)
        self.assertEqual(calc.line_total_value(*args), Decimal('200.00'))
        self.assertEqual(calc.line_yearly_value(*args[:4]), Decimal('0.00'))

    def test_sum_of_scenario(self):
        total = sum(
            calc.line_total_value(*args)
            for args in (
                (BillingMethodChoices.RECURRING, Decimal(1), Decimal(100), 1, self.start, self.end),
                (BillingMethodChoices.ONE_TIME, Decimal(1), Decimal(500), None, self.start, self.end),
                (BillingMethodChoices.USAGE, Decimal(10), Decimal(20), None, self.start, self.end),
            )
        )
        self.assertEqual(total, Decimal('1900.00'))

    def test_quarterly_and_yearly_units(self):
        self.assertEqual(
            calc.line_yearly_value(BillingMethodChoices.RECURRING, Decimal(1), Decimal(300), 3), Decimal('1200.00')
        )
        self.assertEqual(
            calc.line_yearly_value(BillingMethodChoices.RECURRING, Decimal(1), Decimal(1000), 12), Decimal('1000.00')
        )
        self.assertEqual(
            calc.line_total_value(
                BillingMethodChoices.RECURRING, Decimal(1), Decimal(1000), 12, date(2025, 1, 1), date(2026, 6, 30)
            ),
            Decimal('1500.00'),
        )

    def test_open_ended_total_not_available(self):
        self.assertIsNone(
            calc.line_total_value(BillingMethodChoices.RECURRING, Decimal(1), Decimal(100), 1, self.start, None)
        )
        self.assertIsNone(
            calc.line_total_value(BillingMethodChoices.RECURRING, Decimal(1), Decimal(100), 1, None, self.end)
        )
        # one-time and usage lines do not depend on dates
        self.assertEqual(
            calc.line_total_value(BillingMethodChoices.ONE_TIME, Decimal(1), Decimal(100), None, None, None),
            Decimal('100.00'),
        )

    def test_negative_line(self):
        self.assertEqual(
            calc.line_total_value(BillingMethodChoices.RECURRING, Decimal(1), Decimal(-10), 1, self.start, self.end),
            Decimal('-120.00'),
        )


class UsageAndInvoiceLineAmountTestCase(SimpleTestCase):
    """SC-004 and spec user story 6, scenarios 5 and 7."""

    def test_usage_amount(self):
        self.assertEqual(calc.usage_amount(Decimal(10), Decimal(20)), Decimal('200.00'))
        self.assertEqual(calc.usage_amount(Decimal(12), Decimal(20)), Decimal('240.00'))
        self.assertEqual(calc.usage_amount(None, Decimal(20)), Decimal('0.00'))
        self.assertEqual(calc.usage_amount(Decimal('0.3333'), Decimal(10)), Decimal('3.33'))

    def test_invoice_line_amount_by_method(self):
        period = (date(2025, 1, 1), date(2025, 3, 31))
        line_dates = (date(2025, 1, 1), date(2025, 12, 31))
        self.assertEqual(
            calc.invoice_line_amount(BillingMethodChoices.USAGE, Decimal(10), Decimal(20), None, *period, *line_dates),
            Decimal('200.00'),
        )
        self.assertEqual(
            calc.invoice_line_amount(BillingMethodChoices.USAGE, None, Decimal(20), None, *period, *line_dates),
            Decimal('0.00'),
        )
        self.assertEqual(
            calc.invoice_line_amount(BillingMethodChoices.ONE_TIME, Decimal(1), Decimal(500), None, *period,
                                     *line_dates),
            Decimal('500.00'),
        )
        self.assertEqual(
            calc.invoice_line_amount(BillingMethodChoices.RECURRING, Decimal(1), Decimal(100), 1, *period,
                                     *line_dates),
            Decimal('300.00'),
        )

    def test_one_time_without_period(self):
        self.assertEqual(
            calc.invoice_line_amount(BillingMethodChoices.ONE_TIME, Decimal(2), Decimal(50), None, None, None,
                                     None, None),
            Decimal('100.00'),
        )


class RemainingTestCase(SimpleTestCase):
    def test_remaining_never_negative(self):
        self.assertEqual(calc.remaining(Decimal(500), Decimal(200)), Decimal(300))
        self.assertEqual(calc.remaining(Decimal(500), Decimal(500)), Decimal(0))
        self.assertEqual(calc.remaining(Decimal(500), Decimal(700)), Decimal(0))

    def test_remaining_of_a_credit(self):
        self.assertEqual(calc.remaining(Decimal(-100), Decimal(0)), Decimal(-100))
        self.assertEqual(calc.remaining(Decimal(-100), Decimal(-100)), Decimal(0))
        self.assertEqual(calc.remaining(Decimal(-100), Decimal(-150)), Decimal(0))


class OverlapTestCase(SimpleTestCase):
    def test_overlap_days(self):
        self.assertEqual(calc.overlap_days(date(2025, 1, 1), date(2025, 1, 31), None, None), 31)
        self.assertEqual(calc.overlap_days(date(2025, 1, 1), date(2025, 1, 31), date(2025, 1, 11), None), 21)
        self.assertEqual(calc.overlap_days(date(2025, 1, 1), date(2025, 1, 31), None, date(2025, 1, 10)), 10)
        self.assertEqual(calc.overlap_days(date(2025, 1, 1), date(2025, 1, 31), date(2025, 2, 1), None), 0)
