"""Fixes of issue #307: contracts tab permission, API filters, OpenAPI schema, invoice line pre-fill, Amend button."""

from dcim.models import Site
from django.contrib.contenttypes.models import ContentType
from django.urls import include, path, reverse
from drf_spectacular.generators import SchemaGenerator
from rest_framework import status
from utilities.testing import TestCase

from netbox_contract.api import urls as api_urls
from netbox_contract.models import (
    AccountingDimension,
    ContractAssignment,
    ContractType,
    InvoiceStatusChoices,
    ServiceProvider,
)
from netbox_contract.tests.custom import APITestCase
from netbox_contract.tests.helpers import make_contract, make_invoice, make_line, monthly


class ContractsTabPermissionTestCase(TestCase):
    """The Contracts tab of an assigned object is shown to users allowed to view contract assignments."""

    def setUp(self):
        super().setUp()
        self.site = Site.objects.create(name='Site 1', slug='site-1')
        ContractAssignment.objects.create(
            content_type=ContentType.objects.get_for_model(Site), object_id=self.site.pk, contract=make_contract()
        )
        self.tab_url = reverse('dcim:site_contracts', kwargs={'pk': self.site.pk})

    def test_tab_shown_with_the_view_permission(self):
        self.add_permissions('dcim.view_site', 'netbox_contract.view_contractassignment')
        response = self.client.get(self.site.get_absolute_url())
        self.assertContains(response, self.tab_url)

    def test_tab_hidden_without_the_view_permission(self):
        self.add_permissions('dcim.view_site')
        response = self.client.get(self.site.get_absolute_url())
        self.assertNotContains(response, self.tab_url)


class APIFiltersTestCase(APITestCase):
    """The service provider, contract type, accounting dimension and contract assignment endpoints filter."""

    model = ServiceProvider

    def get_list(self, model, query):
        self.add_permissions(f'netbox_contract.view_{model._meta.model_name}')
        url = reverse(f'plugins-api:netbox_contract-api:{model._meta.model_name}-list')
        response = self.client.get(f'{url}?{query}', **self.header)
        self.assertHttpStatus(response, status.HTTP_200_OK)
        return [item['id'] for item in response.data['results']]

    def test_service_providers(self):
        wanted = ServiceProvider.objects.create(name='Alpha', slug='alpha')
        ServiceProvider.objects.create(name='Beta', slug='beta')
        self.assertEqual(self.get_list(ServiceProvider, 'name=Alpha'), [wanted.pk])
        self.assertEqual(self.get_list(ServiceProvider, 'q=alp'), [wanted.pk])

    def test_contract_types(self):
        wanted = ContractType.objects.create(name='Support')
        ContractType.objects.create(name='Licence')
        self.assertEqual(self.get_list(ContractType, 'name=Support'), [wanted.pk])

    def test_accounting_dimensions(self):
        wanted = AccountingDimension.objects.create(name='Department', value='IT')
        AccountingDimension.objects.create(name='Department', value='HR')
        self.assertEqual(self.get_list(AccountingDimension, 'value=IT'), [wanted.pk])

    def test_contract_assignments(self):
        site_type = ContentType.objects.get_for_model(Site)
        site = Site.objects.create(name='Site 1', slug='site-1')
        contract = make_contract(name='Wanted')
        wanted = ContractAssignment.objects.create(content_type=site_type, object_id=site.pk, contract=contract)
        ContractAssignment.objects.create(content_type=site_type, object_id=site.pk, contract=make_contract('Other'))
        self.assertEqual(self.get_list(ContractAssignment, f'contract={contract.pk}'), [wanted.pk])


class OpenAPISchemaTestCase(TestCase):
    """The generic related objects are documented as objects, not as strings."""

    @classmethod
    def setUpTestData(cls):
        patterns = [path('api/plugins/contracts/', include((api_urls.urlpatterns, 'netbox_contract-api')))]
        cls.schemas = SchemaGenerator(patterns=patterns).get_schema(request=None, public=True)['components']['schemas']

    def assertIsObject(self, schema, field):
        self.assertEqual(self.schemas[schema]['properties'][field].get('type'), 'object', f'{schema}.{field}')

    def test_contract_external_party_object(self):
        self.assertIsObject('Contract', 'external_party_object')

    def test_nested_contract_external_party_object(self):
        self.assertIsObject('NestedContract', 'external_party_object')

    def test_contract_assignment_content_object(self):
        self.assertIsObject('ContractAssignment', 'content_object')


class InvoiceLinePrefillTestCase(TestCase):
    """The invoice line add form is pre-filled from an invoice the user may view only."""

    def setUp(self):
        super().setUp()
        contract = make_contract(currency='eur')
        self.invoice = make_invoice(contract, status=InvoiceStatusChoices.STATUS_DRAFT, amount=250)
        self.url = reverse('plugins:netbox_contract:invoiceline_add')
        self.add_permissions('netbox_contract.add_invoiceline')

    def initial(self, invoice):
        response = self.client.get(f'{self.url}?invoice={invoice}')
        self.assertEqual(response.status_code, 200)
        return response.context['form'].initial

    def test_prefilled_from_a_visible_invoice(self):
        self.add_permissions('netbox_contract.view_invoice')
        initial = self.initial(self.invoice.pk)
        self.assertEqual(initial['unit_price'], 250)
        self.assertEqual(initial['currency'], 'eur')

    def test_not_prefilled_from_an_invoice_the_user_cannot_view(self):
        initial = self.initial(self.invoice.pk)
        self.assertIsNone(initial['unit_price'])
        self.assertNotEqual(initial['currency'], 'eur')

    def test_unknown_or_invalid_invoice(self):
        self.add_permissions('netbox_contract.view_invoice')
        for value in (self.invoice.pk + 1000, 'abc', ''):
            with self.subTest(value=value):
                self.assertIsNone(self.initial(value)['unit_price'])


class AmendButtonPermissionTestCase(TestCase):
    """
    The Amend button is shown only to users allowed to amend, as the amend view requires. #307 required add + change;
    #309 replaced them with the amend action (tests/test_amend_permission.py covers the full rule).
    """

    def setUp(self):
        super().setUp()
        self.contract = make_contract()
        self.line = make_line(self.contract, monthly(), 100)
        make_invoice(self.contract, number='JAN', amount=100)
        self.amend_url = reverse('plugins:netbox_contract:contractline_amend', args=[self.line.pk])
        self.add_permissions(
            'netbox_contract.view_contract', 'netbox_contract.view_contractline', 'netbox_contract.change_contractline'
        )

    def pages(self):
        return {
            'line': self.line.get_absolute_url(),
            'line edit': reverse('plugins:netbox_contract:contractline_edit', args=[self.line.pk]),
            'contract': self.contract.get_absolute_url(),
        }

    def test_hidden_without_the_add_permission(self):
        self.assertEqual(self.client.get(self.amend_url).status_code, 403)
        for page, url in self.pages().items():
            with self.subTest(page=page):
                self.assertNotContains(self.client.get(url), self.amend_url)

    def test_shown_with_the_change_and_add_permissions(self):
        """Since #309: shown with the amend action, which add + change no longer replace."""
        self.add_permissions('netbox_contract.add_contractline')
        self.assertEqual(self.client.get(self.amend_url).status_code, 403)
        self.add_permissions('netbox_contract.amend_contractline')
        self.assertEqual(self.client.get(self.amend_url).status_code, 200)
        for page, url in self.pages().items():
            with self.subTest(page=page):
                self.assertContains(self.client.get(url), self.amend_url)
