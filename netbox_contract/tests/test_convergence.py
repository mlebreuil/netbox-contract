"""Gaps found by /speckit-converge (tasks T069 to T071)."""

from decimal import Decimal
from unittest import mock

from django.conf import settings
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from utilities.testing import TestCase

from netbox_contract.models import Contract, Invoice, InvoiceStatusChoices
from netbox_contract.tests.custom import APITestCase
from netbox_contract.tests.helpers import make_contract, make_invoice, make_line, monthly, one_time, yearly

BULK_EDIT = 'plugins:netbox_contract:invoice_bulk_edit'


class InvoiceBulkEditContractsTestCase(TestCase):
    """T069: FR-011, FR-009 and FR-031 also apply to bulk edits of invoices."""

    def setUp(self):
        super().setUp()
        self.user.is_superuser = True
        self.user.save()
        self.usd = make_contract(name='USD')
        self.other_usd = make_contract(name='Other USD')
        self.chf = make_contract(name='CHF', currency='chf')

    def bulk_edit(self, invoices, contracts):
        return self.client.post(reverse(BULK_EDIT), {
            'pk': [invoice.pk for invoice in invoices], 'contracts': [c.pk for c in contracts], '_apply': True,
        })

    def contracts_of(self, invoice):
        return sorted(invoice.contracts.values_list('name', flat=True))

    def test_no_contract_added(self):
        invoice = make_invoice(self.usd, number='A', amount=0, status=InvoiceStatusChoices.STATUS_DRAFT)
        self.bulk_edit([invoice], [self.usd, self.other_usd])
        self.assertEqual(self.contracts_of(invoice), ['USD'])

    def test_currency_must_match(self):
        invoice = make_invoice(self.usd, number='A', amount=0, status=InvoiceStatusChoices.STATUS_DRAFT)
        self.bulk_edit([invoice], [self.chf])
        self.assertEqual(self.contracts_of(invoice), ['USD'])

    def test_contracts_of_a_posted_invoice_are_locked(self):
        invoice = make_invoice(self.usd, number='P', amount=0, status=InvoiceStatusChoices.STATUS_POSTED)
        self.bulk_edit([invoice], [self.other_usd])
        self.assertEqual(self.contracts_of(invoice), ['USD'])

    def test_allowed_change(self):
        invoice = make_invoice(self.usd, number='A', amount=0, status=InvoiceStatusChoices.STATUS_DRAFT)
        response = self.bulk_edit([invoice], [self.other_usd])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.contracts_of(invoice), ['Other USD'])

    def test_invoice_without_contract_can_get_one(self):
        invoice = Invoice.objects.create(number='FREE', amount=0, status=InvoiceStatusChoices.STATUS_DRAFT)
        self.bulk_edit([invoice], [self.usd])
        self.assertEqual(self.contracts_of(invoice), ['USD'])


class InvoiceBulkEditTemplateTestCase(TestCase):
    """T070: the template flag is offered only with show_deprecated_fields."""

    def setUp(self):
        super().setUp()
        self.user.is_superuser = True
        self.user.save()
        self.invoice = make_invoice(make_contract(), number='T', amount=0, status=InvoiceStatusChoices.STATUS_DRAFT)

    def test_template_field_hidden_by_default(self):
        response = self.client.post(reverse(BULK_EDIT), {'pk': [self.invoice.pk]})
        self.assertNotIn('template', response.context['form'].fields)
        self.client.post(reverse(BULK_EDIT), {'pk': [self.invoice.pk], 'template': True, '_apply': True})
        self.invoice.refresh_from_db()
        self.assertFalse(self.invoice.template)

    def test_template_field_with_setting(self):
        with mock.patch.dict(settings.PLUGINS_CONFIG['netbox_contract'], {'show_deprecated_fields': True}):
            response = self.client.post(reverse(BULK_EDIT), {'pk': [self.invoice.pk]})
        self.assertIn('template', response.context['form'].fields)


class ContractValuesQueriesTestCase(APITestCase):
    """T071: the contracts API list computes the contract values without a query per contract."""

    model = Contract

    def setUp(self):
        super().setUp()
        self.add_permissions('netbox_contract.view_contract')

    def add_family(self, name):
        parent = make_contract(name=f'{name} parent')
        make_line(parent, monthly(), 100)
        make_line(parent, one_time(), 50)
        child = make_contract(name=f'{name} child', parent=parent, billable=False)
        make_line(child, yearly(), 120)

    def list_queries(self):
        with CaptureQueriesContext(connection) as queries:
            response = self.client.get(f'{self._get_list_url()}?limit=100', **self.header)
        self.assertEqual(response.status_code, 200)
        return len(queries.captured_queries), response.data['results']

    def test_constant_number_of_queries(self):
        self.add_family('A')
        self.list_queries()  # warm up the caches of the first request (content types)
        few, _ = self.list_queries()
        for name in 'BCDE':
            self.add_family(name)
        many, results = self.list_queries()
        self.assertEqual(few, many)
        values = {item['name']: item for item in results}
        self.assertEqual(Decimal(values['A parent']['total_contract_value']), Decimal('1250.00'))
        self.assertEqual(Decimal(values['A parent']['yearly_billable_value']), Decimal('1320.00'))
        self.assertEqual(Decimal(values['A child']['yearly_billable_value']), Decimal('0.00'))
        self.assertEqual(Decimal(values['A child']['yearly_contract_value']), Decimal('120.00'))
