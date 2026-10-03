"""Spec user story 5: invoice pre-fill from the contract lines (FR-017..FR-020, FR-017a, SC-004)."""

from datetime import date
from decimal import Decimal

from django.contrib.messages import get_messages
from django.urls import reverse
from utilities.testing import TestCase

from netbox_contract.models import ContractLine, InvoiceStatusChoices
from netbox_contract.tests.helpers import (
    make_contract,
    make_invoice,
    make_invoice_line,
    make_line,
    make_unit,
    monthly,
    one_time,
    usage,
    yearly,
)


class PrefillTestCase(TestCase):
    def setUp(self):
        super().setUp()
        self.user.is_superuser = True
        self.user.save()

    def prefill(self, contract):
        response = self.client.get(f"{reverse('plugins:netbox_contract:invoice_add')}?contracts={contract.pk}")
        self.assertEqual(response.status_code, 200)
        return response, response.context['form'].initial

    def test_recurring_line_three_full_months(self):
        """Scenario 1."""
        contract = make_contract(invoice_frequency=3)
        make_line(contract, monthly(), 100)
        _, initial = self.prefill(contract)
        self.assertEqual(initial['period_start'], date(2025, 1, 1))
        self.assertEqual(initial['period_end'], date(2025, 3, 31))
        self.assertEqual(initial['amount'], Decimal('300.00'))

    def test_yearly_unit_three_months(self):
        """Scenario 2."""
        contract = make_contract(invoice_frequency=3)
        make_line(contract, yearly(), 120)
        _, initial = self.prefill(contract)
        self.assertEqual(initial['amount'], Decimal('30.00'))

    def test_partial_period(self):
        """Scenario 3: 20 covered days out of a 30-day period."""
        contract = make_contract(start_date=date(2025, 4, 1), end_date=date(2025, 12, 31))
        make_line(contract, monthly(), 90, start_date=date(2025, 4, 11))
        _, initial = self.prefill(contract)
        self.assertEqual(initial['period_end'], date(2025, 4, 30))
        self.assertEqual(initial['amount'], Decimal('60.00'))

    def test_one_time_line_partly_invoiced(self):
        """Scenario 4: Draft and Canceled invoices are ignored."""
        contract = make_contract()
        line = make_line(contract, one_time(), 500)
        for status, quantity in (
            (InvoiceStatusChoices.STATUS_POSTED, '0.4'),
            (InvoiceStatusChoices.STATUS_DRAFT, '0.2'),
            (InvoiceStatusChoices.STATUS_CANCELED, '0.2'),
        ):
            invoice = make_invoice(contract, number=f'INV-{status}', status=status, amount=500)
            make_invoice_line(invoice, amount=Decimal(quantity) * 500, contract_line=line, quantity=quantity)
        _, initial = self.prefill(contract)
        self.assertEqual(initial['amount'], Decimal('300.00'))

    def test_one_time_line_fully_invoiced(self):
        """Scenario 5."""
        contract = make_contract()
        line = make_line(contract, one_time(), 500)
        invoice = make_invoice(contract, amount=500)
        make_invoice_line(invoice, amount=500, contract_line=line, quantity=1)
        _, initial = self.prefill(contract)
        self.assertIsNone(initial.get('amount'))

    def test_one_time_line_invoiced_more_than_its_total(self):
        contract = make_contract()
        line = make_line(contract, one_time(), 500)
        make_line(contract, monthly(), 10)
        invoice = make_invoice(contract, amount=1000)
        make_invoice_line(invoice, amount=700, contract_line=line, quantity='1.4')
        _, initial = self.prefill(contract)
        self.assertEqual(initial['amount'], Decimal('10.00'))

    def test_contract_without_lines(self):
        """Scenario 6."""
        contract = make_contract(mrc=Decimal(100))
        _, initial = self.prefill(contract)
        self.assertIsNone(initial.get('amount'))
        self.assertEqual(initial['currency'], 'usd')

    def test_usage_line_is_not_proposed(self):
        """Scenario 7."""
        contract = make_contract()
        make_line(contract, usage(), 20, quantity=10)
        make_line(contract, monthly(), 100)
        _, initial = self.prefill(contract)
        self.assertEqual(initial['amount'], Decimal('100.00'))

    def test_mixed_lines(self):
        contract = make_contract()
        make_line(contract, monthly(), 100)
        make_line(contract, make_unit('Quarterly', 'recurring', 3), 30)
        make_line(contract, one_time(), 500)
        _, initial = self.prefill(contract)
        self.assertEqual(initial['amount'], Decimal('610.00'))

    def test_non_billable_contract(self):
        """FR-008 and spec user story 3, scenario 3."""
        parent = make_contract(name='Parent')
        contract = make_contract(name='Child', parent=parent, billable=False)
        make_line(contract, monthly(), 100)
        response, initial = self.prefill(contract)
        self.assertIsNone(initial.get('amount'))
        messages = [str(message) for message in get_messages(response.wsgi_request)]
        self.assertTrue(any('not billable' in message for message in messages), messages)

    def test_non_billable_descendants_are_included(self):
        parent = make_contract(name='Parent')
        make_line(parent, monthly(), 100)
        child = make_contract(name='Child', parent=parent, billable=False)
        make_line(child, monthly(), 10)
        billable_child = make_contract(name='Billable child', parent=parent)
        make_line(billable_child, monthly(), 1)
        _, initial = self.prefill(parent)
        self.assertEqual(initial['amount'], Decimal('110.00'))

    def test_period_follows_the_last_invoice(self):
        contract = make_contract(invoice_frequency=1)
        make_line(contract, monthly(), 100)
        make_invoice(contract, amount=100, period_start=date(2025, 3, 1), period_end=date(2025, 3, 31))
        _, initial = self.prefill(contract)
        self.assertEqual(initial['period_start'], date(2025, 4, 1))
        self.assertEqual(initial['period_end'], date(2025, 4, 30))
        self.assertEqual(initial['amount'], Decimal('100.00'))

    def test_template_invoice_is_ignored(self):
        contract = make_contract()
        line = make_line(contract, one_time(), 500)
        template = make_invoice(contract, number='TPL', amount=500, template=True, period_start=None,
                                period_end=None)
        make_invoice_line(template, amount=500, contract_line=line, quantity=1)
        _, initial = self.prefill(contract)
        self.assertEqual(initial['period_start'], date(2025, 1, 1))
        self.assertEqual(initial['amount'], Decimal('500.00'))

    def test_invoiced_at_conversion(self):
        contract = make_contract()
        line = make_line(contract, one_time(), 500)
        ContractLine.objects.filter(pk=line.pk).update(invoiced_at_conversion=True)
        make_line(contract, monthly(), 100)
        _, initial = self.prefill(contract)
        self.assertEqual(initial['amount'], Decimal('100.00'))

    def test_one_time_line_of_contract_without_posted_invoice(self):
        contract = make_contract()
        make_line(contract, one_time(), 500)
        make_invoice(contract, status=InvoiceStatusChoices.STATUS_DRAFT, amount=0)
        _, initial = self.prefill(contract)
        self.assertEqual(initial['amount'], Decimal('500.00'))

    def test_contract_without_start_date_counts_the_invoice_frequency(self):
        """Decision 2026-09-26: no period, so the recurring line counts for one invoice frequency."""
        contract = make_contract(start_date=None, end_date=None, invoice_frequency=2)
        make_line(contract, monthly(), 100)
        _, initial = self.prefill(contract)
        self.assertIsNone(initial.get('period_start'))
        self.assertEqual(initial['amount'], Decimal('200.00'))

    def test_recurring_line_without_end_date(self):
        contract = make_contract(end_date=None, invoice_frequency=12)
        make_line(contract, monthly(), 100)
        _, initial = self.prefill(contract)
        self.assertEqual(initial['period_end'], date(2025, 12, 31))
        self.assertEqual(initial['amount'], Decimal('1200.00'))

    def test_line_outside_the_period_is_not_proposed(self):
        contract = make_contract()
        make_line(contract, monthly(), 100, start_date=date(2025, 6, 1))
        make_line(contract, one_time(), 40, start_date=date(2025, 9, 1))
        make_line(contract, monthly(), 7)
        _, initial = self.prefill(contract)
        self.assertEqual(initial['amount'], Decimal('7.00'))

    def test_currency_and_editable_values(self):
        """FR-020."""
        contract = make_contract(currency='chf')
        make_line(contract, monthly(), 100)
        response, initial = self.prefill(contract)
        self.assertEqual(initial['currency'], 'chf')
        form = response.context['form']
        for field in ('amount', 'period_start', 'period_end', 'currency'):
            self.assertFalse(form.fields[field].disabled)
