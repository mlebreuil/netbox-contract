"""Lock of contract lines once invoiced (FR-029) and of used units (FR-001a)."""

from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import ProtectedError
from django.test import TestCase
from django.urls import reverse
from utilities.exceptions import AbortRequest
from utilities.testing import TestCase as NetBoxTestCase

from netbox_contract.models import (
    BillingMethodChoices,
    Contract,
    ContractLine,
    InvoiceStatusChoices,
    Unit,
)
from netbox_contract.tests.helpers import (
    make_contract,
    make_invoice,
    make_invoice_line,
    make_line,
    monthly,
    one_time,
)

NEW_CONTRACT_MESSAGE = 'new contract must be created'


class ContractLineLockTestCase(TestCase):
    def setUp(self):
        self.contract = make_contract()
        self.line = make_line(self.contract, monthly(), 100)

    def assertLocked(self, callable_):
        with self.assertRaises((ValidationError, AbortRequest)) as cm:
            callable_()
        exception = cm.exception
        message = exception.message if isinstance(exception, AbortRequest) else ' '.join(exception.messages)
        self.assertIn(NEW_CONTRACT_MESSAGE, message)

    def test_editable_before_any_invoice(self):
        self.line.unit_price = Decimal(150)
        self.line.full_clean()
        self.line.save()
        ContractLine(contract=self.contract, unit=monthly(), unit_price=Decimal(1), description='Other').full_clean()
        self.line.delete()
        self.assertFalse(ContractLine.objects.filter(pk=self.line.pk).exists())

    def test_locked_by_each_invoice_status(self):
        for status in (
            InvoiceStatusChoices.STATUS_DRAFT,
            InvoiceStatusChoices.STATUS_POSTED,
            InvoiceStatusChoices.STATUS_CANCELED,
        ):
            with self.subTest(status=status):
                invoice = make_invoice(self.contract, status=status, amount=100)
                line = ContractLine.objects.get(pk=self.line.pk)

                # change
                line.unit_price = Decimal(150)
                self.assertLocked(line.full_clean)

                # add
                new = ContractLine(contract=self.contract, unit=monthly(), unit_price=Decimal(1), description='New')
                self.assertLocked(new.full_clean)

                # delete
                self.assertLocked(ContractLine.objects.get(pk=self.line.pk).delete)
                with transaction.atomic():
                    self.assertLocked(ContractLine.objects.filter(pk=self.line.pk).delete)
                self.assertTrue(ContractLine.objects.filter(pk=self.line.pk).exists())

                invoice.delete()

    def test_deleting_the_contract_cascades_to_its_lines(self):
        make_invoice(self.contract, amount=100)
        self.contract.delete()
        self.assertFalse(ContractLine.objects.filter(pk=self.line.pk).exists())

    def test_deleting_a_parent_contract_cascades_to_the_lines_of_its_children(self):
        child = make_contract(name='Child', parent=self.contract, billable=False)
        child_line = make_line(child, monthly(), 10)
        invoice = make_invoice(self.contract, amount=100)
        make_invoice_line(invoice, amount=10, contract_line=child_line, quantity=1)
        Contract.objects.filter(pk=self.contract.pk).delete()
        self.assertFalse(ContractLine.objects.filter(pk=child_line.pk).exists())


class ReferencedLineLockTestCase(TestCase):
    """Spec user story 1, scenario 9: a non-billable child invoiced through its parent."""

    def setUp(self):
        self.parent = make_contract(name='Parent')
        self.child = make_contract(name='Child', parent=self.parent, billable=False)
        self.used = make_line(self.child, monthly(), 10, description='Used')
        self.unused = make_line(self.child, monthly(), 20, description='Unused')
        invoice = make_invoice(self.parent, amount=100)
        make_invoice_line(invoice, amount=10, contract_line=self.used, quantity=1)

    def test_referenced_line_cannot_change(self):
        self.used.unit_price = Decimal(99)
        with self.assertRaises(ValidationError) as cm:
            self.used.full_clean()
        self.assertIn(NEW_CONTRACT_MESSAGE, ' '.join(cm.exception.messages))

    def test_referenced_line_cannot_be_deleted(self):
        with self.assertRaises(AbortRequest):
            self.used.delete()
        self.assertTrue(ContractLine.objects.filter(pk=self.used.pk).exists())

    def test_unreferenced_sibling_stays_editable(self):
        self.unused.unit_price = Decimal(25)
        self.unused.full_clean()
        self.unused.save()
        self.unused.delete()


class UnitLockTestCase(TestCase):
    def setUp(self):
        self.unit = Unit.objects.create(name='Quarterly', billing_method=BillingMethodChoices.RECURRING, months=3)
        self.contract = make_contract()
        self.line = make_line(self.contract, self.unit, 300)

    def test_used_unit_cannot_be_deleted(self):
        with self.assertRaises(ProtectedError):
            self.unit.delete()

    def test_unused_unit_can_be_deleted(self):
        unit = one_time()
        unit.delete()

    def test_months_change_allowed_without_invoice(self):
        """Scenario 6."""
        self.unit.months = 6
        self.unit.full_clean()
        self.unit.save()
        self.unit.description = 'Any'
        self.unit.full_clean()

    def test_months_and_method_change_refused_once_invoiced(self):
        make_invoice(self.contract, amount=300)
        self.unit.months = 6
        with self.assertRaises(ValidationError) as cm:
            self.unit.full_clean()
        self.assertIn('months', cm.exception.message_dict)

        self.unit.refresh_from_db()
        self.unit.billing_method = BillingMethodChoices.USAGE
        self.unit.months = None
        with self.assertRaises(ValidationError) as cm:
            self.unit.full_clean()
        self.assertIn('billing_method', cm.exception.message_dict)

    def test_other_fields_can_change_once_invoiced(self):
        make_invoice(self.contract, amount=300)
        self.unit.description = 'Every three months'
        self.unit.name = 'Quarter'
        self.unit.full_clean()
        self.unit.save()

    def test_months_change_refused_when_an_invoice_line_references_a_line(self):
        parent = make_contract(name='Parent')
        child = make_contract(name='Child', parent=parent, billable=False)
        unit = Unit.objects.create(name='Half-yearly', billing_method=BillingMethodChoices.RECURRING, months=6)
        line = make_line(child, unit, 600)
        invoice = make_invoice(parent, amount=100, period_start=date(2025, 1, 1), period_end=date(2025, 1, 31))
        make_invoice_line(invoice, amount=100, contract_line=line, quantity=1)
        unit.months = 3
        with self.assertRaises(ValidationError):
            unit.full_clean()


class LockViewsTestCase(NetBoxTestCase):
    def setUp(self):
        super().setUp()
        self.user.is_superuser = True
        self.user.save()
        self.contract = make_contract()
        self.line = make_line(self.contract, monthly(), 100)
        make_invoice(self.contract, amount=100)

    def test_delete_view_refuses(self):
        url = reverse('plugins:netbox_contract:contractline_delete', args=[self.line.pk])
        response = self.client.post(url, {'confirm': True}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(ContractLine.objects.filter(pk=self.line.pk).exists())
        self.assertIn(NEW_CONTRACT_MESSAGE, response.content.decode())

    def test_edit_view_refuses(self):
        url = reverse('plugins:netbox_contract:contractline_edit', args=[self.line.pk])
        response = self.client.post(url, {
            'contract': self.contract.pk,
            'description': 'Changed',
            'quantity': 1,
            'unit_price': 150,
            'unit': self.line.unit.pk,
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(NEW_CONTRACT_MESSAGE, response.content.decode())
        self.line.refresh_from_db()
        self.assertEqual(self.line.description, 'Line')

    def test_contract_page_hides_line_buttons_and_shows_notice(self):
        response = self.client.get(reverse('plugins:netbox_contract:contract', args=[self.contract.pk]))
        content = response.content.decode()
        self.assertIn(NEW_CONTRACT_MESSAGE, content)
        self.assertNotIn(f"{reverse('plugins:netbox_contract:contractline_add')}?contract={self.contract.pk}", content)
