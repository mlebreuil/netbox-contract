"""Preview of the generated lines on the new invoice form, with editable quantities and unit prices (FR-032)."""

from datetime import date
from decimal import Decimal

from django.urls import reverse
from utilities.testing import TestCase

from netbox_contract.models import AccountingDimension, ContractLine, Invoice
from netbox_contract.services import invoicing
from netbox_contract.tests.helpers import make_contract, make_line, monthly, one_time, usage

ADD_URL = 'plugins:netbox_contract:invoice_add'
PREVIEW_URL = 'plugins:netbox_contract:invoice_lines_preview'


class LinesPreviewServiceTestCase(TestCase):
    def setUp(self):
        super().setUp()
        self.contract = make_contract()
        self.hosting = make_line(self.contract, monthly(), 100, description='Hosting')
        self.traffic = make_line(self.contract, usage(), 20, description='Traffic')

    def test_overrides_change_quantity_and_price(self):
        overrides = {
            self.traffic.pk: {'quantity': Decimal(10)},
            self.hosting.pk: {'unit_price': Decimal(90), 'quantity': Decimal(2)},
        }
        lines = invoicing.lines_to_generate(self.contract, date(2025, 1, 1), date(2025, 1, 31), overrides)
        by_line = {line.contract_line: line for line in lines}
        self.assertEqual(
            (by_line[self.hosting].quantity, by_line[self.hosting].unit_price, by_line[self.hosting].amount),
            (Decimal(2), Decimal(90), Decimal('180.00')),
        )
        self.assertEqual(by_line[self.traffic].amount, Decimal('200.00'))
        errors = invoicing.check_new_invoice(
            self.contract, Decimal(379), date(2025, 1, 1), date(2025, 1, 31), overrides
        )
        self.assertIn('380.00', errors[0])

    def test_parse_line_overrides(self):
        data = {
            f'line-{self.traffic.pk}-quantity': '12.5',
            f'line-{self.traffic.pk}-unit_price': '',
            f'line-{self.hosting.pk}-quantity': '',
            'line-x-quantity': '3',
            'amount': '100',
        }
        overrides, errors = invoicing.parse_line_overrides(data)
        self.assertEqual(errors, [])
        self.assertEqual(
            overrides, {self.traffic.pk: {'quantity': Decimal('12.5')}, self.hosting.pk: {'quantity': None}}
        )
        _, errors = invoicing.parse_line_overrides({f'line-{self.traffic.pk}-unit_price': 'abc'})
        self.assertEqual(len(errors), 1)


class NewInvoiceFormPreviewTestCase(TestCase):
    def setUp(self):
        super().setUp()
        self.user.is_superuser = True
        self.user.save()
        self.parent = make_contract(name='Parent')
        self.hosting = make_line(self.parent, monthly(), 100, description='Hosting')
        self.child = make_contract(name='Child', parent=self.parent, billable=False)
        self.traffic = make_line(self.child, usage(), 20, description='Traffic')
        self.setup_fee = make_line(self.parent, one_time(), 50, description='Setup')

    def data(self, **extra):
        return {
            'number': 'PREVIEW-1',
            'status': 'draft',
            'period_start': '2025-01-01',
            'period_end': '2025-01-31',
            'currency': 'usd',
            'amount': '1000',
            'contracts': [self.parent.pk],
            **extra,
        }

    def test_preview_on_the_add_form(self):
        response = self.client.get(f'{reverse(ADD_URL)}?contracts={self.parent.pk}')
        content = response.content.decode()
        self.assertIn('Lines to generate', content)
        self.assertIn(reverse(PREVIEW_URL), content)
        for line in (self.hosting, self.traffic, self.setup_fee):
            self.assertIn(f'name="line-{line.pk}-quantity"', content)
            self.assertIn(f'name="line-{line.pk}-unit_price"', content)
        self.assertIn('Traffic', content)
        preview = response.context['lines_preview']
        self.assertEqual(preview['total'], Decimal('150.00'))

    def test_no_preview_without_contract_or_when_editing(self):
        response = self.client.get(reverse(ADD_URL))
        self.assertIn('Choose a contract', response.content.decode())
        invoice = Invoice.objects.create(number='OLD', amount=0, status='draft')
        response = self.client.get(reverse('plugins:netbox_contract:invoice_edit', args=[invoice.pk]))
        self.assertNotIn('Lines to generate', response.content.decode())

    def test_preview_endpoint_recalculates(self):
        response = self.client.post(reverse(PREVIEW_URL), self.data(**{
            f'line-{self.traffic.pk}-quantity': '10',
            f'line-{self.hosting.pk}-unit_price': '80',
            'period_end': '2025-03-31',
        }))
        self.assertEqual(response.status_code, 200)
        preview = response.context['lines_preview']
        amounts = {row['line'].contract_line: row['line'].amount for row in preview['rows']}
        # three months at 80, 10 x 20, setup 50
        self.assertEqual(amounts[self.hosting], Decimal('240.00'))
        self.assertEqual(amounts[self.traffic], Decimal('200.00'))
        self.assertEqual(preview['total'], Decimal('490.00'))
        self.assertFalse(preview['amount_too_low'])
        self.assertIn('value="10"', response.content.decode())

    def test_preview_warns_when_the_amount_is_too_low(self):
        response = self.client.post(reverse(PREVIEW_URL), self.data(amount='100'))
        self.assertTrue(response.context['lines_preview']['amount_too_low'])
        self.assertIn('lower than the total', response.content.decode())

    def test_preview_of_a_non_billable_contract(self):
        response = self.client.post(reverse(PREVIEW_URL), self.data(contracts=[self.child.pk]))
        self.assertIn('not billable', response.content.decode())

    def test_preview_requires_the_add_invoice_permission(self):
        self.user.is_superuser = False
        self.user.save()
        response = self.client.post(reverse(PREVIEW_URL), self.data())
        self.assertEqual(response.status_code, 403)

    def test_create_with_quantities_and_prices(self):
        response = self.client.post(reverse(ADD_URL), self.data(**{
            f'line-{self.traffic.pk}-quantity': '10',
            f'line-{self.hosting.pk}-unit_price': '90',
            f'line-{self.setup_fee.pk}-quantity': '1',
        }))
        self.assertEqual(response.status_code, 302, response.content.decode()[-2000:])
        invoice = Invoice.objects.get(number='PREVIEW-1')
        lines = {line.contract_line: line for line in invoice.invoicelines.all()}
        self.assertEqual((lines[self.traffic].quantity, lines[self.traffic].amount), (Decimal(10), Decimal('200.00')))
        self.assertEqual((lines[self.hosting].unit_price, lines[self.hosting].amount), (Decimal(90), Decimal('90.00')))
        self.assertEqual(lines[self.setup_fee].amount, Decimal('50.00'))
        self.assertEqual(ContractLine.objects.get(pk=self.hosting.pk).unit_price, Decimal(100))

    def test_create_refused_when_the_amount_is_lower_than_the_edited_lines(self):
        response = self.client.post(reverse(ADD_URL), self.data(amount='200', **{
            f'line-{self.traffic.pk}-quantity': '10',
        }))
        self.assertEqual(response.status_code, 200)
        self.assertIn('350.00', response.content.decode())
        self.assertFalse(Invoice.objects.filter(number='PREVIEW-1').exists())
        # the preview keeps the typed quantity
        self.assertIn('value="10"', response.content.decode())

    def test_invalid_quantity(self):
        response = self.client.post(reverse(ADD_URL), self.data(**{f'line-{self.traffic.pk}-quantity': 'many'}))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Invoice.objects.filter(number='PREVIEW-1').exists())

    def test_create_without_edits_generates_the_default_lines(self):
        response = self.client.post(reverse(ADD_URL), self.data())
        self.assertEqual(response.status_code, 302)
        invoice = Invoice.objects.get(number='PREVIEW-1')
        self.assertEqual(invoice.invoicelines.count(), 3)
        self.assertIsNone(invoice.invoicelines.get(contract_line=self.traffic).quantity)


class ExtraLinesTestCase(TestCase):
    """Lines added to a new invoice in the preview, without contract line (FR-032)."""

    def setUp(self):
        super().setUp()
        self.user.is_superuser = True
        self.user.save()
        self.contract = make_contract()
        self.hosting = make_line(self.contract, monthly(), 100, description='Hosting')

    def data(self, **extra):
        return {
            'number': 'EXTRA-1',
            'status': 'draft',
            'period_start': '2025-01-01',
            'period_end': '2025-01-31',
            'currency': 'usd',
            'amount': '1000',
            'contracts': [self.contract.pk],
            **extra,
        }

    def test_add_and_remove_a_line_in_the_preview(self):
        response = self.client.post(reverse(PREVIEW_URL), self.data(add_line='1'))
        content = response.content.decode()
        for field in ('description', 'unit', 'unit_price', 'quantity'):
            self.assertIn(f'name="extra-0-{field}"', content)
        self.assertIn('Add a line', content)
        response = self.client.post(reverse(PREVIEW_URL), self.data(**{
            'extra-0-description': 'Travel', 'extra-0-unit_price': '', 'extra-0-quantity': '',
            'extra-1-description': 'Installation', 'extra-1-unit_price': '120', 'extra-1-quantity': '2',
            'remove_line': '0',
        }))
        preview = response.context['lines_preview']
        self.assertEqual([row['description'] for row in preview['extra_rows']], ['Installation'])
        self.assertEqual(preview['extra_rows'][0]['amount'], Decimal('240.00'))
        self.assertEqual(preview['total'], Decimal('340.00'))

    def test_extra_line_with_a_recurring_unit(self):
        response = self.client.post(reverse(PREVIEW_URL), self.data(**{
            'period_end': '2025-03-31',
            'extra-0-description': 'Extra support', 'extra-0-unit': monthly().pk,
            'extra-0-unit_price': '10', 'extra-0-quantity': '1',
        }))
        self.assertEqual(response.context['lines_preview']['extra_rows'][0]['amount'], Decimal('30.00'))

    def test_create_with_extra_lines(self):
        response = self.client.post(reverse(ADD_URL), self.data(**{
            'extra-0-description': 'Installation', 'extra-0-unit': one_time().pk,
            'extra-0-unit_price': '120', 'extra-0-quantity': '2',
            'extra-1-description': '', 'extra-1-unit_price': '', 'extra-1-quantity': '',
        }))
        self.assertEqual(response.status_code, 302, response.content.decode()[-2000:])
        invoice = Invoice.objects.get(number='EXTRA-1')
        self.assertEqual(invoice.invoicelines.count(), 2)
        extra = invoice.invoicelines.get(contract_line__isnull=True)
        self.assertEqual(
            (extra.comments, extra.unit, extra.unit_price, extra.quantity, extra.amount),
            ('Installation', one_time(), Decimal(120), Decimal(2), Decimal('240.00')),
        )

    def test_incomplete_extra_line_refused(self):
        response = self.client.post(reverse(ADD_URL), self.data(**{
            'extra-0-description': 'Installation', 'extra-0-quantity': '2',
        }))
        self.assertEqual(response.status_code, 200)
        self.assertIn('Installation', response.content.decode())
        self.assertFalse(Invoice.objects.filter(number='EXTRA-1').exists())

    def test_extra_lines_count_in_the_amount_check(self):
        response = self.client.post(reverse(ADD_URL), self.data(amount='300', **{
            'extra-0-description': 'Installation', 'extra-0-unit_price': '120', 'extra-0-quantity': '2',
        }))
        self.assertEqual(response.status_code, 200)
        self.assertIn('340.00', response.content.decode())
        self.assertFalse(Invoice.objects.filter(number='EXTRA-1').exists())


class PreviewDimensionsTestCase(TestCase):
    """Accounting dimensions of the lines in the preview of a new invoice (FR-032)."""

    def setUp(self):
        super().setUp()
        self.user.is_superuser = True
        self.user.save()
        self.contract = make_contract()
        self.account = AccountingDimension.objects.create(name='account', value='A1')
        self.other_account = AccountingDimension.objects.create(name='account', value='A2')
        self.department = AccountingDimension.objects.create(name='department', value='IT')
        self.hosting = make_line(self.contract, monthly(), 100, description='Hosting')
        self.hosting.accounting_dimensions.set([self.account])

    def data(self, **extra):
        return {
            'number': 'DIM-1', 'status': 'draft', 'period_start': '2025-01-01', 'period_end': '2025-01-31',
            'currency': 'usd', 'amount': '1000', 'contracts': [self.contract.pk], **extra,
        }

    def test_selectors_in_the_preview(self):
        response = self.client.post(reverse(PREVIEW_URL), self.data(add_line='1'))
        content = response.content.decode()
        self.assertIn(f'name="line-{self.hosting.pk}-accounting_dimensions"', content)
        self.assertIn('name="extra-0-accounting_dimensions"', content)
        row = response.context['lines_preview']['rows'][0]
        self.assertEqual(list(row['dimensions_form'].initial['accounting_dimensions']), [self.account.pk])

    def test_create_with_changed_dimensions(self):
        prefix = f'line-{self.hosting.pk}'
        response = self.client.post(reverse(ADD_URL), self.data(**{
            f'{prefix}-dimensions': '1',
            f'{prefix}-accounting_dimensions': [self.other_account.pk, self.department.pk],
            'extra-0-description': 'Travel', 'extra-0-unit_price': '50', 'extra-0-quantity': '1',
            'extra-0-dimensions': '1', 'extra-0-accounting_dimensions': [self.department.pk],
        }))
        self.assertEqual(response.status_code, 302, response.content.decode()[-2000:])
        invoice = Invoice.objects.get(number='DIM-1')
        generated = invoice.invoicelines.get(contract_line=self.hosting)
        self.assertEqual(set(generated.accounting_dimensions.all()), {self.other_account, self.department})
        added = invoice.invoicelines.get(contract_line__isnull=True)
        self.assertEqual(list(added.accounting_dimensions.all()), [self.department])
        # the contract line keeps its own dimensions
        self.assertEqual(list(self.hosting.accounting_dimensions.all()), [self.account])

    def test_cleared_dimensions(self):
        response = self.client.post(reverse(ADD_URL), self.data(**{f'line-{self.hosting.pk}-dimensions': '1'}))
        self.assertEqual(response.status_code, 302)
        generated = Invoice.objects.get(number='DIM-1').invoicelines.get()
        self.assertFalse(generated.accounting_dimensions.exists())

    def test_duplicate_dimension_names_refused(self):
        response = self.client.post(reverse(ADD_URL), self.data(**{
            f'line-{self.hosting.pk}-dimensions': '1',
            f'line-{self.hosting.pk}-accounting_dimensions': [self.account.pk, self.other_account.pk],
        }))
        self.assertEqual(response.status_code, 200)
        self.assertIn('Hosting', response.content.decode())
        self.assertFalse(Invoice.objects.filter(number='DIM-1').exists())

    def test_mandatory_dimensions(self):
        from unittest import mock

        from django.conf import settings

        with mock.patch.dict(settings.PLUGINS_CONFIG['netbox_contract'], {'mandatory_dimensions': ['department']}):
            response = self.client.post(reverse(ADD_URL), self.data())
            self.assertEqual(response.status_code, 200)
            self.assertIn('department', response.content.decode())
            self.assertFalse(Invoice.objects.filter(number='DIM-1').exists())
            response = self.client.post(reverse(ADD_URL), self.data(**{
                f'line-{self.hosting.pk}-dimensions': '1',
                f'line-{self.hosting.pk}-accounting_dimensions': [self.account.pk, self.department.pk],
            }))
            self.assertEqual(response.status_code, 302, response.content.decode()[-2000:])
