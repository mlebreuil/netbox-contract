"""
Issue #309, user story 3: nested objects and brief representations in the REST API (spec 003, research D7,
contracts/rest-api.md). 2.5.0 removes no REST field; the fields a later release will remove are announced.
"""

import re
from pathlib import Path
from unittest import SkipTest

from dcim.models import Site
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.urls import include, path, reverse
from drf_spectacular.generators import SchemaGenerator
from rest_framework import status

from netbox_contract.api import serializers
from netbox_contract.api import urls as api_urls
from netbox_contract.models import (
    AccountingDimension,
    ContractAssignment,
    ContractLine,
    ContractType,
    InvoiceStatusChoices,
    ServiceProvider,
)
from netbox_contract.tests.custom import APITestCase
from netbox_contract.tests.helpers import make_contract, make_invoice, make_invoice_line, make_line, monthly

DRAFT = InvoiceStatusChoices.STATUS_DRAFT


def repository_file(*parts):
    """
    A file of the plugin repository: next to the package in an editable install (development), or in the checkout
    beside NetBox's when the package is installed in site-packages (CI runs from NetBox's directory).
    """
    for root in (Path(__file__).resolve().parents[2], Path.cwd().parent / 'netbox-contract', Path.cwd()):
        candidate = root.joinpath(*parts)
        if candidate.is_file():
            return candidate
    raise SkipTest(f'{"/".join(parts)} is not available next to this installation')


# Today's nested contract (assignments, contract lines, contract parent): kept unchanged in 2.5.0 (FR-009)
NESTED_CONTRACT = {
    'id', 'url', 'display', 'name', 'contract_type', 'external_party_object_type', 'external_party_object_id',
    'external_party_object', 'external_reference', 'internal_party', 'tenant', 'status', 'start_date', 'end_date',
    'initial_term', 'renewal_term', 'notice_period', 'currency', 'mrc', 'yrc', 'nrc', 'invoice_frequency',
    'comments', 'documents',
}
# Today's contracts of an invoice: the full contract
FULL_CONTRACT = {
    'id', 'url', 'display', 'name', 'contract_type', 'external_party_object_type', 'external_party_object_id',
    'external_party_object', 'external_reference', 'internal_party', 'tenant', 'status', 'start_date', 'end_date',
    'initial_term', 'renewal_term', 'notice_period', 'currency', 'mrc', 'yrc', 'nrc', 'invoice_frequency',
    'billable', 'total_contract_value', 'yearly_contract_value', 'yearly_billable_value', 'comments', 'documents',
    'parent', 'tags', 'custom_fields', 'created', 'last_updated',
}
NESTED_INVOICE = {'id', 'url', 'display', 'number'}
NESTED_DIMENSION = {'id', 'url', 'display', 'name', 'value'}
BRIEF_CONTRACT_LINE = {
    'id', 'url', 'display', 'contract', 'description', 'quantity', 'unit', 'unit_price', 'currency', 'start_date',
    'end_date',
}

# "Brief fields in 2.5.0" of contracts/rest-api.md
BRIEF_FIELDS = {
    'contracts': {
        'id', 'url', 'display', 'name', 'contract_type', 'external_party_object_type', 'external_party_object_id',
        'external_party_object', 'external_reference', 'internal_party', 'tenant', 'status', 'start_date', 'end_date',
        'initial_term', 'renewal_term', 'currency', 'mrc', 'yrc', 'nrc', 'invoice_frequency', 'billable', 'comments',
        'parent',
    },
    'invoices': {
        'id', 'url', 'display', 'number', 'date', 'template', 'contracts', 'period_start', 'period_end', 'currency',
        'amount', 'comments',
    },
    'invoiceline': {'id', 'url', 'display', 'invoice', 'accounting_dimensions', 'amount', 'currency'},
    'contract-lines': BRIEF_CONTRACT_LINE,
    'accountingdimension': NESTED_DIMENSION,
    'units': {'id', 'url', 'display', 'name', 'description', 'billing_method', 'months'},
    'contracttype': {'id', 'url', 'display', 'name', 'slug', 'description'},
    'serviceproviders': {'id', 'url', 'display', 'name', 'slug', 'description'},
    'contractassignment': {'id', 'url', 'display', 'content_object', 'contract', 'tags', 'custom_fields'},
}

# "Deprecations announced in 2.5.0" of contracts/rest-api.md (FR-012a)
DEPRECATED_NESTED_CONTRACT = NESTED_CONTRACT - {'id', 'url', 'display', 'name', 'status'}
DEPRECATED_INVOICE_CONTRACTS = FULL_CONTRACT - {'id', 'url', 'display', 'name', 'status'}
DEPRECATED_BRIEF = BRIEF_FIELDS['contracts'] - {'id', 'url', 'display', 'name', 'status'}
DEPRECATED_INVOICE_BRIEF = BRIEF_FIELDS['invoices'] - NESTED_INVOICE


class NestedAPITestCase(APITestCase):
    model = ContractLine

    def setUp(self):
        super().setUp()
        self.user.is_superuser = True
        self.user.save()
        self.contract_type = ContractType.objects.create(name='Maintenance')
        self.parent = make_contract(name='Parent')
        self.contract = make_contract(name='C-1', contract_type=self.contract_type, parent=self.parent)
        self.dimension = AccountingDimension.objects.create(name='Cost center', value='CC1')
        self.line = make_line(self.contract, monthly(), 100, description='Old terms')
        self.line.accounting_dimensions.add(self.dimension)
        self.successor = make_line(self.contract, monthly(), 110, description='New terms', replaces=self.line)
        self.invoice = make_invoice(self.contract, number='INV-1', amount=100, status=DRAFT)
        self.invoice_line = make_invoice_line(self.invoice, contract_line=self.line, quantity=1)
        self.invoice_line.accounting_dimensions.add(self.dimension)
        self.site = Site.objects.create(name='Site 1', slug='site-1')
        self.assignment = ContractAssignment.objects.create(
            content_type=ContentType.objects.get_for_model(Site), object_id=self.site.pk, contract=self.contract
        )

    def get(self, endpoint, pk=None, **params):
        name = f'plugins-api:netbox_contract-api:{endpoint}-{"detail" if pk else "list"}'
        url = reverse(name, args=[pk] if pk else [])
        response = self.client.get(url, params, **self.header)
        self.assertHttpStatus(response, status.HTTP_200_OK)
        return response.json()


class NestedSnapshotTestCase(NestedAPITestCase):
    """T035 (guard): the nested objects clients read today keep their keys and value types (US3-1 to US3-3)."""

    def test_nested_contract(self):
        for endpoint, pk, field in (
            ('contractassignment', self.assignment.pk, 'contract'),
            ('contractline', self.line.pk, 'contract'),
            ('contract', self.contract.pk, 'parent'),
        ):
            with self.subTest(endpoint=endpoint, field=field):
                nested = self.get(endpoint, pk)[field]
                self.assertEqual(set(nested), NESTED_CONTRACT)
                if field == 'contract':
                    self.assertEqual(nested['contract_type'], self.contract_type.pk)  # an id, not an object

    def test_invoice_contracts(self):
        contracts = self.get('invoice', self.invoice.pk)['contracts']
        self.assertEqual(len(contracts), 1)
        self.assertEqual(set(contracts[0]), FULL_CONTRACT)

    def test_invoice_line_relations(self):
        data = self.get('invoiceline', self.invoice_line.pk)
        self.assertEqual(set(data['invoice']), NESTED_INVOICE)
        self.assertEqual(set(data['accounting_dimensions'][0]), NESTED_DIMENSION)
        self.assertEqual(set(self.get('contractline', self.line.pk)['accounting_dimensions'][0]), NESTED_DIMENSION)


class ReplacesTestCase(NestedAPITestCase):
    """T036: `replaces` is the brief contract line (US3-3)."""

    def test_replaces(self):
        replaces = self.get('contractline', self.successor.pk)['replaces']
        self.assertEqual(set(replaces), BRIEF_CONTRACT_LINE)
        self.assertEqual(replaces['id'], self.line.pk)


class NestedWriteTestCase(NestedAPITestCase):
    """T037 (guard): related objects are written by id or by attributes, as before (US3-4)."""

    def post(self, name, data):
        url = reverse(f'plugins-api:netbox_contract-api:{name}-list')
        return self.client.post(url, data, format='json', **self.header)

    def test_contract_by_id_and_by_attributes(self):
        other = make_contract(name='Open contract')
        for value in (other.pk, {'name': 'Open contract'}):
            with self.subTest(value=value):
                response = self.post('contractline', {
                    'contract': value, 'description': 'Support', 'unit': monthly().pk, 'unit_price': '5',
                })
                self.assertHttpStatus(response, status.HTTP_201_CREATED)
                self.assertEqual(response.data['contract']['id'], other.pk)
        site = Site.objects.create(name='Site 2', slug='site-2')
        response = self.post('contractassignment', {
            'content_type': 'dcim.site', 'object_id': site.pk, 'contract': {'name': 'Open contract'},
        })
        self.assertHttpStatus(response, status.HTTP_201_CREATED)

    def test_invoice_by_id(self):
        invoice = make_invoice(self.parent, number='INV-2', amount=10, status=DRAFT)
        response = self.post('invoiceline', {'invoice': invoice.pk, 'amount': '3', 'currency': 'usd'})
        self.assertHttpStatus(response, status.HTTP_201_CREATED)
        self.assertEqual(response.data['invoice']['id'], invoice.pk)

    def test_unknown_or_ambiguous_attributes(self):
        make_contract(name='Twin')
        make_contract(name='Twin', external_reference='second')
        for value in ({'name': 'Nothing'}, {'name': 'Twin'}):
            with self.subTest(value=value):
                response = self.post('contractline', {
                    'contract': value, 'description': 'Support', 'unit': monthly().pk, 'unit_price': '5',
                })
                self.assertHttpStatus(response, status.HTTP_400_BAD_REQUEST)


class BriefTestCase(NestedAPITestCase):
    """T038: brief=true returns the 2.5.0 brief sets, which only add fields (US3-5)."""

    def setUp(self):
        super().setUp()
        ServiceProvider.objects.create(name='Telco', slug='telco')

    def test_brief_sets(self):
        for endpoint, expected in BRIEF_FIELDS.items():
            name = {'contracts': 'contract', 'invoices': 'invoice', 'contract-lines': 'contractline',
                    'units': 'unit', 'serviceproviders': 'serviceprovider'}.get(endpoint, endpoint)
            with self.subTest(endpoint=endpoint):
                results = self.get(name, brief='true')['results']
                self.assertTrue(results)
                self.assertEqual(set(results[0]), expected)

    def test_declared_brief_fields_exist(self):
        for serializer in (
            serializers.ContractSerializer, serializers.InvoiceSerializer, serializers.InvoiceLineSerializer,
            serializers.ContractLineSerializer, serializers.AccountingDimensionSerializer,
            serializers.UnitSerializer, serializers.ContractTypeSerializer, serializers.ServiceProviderSerializer,
            serializers.ContractAssignmentSerializer,
        ):
            with self.subTest(serializer=serializer.__name__):
                declared = set(serializer.Meta.brief_fields)
                self.assertLessEqual(declared, set(serializer.Meta.fields))


class SchemaTestCase(APITestCase):
    """T039: OpenAPI components of the nested objects (US3-6)."""

    model = ContractLine

    @classmethod
    def setUpTestData(cls):
        patterns = [path('api/plugins/contracts/', include((api_urls.urlpatterns, 'netbox_contract-api')))]
        cls.schemas = SchemaGenerator(patterns=patterns).get_schema(request=None, public=True)['components']['schemas']

    def properties(self, name):
        return set(self.schemas[name]['properties'])

    def test_brief_components(self):
        self.assertEqual(self.properties('BriefInvoice'), NESTED_INVOICE)
        self.assertEqual(self.properties('BriefContractLine'), BRIEF_CONTRACT_LINE)
        # The accounting dimension lists are SerializedPKRelatedField(nested=True): NetBox 4.6.10 (the CI pin)
        # documents them with the brief component (netbox#22989); earlier 4.6 releases used the model's component.
        # The response holds the brief accounting dimension either way (NestedSnapshotTestCase).
        if tuple(int(part) for part in settings.RELEASE.version.split('.')[:3]) >= (4, 6, 10):
            component = 'BriefAccountingDimension'
            self.assertEqual(self.properties(component), NESTED_DIMENSION)
        else:
            component = 'AccountingDimension'
        for schema in ('ContractLine', 'InvoiceLine'):
            items = self.schemas[schema]['properties']['accounting_dimensions']['items']
            self.assertEqual(items['$ref'], f'#/components/schemas/{component}')
        for gone in ('NestedInvoice', 'NestedAccountingDimension', 'NestedContractLine'):
            self.assertNotIn(gone, self.schemas)

    def test_nested_contract_kept_and_deprecated(self):
        self.assertEqual(self.properties('NestedContract'), NESTED_CONTRACT)
        for field in DEPRECATED_NESTED_CONTRACT:
            with self.subTest(field=field):
                self.assertIn('Deprecated', self.schemas['NestedContract']['properties'][field].get('description', ''))

    def test_generic_objects(self):
        self.assertEqual(self.schemas['Contract']['properties']['external_party_object'].get('type'), 'object')
        self.assertEqual(
            self.schemas['ContractAssignment']['properties']['content_object'].get('type'), 'object'
        )


class DeprecationNoticeTestCase(APITestCase):
    """T040: every field to be removed later is announced in the changelog and the API docs (US3-7, FR-012a)."""

    model = ContractLine

    def notice(self, text, start, end):
        match = re.search(f'{start}(.*?)(?:{end})', text, re.S)
        self.assertIsNotNone(match, start)
        return match.group(1)

    def test_changelog(self):
        # The changelog follows the NetBox release notes: the #309 item of the 2.5.0 "Deprecations" section
        changelog = repository_file('CHANGELOG.md').read_text()
        release = self.notice(changelog, r'\n### Version 2\.5\.0\n', r'\n### ')
        section = self.notice(release, r'\n#### Deprecations\n', r'\n#### ')
        deprecations = self.notice(section, r'\n\* \[#309\]', r'\n\* \[#|\Z')
        for field in DEPRECATED_NESTED_CONTRACT | DEPRECATED_INVOICE_CONTRACTS | DEPRECATED_BRIEF \
                | DEPRECATED_INVOICE_BRIEF:
            with self.subTest(field=field):
                self.assertIn(f'`{field}`', deprecations)

    def test_api_docs(self):
        docs = repository_file('docs', 'api.md').read_text()
        section = self.notice(docs, r'## Deprecated nested fields', r'\n## |\Z')
        for field in DEPRECATED_NESTED_CONTRACT | DEPRECATED_INVOICE_CONTRACTS | DEPRECATED_BRIEF \
                | DEPRECATED_INVOICE_BRIEF:
            with self.subTest(field=field):
                self.assertIn(f'`{field}`', section)
