"""REST and GraphQL API of the nine models: NetBox's complete API test case (#309 T046) and model rules."""

from datetime import date
from decimal import Decimal

from circuits.models import Provider
from dcim.models import Site
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from netbox.choices import ColorChoices
from rest_framework import status
from utilities.testing import APIViewTestCases

from netbox_contract.models import (
    AccountingDimension,
    BillingMethodChoices,
    Contract,
    ContractAssignment,
    ContractLine,
    ContractType,
    Invoice,
    InvoiceLine,
    InvoiceStatusChoices,
    ServiceProvider,
    StatusChoices,
    Unit,
)
from netbox_contract.tests.custom import APITestCase
from netbox_contract.tests.helpers import make_contract, make_invoice, make_line, monthly, one_time


class UnitAPITestCase(
    APITestCase,
    APIViewTestCases.APIViewTestCase,
):
    model = Unit
    brief_fields = ['billing_method', 'description', 'display', 'id', 'months', 'name', 'url']
    create_data = [
        {'name': 'Quarterly', 'billing_method': BillingMethodChoices.RECURRING, 'months': 3},
        {'name': 'Gigabyte', 'billing_method': BillingMethodChoices.USAGE},
        {'name': 'Installation', 'billing_method': BillingMethodChoices.ONE_TIME, 'description': 'Paid once'},
    ]
    bulk_update_data = {'description': 'Updated'}

    @classmethod
    def setUpTestData(cls):
        Unit.objects.create(name='Monthly', billing_method=BillingMethodChoices.RECURRING, months=1)
        Unit.objects.create(name='Yearly', billing_method=BillingMethodChoices.RECURRING, months=12)
        Unit.objects.create(name='Setup', billing_method=BillingMethodChoices.ONE_TIME)

    def test_validation_errors(self):
        self.add_permissions('netbox_contract.add_unit')
        url = self._get_list_url()
        response = self.client.post(url, {'name': 'Bad', 'billing_method': 'recurring'}, format='json', **self.header)
        self.assertHttpStatus(response, status.HTTP_400_BAD_REQUEST)
        self.assertIn('months', response.data)
        response = self.client.post(
            url, {'name': 'Bad', 'billing_method': 'usage', 'months': 2}, format='json', **self.header
        )
        self.assertHttpStatus(response, status.HTTP_400_BAD_REQUEST)
        self.assertIn('months', response.data)

    def test_used_unit_cannot_be_deleted(self):
        self.add_permissions('netbox_contract.delete_unit')
        unit = Unit.objects.get(name='Monthly')
        make_line(make_contract(), unit, 100)
        response = self.client.delete(self._get_detail_url(unit), **self.header)
        self.assertHttpStatus(response, status.HTTP_409_CONFLICT)
        self.assertTrue(Unit.objects.filter(pk=unit.pk).exists())

    def test_months_locked_once_invoiced(self):
        self.add_permissions('netbox_contract.change_unit')
        unit = Unit.objects.get(name='Monthly')
        contract = make_contract()
        make_line(contract, unit, 100)
        make_invoice(contract, amount=100)
        response = self.client.patch(self._get_detail_url(unit), {'months': 2}, format='json', **self.header)
        self.assertHttpStatus(response, status.HTTP_400_BAD_REQUEST)
        response = self.client.patch(self._get_detail_url(unit), {'description': 'x'}, format='json', **self.header)
        self.assertHttpStatus(response, status.HTTP_200_OK)


class ContractLineAPITestCase(
    APITestCase,
    APIViewTestCases.APIViewTestCase,
):
    model = ContractLine
    brief_fields = [
        'contract', 'currency', 'description', 'display', 'end_date', 'id', 'quantity', 'start_date', 'unit',
        'unit_price', 'url',
    ]
    bulk_update_data = {'comments': 'Updated'}

    @classmethod
    def setUpTestData(cls):
        contract = make_contract(name='Contract A')
        unit = monthly()
        dimension = AccountingDimension.objects.create(name='account', value='A1')
        for price in (100, 200, 300):
            make_line(contract, unit, price, description=f'Line {price}')

        cls.create_data = [
            {
                'contract': contract.pk,
                'description': 'API line 1',
                'quantity': 2,
                'unit_price': 50,
                'unit': unit.pk,
                'currency': 'usd',
                'start_date': date(2025, 2, 1),
                'end_date': date(2025, 11, 30),
                'accounting_dimensions': [dimension.pk],
            },
            {
                'contract': contract.pk,
                'description': 'API line 2',
                'unit_price': 10,
                'unit': unit.pk,
            },
            {
                'contract': contract.pk,
                'description': 'API line 3',
                'unit_price': -5,
                'quantity': 0,
                'unit': unit.pk,
            },
        ]

    def test_defaults_and_computed_values(self):
        self.add_permissions('netbox_contract.add_contractline', 'netbox_contract.view_contractline')
        contract = make_contract(name='Contract B', currency='eur')
        response = self.client.post(
            self._get_list_url(),
            {'contract': contract.pk, 'description': 'Hosting', 'unit_price': '100', 'unit': monthly().pk},
            format='json',
            **self.header,
        )
        self.assertHttpStatus(response, status.HTTP_201_CREATED)
        self.assertEqual(response.data['currency'], 'eur')
        self.assertEqual(response.data['start_date'], '2025-01-01')
        self.assertEqual(response.data['end_date'], '2025-12-31')
        self.assertEqual(Decimal(response.data['total_value']), Decimal('1200.00'))
        self.assertEqual(Decimal(response.data['yearly_value']), Decimal('1200.00'))
        self.assertFalse(response.data['invoiced_at_conversion'])

    def test_invoiced_at_conversion_is_read_only(self):
        self.add_permissions('netbox_contract.add_contractline')
        data = dict(self.create_data[1], invoiced_at_conversion=True)
        response = self.client.post(self._get_list_url(), data, format='json', **self.header)
        self.assertHttpStatus(response, status.HTTP_201_CREATED)
        self.assertFalse(ContractLine.objects.get(pk=response.data['id']).invoiced_at_conversion)

    def test_dates_outside_contract_refused(self):
        self.add_permissions('netbox_contract.add_contractline')
        data = dict(self.create_data[1], end_date='2026-03-31')
        response = self.client.post(self._get_list_url(), data, format='json', **self.header)
        self.assertHttpStatus(response, status.HTTP_400_BAD_REQUEST)
        self.assertIn('end_date', response.data)

    def test_lock_once_invoiced(self):
        self.add_permissions(
            'netbox_contract.add_contractline',
            'netbox_contract.change_contractline',
            'netbox_contract.delete_contractline',
        )
        line = ContractLine.objects.first()
        make_invoice(line.contract, amount=100)

        response = self.client.post(self._get_list_url(), self.create_data[1], format='json', **self.header)
        self.assertHttpStatus(response, status.HTTP_400_BAD_REQUEST)
        self.assertIn('new contract must be created', str(response.data))

        response = self.client.patch(self._get_detail_url(line), {'unit_price': '1'}, format='json', **self.header)
        self.assertHttpStatus(response, status.HTTP_400_BAD_REQUEST)
        self.assertIn('new contract must be created', str(response.data))

        response = self.client.delete(self._get_detail_url(line), **self.header)
        self.assertHttpStatus(response, status.HTTP_400_BAD_REQUEST)
        self.assertIn('new contract must be created', str(response.data))
        self.assertTrue(ContractLine.objects.filter(pk=line.pk).exists())

    def test_filters(self):
        self.add_permissions('netbox_contract.view_contractline')
        other = make_contract(name='Other', currency='eur')
        setup = Unit.objects.create(name='Setup', billing_method=BillingMethodChoices.ONE_TIME)
        make_line(other, setup, 500, description='Setup fee', start_date=date(2025, 1, 1))
        url = reverse('plugins-api:netbox_contract-api:contractline-list')

        response = self.client.get(f'{url}?contract_id={other.pk}', **self.header)
        self.assertEqual(response.data['count'], 1)
        response = self.client.get(f'{url}?billing_method=one_time', **self.header)
        self.assertEqual(response.data['count'], 1)
        response = self.client.get(f'{url}?billing_method=recurring', **self.header)
        self.assertEqual(response.data['count'], 3)
        response = self.client.get(f'{url}?currency=eur', **self.header)
        self.assertEqual(response.data['count'], 1)
        response = self.client.get(f'{url}?unit_id={setup.pk}', **self.header)
        self.assertEqual(response.data['count'], 1)
        response = self.client.get(f'{url}?q=setup', **self.header)
        self.assertEqual(response.data['count'], 1)


class ContractAPITestCase(APITestCase):
    """contracts/: billable flag, computed values and deprecated fields (US3)."""

    model = Contract

    def setUp(self):
        super().setUp()
        self.add_permissions('netbox_contract.view_contract', 'netbox_contract.change_contract')
        self.contract = make_contract(name='Valued', mrc=Decimal(100))
        make_line(self.contract, monthly(), 100)
        make_line(self.contract, one_time(), 500)
        self.open_ended = make_contract(name='Open', end_date=None, billable=False)
        make_line(self.open_ended, monthly(), 10)

    def test_computed_values(self):
        response = self.client.get(self._get_detail_url(self.contract), **self.header)
        self.assertHttpStatus(response, status.HTTP_200_OK)
        self.assertTrue(response.data['billable'])
        self.assertEqual(Decimal(response.data['total_contract_value']), Decimal('1700.00'))
        self.assertEqual(Decimal(response.data['yearly_contract_value']), Decimal('1200.00'))
        self.assertEqual(Decimal(response.data['yearly_billable_value']), Decimal('1200.00'))
        self.assertEqual(Decimal(response.data['mrc']), Decimal(100))

        response = self.client.get(self._get_detail_url(self.open_ended), **self.header)
        self.assertIsNone(response.data['total_contract_value'])
        self.assertEqual(Decimal(response.data['yearly_contract_value']), Decimal('120.00'))
        self.assertEqual(Decimal(response.data['yearly_billable_value']), Decimal('0.00'))

    def test_list_values_and_billable_filter(self):
        url = self._get_list_url()
        response = self.client.get(url, **self.header)
        values = {item['name']: Decimal(item['yearly_contract_value']) for item in response.data['results']}
        self.assertEqual(values, {'Valued': Decimal('1200.00'), 'Open': Decimal('120.00')})
        response = self.client.get(f'{url}?billable=false', **self.header)
        self.assertEqual([item['name'] for item in response.data['results']], ['Open'])
        response = self.client.get(f'{url}?billable=true', **self.header)
        self.assertEqual([item['name'] for item in response.data['results']], ['Valued'])

    def test_billable_writable_and_values_read_only(self):
        url = self._get_detail_url(self.contract)
        response = self.client.patch(
            url, {'billable': False, 'total_contract_value': '1', 'yearly_contract_value': '1'}, format='json',
            **self.header,
        )
        self.assertHttpStatus(response, status.HTTP_200_OK)
        self.contract.refresh_from_db()
        self.assertFalse(self.contract.billable)
        self.assertEqual(Decimal(response.data['total_contract_value']), Decimal('1700.00'))

    def test_billable_locked_once_invoiced(self):
        make_invoice(self.contract, amount=100)
        response = self.client.patch(
            self._get_detail_url(self.contract), {'billable': False}, format='json', **self.header
        )
        self.assertHttpStatus(response, status.HTTP_400_BAD_REQUEST)
        self.assertIn('billable', response.data)


#
# Complete API test cases (REST and GraphQL) of the other models (#309 T046)
#

DRAFT = InvoiceStatusChoices.STATUS_DRAFT


class ContractTypeAPIViewTestCase(APITestCase, APIViewTestCases.APIViewTestCase):
    model = ContractType
    brief_fields = ['description', 'display', 'id', 'name', 'slug', 'url']
    create_data = [
        {'name': 'Type 4', 'description': 'Fourth', 'color': ColorChoices.COLOR_GREEN},
        {'name': 'Type 5', 'color': ColorChoices.COLOR_RED},
        {'name': 'Type 6'},
    ]
    bulk_update_data = {'description': 'Updated'}

    @classmethod
    def setUpTestData(cls):
        ContractType.objects.create(name='Type 1', description='First', color=ColorChoices.COLOR_BLUE)
        ContractType.objects.create(name='Type 2', description='Second', color=ColorChoices.COLOR_RED)
        ContractType.objects.create(name='Type 3', description='Third', color=ColorChoices.COLOR_GREEN)


class ServiceProviderAPIViewTestCase(APITestCase, APIViewTestCases.APIViewTestCase):
    model = ServiceProvider
    brief_fields = ['description', 'display', 'id', 'name', 'slug', 'url']
    create_data = [
        {'name': 'Provider 4', 'slug': 'provider-4'},
        {'name': 'Provider 5', 'slug': 'provider-5', 'portal_url': 'https://five.example'},
        {'name': 'Provider 6', 'slug': 'provider-6', 'comments': 'Sixth'},
    ]
    bulk_update_data = {'comments': 'Updated'}

    @classmethod
    def setUpTestData(cls):
        ServiceProvider.objects.create(name='Provider 1', slug='provider-1', portal_url='https://one.example')
        ServiceProvider.objects.create(name='Provider 2', slug='provider-2')
        ServiceProvider.objects.create(name='Provider 3', slug='provider-3', comments='Third')


class AccountingDimensionAPIViewTestCase(APITestCase, APIViewTestCases.APIViewTestCase):
    model = AccountingDimension
    brief_fields = ['display', 'id', 'name', 'url', 'value']
    create_data = [
        {'name': 'account', 'value': 'A4', 'status': StatusChoices.STATUS_ACTIVE},
        {'name': 'account', 'value': 'A5'},
        {'name': 'department', 'value': 'D1', 'comments': 'Department'},
    ]
    bulk_update_data = {'comments': 'Updated'}

    @classmethod
    def setUpTestData(cls):
        AccountingDimension.objects.create(name='account', value='A1')
        AccountingDimension.objects.create(name='account', value='A2', comments='Second')
        AccountingDimension.objects.create(name='cost center', value='CC1')


class ContractAPIViewTestCase(APITestCase, APIViewTestCases.APIViewTestCase):
    model = Contract
    # Written as "app_label.model", stored as a content type
    validation_excluded_fields = ['external_party_object_type']
    brief_fields = [
        'billable', 'comments', 'contract_type', 'currency', 'display', 'end_date', 'external_party_object',
        'external_party_object_id', 'external_party_object_type', 'external_reference', 'id', 'initial_term',
        'internal_party', 'invoice_frequency', 'mrc', 'name', 'nrc', 'parent', 'renewal_term', 'start_date',
        'status', 'tenant', 'url', 'yrc',
    ]
    bulk_update_data = {'comments': 'Updated'}

    @classmethod
    def setUpTestData(cls):
        provider = Provider.objects.create(name='Provider A', slug='provider-a')
        contract_type = ContractType.objects.create(name='Maintenance')
        make_contract(name='Contract 1', contract_type=contract_type, external_reference='EXT-1')
        make_contract(name='Contract 2', external_reference='EXT-2')
        make_contract(name='Contract 3', end_date=date(2026, 6, 30))
        common = {
            'external_party_object_type': 'circuits.provider',
            'external_party_object_id': provider.pk,
            'internal_party': 'default',
            'status': StatusChoices.STATUS_ACTIVE,
            'currency': 'usd',
            'invoice_frequency': 1,
            'start_date': date(2025, 1, 1),
            'end_date': date(2025, 12, 31),
        }
        cls.create_data = [
            dict(common, name='Contract 4', contract_type=contract_type.pk),
            dict(common, name='Contract 5', external_reference='EXT-5'),
            dict(common, name='Contract 6', billable=False),
        ]


class InvoiceAPIViewTestCase(APITestCase, APIViewTestCases.APIViewTestCase):
    model = Invoice
    brief_fields = [
        'amount', 'comments', 'contracts', 'currency', 'date', 'display', 'id', 'number', 'period_end',
        'period_start', 'template', 'url',
    ]
    bulk_update_data = {'comments': 'Updated'}

    @classmethod
    def setUpTestData(cls):
        contract = make_contract(name='Invoiced contract')
        for month in (1, 2, 3):
            make_invoice(contract, number=f'INV-{month}', amount=100, status=DRAFT, date=date(2025, month, 25),
                         period_start=date(2025, month, 1), period_end=date(2025, month, 28))
        # Contracts without lines: a new invoice generates no line
        cls.create_data = [
            {
                'number': f'INV-{month}', 'contracts': [make_contract(name=f'New contract {month}').pk],
                'date': date(2025, month, 25), 'period_start': date(2025, month, 1),
                'period_end': date(2025, month, 28), 'currency': 'usd', 'amount': Decimal('0.00'),
            }
            for month in (4, 5, 6)
        ]


class InvoiceLineAPIViewTestCase(APITestCase, APIViewTestCases.APIViewTestCase):
    model = InvoiceLine
    brief_fields = ['accounting_dimensions', 'amount', 'currency', 'display', 'id', 'invoice', 'url']
    bulk_update_data = {'comments': 'Updated'}

    @classmethod
    def setUpTestData(cls):
        contract = make_contract(name='Invoiced contract')
        line = make_line(contract, monthly(), 10)
        invoice = make_invoice(contract, number='INV-1', amount=1000, status=DRAFT)
        for quantity in (1, 2, 3):
            InvoiceLine.objects.create(invoice=invoice, contract_line=line, quantity=quantity, unit_price=10,
                                       currency='usd')
        dimension = AccountingDimension.objects.create(name='account', value='A1')
        cls.create_data = [
            {'invoice': invoice.pk, 'contract_line': line.pk, 'quantity': 4},
            {'invoice': invoice.pk, 'amount': 15, 'currency': 'usd'},
            {'invoice': invoice.pk, 'unit_price': 7, 'quantity': 2, 'currency': 'usd',
             'accounting_dimensions': [dimension.pk]},
        ]


class ContractAssignmentAPIViewTestCase(APITestCase, APIViewTestCases.APIViewTestCase):
    model = ContractAssignment
    brief_fields = ['content_object', 'contract', 'custom_fields', 'display', 'id', 'tags', 'url']
    # Written as "app_label.model", stored as a content type
    validation_excluded_fields = ['content_type']

    @classmethod
    def setUpTestData(cls):
        contract = make_contract(name='Assigned contract')
        site_type = ContentType.objects.get_for_model(Site)
        sites = [Site.objects.create(name=f'Site {i}', slug=f'site-{i}') for i in range(1, 7)]
        for site in sites[:3]:
            ContractAssignment.objects.create(content_type=site_type, object_id=site.pk, contract=contract)
        cls.create_data = [
            {'content_type': 'dcim.site', 'object_id': site.pk, 'contract': contract.pk} for site in sites[3:]
        ]
        cls.bulk_update_data = {'contract': make_contract(name='Other contract').pk}
