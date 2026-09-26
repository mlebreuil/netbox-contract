"""Spec user story 4: consistent currencies (FR-009..FR-011)."""

from decimal import Decimal

from circuits.models import Provider
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from utilities.testing import TestCase as NetBoxTestCase

from netbox_contract.models import Contract, ContractLine, Invoice, InvoiceLine
from netbox_contract.tests.custom import APITestCase
from netbox_contract.tests.helpers import (
    make_contract,
    make_invoice,
    make_invoice_line,
    make_line,
    make_provider,
    monthly,
)


def all_messages(exception):
    return ' '.join(exception.messages)


class ModelCurrencyTestCase(TestCase):
    def test_contract_line_currency_must_match(self):
        """Scenario 1."""
        contract = make_contract(currency='eur')
        line = ContractLine(contract=contract, unit=monthly(), unit_price=Decimal(1), description='x', currency='chf')
        with self.assertRaises(ValidationError) as cm:
            line.full_clean()
        self.assertIn('currency', cm.exception.message_dict)
        self.assertIn('CHF', all_messages(cm.exception))
        self.assertIn('EUR', all_messages(cm.exception))
        line.currency = 'eur'
        line.full_clean()

    def test_invoice_line_currency_must_match(self):
        """Scenario 3."""
        invoice = make_invoice(None, amount=100, currency='eur')
        line = InvoiceLine(invoice=invoice, amount=Decimal(10), currency='chf')
        with self.assertRaises(ValidationError) as cm:
            line.full_clean()
        self.assertIn('currency', cm.exception.message_dict)
        self.assertIn('CHF', all_messages(cm.exception))
        self.assertIn('EUR', all_messages(cm.exception))

    def test_existing_mismatched_invoice_line_can_still_be_edited(self):
        invoice = make_invoice(None, amount=100, currency='eur')
        line = make_invoice_line(invoice, amount=10, currency='chf')
        line.comments = 'Unrelated change'
        line.full_clean()

    def test_contract_currency_change_refused_with_invoices(self):
        """Scenario 4."""
        contract = make_contract(currency='eur')
        make_line(contract, monthly(), 100)
        make_invoice(contract, number='INV-1', amount=100)
        contract.currency = 'chf'
        with self.assertRaises(ValidationError) as cm:
            contract.full_clean()
        self.assertIn('currency', cm.exception.message_dict)
        self.assertIn('INV-1', all_messages(cm.exception))

    def test_contract_currency_change_refused_with_referencing_invoice_lines(self):
        parent = make_contract(name='Parent', currency='eur')
        child = make_contract(name='Child', currency='eur', parent=parent, billable=False)
        line = make_line(child, monthly(), 10)
        invoice = make_invoice(parent, number='INV-P', amount=100)
        make_invoice_line(invoice, amount=10, contract_line=line, quantity=1)
        child.parent = None
        child.billable = True
        child.save()
        child.currency = 'chf'
        with self.assertRaises(ValidationError) as cm:
            child.full_clean()
        self.assertIn('currency', cm.exception.message_dict)

    def test_contract_lines_follow_the_contract_currency(self):
        """Scenario 4: with only contract lines, the change is accepted and the lines follow."""
        contract = make_contract(currency='eur')
        line = make_line(contract, monthly(), 100)
        contract.currency = 'chf'
        contract.full_clean()
        contract.save()
        line.refresh_from_db()
        self.assertEqual(line.currency, 'chf')

    def test_non_billable_child_needs_parent_currency(self):
        """Scenario 5."""
        parent = make_contract(name='Parent', currency='eur')
        child = make_contract(name='Child', currency='chf', billable=False)
        child.parent = parent
        with self.assertRaises(ValidationError) as cm:
            child.full_clean()
        self.assertIn('parent', cm.exception.message_dict)
        self.assertIn('CHF', all_messages(cm.exception))
        self.assertIn('EUR', all_messages(cm.exception))

    def test_billable_child_may_have_another_currency(self):
        parent = make_contract(name='Parent', currency='eur')
        child = make_contract(name='Child', currency='chf')
        child.parent = parent
        child.full_clean()

    def test_child_becoming_non_billable_needs_parent_currency(self):
        parent = make_contract(name='Parent', currency='eur')
        child = make_contract(name='Child', currency='chf', parent=parent)
        child.billable = False
        with self.assertRaises(ValidationError):
            child.full_clean()

    def test_parent_currency_change_checked_against_non_billable_children(self):
        parent = make_contract(name='Parent', currency='eur')
        make_contract(name='Child', currency='eur', parent=parent, billable=False)
        parent.currency = 'chf'
        with self.assertRaises(ValidationError) as cm:
            parent.full_clean()
        self.assertIn('Child', all_messages(cm.exception))


class InvoiceFormCurrencyTestCase(NetBoxTestCase):
    def setUp(self):
        super().setUp()
        self.user.is_superuser = True
        self.user.save()
        self.eur = make_contract(name='EUR contract', currency='eur')
        self.chf = make_contract(name='CHF contract', currency='chf')

    def post_invoice(self, contracts, currency='eur', instance=None, **extra):
        data = {
            'number': 'INV-X',
            'date': '2025-01-31',
            'status': 'posted',
            'period_start': '2025-01-01',
            'period_end': '2025-01-31',
            'currency': currency,
            'amount': '0',
            'contracts': [c.pk for c in contracts],
            **extra,
        }
        if instance:
            url = reverse('plugins:netbox_contract:invoice_edit', args=[instance.pk])
        else:
            url = reverse('plugins:netbox_contract:invoice_add')
        return self.client.post(url, data)

    def test_invoice_currency_must_match_its_contract(self):
        """Scenario 2."""
        response = self.post_invoice([self.chf], currency='eur')
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn('CHF', content)
        self.assertIn('EUR', content)
        self.assertFalse(Invoice.objects.filter(number='INV-X').exists())
        response = self.post_invoice([self.chf], currency='chf')
        self.assertEqual(response.status_code, 302)

    def test_new_invoice_limited_to_one_contract(self):
        """Scenario 6."""
        other = make_contract(name='Other EUR', currency='eur')
        response = self.post_invoice([self.eur, other])
        self.assertEqual(response.status_code, 200)
        self.assertIn('one contract', response.content.decode())
        self.assertFalse(Invoice.objects.filter(number='INV-X').exists())

    def test_existing_multi_contract_invoice_stays_editable(self):
        """Scenario 6: grandfathered invoices."""
        other = make_contract(name='Other EUR', currency='eur')
        invoice = make_invoice(self.eur, number='OLD', amount=0, currency='eur')
        invoice.contracts.add(other)
        response = self.post_invoice([self.eur, other], instance=invoice, number='OLD', comments='Edited')
        self.assertEqual(response.status_code, 302)
        invoice.refresh_from_db()
        self.assertEqual(invoice.comments, 'Edited')
        third = make_contract(name='Third EUR', currency='eur')
        response = self.post_invoice([self.eur, other, third], instance=invoice, number='OLD')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(invoice.contracts.count(), 2)

    def test_contract_line_form_refuses_other_currency(self):
        data = {
            'contract': self.eur.pk,
            'description': 'Line',
            'quantity': 1,
            'unit_price': 10,
            'unit': monthly().pk,
            'currency': 'chf',
        }
        response = self.client.post(reverse('plugins:netbox_contract:contractline_add'), data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('CHF', response.content.decode())
        self.assertFalse(ContractLine.objects.exists())

    def test_contract_form_currency_change(self):
        make_line(self.eur, monthly(), 10)
        provider = make_provider()
        data = {
            'name': self.eur.name,
            'external_party_object_type': ContentType.objects.get_for_model(Provider).pk,
            'external_party_object': provider.pk,
            'internal_party': 'default',
            'status': 'active',
            'currency': 'usd',
            'notice_period': 90,
            'invoice_frequency': 1,
            'billable': True,
            'start_date': '2025-01-01',
            'end_date': '2025-12-31',
        }
        url = reverse('plugins:netbox_contract:contract_edit', args=[self.eur.pk])
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(set(self.eur.lines.values_list('currency', flat=True)), {'usd'})
        make_invoice(self.eur, number='INV-USD', amount=0, currency='usd')
        response = self.client.post(url, dict(data, currency='eur'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('INV-USD', response.content.decode())
        self.assertEqual(Contract.objects.get(pk=self.eur.pk).currency, 'usd')


class APICurrencyTestCase(APITestCase):
    model = Invoice

    def setUp(self):
        super().setUp()
        self.add_permissions(
            'netbox_contract.add_invoice', 'netbox_contract.change_invoice', 'netbox_contract.view_invoice',
            'netbox_contract.add_contractline', 'netbox_contract.add_invoiceline',
            'netbox_contract.change_contract', 'netbox_contract.view_contract',
        )
        self.eur = make_contract(name='EUR contract', currency='eur')
        self.chf = make_contract(name='CHF contract', currency='chf')

    def invoice_data(self, contracts, currency):
        return {
            'number': 'API-INV',
            'status': 'posted',
            'period_start': '2025-01-01',
            'period_end': '2025-01-31',
            'currency': currency,
            'amount': '0',
            'contracts': [c.pk for c in contracts],
        }

    def test_invoice_currency(self):
        response = self.client.post(
            self._get_list_url(), self.invoice_data([self.chf], 'eur'), format='json', **self.header
        )
        self.assertHttpStatus(response, status.HTTP_400_BAD_REQUEST)
        self.assertIn('CHF', str(response.data))
        response = self.client.post(
            self._get_list_url(), self.invoice_data([self.chf], 'chf'), format='json', **self.header
        )
        self.assertHttpStatus(response, status.HTTP_201_CREATED)

    def test_new_invoice_with_two_contracts(self):
        other = make_contract(name='Other', currency='eur')
        response = self.client.post(
            self._get_list_url(), self.invoice_data([self.eur, other], 'eur'), format='json', **self.header
        )
        self.assertHttpStatus(response, status.HTTP_400_BAD_REQUEST)

    def test_existing_multi_contract_invoice(self):
        other = make_contract(name='Other', currency='eur')
        invoice = make_invoice(self.eur, number='OLD', amount=0, currency='eur')
        invoice.contracts.add(other)
        url = self._get_detail_url(invoice)
        response = self.client.patch(url, {'comments': 'Edited'}, format='json', **self.header)
        self.assertHttpStatus(response, status.HTTP_200_OK)
        third = make_contract(name='Third', currency='eur')
        response = self.client.patch(
            url, {'contracts': [self.eur.pk, other.pk, third.pk]}, format='json', **self.header
        )
        self.assertHttpStatus(response, status.HTTP_400_BAD_REQUEST)

    def test_contract_line_and_invoice_line_currency(self):
        url = reverse('plugins-api:netbox_contract-api:contractline-list')
        data = {'contract': self.eur.pk, 'description': 'x', 'unit_price': 1, 'unit': monthly().pk, 'currency': 'chf'}
        response = self.client.post(url, data, format='json', **self.header)
        self.assertHttpStatus(response, status.HTTP_400_BAD_REQUEST)
        self.assertIn('currency', response.data)

        invoice = make_invoice(None, amount=100, currency='eur')
        url = reverse('plugins-api:netbox_contract-api:invoiceline-list')
        data = {'invoice': invoice.pk, 'amount': 10, 'currency': 'chf'}
        response = self.client.post(url, data, format='json', **self.header)
        self.assertHttpStatus(response, status.HTTP_400_BAD_REQUEST)
        self.assertIn('currency', response.data)

    def test_contract_currency_change(self):
        make_invoice(self.eur, number='INV-E', amount=0, currency='eur')
        url = reverse('plugins-api:netbox_contract-api:contract-detail', args=[self.eur.pk])
        response = self.client.patch(url, {'currency': 'chf'}, format='json', **self.header)
        self.assertHttpStatus(response, status.HTTP_400_BAD_REQUEST)
        self.assertIn('currency', response.data)

    def test_non_billable_child_parent_currency(self):
        child = make_contract(name='Child', currency='chf', billable=False)
        url = reverse('plugins-api:netbox_contract-api:contract-detail', args=[child.pk])
        response = self.client.patch(url, {'parent': self.eur.pk}, format='json', **self.header)
        self.assertHttpStatus(response, status.HTTP_400_BAD_REQUEST)
        self.assertIn('parent', response.data)
