"""Amendment of the price or quantity of a contract line from a date (FR-030, decision I10)."""

from datetime import date
from decimal import Decimal

from core.models import ObjectChange
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from utilities.testing import TestCase as NetBoxTestCase

from netbox_contract.models import AccountingDimension, ContractLine, InvoiceStatusChoices
from netbox_contract.services import invoicing
from netbox_contract.services.amendments import AmendmentError, amend_contract_line
from netbox_contract.tests.custom import APITestCase
from netbox_contract.tests.helpers import (
    make_contract,
    make_invoice,
    make_invoice_line,
    make_line,
    monthly,
    one_time,
    usage,
)


class AmendmentTestCase(TestCase):
    def setUp(self):
        self.contract = make_contract(start_date=date(2025, 1, 1), end_date=date(2025, 12, 31))
        self.line = make_line(self.contract, monthly(), 100, quantity=2, description='Hosting', comments='Initial')
        self.dimension = AccountingDimension.objects.create(name='account', value='A1')
        self.line.accounting_dimensions.set([self.dimension])
        self.line.tags.add('hosting')
        invoice = make_invoice(self.contract, number='JAN', amount=1000,
                               period_start=date(2025, 1, 1), period_end=date(2025, 1, 31))
        make_invoice_line(invoice, contract_line=self.line, quantity=2)

    def test_price_change_from_a_date(self):
        new = amend_contract_line(self.line, date(2025, 7, 1), 'Yearly indexation', unit_price=Decimal(110))
        self.line.refresh_from_db()
        self.assertEqual(self.line.end_date, date(2025, 6, 30))
        self.assertEqual(self.line.unit_price, Decimal(100))
        self.assertEqual(new.replaces, self.line)
        self.assertEqual(new.start_date, date(2025, 7, 1))
        self.assertEqual(new.end_date, date(2025, 12, 31))
        self.assertEqual(new.unit_price, Decimal(110))
        self.assertEqual(new.quantity, 2)
        self.assertEqual(
            (new.contract, new.unit, new.currency, new.description),
            (self.line.contract, self.line.unit, self.line.currency, self.line.description),
        )
        self.assertEqual(list(new.accounting_dimensions.all()), [self.dimension])
        self.assertEqual(list(new.tags.names()), ['hosting'])
        self.assertIn('Yearly indexation', new.comments)
        self.assertEqual(list(self.line.replaced_by.all()), [new])

    def test_quantity_change(self):
        new = amend_contract_line(self.line, date(2025, 3, 1), 'Two more servers', quantity=Decimal(4))
        self.assertEqual((new.quantity, new.unit_price), (Decimal(4), Decimal(100)))

    def test_values_after_the_change(self):
        """Totals count each price for its own period; yearly values only the current line."""
        amend_contract_line(self.line, date(2025, 7, 1), 'Indexation', unit_price=Decimal(110))
        # 2 x 100 x 6 + 2 x 110 x 6
        self.assertEqual(self.contract.total_contract_value, Decimal('2520.00'))
        self.assertEqual(self.contract.yearly_contract_value, Decimal('2640.00'))
        self.assertEqual(self.contract.yearly_billable_value, Decimal('2640.00'))

    def test_open_ended_line(self):
        contract = make_contract(name='Open', end_date=None)
        line = make_line(contract, monthly(), 100)
        new = amend_contract_line(line, date(2025, 5, 1), 'Renegotiated', unit_price=Decimal(90))
        self.assertIsNone(new.end_date)
        line.refresh_from_db()
        self.assertEqual(line.end_date, date(2025, 4, 30))

    def test_usage_line(self):
        line = make_line(self.contract, usage(), 20)
        new = amend_contract_line(line, date(2025, 2, 1), 'New tariff', unit_price=Decimal(18))
        self.assertEqual(new.unit_price, Decimal(18))

    def test_invoices_after_the_change(self):
        amend_contract_line(self.line, date(2025, 7, 1), 'Indexation', unit_price=Decimal(110))
        june = invoicing.propose_invoice(self.contract, date(2025, 6, 1), date(2025, 6, 30))
        july = invoicing.propose_invoice(self.contract, date(2025, 7, 1), date(2025, 7, 31))
        self.assertEqual(june.total, Decimal('200.00'))
        self.assertEqual(july.total, Decimal('220.00'))
        # a period across the change gets both lines, each prorated by its days (FR-018): 600 x 30/92, 660 x 62/92
        quarter = invoicing.lines_to_generate(self.contract, date(2025, 6, 1), date(2025, 8, 31))
        self.assertEqual(sorted(line.amount for line in quarter), [Decimal('195.65'), Decimal('444.78')])

    def test_invoiced_amounts_do_not_change(self):
        invoice_line = self.line.invoicelines.get()
        amend_contract_line(self.line, date(2025, 2, 1), 'Indexation', unit_price=Decimal(110))
        invoice_line.full_clean()
        invoice_line.save()
        self.assertEqual(invoice_line.amount, Decimal('200.00'))

    def test_amending_twice(self):
        second = amend_contract_line(self.line, date(2025, 4, 1), 'First', unit_price=Decimal(105))
        third = amend_contract_line(second, date(2025, 10, 1), 'Second', unit_price=Decimal(110))
        self.assertEqual(third.replaces, second)
        self.assertEqual(self.contract.yearly_contract_value, Decimal('2640.00'))


class AmendmentRulesTestCase(TestCase):
    def setUp(self):
        self.contract = make_contract()
        self.line = make_line(self.contract, monthly(), 100)
        invoice = make_invoice(self.contract, number='Q1', amount=1000,
                               period_start=date(2025, 1, 1), period_end=date(2025, 3, 31))
        make_invoice_line(invoice, contract_line=self.line, quantity=1)

    def assertRefused(self, field, **kwargs):
        arguments = {'effective_date': date(2025, 7, 1), 'reason': 'Reason', 'unit_price': Decimal(110)}
        arguments.update(kwargs)
        with self.assertRaises(AmendmentError) as cm:
            amend_contract_line(self.line, **arguments)
        self.assertIn(field, cm.exception.errors)
        self.assertEqual(ContractLine.objects.count(), 1)

    def test_reason_is_required(self):
        self.assertRefused('reason', reason='  ')

    def test_something_must_change(self):
        self.assertRefused('unit_price', unit_price=None)
        self.assertRefused('unit_price', unit_price=Decimal(100), quantity=Decimal(1))

    def test_not_before_the_end_of_the_last_invoiced_period(self):
        self.assertRefused('effective_date', effective_date=date(2025, 3, 31))
        amend_contract_line(self.line, date(2025, 4, 1), 'Reason', unit_price=Decimal(110))

    def test_draft_invoices_count_canceled_do_not(self):
        make_invoice(self.contract, number='Q2-draft', amount=1000, status=InvoiceStatusChoices.STATUS_DRAFT,
                     period_start=date(2025, 4, 1), period_end=date(2025, 6, 30))
        make_invoice(self.contract, number='Q3-canceled', amount=1000, status=InvoiceStatusChoices.STATUS_CANCELED,
                     period_start=date(2025, 7, 1), period_end=date(2025, 9, 30))
        self.assertRefused('effective_date', effective_date=date(2025, 6, 30))
        amend_contract_line(self.line, date(2025, 7, 1), 'Reason', unit_price=Decimal(110))

    def test_invoices_of_the_contract_without_references_count(self):
        """Converted lines are invoiced by invoices that do not reference them."""
        contract = make_contract(name='Converted')
        line = make_line(contract, monthly(), 100)
        make_invoice(contract, number='OLD', amount=100, period_start=date(2025, 5, 1), period_end=date(2025, 5, 31))
        with self.assertRaises(AmendmentError):
            amend_contract_line(line, date(2025, 5, 15), 'Reason', unit_price=Decimal(110))
        amend_contract_line(line, date(2025, 6, 1), 'Reason', unit_price=Decimal(110))

    def test_date_within_the_line(self):
        self.assertRefused('effective_date', effective_date=date(2026, 1, 1))
        contract = make_contract(name='Not invoiced')
        line = make_line(contract, monthly(), 100)
        with self.assertRaises(AmendmentError) as cm:
            amend_contract_line(line, date(2025, 1, 1), 'Reason', unit_price=Decimal(110))
        self.assertIn('effective_date', cm.exception.errors)

    def test_one_time_line_refused(self):
        line = make_line(make_contract(name='Setup'), one_time(), 500)
        with self.assertRaises(AmendmentError):
            amend_contract_line(line, date(2025, 7, 1), 'Reason', unit_price=Decimal(400))

    def test_replaced_line_refused(self):
        amend_contract_line(self.line, date(2025, 7, 1), 'First', unit_price=Decimal(110))
        self.line.refresh_from_db()
        with self.assertRaises(AmendmentError):
            amend_contract_line(self.line, date(2025, 5, 1), 'Again', unit_price=Decimal(120))


class AmendmentViewTestCase(NetBoxTestCase):
    def setUp(self):
        super().setUp()
        self.user.is_superuser = True
        self.user.save()
        self.contract = make_contract()
        self.line = make_line(self.contract, monthly(), 100)
        make_invoice(self.contract, number='JAN', amount=100)
        self.url = reverse('plugins:netbox_contract:contractline_amend', args=[self.line.pk])

    def test_button_on_the_line_page(self):
        response = self.client.get(self.line.get_absolute_url())
        self.assertContains(response, self.url)
        self.assertContains(response, '</i> Amend\n')
        self.assertContains(response, 'To change its price or quantity from a date, use Amend')

    def test_amend_button_on_the_contract_page(self):
        setup = make_line(self.contract, one_time(), 500, description='Setup')
        content = self.client.get(self.contract.get_absolute_url()).content.decode()
        self.assertIn(self.url, content)
        self.assertNotIn(reverse('plugins:netbox_contract:contractline_amend', args=[setup.pk]), content)
        self.assertIn('Amend', content)

    def test_amend_button_on_the_edit_page_of_a_locked_line(self):
        edit_url = reverse('plugins:netbox_contract:contractline_edit', args=[self.line.pk])
        response = self.client.get(edit_url)
        self.assertContains(response, self.url)
        self.assertContains(response, '</i> Amend\n')

    def test_no_amend_button_once_replaced_or_before_invoicing(self):
        new = amend_contract_line(self.line, date(2025, 7, 1), 'Indexation', unit_price=Decimal(110))
        content = self.client.get(self.contract.get_absolute_url()).content.decode()
        self.assertNotIn(self.url, content)
        self.assertIn(reverse('plugins:netbox_contract:contractline_amend', args=[new.pk]), content)
        other = make_contract(name='Not invoiced')
        line = make_line(other, monthly(), 10)
        response = self.client.get(reverse('plugins:netbox_contract:contractline_edit', args=[line.pk]))
        self.assertNotContains(response, reverse('plugins:netbox_contract:contractline_amend', args=[line.pk]))

    def test_amend_through_the_form(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)
        response = self.client.post(
            self.url, {'effective_date': '2025-07-01', 'unit_price': '110', 'reason': 'Yearly indexation'}
        )
        new = ContractLine.objects.get(replaces=self.line)
        self.assertRedirects(response, new.get_absolute_url(), fetch_redirect_response=False)
        self.assertEqual(new.unit_price, Decimal(110))
        line_type = ContentType.objects.get_for_model(ContractLine)
        messages = set(
            ObjectChange.objects.filter(changed_object_type=line_type).values_list('message', flat=True)
        )
        self.assertEqual(messages, {'Yearly indexation'})
        self.assertEqual(
            ObjectChange.objects.filter(changed_object_type=line_type, changed_object_id=self.line.pk).count(), 1
        )

    def test_errors_are_shown(self):
        response = self.client.post(self.url, {'effective_date': '2025-07-01', 'unit_price': '110', 'reason': ''})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(ContractLine.objects.filter(replaces=self.line).exists())
        response = self.client.post(self.url, {'effective_date': '2025-01-15', 'unit_price': '110', 'reason': 'x'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('2025-01-31', response.content.decode())

    def test_permission_required(self):
        self.user.is_superuser = False
        self.user.save()
        self.add_permissions('netbox_contract.view_contractline')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)


class AmendmentAPITestCase(APITestCase):
    model = ContractLine

    def setUp(self):
        super().setUp()
        self.contract = make_contract()
        self.line = make_line(self.contract, monthly(), 100)
        make_invoice(self.contract, number='JAN', amount=100)
        self.url = reverse('plugins-api:netbox_contract-api:contractline-amend', args=[self.line.pk])

    def test_amend(self):
        self.add_permissions('netbox_contract.amend_contractline', 'netbox_contract.view_contractline')
        response = self.client.post(
            self.url, {'effective_date': '2025-07-01', 'quantity': 3, 'reason': 'More seats'}, format='json',
            **self.header,
        )
        self.assertHttpStatus(response, status.HTTP_201_CREATED)
        self.assertEqual(response.data['replaces']['id'], self.line.pk)
        self.assertEqual(Decimal(response.data['quantity']), Decimal(3))
        response = self.client.get(reverse('plugins-api:netbox_contract-api:contractline-detail', args=[self.line.pk]),
                                   **self.header)
        self.assertEqual(response.data['end_date'], '2025-06-30')

    def test_errors_and_permissions(self):
        response = self.client.post(self.url, {'effective_date': '2025-07-01', 'quantity': 3, 'reason': 'x'},
                                    format='json', **self.header)
        self.assertHttpStatus(response, status.HTTP_403_FORBIDDEN)
        self.add_permissions('netbox_contract.amend_contractline', 'netbox_contract.view_contractline')
        response = self.client.post(self.url, {'effective_date': '2025-07-01', 'quantity': 3}, format='json',
                                    **self.header)
        self.assertHttpStatus(response, status.HTTP_400_BAD_REQUEST)
        self.assertIn('reason', response.data)
