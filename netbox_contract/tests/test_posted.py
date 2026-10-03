"""Posted invoices are locked; new invoices are Draft by default (FR-031, decision I12)."""

from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from rest_framework import status as http_status
from utilities.exceptions import AbortRequest
from utilities.testing import TestCase as NetBoxTestCase

from netbox_contract.models import AccountingDimension, Invoice, InvoiceLine, InvoiceStatusChoices
from netbox_contract.tests.custom import APITestCase
from netbox_contract.tests.helpers import (
    make_contract,
    make_invoice,
    make_invoice_line,
    make_line,
    monthly,
    usage,
    yearly,
)

POSTED = InvoiceStatusChoices.STATUS_POSTED
DRAFT = InvoiceStatusChoices.STATUS_DRAFT
CANCELED = InvoiceStatusChoices.STATUS_CANCELED


class DefaultStatusTestCase(NetBoxTestCase):
    def test_new_invoices_are_draft(self):
        self.assertEqual(Invoice(number='X', amount=1).status, DRAFT)
        self.user.is_superuser = True
        self.user.save()
        form = self.client.get(reverse('plugins:netbox_contract:invoice_add')).context['form']
        self.assertEqual(form['status'].value(), DRAFT)


class PostedInvoiceLinesTestCase(TestCase):
    def setUp(self):
        self.contract = make_contract()
        self.contract_line = make_line(self.contract, usage(), 20)
        self.invoice = make_invoice(self.contract, amount=1000, status=DRAFT)
        self.line = make_invoice_line(self.invoice, contract_line=self.contract_line, quantity=5)
        self.dimension = AccountingDimension.objects.create(name='account', value='A1')

    def post(self):
        self.invoice.status = POSTED
        self.invoice.save()

    def test_unit_and_price_editable_on_a_draft_invoice(self):
        self.line.unit = yearly()
        self.line.unit_price = Decimal(12)
        self.line.quantity = Decimal(2)
        self.line.full_clean()
        self.line.save()
        # yearly unit over January: 2 x 12 x 1/12
        self.assertEqual(self.line.amount, Decimal('2.00'))
        self.line.unit = usage()
        self.line.full_clean()
        self.line.save()
        self.assertEqual(self.line.amount, Decimal('24.00'))

    def test_amount_fields_locked_on_a_posted_invoice(self):
        self.post()
        for field, value in (
            ('unit_price', Decimal(1)), ('quantity', Decimal(6)), ('unit', monthly()), ('amount', Decimal(1)),
            ('currency', 'eur'), ('contract_line', None),
        ):
            with self.subTest(field=field):
                line = InvoiceLine.objects.get(pk=self.line.pk)
                setattr(line, field, value)
                with self.assertRaises(ValidationError) as cm:
                    line.full_clean()
                self.assertIn('posted', ' '.join(cm.exception.messages).lower())

    def test_internal_fields_stay_editable(self):
        self.post()
        self.line.comments = 'Booked on account A1'
        self.line.full_clean()
        self.line.save()
        self.line.accounting_dimensions.set([self.dimension])
        self.line.refresh_from_db()
        self.assertEqual(self.line.amount, Decimal('100.00'))

    def test_no_line_added_to_a_posted_invoice(self):
        self.post()
        with self.assertRaises(ValidationError):
            InvoiceLine(invoice=self.invoice, amount=Decimal(1), currency='usd').full_clean()

    def test_no_line_moved_off_a_posted_invoice(self):
        self.post()
        other = make_invoice(self.contract, number='OTHER', amount=1000, status=DRAFT)
        self.line.invoice = other
        with self.assertRaises(ValidationError):
            self.line.full_clean()

    def test_no_line_deleted_from_a_posted_invoice(self):
        self.post()
        with self.assertRaises(AbortRequest):
            self.line.delete()
        self.assertTrue(InvoiceLine.objects.filter(pk=self.line.pk).exists())

    def test_deleting_the_invoice_deletes_its_lines(self):
        self.post()
        self.invoice.delete()
        self.assertFalse(InvoiceLine.objects.filter(pk=self.line.pk).exists())

    def test_amount_not_recalculated_on_a_posted_invoice(self):
        self.post()
        Invoice.objects.filter(pk=self.invoice.pk).update(period_end=date(2025, 3, 31))
        line = InvoiceLine.objects.get(pk=self.line.pk)
        line.comments = 'x'
        line.save()
        self.assertEqual(line.amount, Decimal('100.00'))

    def test_canceled_and_template_invoices_are_not_locked(self):
        for invoice in (
            make_invoice(self.contract, number='C', amount=100, status=CANCELED),
            make_invoice(None, number='_invoice_template_x', amount=100, status=POSTED, template=True,
                         period_start=None, period_end=None),
        ):
            with self.subTest(invoice=invoice.number):
                line = InvoiceLine(invoice=invoice, amount=Decimal(10), currency='usd')
                line.full_clean()
                line.save()
                line.amount = Decimal(20)
                line.full_clean()
                line.delete()


class PostedInvoiceHeaderTestCase(TestCase):
    def setUp(self):
        self.contract = make_contract()
        self.invoice = make_invoice(self.contract, amount=100, status=POSTED)

    def test_amount_currency_and_period_locked(self):
        for field, value in (
            ('amount', Decimal(200)), ('currency', 'eur'), ('period_start', date(2025, 1, 2)),
            ('period_end', date(2025, 2, 28)),
        ):
            with self.subTest(field=field):
                invoice = Invoice.objects.get(pk=self.invoice.pk)
                setattr(invoice, field, value)
                with self.assertRaises(ValidationError) as cm:
                    invoice.full_clean()
                self.assertIn(field, cm.exception.message_dict)

    def test_status_can_change_then_edits_are_possible(self):
        self.invoice.status = DRAFT
        self.invoice.full_clean()
        self.invoice.save()
        self.invoice.amount = Decimal(200)
        self.invoice.full_clean()
        self.invoice.save()
        self.invoice.status = CANCELED
        self.invoice.full_clean()

    def test_other_fields_editable(self):
        self.invoice.comments = 'Paid'
        self.invoice.number = 'INV-2025-001'
        self.invoice.full_clean()


class PostedInvoiceViewsTestCase(NetBoxTestCase):
    def setUp(self):
        super().setUp()
        self.user.is_superuser = True
        self.user.save()
        self.contract = make_contract()
        contract_line = make_line(self.contract, usage(), 20)
        self.invoice = make_invoice(self.contract, amount=1000, status=POSTED)
        self.line = make_invoice_line(self.invoice, contract_line=contract_line, quantity=5)

    def test_invoice_page(self):
        content = self.client.get(self.invoice.get_absolute_url()).content.decode()
        self.assertNotIn(f"{reverse('plugins:netbox_contract:invoiceline_add')}?invoice={self.invoice.pk}", content)
        self.assertIn('This invoice is posted', content)

    def test_invoice_line_form(self):
        url = reverse('plugins:netbox_contract:invoiceline_edit', args=[self.line.pk])
        form = self.client.get(url).context['form']
        for field in ('invoice', 'contract_line', 'unit', 'unit_price', 'quantity', 'currency', 'amount'):
            self.assertTrue(form.fields[field].disabled, field)
        for field in ('accounting_dimensions', 'comments', 'tags'):
            self.assertFalse(form.fields[field].disabled, field)
        response = self.client.post(url, {'quantity': '9', 'comments': 'Booked'})
        self.assertEqual(response.status_code, 302, response.content.decode()[-1500:])
        self.line.refresh_from_db()
        self.assertEqual((self.line.quantity, self.line.comments), (Decimal(5), 'Booked'))

    def test_invoice_form(self):
        url = reverse('plugins:netbox_contract:invoice_edit', args=[self.invoice.pk])
        form = self.client.get(url).context['form']
        for field in ('amount', 'currency', 'period_start', 'period_end', 'contracts'):
            self.assertTrue(form.fields[field].disabled, field)
        self.assertFalse(form.fields['status'].disabled)
        self.assertFalse(form.fields['comments'].disabled)

    def test_line_delete_refused(self):
        response = self.client.post(
            reverse('plugins:netbox_contract:invoiceline_delete', args=[self.line.pk]), {'confirm': True}, follow=True
        )
        self.assertTrue(InvoiceLine.objects.filter(pk=self.line.pk).exists())
        self.assertIn('posted', response.content.decode().lower())


class PostedInvoiceAPITestCase(APITestCase):
    model = InvoiceLine

    def setUp(self):
        super().setUp()
        self.add_permissions(
            'netbox_contract.add_invoiceline', 'netbox_contract.change_invoiceline',
            'netbox_contract.delete_invoiceline', 'netbox_contract.view_invoiceline',
            'netbox_contract.add_invoice', 'netbox_contract.change_invoice', 'netbox_contract.view_invoice',
        )
        self.contract = make_contract()
        self.contract_line = make_line(self.contract, usage(), 20)
        self.invoice = make_invoice(self.contract, amount=1000, status=POSTED)
        self.line = make_invoice_line(self.invoice, contract_line=self.contract_line, quantity=5)

    def test_lines_of_a_posted_invoice(self):
        url = self._get_detail_url(self.line)
        response = self.client.patch(url, {'quantity': 6}, format='json', **self.header)
        self.assertHttpStatus(response, http_status.HTTP_400_BAD_REQUEST)
        response = self.client.patch(url, {'comments': 'ok'}, format='json', **self.header)
        self.assertHttpStatus(response, http_status.HTTP_200_OK)
        response = self.client.delete(url, **self.header)
        self.assertHttpStatus(response, http_status.HTTP_400_BAD_REQUEST)
        response = self.client.post(
            self._get_list_url(), {'invoice': self.invoice.pk, 'amount': 1, 'currency': 'usd'}, format='json',
            **self.header,
        )
        self.assertHttpStatus(response, http_status.HTTP_400_BAD_REQUEST)

    def test_posted_invoice(self):
        url = reverse('plugins-api:netbox_contract-api:invoice-detail', args=[self.invoice.pk])
        response = self.client.patch(url, {'amount': '2000'}, format='json', **self.header)
        self.assertHttpStatus(response, http_status.HTTP_400_BAD_REQUEST)
        other = make_contract(name='Other')
        response = self.client.patch(url, {'contracts': [other.pk]}, format='json', **self.header)
        self.assertHttpStatus(response, http_status.HTTP_400_BAD_REQUEST)
        response = self.client.patch(url, {'status': DRAFT}, format='json', **self.header)
        self.assertHttpStatus(response, http_status.HTTP_200_OK)

    def test_new_invoice_defaults_to_draft_and_gets_its_lines(self):
        url = reverse('plugins-api:netbox_contract-api:invoice-list')
        data = {'number': 'API', 'amount': '1000', 'currency': 'usd', 'contracts': [self.contract.pk],
                'period_start': '2025-02-01', 'period_end': '2025-02-28'}
        response = self.client.post(url, data, format='json', **self.header)
        self.assertHttpStatus(response, http_status.HTTP_201_CREATED)
        self.assertEqual(Invoice.objects.get(number='API').status, DRAFT)
        response = self.client.post(url, dict(data, number='API-P', status=POSTED), format='json', **self.header)
        self.assertHttpStatus(response, http_status.HTTP_201_CREATED)
        self.assertEqual(Invoice.objects.get(number='API-P').invoicelines.count(), 1)
