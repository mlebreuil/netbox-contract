"""Issue #309, user story 4: the GraphQL API (spec 003, research D8, contracts/graphql.md)."""

from dcim.models import Site
from django.contrib.contenttypes.models import ContentType
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from tenancy.models import Tenant

from netbox_contract.models import (
    Contract,
    ContractAssignment,
    ContractType,
    InvoiceStatusChoices,
    ServiceProvider,
    StatusChoices,
)
from netbox_contract.tests.custom import APITestCase
from netbox_contract.tests.helpers import add_constrained_permission, make_contract, make_invoice, make_line, monthly

DRAFT = InvoiceStatusChoices.STATUS_DRAFT


class GraphQLTestCase(APITestCase):
    model = Contract

    def setUp(self):
        super().setUp()
        self.contract_type = ContractType.objects.create(name='Maintenance')
        self.parent = make_contract(name='Parent')
        self.contract = make_contract(name='Active', contract_type=self.contract_type, parent=self.parent)
        self.cancelled = make_contract(name='Cancelled')
        Contract.objects.filter(pk=self.cancelled.pk).update(status=StatusChoices.STATUS_CANCELED)
        self.child = make_contract(name='Child', parent=self.contract, billable=False)
        self.line = make_line(self.contract, monthly(), 100, description='Monthly fee')
        self.invoice = make_invoice(self.contract, number='INV-1', amount=100, status=DRAFT)
        self.site = Site.objects.create(name='Site 1', slug='site-1')
        self.assignment = ContractAssignment.objects.create(
            content_type=ContentType.objects.get_for_model(Site), object_id=self.site.pk, contract=self.contract
        )

    def query(self, query):
        response = self.client.post(reverse('graphql'), data={'query': query}, format='json', **self.header)
        self.assertEqual(response.status_code, 200, response.content)
        return response.json()

    def data(self, query):
        result = self.query(query)
        self.assertNotIn('errors', result, result.get('errors'))
        return result['data']

    def superuser(self):
        self.user.is_superuser = True
        self.user.save()


class QueryTestCase(GraphQLTestCase):
    def test_filtered_contract_list_with_relations(self):
        """US4-1: a filtered list with the contract's relations."""
        self.superuser()
        data = self.data('''{
            contract_list(filters: {status: {exact: STATUS_ACTIVE}, name: {exact: "Active"}}) {
                name contract_type { name } lines { description } invoices { number }
                assignments { id } parent { name } childs { name }
            }
        }''')
        self.assertEqual(data['contract_list'], [{
            'name': 'Active', 'contract_type': {'name': 'Maintenance'}, 'lines': [{'description': 'Monthly fee'}],
            'invoices': [{'number': 'INV-1'}], 'assignments': [{'id': str(self.assignment.pk)}],
            'parent': {'name': 'Parent'}, 'childs': [{'name': 'Child'}],
        }])
        names = {c['name'] for c in self.data('{ contract_list(filters: {status: {exact: STATUS_ACTIVE}}) { name } }')
                 ['contract_list']}
        self.assertNotIn('Cancelled', names)

    def test_permissions(self):
        """US4-3: results are restricted to what the user may view, constraints included."""
        self.add_permissions('netbox_contract.view_contract')
        self.assertEqual(self.data('{ invoice_list { number } }')['invoice_list'], [])
        add_constrained_permission(self.user, 'netbox_contract.view_contractline', {'contract': self.parent.pk})
        self.assertEqual(self.data('{ contract_line_list { description } }')['contract_line_list'], [])
        add_constrained_permission(self.user, 'netbox_contract.view_contractline', {'contract': self.contract.pk})
        self.assertEqual(
            self.data('{ contract_line_list { description } }')['contract_line_list'], [{'description': 'Monthly fee'}]
        )

    def test_generic_relations(self):
        """US4-4: the external party and the assigned object are returned with their type."""
        self.superuser()
        provider = ServiceProvider.objects.create(name='Telco', slug='telco')
        Contract.objects.filter(pk=self.cancelled.pk).update(
            external_party_object_type=ContentType.objects.get_for_model(ServiceProvider),
            external_party_object_id=provider.pk,
        )
        data = self.data('''{
            contract_list {
                name
                external_party_object {
                    __typename
                    ... on ServiceProviderType { name }
                    ... on ProviderType { name }
                }
            }
            contract_assignment_list { content_object { __typename ... on SiteType { name } } }
        }''')
        parties = {c['name']: c['external_party_object'] for c in data['contract_list']}
        self.assertEqual(parties['Cancelled'], {'__typename': 'ServiceProviderType', 'name': 'Telco'})
        self.assertEqual(parties['Active'], {'__typename': 'ProviderType', 'name': 'Provider A'})
        self.assertEqual(data['contract_assignment_list'], [{'content_object': {'__typename': 'SiteType',
                                                                                'name': 'Site 1'}}])

    def test_assigned_object_outside_the_union(self):
        """contracts/graphql.md: a model outside the union resolves to null; content_type and object_id remain."""
        self.superuser()
        tenant = Tenant.objects.create(name='Tenant A', slug='tenant-a')
        assignment = ContractAssignment.objects.create(
            content_type=ContentType.objects.get_for_model(Tenant), object_id=tenant.pk, contract=self.contract
        )
        data = self.data(f'''{{
            contract_assignment(id: {assignment.pk}) {{
                object_id content_type {{ app_label model }} content_object {{ __typename }}
            }}
        }}''')
        self.assertEqual(data['contract_assignment'], {
            'object_id': tenant.pk, 'content_type': {'app_label': 'tenancy', 'model': 'tenant'},
            'content_object': None,
        })

    def test_deprecated_fields(self):
        """US4-5: deprecated fields are present and marked deprecated."""
        self.superuser()
        for type_name, fields in (('ContractType', {'mrc', 'yrc', 'nrc'}), ('InvoiceType', {'template'})):
            data = self.data(f'{{ __type(name: "{type_name}") {{ fields(includeDeprecated: true) '
                             f'{{ name isDeprecated }} }} }}')
            deprecated = {f['name'] for f in data['__type']['fields'] if f['isDeprecated']}
            with self.subTest(type=type_name):
                self.assertEqual(deprecated, fields)

    def test_computed_values_not_exposed(self):
        """FR-015a, edge case: computed values are REST only."""
        self.superuser()
        result = self.query('{ contract_list { yearly_contract_value } }')
        self.assertIn('errors', result)

    def test_generic_relations_query_count(self):
        """Plan performance goal: no query per object for the generic relations."""
        self.superuser()

        def count():
            with CaptureQueriesContext(connection) as queries:
                self.data('''{
                    contract_list { external_party_object { __typename } }
                    contract_assignment_list { content_object { __typename } }
                }''')
            return len(queries)

        count()  # the first request also records the token's use
        before = count()
        for i in range(8):
            contract = make_contract(name=f'More {i}')
            site = Site.objects.create(name=f'More site {i}', slug=f'more-site-{i}')
            ContractAssignment.objects.create(
                content_type=ContentType.objects.get_for_model(Site), object_id=site.pk, contract=contract
            )
        self.assertEqual(count(), before)
