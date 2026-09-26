"""REST API of the contract lines feature (contracts/rest-api.md)."""

from datetime import date
from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from utilities.testing import APIViewTestCases

from netbox_contract.models import AccountingDimension, BillingMethodChoices, Contract, ContractLine, Unit
from netbox_contract.tests.custom import APITestCase
from netbox_contract.tests.helpers import make_contract, make_invoice, make_line, monthly, one_time


class UnitAPITestCase(
    APITestCase,
    APIViewTestCases.GetObjectViewTestCase,
    APIViewTestCases.ListObjectsViewTestCase,
    APIViewTestCases.CreateObjectViewTestCase,
    APIViewTestCases.UpdateObjectViewTestCase,
    APIViewTestCases.DeleteObjectViewTestCase,
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
    APIViewTestCases.GetObjectViewTestCase,
    APIViewTestCases.ListObjectsViewTestCase,
    APIViewTestCases.CreateObjectViewTestCase,
    APIViewTestCases.UpdateObjectViewTestCase,
    APIViewTestCases.DeleteObjectViewTestCase,
):
    model = ContractLine
    brief_fields = ['contract', 'currency', 'description', 'display', 'id', 'quantity', 'unit', 'unit_price', 'url']
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
