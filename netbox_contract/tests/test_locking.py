"""Lock of contract lines once invoiced (FR-029) and of used units (FR-001a)."""

from datetime import date
from decimal import Decimal

from core.models import ObjectType
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import ProtectedError
from django.test import TestCase
from django.urls import reverse
from extras.choices import CustomFieldTypeChoices
from extras.models import CustomField
from rest_framework import status as http_status
from utilities.exceptions import AbortRequest
from utilities.testing import TestCase as NetBoxTestCase

from netbox_contract.models import (
    AccountingDimension,
    BillingMethodChoices,
    Contract,
    ContractLine,
    InvoiceStatusChoices,
    Unit,
)
from netbox_contract.tests.custom import APITestCase
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

    def test_edit_view_keeps_the_contract_terms(self):
        url = reverse('plugins:netbox_contract:contractline_edit', args=[self.line.pk])
        response = self.client.post(url, {
            'contract': self.contract.pk,
            'description': 'Changed',
            'quantity': 1,
            'unit_price': 150,
            'unit': self.line.unit.pk,
        })
        self.assertEqual(response.status_code, 302)
        self.line.refresh_from_db()
        self.assertEqual(self.line.description, 'Line')
        self.assertEqual(self.line.unit_price, Decimal(100))

    def test_add_view_refuses(self):
        response = self.client.post(reverse('plugins:netbox_contract:contractline_add'), {
            'contract': self.contract.pk,
            'description': 'New',
            'quantity': 1,
            'unit_price': 150,
            'unit': self.line.unit.pk,
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(NEW_CONTRACT_MESSAGE, response.content.decode())
        self.assertEqual(ContractLine.objects.count(), 1)

    def test_contract_page_hides_line_buttons_and_shows_notice(self):
        response = self.client.get(reverse('plugins:netbox_contract:contract', args=[self.contract.pk]))
        content = response.content.decode()
        self.assertIn(NEW_CONTRACT_MESSAGE, content)
        self.assertNotIn(f"{reverse('plugins:netbox_contract:contractline_add')}?contract={self.contract.pk}", content)
        self.assertIn(reverse('plugins:netbox_contract:contractline_edit', args=[self.line.pk]), content)
        self.assertNotIn(reverse('plugins:netbox_contract:contractline_delete', args=[self.line.pk]), content)
        self.assertIn('accounting dimensions, comments and tags can still be edited', content)


class InternalFieldsOfLockedLineTestCase(NetBoxTestCase):
    """Accounting dimensions, comments and tags stay editable on a locked contract line (FR-029, decision I9)."""

    def setUp(self):
        super().setUp()
        self.user.is_superuser = True
        self.user.save()
        self.contract = make_contract()
        self.line = make_line(self.contract, monthly(), 100)
        self.old = AccountingDimension.objects.create(name='account', value='OLD')
        self.new = AccountingDimension.objects.create(name='account', value='NEW')
        self.line.accounting_dimensions.set([self.old])
        self.invoice = make_invoice(self.contract, amount=100)
        self.invoice_line = make_invoice_line(self.invoice, contract_line=self.line, quantity=1, amount=100)
        self.invoice_line.accounting_dimensions.set([self.old])

    def test_model_accepts_internal_changes(self):
        self.line.comments = 'Moved to the new cost center'
        self.line.full_clean()
        self.line.save()
        self.line.accounting_dimensions.set([self.new])
        self.line.tags.add('reviewed')
        self.line.refresh_from_db()
        self.assertEqual(list(self.line.accounting_dimensions.all()), [self.new])

    def test_model_refuses_contract_terms(self):
        custom_field = CustomField.objects.create(name='po_number', type=CustomFieldTypeChoices.TYPE_TEXT)
        custom_field.object_types.set([ObjectType.objects.get_for_model(ContractLine)])
        for field, value in (
            ('description', 'Changed'), ('quantity', Decimal(2)), ('unit_price', Decimal(1)),
            ('start_date', date(2025, 2, 1)), ('end_date', date(2025, 11, 30)),
            ('custom_field_data', {'po_number': 'PO-1'}),
        ):
            with self.subTest(field=field):
                line = ContractLine.objects.get(pk=self.line.pk)
                setattr(line, field, value)
                with self.assertRaises(ValidationError) as cm:
                    line.full_clean()
                self.assertIn(NEW_CONTRACT_MESSAGE, ' '.join(cm.exception.messages))

    def test_existing_invoice_lines_keep_their_dimensions(self):
        self.line.accounting_dimensions.set([self.new])
        self.assertEqual(list(self.invoice_line.accounting_dimensions.all()), [self.old])

    def test_edit_form_of_a_locked_line(self):
        url = reverse('plugins:netbox_contract:contractline_edit', args=[self.line.pk])
        form = self.client.get(url).context['form']
        for field in ('contract', 'description', 'quantity', 'unit_price', 'unit', 'currency', 'start_date',
                      'end_date'):
            self.assertTrue(form.fields[field].disabled, field)
        for field in ('accounting_dimensions', 'comments', 'tags'):
            self.assertFalse(form.fields[field].disabled, field)

        # disabled fields keep their values even if a client sends others
        response = self.client.post(url, {
            'contract': self.contract.pk,
            'description': 'Ignored',
            'quantity': 5,
            'unit_price': 1,
            'unit': self.line.unit.pk,
            'accounting_dimensions': [self.new.pk],
            'comments': 'New cost center',
        })
        self.assertEqual(response.status_code, 302, response.content.decode()[-1500:])
        self.line.refresh_from_db()
        self.assertEqual(self.line.description, 'Line')
        self.assertEqual(self.line.unit_price, Decimal(100))
        self.assertEqual(list(self.line.accounting_dimensions.all()), [self.new])
        self.assertEqual(self.line.comments, 'New cost center')

    def test_deleting_stays_refused(self):
        with self.assertRaises(AbortRequest):
            self.line.delete()


class InternalFieldsAPITestCase(APITestCase):
    model = ContractLine

    def test_api(self):
        self.add_permissions('netbox_contract.change_contractline', 'netbox_contract.view_contractline')
        contract = make_contract()
        line = make_line(contract, monthly(), 100)
        make_invoice(contract, amount=100)
        dimension = AccountingDimension.objects.create(name='account', value='NEW')
        url = self._get_detail_url(line)
        response = self.client.patch(
            url, {'accounting_dimensions': [dimension.pk], 'comments': 'x'}, format='json', **self.header
        )
        self.assertHttpStatus(response, http_status.HTTP_200_OK)
        self.assertEqual([d['id'] for d in response.data['accounting_dimensions']], [dimension.pk])
        response = self.client.patch(url, {'unit_price': 1}, format='json', **self.header)
        self.assertHttpStatus(response, http_status.HTTP_400_BAD_REQUEST)
