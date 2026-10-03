"""Spec user story 3: billable flag and computed contract values (FR-005..FR-008a)."""

from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from utilities.testing import TestCase as NetBoxTestCase

from netbox_contract.tests.helpers import (
    make_contract,
    make_invoice,
    make_invoice_line,
    make_line,
    monthly,
    one_time,
    usage,
    yearly,
)


class ContractValuesTestCase(TestCase):
    def test_scenario_1(self):
        """Total 1,900 (1,200 + 500 + 200) and yearly 1,200 (recurring lines only)."""
        contract = make_contract()
        make_line(contract, monthly(), 100)
        make_line(contract, one_time(), 500)
        make_line(contract, usage(), 20, quantity=10)
        self.assertEqual(contract.total_contract_value, Decimal('1900.00'))
        self.assertEqual(contract.yearly_contract_value, Decimal('1200.00'))
        self.assertEqual(contract.yearly_billable_value, Decimal('1200.00'))

    def test_contract_without_lines(self):
        contract = make_contract()
        self.assertEqual(contract.total_contract_value, Decimal('0.00'))
        self.assertEqual(contract.yearly_contract_value, Decimal('0.00'))
        self.assertEqual(contract.yearly_billable_value, Decimal('0.00'))

    def test_open_ended_total_not_available(self):
        """Scenario 4."""
        contract = make_contract(end_date=None)
        make_line(contract, monthly(), 100)
        make_line(contract, one_time(), 500)
        self.assertIsNone(contract.total_contract_value)
        self.assertEqual(contract.yearly_contract_value, Decimal('1200.00'))

    def test_line_end_date_on_open_ended_contract(self):
        contract = make_contract(end_date=None)
        make_line(contract, monthly(), 100, end_date=date(2025, 6, 30))
        self.assertEqual(contract.total_contract_value, Decimal('600.00'))

    def test_zero_and_negative_amounts(self):
        contract = make_contract()
        make_line(contract, monthly(), 100)
        make_line(contract, monthly(), -25, description='Discount')
        make_line(contract, one_time(), 0, description='Free setup')
        make_line(contract, yearly(), 120, quantity=0, description='Not used')
        self.assertEqual(contract.total_contract_value, Decimal('900.00'))
        self.assertEqual(contract.yearly_contract_value, Decimal('900.00'))

    def test_values_follow_line_changes(self):
        """Spec user story 1, scenario 7: editing or deleting a line updates the contract values."""
        contract = make_contract()
        line = make_line(contract, monthly(), 100)
        other = make_line(contract, one_time(), 500)
        line.unit_price = Decimal(50)
        line.save()
        self.assertEqual(contract.total_contract_value, Decimal('1100.00'))
        other.delete()
        self.assertEqual(contract.total_contract_value, Decimal('600.00'))
        self.assertEqual(contract.yearly_contract_value, Decimal('600.00'))


class BillableHierarchyTestCase(TestCase):
    """Scenario 2 and a multi-level hierarchy."""

    def setUp(self):
        self.parent = make_contract(name='Parent')
        make_line(self.parent, monthly(), 100)
        self.child = make_contract(name='Child', parent=self.parent, billable=False)
        make_line(self.child, monthly(), 50)
        make_line(self.child, one_time(), 999)
        self.grandchild = make_contract(name='Grandchild', parent=self.child, billable=False)
        make_line(self.grandchild, yearly(), 240)
        self.billable_child = make_contract(name='Billable child', parent=self.parent)
        make_line(self.billable_child, monthly(), 10)
        self.under_billable = make_contract(name='Under billable', parent=self.billable_child, billable=False)
        make_line(self.under_billable, monthly(), 1)

    def test_parent_includes_non_billable_descendants(self):
        # 1,200 own + 600 child + 240 grandchild
        self.assertEqual(self.parent.yearly_billable_value, Decimal('2040.00'))
        self.assertEqual(self.parent.yearly_contract_value, Decimal('1200.00'))

    def test_non_billable_child_has_no_billable_value(self):
        self.assertEqual(self.child.yearly_billable_value, Decimal('0.00'))
        self.assertEqual(self.child.yearly_contract_value, Decimal('600.00'))

    def test_billable_child_is_not_rolled_up(self):
        # 120 own + 12 of its non-billable child
        self.assertEqual(self.billable_child.yearly_billable_value, Decimal('132.00'))

    def test_billing_scope(self):
        self.assertEqual(
            {contract.name for contract in self.parent.billing_scope()}, {'Parent', 'Child', 'Grandchild'}
        )
        self.assertEqual({contract.name for contract in self.child.billing_scope()}, {'Child', 'Grandchild'})


class BillableLockTestCase(TestCase):
    """FR-008a and scenario 5."""

    def setUp(self):
        self.parent = make_contract(name='Parent')
        self.child = make_contract(name='Child', parent=self.parent, billable=False)
        self.grandchild = make_contract(name='Grandchild', parent=self.child, billable=False)

    def assertBillableLocked(self, contract):
        contract.refresh_from_db()
        contract.billable = not contract.billable
        with self.assertRaises(ValidationError) as cm:
            contract.full_clean()
        self.assertIn('billable', cm.exception.message_dict)

    def test_change_accepted_without_invoice(self):
        for contract in (self.parent, self.child, self.grandchild):
            contract.billable = not contract.billable
            contract.full_clean()

    def test_refused_when_the_contract_has_an_invoice(self):
        make_invoice(self.parent, amount=0)
        self.assertBillableLocked(self.parent)

    def test_refused_when_an_ancestor_has_an_invoice(self):
        make_invoice(self.parent, amount=0)
        self.assertBillableLocked(self.child)
        self.assertBillableLocked(self.grandchild)

    def test_refused_when_a_descendant_has_an_invoice(self):
        make_invoice(self.grandchild, amount=0)
        self.assertBillableLocked(self.parent)
        self.assertBillableLocked(self.child)

    def test_refused_when_an_invoice_line_references_one_of_its_lines(self):
        other = make_contract(name='Other')
        line = make_line(other, monthly(), 10)
        invoice = make_invoice(None, amount=100)
        make_invoice_line(invoice, amount=10, contract_line=line, quantity=1)
        self.assertBillableLocked(other)

    def test_other_fields_can_change_with_invoices(self):
        make_invoice(self.parent, amount=0)
        self.parent.refresh_from_db()
        self.parent.comments = 'Still editable'
        self.parent.full_clean()


class ValuesViewsTestCase(NetBoxTestCase):
    def setUp(self):
        super().setUp()
        self.user.is_superuser = True
        self.user.save()

    def test_detail_page_shows_the_values(self):
        contract = make_contract()
        make_line(contract, monthly(), 100)
        make_line(contract, one_time(), 500)
        content = self.client.get(reverse('plugins:netbox_contract:contract', args=[contract.pk])).content.decode()
        self.assertIn('Total contract value', content)
        self.assertIn('1700.00', content)
        self.assertIn('Yearly billable value', content)
        self.assertIn('1200.00', content)

    def test_detail_page_not_available(self):
        contract = make_contract(end_date=None)
        make_line(contract, monthly(), 100)
        content = self.client.get(reverse('plugins:netbox_contract:contract', args=[contract.pk])).content.decode()
        self.assertIn('Not available', content)

    def test_list_shows_yearly_value_and_billable(self):
        contract = make_contract(name='Listed')
        make_line(contract, monthly(), 100)
        make_line(contract, yearly(), 240)
        make_line(contract, one_time(), 500)
        response = self.client.get(reverse('plugins:netbox_contract:contract_list'))
        table = response.context['table']
        row = next(row for row in table.rows if row.record.pk == contract.pk)
        self.assertEqual(row.record.yearly_value, Decimal('1440.00'))
        self.assertIn('billable', [column.name for column in table.columns.iterall()])
        self.assertIn('1440.00', response.content.decode())
