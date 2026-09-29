"""Spec user story 6: invoice lines generated at invoice creation (FR-021..FR-025, SC-006)."""

from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from utilities.testing import TestCase as NetBoxTestCase

from netbox_contract.models import AccountingDimension, ContractLine, Invoice, InvoiceLine, InvoiceStatusChoices
from netbox_contract.services import invoicing
from netbox_contract.tests.custom import APITestCase
from netbox_contract.tests.helpers import (
    make_contract,
    make_invoice,
    make_invoice_line,
    make_line,
    make_unit,
    monthly,
    one_time,
    usage,
)

DRAFT = InvoiceStatusChoices.STATUS_DRAFT


class HierarchyMixin:
    def build_hierarchy(self):
        self.account = AccountingDimension.objects.create(name='account', value='A1')
        self.department = AccountingDimension.objects.create(name='department', value='IT')
        self.parent = make_contract(name='Parent')
        self.parent_line = make_line(self.parent, monthly(), 100, description='Parent hosting')
        self.parent_line.accounting_dimensions.set([self.account, self.department])
        self.child = make_contract(name='Child', parent=self.parent, billable=False)
        self.child_line = make_line(self.child, monthly(), 10, description='Child support')
        self.usage_line = make_line(self.child, usage(), 20, quantity=5, description='Traffic')
        self.grandchild = make_contract(name='Grandchild', parent=self.child, billable=False)
        self.setup_line = make_line(self.grandchild, one_time(), 50, description='Setup')
        self.billable_child = make_contract(name='Billable child', parent=self.parent)
        make_line(self.billable_child, monthly(), 1, description='Invoiced by the child')


class GenerationViewTestCase(HierarchyMixin, NetBoxTestCase):
    def setUp(self):
        super().setUp()
        self.user.is_superuser = True
        self.user.save()
        self.build_hierarchy()

    def create_invoice(self, contract, amount='1000', **extra):
        data = {
            'number': 'GEN-1',
            'date': '2025-01-31',
            'status': 'draft',
            'period_start': '2025-01-01',
            'period_end': '2025-01-31',
            'currency': contract.currency,
            'amount': amount,
            'contracts': [contract.pk],
            **extra,
        }
        return self.client.post(reverse('plugins:netbox_contract:invoice_add'), data)

    def test_lines_generated_for_the_hierarchy(self):
        """Scenarios 1 to 3."""
        response = self.create_invoice(self.parent)
        self.assertEqual(response.status_code, 302, response.content.decode()[-2000:])
        invoice = Invoice.objects.get(number='GEN-1')
        lines = {line.contract_line: line for line in invoice.invoicelines.all()}
        self.assertEqual(set(lines), {self.parent_line, self.child_line, self.usage_line, self.setup_line})

        parent = lines[self.parent_line]
        self.assertEqual(parent.quantity, 1)
        self.assertEqual(parent.amount, Decimal('100.00'))
        self.assertEqual(parent.currency, invoice.currency)
        self.assertEqual(set(parent.accounting_dimensions.all()), {self.account, self.department})
        self.assertEqual(parent.unit, self.parent_line.unit)
        self.assertEqual(parent.unit_price, Decimal(100))
        self.assertEqual(lines[self.child_line].amount, Decimal('10.00'))
        self.assertEqual(lines[self.setup_line].amount, Decimal('50.00'))

    def test_usage_line_generated_without_quantity(self):
        """Scenario 5."""
        self.create_invoice(self.parent)
        line = InvoiceLine.objects.get(contract_line=self.usage_line)
        self.assertIsNone(line.quantity)
        self.assertEqual(line.amount, Decimal('0.00'))

        line.quantity = Decimal(10)
        line.full_clean()
        line.save()
        self.assertEqual(line.amount, Decimal('200.00'))
        line.quantity = Decimal(12)
        line.full_clean()
        line.save()
        line.refresh_from_db()
        self.assertEqual(line.amount, Decimal('240.00'))

    def test_editing_a_generated_line_keeps_the_reference(self):
        """Scenario 6, through the invoice line form."""
        self.create_invoice(self.parent)
        line = InvoiceLine.objects.get(contract_line=self.usage_line)
        response = self.client.post(
            reverse('plugins:netbox_contract:invoiceline_edit', args=[line.pk]),
            {
                'invoice': line.invoice.pk,
                'contract_line': self.usage_line.pk,
                'unit': self.usage_line.unit.pk,
                'unit_price': '20',
                'quantity': '3',
                'currency': line.currency,
                'amount': '9999',
                'accounting_dimensions': [self.account.pk],
            },
        )
        self.assertEqual(response.status_code, 302, response.content.decode()[-2000:])
        line.refresh_from_db()
        self.assertEqual(line.contract_line, self.usage_line)
        self.assertEqual(line.amount, Decimal('60.00'))
        self.assertEqual(list(line.accounting_dimensions.all()), [self.account])

    def test_edit_form_of_a_line_with_a_contract_line(self):
        """Only the quantity (and the internal fields) can change; unit and unit price are shown read-only."""
        self.create_invoice(self.parent)
        line = InvoiceLine.objects.get(contract_line=self.parent_line)
        url = reverse('plugins:netbox_contract:invoiceline_edit', args=[line.pk])
        response = self.client.get(url)
        form = response.context['form']
        content = response.content.decode()
        self.assertIn('Unit price', content)
        self.assertIn('Monthly', content)
        for field in ('invoice', 'contract_line', 'currency', 'amount'):
            self.assertTrue(form.fields[field].disabled, field)
        for field in ('unit', 'unit_price', 'quantity', 'accounting_dimensions', 'comments', 'tags'):
            self.assertFalse(form.fields[field].disabled, field)
        self.assertEqual(form.initial['unit'], self.parent_line.unit.pk)
        self.assertEqual(form.initial['unit_price'], Decimal(100))
        names = list(form.fields)
        position = names.index('contract_line')
        self.assertEqual(names[position + 1:position + 3], ['unit', 'unit_price'])

        response = self.client.post(url, {
            'unit': self.parent_line.unit.pk, 'unit_price': '100', 'quantity': '2', 'amount': '1',
            'accounting_dimensions': [self.account.pk],
        })
        self.assertEqual(response.status_code, 302, response.content.decode()[-1500:])
        line.refresh_from_db()
        self.assertEqual((line.quantity, line.amount), (Decimal(2), Decimal('200.00')))
        self.assertEqual((line.contract_line, line.invoice.number), (self.parent_line, 'GEN-1'))

    def test_edit_form_of_a_manual_line(self):
        invoice = make_invoice(None, number='MANUAL', amount=100, status=DRAFT)
        line = make_invoice_line(invoice, amount=40)
        form = self.client.get(reverse('plugins:netbox_contract:invoiceline_edit', args=[line.pk])).context['form']
        self.assertTrue(form.fields['amount'].disabled)
        self.assertFalse(form.fields['unit'].disabled)
        self.assertFalse(form.fields['unit_price'].disabled)
        self.assertEqual(form.initial['unit_price'], Decimal(40))

    def test_non_billable_contract_refused(self):
        """Scenario 4."""
        response = self.create_invoice(self.child)
        self.assertEqual(response.status_code, 200)
        self.assertIn('not billable', response.content.decode())
        self.assertFalse(Invoice.objects.filter(number='GEN-1').exists())
        self.assertFalse(InvoiceLine.objects.exists())

    def test_amount_lower_than_the_lines_refused(self):
        """Scenario 9: the lines total 160."""
        response = self.create_invoice(self.parent, amount='150')
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn('150', content)
        self.assertIn('160.00', content)
        self.assertFalse(Invoice.objects.filter(number='GEN-1').exists())
        response = self.create_invoice(self.parent, amount='160')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Invoice.objects.get(number='GEN-1').invoicelines.count(), 4)

    def test_no_generation_when_an_invoice_is_edited(self):
        invoice = make_invoice(self.parent, number='EXISTING', amount=1000, status=InvoiceStatusChoices.STATUS_DRAFT)
        response = self.client.post(
            reverse('plugins:netbox_contract:invoice_edit', args=[invoice.pk]),
            {
                'number': 'EXISTING',
                'status': 'draft',
                'period_start': '2025-01-01',
                'period_end': '2025-01-31',
                'currency': 'usd',
                'amount': '1000',
                'contracts': [self.parent.pk],
                'comments': 'Edited',
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(invoice.invoicelines.count(), 0)

    def test_no_generation_through_bulk_import(self):
        csv = (
            'number,contracts,status,currency,amount,period_start,period_end\n'
            'IMP-1,Parent,draft,usd,1000,2025-01-01,2025-01-31'
        )
        response = self.client.post(
            reverse('plugins:netbox_contract:invoice_bulk_import'),
            {'data': csv, 'format': 'csv', 'csv_delimiter': 'auto'},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Invoice.objects.get(number='IMP-1').invoicelines.count(), 0)

    def test_import_invoice_line_with_a_contract_line(self):
        invoice = make_invoice(self.parent, number='IMPORTED', amount=1000, status=DRAFT)
        csv = f'invoice,contract_line,quantity,currency,amount\nIMPORTED,{self.usage_line.pk},4,usd,'
        response = self.client.post(
            reverse('plugins:netbox_contract:invoiceline_bulk_import'),
            {'data': csv, 'format': 'csv', 'csv_delimiter': 'auto'},
        )
        self.assertEqual(response.status_code, 302)
        line = invoice.invoicelines.get()
        self.assertEqual(line.contract_line, self.usage_line)
        self.assertEqual(line.amount, Decimal('80.00'))

    def test_invoice_without_contract(self):
        response = self.client.post(
            reverse('plugins:netbox_contract:invoice_add'),
            {'number': 'FREE', 'status': 'draft', 'currency': 'usd', 'amount': '10'},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Invoice.objects.get(number='FREE').invoicelines.count(), 0)

    def test_template_lines_are_not_copied(self):
        """Scenario 8."""
        template = Invoice.objects.create(number='_invoice_template_Parent', template=True, amount=Decimal(77))
        template.contracts.add(self.parent)
        InvoiceLine.objects.create(invoice=template, amount=Decimal(77), currency='usd', comments='Template line')
        self.create_invoice(self.parent)
        invoice = Invoice.objects.get(number='GEN-1')
        self.assertFalse(invoice.invoicelines.filter(comments='Template line').exists())
        self.assertEqual(invoice.invoicelines.count(), 4)
        template.refresh_from_db()
        self.assertTrue(template.template)
        self.assertEqual(template.invoicelines.count(), 1)

    def test_invoice_line_form_limits_contract_lines_to_the_invoice(self):
        invoice = make_invoice(self.parent, number='LIMIT', amount=1000)
        url = reverse('plugins-api:netbox_contract-api:contractline-list')
        response = self.client.get(f'{url}?invoice_id={invoice.pk}')
        self.assertEqual(
            {item['id'] for item in response.json()['results']},
            {self.parent_line.pk, self.child_line.pk, self.usage_line.pk, self.setup_line.pk},
        )


class GenerationRulesTestCase(TestCase):
    def test_recurring_line_over_three_months(self):
        """Scenario 7."""
        contract = make_contract(invoice_frequency=3)
        line = make_line(contract, monthly(), 100)
        invoice = make_invoice(contract, amount=300, period_start=date(2025, 1, 1), period_end=date(2025, 3, 31))
        (generated,) = invoicing.generate_invoice_lines(invoice)
        self.assertEqual(generated.contract_line, line)
        self.assertEqual(generated.quantity, 1)
        self.assertEqual(generated.amount, Decimal('300.00'))

    def test_one_time_quantity_reduced_by_posted_invoices(self):
        contract = make_contract()
        line = make_line(contract, one_time(), 100, quantity=5)
        posted = make_invoice(contract, number='P', amount=1000)
        make_invoice_line(posted, contract_line=line, quantity=2, amount=200)
        draft = make_invoice(contract, number='D', amount=1000, status=InvoiceStatusChoices.STATUS_DRAFT)
        make_invoice_line(draft, contract_line=line, quantity=1, amount=100)
        invoice = make_invoice(contract, number='NEW', amount=1000, status=InvoiceStatusChoices.STATUS_DRAFT)
        (generated,) = invoicing.generate_invoice_lines(invoice)
        self.assertEqual(generated.quantity, 3)
        self.assertEqual(generated.amount, Decimal('300.00'))

    def test_one_time_fully_invoiced_or_flagged_is_skipped(self):
        contract = make_contract()
        line = make_line(contract, one_time(), 100, quantity=2)
        flagged = make_line(contract, one_time(), 70, description='Converted')
        ContractLine.objects.filter(pk=flagged.pk).update(invoiced_at_conversion=True)
        posted = make_invoice(contract, number='P', amount=1000)
        make_invoice_line(posted, contract_line=line, quantity=3, amount=300)
        invoice = make_invoice(contract, number='NEW', amount=1000)
        self.assertEqual(invoicing.generate_invoice_lines(invoice), [])

    def test_total_to_generate(self):
        contract = make_contract()
        make_line(contract, monthly(), 100)
        make_line(contract, one_time(), 60)
        make_line(contract, usage(), 5, quantity=10)
        errors = invoicing.check_new_invoice(contract, Decimal(159), date(2025, 1, 1), date(2025, 1, 31))
        self.assertEqual(len(errors), 1)
        self.assertIn('160.00', errors[0])
        self.assertEqual(invoicing.check_new_invoice(contract, Decimal(160), date(2025, 1, 1), date(2025, 1, 31)), [])

    def test_recurring_line_without_period_counts_the_invoice_frequency(self):
        """Decision 2026-09-26: without an invoice period, a recurring line counts for one invoice frequency."""
        contract = make_contract(start_date=None, end_date=None, invoice_frequency=3)
        make_line(contract, monthly(), 100)
        errors = invoicing.check_new_invoice(contract, Decimal(299), None, None)
        self.assertEqual(len(errors), 1)
        self.assertIn('300.00', errors[0])
        self.assertEqual(invoicing.check_new_invoice(contract, Decimal(300), None, None), [])
        invoice = make_invoice(contract, amount=1000, period_start=None, period_end=None, status=DRAFT)
        (generated,) = invoicing.generate_invoice_lines(invoice)
        self.assertEqual(generated.amount, Decimal('300.00'))
        generated.quantity = Decimal(2)
        generated.full_clean()
        generated.save()
        self.assertEqual(generated.amount, Decimal('600.00'))

    def test_credit_line(self):
        contract = make_contract()
        make_line(contract, monthly(), 100)
        make_line(contract, monthly(), -30, description='Discount')
        self.assertEqual(invoicing.check_new_invoice(contract, Decimal(70), date(2025, 1, 1), date(2025, 1, 31)), [])
        invoice = make_invoice(contract, amount=70)
        amounts = sorted(line.amount for line in invoicing.generate_invoice_lines(invoice))
        self.assertEqual(amounts, [Decimal('-30.00'), Decimal('100.00')])

    def test_amount_recalculated_when_saved_after_a_period_change(self):
        """Edge case: the amounts follow the invoice period when each line is saved again."""
        contract = make_contract()
        make_line(contract, monthly(), 100)
        invoice = make_invoice(contract, amount=1000, status=DRAFT)
        (generated,) = invoicing.generate_invoice_lines(invoice)
        self.assertEqual(generated.amount, Decimal('100.00'))
        invoice.period_end = date(2025, 2, 28)
        invoice.save()
        generated.refresh_from_db()
        self.assertEqual(generated.amount, Decimal('100.00'))
        generated.full_clean()
        generated.save()
        self.assertEqual(generated.amount, Decimal('200.00'))

    def test_generated_lines_use_the_invoice_currency(self):
        contract = make_contract(currency='chf')
        make_line(contract, monthly(), 100)
        invoice = make_invoice(contract, amount=100)
        (generated,) = invoicing.generate_invoice_lines(invoice)
        self.assertEqual(generated.currency, 'chf')


class InvoiceLineRulesTestCase(TestCase):
    def setUp(self):
        self.contract = make_contract()
        self.line = make_line(self.contract, usage(), 20)
        self.invoice = make_invoice(self.contract, amount=1000, status=DRAFT)

    def test_contract_line_of_an_unrelated_contract_refused(self):
        """FR-021a."""
        other = make_contract(name='Other')
        other_line = make_line(other, usage(), 20)
        invoice_line = InvoiceLine(invoice=self.invoice, contract_line=other_line, quantity=1, currency='usd')
        with self.assertRaises(ValidationError) as cm:
            invoice_line.full_clean()
        self.assertIn('contract_line', cm.exception.message_dict)

    def test_contract_line_of_a_billable_child_refused(self):
        child = make_contract(name='Billable child', parent=self.contract)
        child_line = make_line(child, usage(), 20)
        invoice_line = InvoiceLine(invoice=self.invoice, contract_line=child_line, quantity=1, currency='usd')
        with self.assertRaises(ValidationError):
            invoice_line.full_clean()

    def test_amount_ignored_with_a_contract_line(self):
        invoice_line = InvoiceLine(
            invoice=self.invoice, contract_line=self.line, quantity=Decimal(2), amount=Decimal(1), currency='usd'
        )
        invoice_line.full_clean()
        invoice_line.save()
        self.assertEqual(invoice_line.amount, Decimal('40.00'))

    def test_unit_price_required_without_a_contract_line(self):
        invoice_line = InvoiceLine(invoice=self.invoice, currency='usd')
        with self.assertRaises(ValidationError) as cm:
            invoice_line.full_clean()
        self.assertIn('unit_price', cm.exception.message_dict)
        invoice_line.unit_price = Decimal(5)
        invoice_line.full_clean()

    def test_invoice_line_name(self):
        invoice_line = InvoiceLine(invoice=self.invoice, contract_line=self.line, quantity=1, currency='usd')
        invoice_line.save()
        self.assertEqual(str(invoice_line), f'INV line {invoice_line.pk}')
        self.assertEqual(str(InvoiceLine(invoice=self.invoice)), 'INV new line')

    def test_lines_cannot_exceed_the_invoice_amount(self):
        invoice_line = InvoiceLine(invoice=self.invoice, contract_line=self.line, quantity=Decimal(51), currency='usd')
        with self.assertRaises(ValidationError):
            invoice_line.full_clean()


class GenerationAPITestCase(HierarchyMixin, APITestCase):
    model = Invoice

    def setUp(self):
        super().setUp()
        self.add_permissions(
            'netbox_contract.add_invoice', 'netbox_contract.view_invoice', 'netbox_contract.change_invoice',
            'netbox_contract.add_invoiceline', 'netbox_contract.change_invoiceline', 'netbox_contract.view_invoiceline',
        )
        self.build_hierarchy()

    def invoice_data(self, contract, amount='1000'):
        return {
            'number': 'API-GEN',
            'status': 'draft',
            'period_start': '2025-01-01',
            'period_end': '2025-01-31',
            'currency': contract.currency,
            'amount': amount,
            'contracts': [contract.pk],
        }

    def test_creation_generates_the_lines(self):
        response = self.client.post(self._get_list_url(), self.invoice_data(self.parent), format='json', **self.header)
        self.assertHttpStatus(response, status.HTTP_201_CREATED)
        invoice = Invoice.objects.get(pk=response.data['id'])
        self.assertEqual(invoice.invoicelines.count(), 4)
        response = self.client.patch(
            self._get_detail_url(invoice), {'comments': 'Edited'}, format='json', **self.header
        )
        self.assertHttpStatus(response, status.HTTP_200_OK)
        self.assertEqual(invoice.invoicelines.count(), 4)

    def test_creation_refused(self):
        response = self.client.post(self._get_list_url(), self.invoice_data(self.child), format='json', **self.header)
        self.assertHttpStatus(response, status.HTTP_400_BAD_REQUEST)
        self.assertIn('not billable', str(response.data))
        response = self.client.post(
            self._get_list_url(), self.invoice_data(self.parent, amount='10'), format='json', **self.header
        )
        self.assertHttpStatus(response, status.HTTP_400_BAD_REQUEST)
        self.assertIn('160.00', str(response.data))
        self.assertFalse(Invoice.objects.exists())

    def test_invoice_line_fields(self):
        self.client.post(self._get_list_url(), self.invoice_data(self.parent), format='json', **self.header)
        line = InvoiceLine.objects.get(contract_line=self.usage_line)
        url = reverse('plugins-api:netbox_contract-api:invoiceline-detail', args=[line.pk])
        response = self.client.patch(url, {'quantity': 10, 'amount': 1}, format='json', **self.header)
        self.assertHttpStatus(response, status.HTTP_200_OK)
        self.assertEqual(Decimal(response.data['amount']), Decimal('200.00'))
        self.assertEqual(Decimal(response.data['quantity']), Decimal(10))
        self.assertEqual(Decimal(response.data['unit_price']), Decimal(20))
        self.assertEqual(response.data['unit']['id'], self.usage_line.unit.pk)
        self.assertEqual(response.data['contract_line']['id'], self.usage_line.pk)

        response = self.client.patch(url, {'unit_price': 1}, format='json', **self.header)
        self.assertHttpStatus(response, status.HTTP_200_OK)
        self.assertEqual(Decimal(response.data['amount']), Decimal('10.00'))

        url = reverse('plugins-api:netbox_contract-api:invoiceline-list')
        response = self.client.post(
            url, {'invoice': line.invoice.pk, 'currency': 'usd', 'unit': self.usage_line.unit.pk, 'unit_price': 7,
                  'quantity': 3}, format='json', **self.header,
        )
        self.assertHttpStatus(response, status.HTTP_201_CREATED)
        self.assertEqual(Decimal(response.data['amount']), Decimal('21.00'))

        invoice = line.invoice
        url = reverse('plugins-api:netbox_contract-api:invoiceline-list')
        response = self.client.post(
            url, {'invoice': invoice.pk, 'currency': 'usd', 'comments': 'no amount'}, format='json', **self.header
        )
        self.assertHttpStatus(response, status.HTTP_400_BAD_REQUEST)
        self.assertIn('unit_price', response.data)


class InvoiceLineUnitPriceTestCase(TestCase):
    """Invoice lines carry their own unit and unit price, fixed at creation (FR-024, decision I11)."""

    def setUp(self):
        self.contract = make_contract()
        self.monthly_line = make_line(self.contract, monthly(), 100)
        self.usage_line = make_line(self.contract, usage(), 20, description='Traffic')
        self.invoice = make_invoice(self.contract, amount=10000, status=DRAFT)

    def new_line(self, **kwargs):
        line = InvoiceLine(invoice=self.invoice, currency='usd', **kwargs)
        line.full_clean()
        line.save()
        return line

    def test_generated_lines_copy_unit_and_price(self):
        for generated in invoicing.generate_invoice_lines(self.invoice):
            self.assertEqual(generated.unit, generated.contract_line.unit)
            self.assertEqual(generated.unit_price, generated.contract_line.unit_price)

    def test_new_line_defaults_from_its_contract_line(self):
        line = self.new_line(contract_line=self.usage_line, quantity=Decimal(3))
        self.assertEqual(
            (line.unit, line.unit_price, line.amount), (self.usage_line.unit, Decimal(20), Decimal('60.00'))
        )

    def test_new_line_overrides_the_contract_line_price(self):
        line = self.new_line(contract_line=self.monthly_line, quantity=Decimal(1), unit_price=Decimal(90))
        self.assertEqual((line.unit, line.amount), (self.monthly_line.unit, Decimal('90.00')))
        self.monthly_line.refresh_from_db()
        self.assertEqual(self.monthly_line.unit_price, Decimal(100))

    def test_manual_line_with_unit_and_price(self):
        self.assertEqual(self.new_line(unit=usage(), unit_price=Decimal(20), quantity=Decimal(3)).amount,
                         Decimal('60.00'))
        # a recurring unit is prorated to the invoice period (January, one month)
        self.assertEqual(self.new_line(unit=monthly(), unit_price=Decimal(100), quantity=Decimal(1)).amount,
                         Decimal('100.00'))
        self.assertEqual(self.new_line(unit_price=Decimal(15), quantity=Decimal(2)).amount, Decimal('30.00'))

    def test_manual_line_amount_alone_becomes_its_unit_price(self):
        line = self.new_line(amount=Decimal('12.34'))
        self.assertEqual((line.quantity, line.unit_price, line.amount), (1, Decimal('12.34'), Decimal('12.34')))

    def test_unit_and_price_editable_until_the_invoice_is_posted(self):
        line = self.new_line(contract_line=self.usage_line, quantity=Decimal(3))
        line.quantity = Decimal(4)
        line.unit_price = Decimal(15)
        line.full_clean()
        line.save()
        self.assertEqual(line.amount, Decimal('60.00'))
        manual = self.new_line(amount=Decimal(5), quantity=Decimal(2))
        manual.unit_price = Decimal(2)
        manual.full_clean()
        manual.save()
        self.assertEqual(manual.amount, Decimal('4.00'))
        self.invoice.status = InvoiceStatusChoices.STATUS_POSTED
        self.invoice.save()
        for field, value in (('unit_price', Decimal(1)), ('unit', monthly())):
            with self.subTest(field=field):
                changed = InvoiceLine.objects.get(pk=line.pk)
                setattr(changed, field, value)
                with self.assertRaises(ValidationError) as cm:
                    changed.full_clean()
                self.assertIn(field, cm.exception.message_dict)

    def test_unit_used_by_an_invoice_line_is_locked(self):
        unit = make_unit('Every 2 months', 'recurring', 2)
        self.new_line(unit=unit, unit_price=Decimal(10), quantity=Decimal(1))
        unit.months = 3
        with self.assertRaises(ValidationError):
            unit.full_clean()

    def test_migration_copies_the_contract_line_prices(self):
        import importlib

        from django.apps import apps

        line = self.new_line(contract_line=self.usage_line, quantity=Decimal(3))
        InvoiceLine.objects.filter(pk=line.pk).update(unit=None, unit_price=None)
        manual = self.new_line(amount=Decimal(5))
        migration = importlib.import_module('netbox_contract.migrations.0047_invoiceline_unit_unit_price')
        migration.copy_contract_line_prices(apps, None)
        line.refresh_from_db()
        manual.refresh_from_db()
        self.assertEqual(
            (line.unit, line.unit_price, line.amount), (self.usage_line.unit, Decimal(20), Decimal('60.00'))
        )
        # a manual line got its amount as unit price when it was created (decision I14)
        self.assertEqual((manual.unit, manual.unit_price), (None, Decimal(5)))


class InvoiceLineFormUnitPriceTestCase(NetBoxTestCase):
    def setUp(self):
        super().setUp()
        self.user.is_superuser = True
        self.user.save()
        self.contract = make_contract()
        self.line = make_line(self.contract, usage(), 20)
        self.invoice = make_invoice(self.contract, amount=1000, status=DRAFT)

    def test_new_line_form(self):
        url = reverse('plugins:netbox_contract:invoiceline_add')
        form = self.client.get(f'{url}?invoice={self.invoice.pk}').context['form']
        for field in ('unit', 'unit_price', 'quantity', 'contract_line'):
            self.assertFalse(form.fields[field].disabled, field)
        response = self.client.post(url, {
            'invoice': self.invoice.pk, 'contract_line': self.line.pk, 'unit_price': '18', 'quantity': '5',
            'currency': 'usd', 'amount': '1',
        })
        self.assertEqual(response.status_code, 302, response.content.decode()[-1500:])
        created = InvoiceLine.objects.get(invoice=self.invoice)
        self.assertEqual(
            (created.unit, created.unit_price, created.amount), (self.line.unit, Decimal(18), Decimal('90.00'))
        )

    def test_import_with_unit_and_price(self):
        csv = f'invoice,unit,unit_price,quantity,currency\n{self.invoice.number},{self.line.unit.name},4,3,usd'
        response = self.client.post(
            reverse('plugins:netbox_contract:invoiceline_bulk_import'),
            {'data': csv, 'format': 'csv', 'csv_delimiter': 'auto'},
        )
        self.assertEqual(response.status_code, 302, response.content.decode()[-1500:])
        self.assertEqual(InvoiceLine.objects.get(invoice=self.invoice).amount, Decimal('12.00'))
