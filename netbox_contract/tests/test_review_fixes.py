"""Fixes after the code review of 2026-09-27 (tasks T075 to T083)."""

from datetime import date, timedelta
from decimal import Decimal

from core.models import ObjectType
from django.core.exceptions import ValidationError
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from users.models import ObjectPermission
from utilities.exceptions import AbortRequest
from utilities.testing import TestCase

from netbox_contract.models import Contract, ContractLine, InvoiceStatusChoices
from netbox_contract.services import invoicing
from netbox_contract.services.amendments import amend_contract_line
from netbox_contract.tests.helpers import (
    make_contract,
    make_invoice,
    make_invoice_line,
    make_line,
    monthly,
)

DRAFT = InvoiceStatusChoices.STATUS_DRAFT
POSTED = InvoiceStatusChoices.STATUS_POSTED


class NoPeriodTestCase(TestCase):
    """T075: without an invoice period only the lines active today are invoiced."""

    def test_ended_and_replaced_lines_are_not_billed(self):
        contract = make_contract(start_date=None, end_date=None)
        line = make_line(contract, monthly(), 100, start_date=date(2020, 1, 1), end_date=None)
        new = amend_contract_line(line, date(2021, 1, 1), 'Indexation', unit_price=Decimal(120))
        make_line(contract, monthly(), 7, start_date=date(2020, 1, 1), end_date=date(2020, 6, 30), description='Old')
        make_line(contract, monthly(), 9, start_date=date.today() + timedelta(days=30), end_date=None,
                  description='Future')
        lines = invoicing.lines_to_generate(contract, None, None)
        self.assertEqual([planned.contract_line for planned in lines], [new])
        self.assertEqual(invoicing.propose_invoice(contract, None, None).total, Decimal('120.00'))


class PrefillLastInvoiceTestCase(TestCase):
    """T076: an invoice without end date does not break the pre-fill."""

    def test_invoice_without_period_is_ignored(self):
        self.user.is_superuser = True
        self.user.save()
        contract = make_contract()
        make_invoice(contract, number='NOPERIOD', amount=0, status=DRAFT, period_start=None, period_end=None)
        make_invoice(contract, number='JAN', amount=0, status=DRAFT)
        response = self.client.get(f"{reverse('plugins:netbox_contract:invoice_add')}?contracts={contract.pk}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['form'].initial['period_start'], date(2025, 2, 1))


class PreviewPermissionsTestCase(TestCase):
    """T077: the pre-fill and the preview only show contracts the user may view."""

    def setUp(self):
        super().setUp()
        self.visible = make_contract(name='Visible')
        make_line(self.visible, monthly(), 100, description='Visible line')
        self.hidden = make_contract(name='Hidden')
        make_line(self.hidden, monthly(), 100, description='Secret line')
        self.add_permissions('netbox_contract.add_invoice')
        permission = ObjectPermission.objects.create(
            name='Visible contracts', actions=['view'], constraints={'name': 'Visible'}
        )
        permission.users.add(self.user)
        permission.object_types.add(ObjectType.objects.get_for_model(Contract))

    def preview(self, contract):
        return self.client.post(reverse('plugins:netbox_contract:invoice_lines_preview'), {
            'contracts': [contract.pk], 'period_start': '2025-01-01', 'period_end': '2025-01-31',
        }).content.decode()

    def test_preview(self):
        self.assertIn('Visible line', self.preview(self.visible))
        self.assertNotIn('Secret line', self.preview(self.hidden))

    def test_prefill(self):
        response = self.client.get(f"{reverse('plugins:netbox_contract:invoice_add')}?contracts={self.hidden.pk}")
        self.assertNotIn('Secret line', response.content.decode())
        self.assertIsNone(response.context['form'].initial.get('amount'))


class ParentCurrencyTestCase(TestCase):
    """T078: a parent changes currency together with its non-billable descendants."""

    def setUp(self):
        self.parent = make_contract(name='Parent', currency='eur')
        self.child = make_contract(name='Child', currency='eur', parent=self.parent, billable=False)
        self.grandchild = make_contract(name='Grandchild', currency='eur', parent=self.child, billable=False)
        self.billable_child = make_contract(name='Billable child', currency='eur', parent=self.parent)
        self.line = make_line(self.grandchild, monthly(), 10)

    def test_descendants_follow(self):
        self.parent.currency = 'usd'
        self.parent.full_clean()
        self.parent.save()
        for contract, expected in ((self.child, 'usd'), (self.grandchild, 'usd'), (self.billable_child, 'eur')):
            contract.refresh_from_db()
            self.assertEqual(contract.currency, expected, contract.name)
        self.line.refresh_from_db()
        self.assertEqual(self.line.currency, 'usd')

    def test_refused_when_a_descendant_is_invoiced(self):
        invoice = make_invoice(self.parent, number='INV-P', amount=100, currency='eur')
        make_invoice_line(invoice, contract_line=self.line, quantity=1)
        self.parent.refresh_from_db()
        self.parent.currency = 'usd'
        with self.assertRaises(ValidationError):
            self.parent.full_clean()

    def test_refused_when_a_descendant_has_an_invoice(self):
        make_invoice(self.child, number='INV-C', amount=0, currency='eur')
        self.parent.currency = 'usd'
        with self.assertRaises(ValidationError) as cm:
            self.parent.full_clean()
        self.assertIn('INV-C', ' '.join(cm.exception.messages))


class ZeroPriceTestCase(TestCase):
    """T079: a unit price of 0 typed in the preview is kept."""

    def test_zero_price(self):
        contract = make_contract()
        line = make_line(contract, monthly(), 100)
        (planned,) = invoicing.lines_to_generate(
            contract, date(2025, 1, 1), date(2025, 1, 31), {line.pk: {'unit_price': Decimal(0)}}
        )
        self.assertEqual((planned.unit_price, planned.amount), (Decimal(0), Decimal('0.00')))
        overrides, errors = invoicing.parse_line_overrides({f'line-{line.pk}-unit_price': '0'})
        self.assertEqual(overrides, {line.pk: {'unit_price': Decimal(0)}})


class AmendPermissionTestCase(TestCase):
    """T081: the amend screen needs the add and change contract line permissions."""

    def test_change_only_is_refused(self):
        contract = make_contract()
        line = make_line(contract, monthly(), 100)
        url = reverse('plugins:netbox_contract:contractline_amend', args=[line.pk])
        self.add_permissions('netbox_contract.change_contractline', 'netbox_contract.view_contractline')
        data = {'effective_date': '2025-07-01', 'unit_price': '110', 'reason': 'x'}
        self.assertEqual(self.client.post(url, data).status_code, 403)
        self.assertEqual(ContractLine.objects.count(), 1)
        self.add_permissions('netbox_contract.add_contractline')
        self.assertEqual(self.client.post(url, data).status_code, 302)


class ContractDeletionTestCase(TestCase):
    """T082: a contract whose lines are on Posted invoices cannot be deleted."""

    def setUp(self):
        self.parent = make_contract(name='Parent')
        self.child = make_contract(name='Child', parent=self.parent, billable=False)
        self.line = make_line(self.child, monthly(), 10)
        self.invoice = make_invoice(self.parent, amount=100, status=DRAFT)
        make_invoice_line(self.invoice, contract_line=self.line, quantity=1)

    def test_draft_invoice_does_not_block(self):
        self.parent.delete()
        self.assertFalse(Contract.objects.filter(pk=self.child.pk).exists())

    def test_posted_invoice_blocks(self):
        self.invoice.status = POSTED
        self.invoice.save()
        for contract in (self.child, self.parent):
            with self.subTest(contract=contract.name), self.assertRaises(AbortRequest):
                contract.delete()
        self.assertTrue(ContractLine.objects.filter(pk=self.line.pk).exists())


class ContractValuesOnceTestCase(TestCase):
    """T083: the contract page computes the contract values once."""

    def test_contract_page(self):
        self.user.is_superuser = True
        self.user.save()
        contract = make_contract()
        make_line(contract, monthly(), 100)
        url = reverse('plugins:netbox_contract:contract', args=[contract.pk])
        self.client.get(url)
        with CaptureQueriesContext(connection) as queries:
            response = self.client.get(url)
        self.assertIn('1200.00', response.content.decode())
        tree_scans = [q for q in queries.captured_queries if q['sql'].startswith(
            'SELECT "netbox_contract_contract"."id" AS "pk", "netbox_contract_contract"."parent_id"')]
        self.assertEqual(len(tree_scans), 1)
