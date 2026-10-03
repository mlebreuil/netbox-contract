"""Spec user story 1: describe a contract line by line (FR-001..FR-004, FR-002a)."""

from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from utilities.testing import TestCase as NetBoxTestCase

from netbox_contract.models import AccountingDimension, BillingMethodChoices, ContractLine, Unit
from netbox_contract.tests.helpers import (
    contract_page_with_lines,
    make_contract,
    make_line,
    monthly,
    one_time,
    usage,
    yearly,
)


def new_line(contract, unit, unit_price=100, **kwargs):
    return ContractLine(
        contract=contract, unit=unit, unit_price=Decimal(unit_price), description='New line', **kwargs
    )


class UnitRulesTestCase(TestCase):
    def test_recurring_unit_needs_months(self):
        unit = Unit(name='Recurring', billing_method=BillingMethodChoices.RECURRING)
        with self.assertRaises(ValidationError) as cm:
            unit.full_clean()
        self.assertIn('months', cm.exception.message_dict)

    def test_recurring_unit_months_at_least_one(self):
        unit = Unit(name='Recurring', billing_method=BillingMethodChoices.RECURRING, months=0)
        with self.assertRaises(ValidationError) as cm:
            unit.full_clean()
        self.assertIn('months', cm.exception.message_dict)

    def test_other_units_have_no_months(self):
        for method in (BillingMethodChoices.ONE_TIME, BillingMethodChoices.USAGE):
            unit = Unit(name=method, billing_method=method, months=1)
            with self.assertRaises(ValidationError) as cm:
                unit.full_clean()
            self.assertIn('months', cm.exception.message_dict)
            unit.months = None
            unit.full_clean()

    def test_valid_recurring_unit(self):
        Unit(name='Quarterly', billing_method=BillingMethodChoices.RECURRING, months=3).full_clean()


class ContractLineDefaultsTestCase(TestCase):
    def test_dates_default_to_the_contract(self):
        """Scenario 1."""
        contract = make_contract(start_date=date(2025, 1, 1), end_date=date(2025, 12, 31))
        line = new_line(contract, monthly())
        line.full_clean()
        line.save()
        self.assertEqual(line.start_date, date(2025, 1, 1))
        self.assertEqual(line.end_date, date(2025, 12, 31))

    def test_defaults_applied_on_save_without_clean(self):
        contract = make_contract(currency='eur')
        line = new_line(contract, monthly())
        line.save()
        line.refresh_from_db()
        self.assertEqual(line.currency, 'eur')
        self.assertEqual(line.start_date, contract.start_date)
        self.assertEqual(line.end_date, contract.end_date)

    def test_given_dates_are_kept(self):
        contract = make_contract()
        line = new_line(contract, monthly(), start_date=date(2025, 3, 1), end_date=date(2025, 6, 30))
        line.full_clean()
        self.assertEqual(line.start_date, date(2025, 3, 1))
        self.assertEqual(line.end_date, date(2025, 6, 30))

    def test_currency_defaults_to_the_contract(self):
        """Scenario 4."""
        contract = make_contract(currency='chf')
        line = new_line(contract, monthly())
        line.full_clean()
        self.assertEqual(line.currency, 'chf')

    def test_quantity_defaults_to_one(self):
        line = new_line(make_contract(), monthly())
        self.assertEqual(line.quantity, 1)


class ContractLineValuesTestCase(TestCase):
    def test_recurring_unit_of_twelve_months(self):
        """Scenario 2: the unit price is a price per 12 months."""
        contract = make_contract(start_date=date(2025, 1, 1), end_date=date(2026, 12, 31))
        line = make_line(contract, yearly(), 1200)
        self.assertEqual(line.yearly_value, Decimal('1200.00'))
        self.assertEqual(line.total_value, Decimal('2400.00'))

    def test_values_of_each_nature(self):
        contract = make_contract()
        self.assertEqual(make_line(contract, monthly(), 100).total_value, Decimal('1200.00'))
        self.assertEqual(make_line(contract, one_time(), 500).total_value, Decimal('500.00'))
        self.assertEqual(make_line(contract, usage(), 20, quantity=10).total_value, Decimal('200.00'))
        self.assertEqual(make_line(contract, one_time(), 500).yearly_value, Decimal('0.00'))

    def test_values_update_on_edit(self):
        """Scenario 7 (line level; the contract values are tested in test_values)."""
        contract = make_contract()
        line = make_line(contract, monthly(), 100)
        line.unit_price = Decimal(200)
        line.full_clean()
        line.save()
        line.refresh_from_db()
        self.assertEqual(line.total_value, Decimal('2400.00'))

    def test_open_ended_line_has_no_total(self):
        contract = make_contract(end_date=None)
        line = make_line(contract, monthly(), 100)
        self.assertIsNone(line.total_value)
        self.assertEqual(line.yearly_value, Decimal('1200.00'))

    def test_line_without_dates_uses_the_contract_dates(self):
        contract = make_contract()
        line = make_line(contract, monthly(), 100, start_date=None, end_date=None)
        ContractLine.objects.filter(pk=line.pk).update(start_date=None, end_date=None)
        line.refresh_from_db()
        self.assertEqual(line.total_value, Decimal('1200.00'))


class ContractLineDatesTestCase(TestCase):
    def test_end_after_contract_end_refused(self):
        """Scenario 5: the message names the contract's dates."""
        contract = make_contract(start_date=date(2025, 1, 1), end_date=date(2025, 12, 31))
        line = new_line(contract, monthly(), end_date=date(2026, 3, 31))
        with self.assertRaises(ValidationError) as cm:
            line.full_clean()
        self.assertIn('end_date', cm.exception.message_dict)
        message = ' '.join(cm.exception.message_dict['end_date'])
        self.assertIn('2025-01-01', message)
        self.assertIn('2025-12-31', message)

    def test_start_before_contract_start_refused(self):
        contract = make_contract(start_date=date(2025, 1, 1), end_date=date(2025, 12, 31))
        line = new_line(contract, monthly(), start_date=date(2024, 12, 1))
        with self.assertRaises(ValidationError) as cm:
            line.full_clean()
        self.assertIn('start_date', cm.exception.message_dict)
        self.assertIn('2025-01-01', ' '.join(cm.exception.message_dict['start_date']))

    def test_dates_on_the_contract_bounds_accepted(self):
        contract = make_contract(start_date=date(2025, 1, 1), end_date=date(2025, 12, 31))
        new_line(contract, monthly(), start_date=date(2025, 1, 1), end_date=date(2025, 12, 31)).full_clean()

    def test_contract_without_start_date(self):
        contract = make_contract(start_date=None, end_date=date(2025, 12, 31))
        new_line(contract, monthly(), start_date=date(2000, 1, 1)).full_clean()
        line = new_line(contract, monthly(), start_date=date(2000, 1, 1), end_date=date(2026, 1, 1))
        with self.assertRaises(ValidationError) as cm:
            line.full_clean()
        self.assertIn('end_date', cm.exception.message_dict)

    def test_contract_without_end_date(self):
        contract = make_contract(start_date=date(2025, 1, 1), end_date=None)
        new_line(contract, monthly(), end_date=date(2040, 1, 1)).full_clean()
        line = new_line(contract, monthly(), start_date=date(2024, 1, 1))
        with self.assertRaises(ValidationError) as cm:
            line.full_clean()
        self.assertIn('start_date', cm.exception.message_dict)

    def test_open_ended_contract(self):
        contract = make_contract(start_date=None, end_date=None)
        new_line(contract, monthly(), start_date=date(2000, 1, 1), end_date=date(2040, 1, 1)).full_clean()

    def test_end_before_start_refused(self):
        contract = make_contract()
        line = new_line(contract, monthly(), start_date=date(2025, 6, 1), end_date=date(2025, 5, 1))
        with self.assertRaises(ValidationError) as cm:
            line.full_clean()
        self.assertIn('end_date', cm.exception.message_dict)

    def test_contract_dates_leaving_lines_outside_refused(self):
        contract = make_contract(start_date=date(2025, 1, 1), end_date=date(2025, 12, 31))
        make_line(contract, monthly(), 100, start_date=date(2025, 1, 1), end_date=date(2025, 12, 31))
        contract.end_date = date(2025, 6, 30)
        with self.assertRaises(ValidationError) as cm:
            contract.full_clean()
        self.assertIn('end_date', cm.exception.message_dict)
        contract.refresh_from_db()
        contract.start_date = date(2025, 2, 1)
        with self.assertRaises(ValidationError) as cm:
            contract.full_clean()
        self.assertIn('start_date', cm.exception.message_dict)

    def test_contract_dates_keeping_lines_inside_accepted(self):
        contract = make_contract(start_date=date(2025, 1, 1), end_date=date(2025, 12, 31))
        make_line(contract, monthly(), 100, start_date=date(2025, 3, 1), end_date=date(2025, 6, 30))
        contract.start_date = date(2025, 2, 1)
        contract.end_date = date(2026, 12, 31)
        contract.full_clean()

    def test_line_without_dates_does_not_block_contract_dates(self):
        contract = make_contract(start_date=None, end_date=None)
        make_line(contract, monthly(), 100)
        contract.start_date = date(2025, 1, 1)
        contract.end_date = date(2025, 12, 31)
        contract.full_clean()


class ContractLineDimensionsTestCase(NetBoxTestCase):
    def test_several_dimensions_shown_on_contract(self):
        """Scenario 3."""
        self.user.is_superuser = True
        self.user.save()
        contract = make_contract()
        line = make_line(contract, monthly(), 100, description='Hosting')
        dimensions = [
            AccountingDimension.objects.create(name='account', value='A100'),
            AccountingDimension.objects.create(name='department', value='IT'),
        ]
        line.accounting_dimensions.set(dimensions)
        self.assertEqual(line.accounting_dimensions.count(), 2)

        content = contract_page_with_lines(self.client, contract)
        self.assertIn('Hosting', content)
        self.assertIn('account:A100', content)
        self.assertIn('department:IT', content)

    def test_add_button_carries_the_contract(self):
        self.user.is_superuser = True
        self.user.save()
        contract = make_contract()
        response = self.client.get(reverse('plugins:netbox_contract:contract', args=[contract.pk]))
        self.assertContains(response, f"{reverse('plugins:netbox_contract:contractline_add')}?contract={contract.pk}")

        response = self.client.get(f"{reverse('plugins:netbox_contract:contractline_add')}?contract={contract.pk}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['form'].initial.get('contract'), str(contract.pk))
