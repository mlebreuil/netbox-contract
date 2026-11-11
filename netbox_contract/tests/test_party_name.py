"""Search contracts by external party name (feature 009, issue #333).

The shared condition, the contract quick search, the party-name filter of the list view and the REST API, and the
GraphQL filter. Fixture: two party types, a service provider and a circuit provider that share one primary key,
a contract without party and a contract that is not Active.
"""

from urllib.parse import urlencode

from circuits.models import Provider
from django.contrib.contenttypes.models import ContentType
from django.db import connection
from django.http import QueryDict
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from extras.models import CachedValue
from utilities.testing import TestCase

from netbox_contract.external_party import party_name_condition
from netbox_contract.filtersets import ContractFilterSet
from netbox_contract.forms import ContractFilterForm
from netbox_contract.models import Contract, ServiceProvider, StatusChoices
from netbox_contract.tests.custom import APITestCase
from netbox_contract.tests.helpers import add_constrained_permission, make_line, monthly
from netbox_contract.tests.test_graphql import GraphQLTestCase

CARRIERS = {'Support G', 'Support I', 'Support C', 'Acme framework'}  # parties whose name contains 'carrier'
SHARED_ID = 9_000_001  # a service provider and a circuit provider with the same primary key


def new_contract(name, party, status=StatusChoices.STATUS_ACTIVE):
    return Contract.objects.create(
        name=name,
        external_party_object_type=ContentType.objects.get_for_model(type(party)) if party else None,
        external_party_object_id=party.pk if party else None,
        internal_party='default',
        status=status,
        start_date='2025-01-01',
        end_date='2025-12-31',
        currency='usd',
        invoice_frequency=1,
    )


def build_fixture(test):
    """Create the providers and contracts of the feature (009-T002); names are kept on `test`."""
    test.acme = ServiceProvider.objects.create(pk=SHARED_ID, name='Acme Telecom', slug='acme-telecom')
    test.globex = Provider.objects.create(name='Globex Carrier', slug='globex-carrier')
    test.initech = Provider.objects.create(pk=SHARED_ID, name='Initech Carrier', slug='initech-carrier')
    test.carrier_sp = ServiceProvider.objects.create(name='Carrier Services', slug='carrier-services')
    test.shared_sp = ServiceProvider.objects.create(name='Shared Name', slug='shared-sp')
    test.shared_cp = Provider.objects.create(name='Shared Name', slug='shared-cp')
    new_contract('Support A', test.acme)
    new_contract('Support Old', test.acme, status=StatusChoices.STATUS_CANCELED)
    new_contract('Support G', test.globex)
    new_contract('Support I', test.initech)
    new_contract('Support C', test.carrier_sp)
    new_contract('Shared SP', test.shared_sp)
    new_contract('Shared CP', test.shared_cp)
    new_contract('Acme framework', test.globex)  # its own name contains the text
    new_contract('Orphan', None)


def names(queryset):
    return set(queryset.values_list('name', flat=True))


def fs(**params):
    """A ContractFilterSet on a query string (lists are repeated parameters)."""
    return ContractFilterSet(QueryDict(urlencode(params, doseq=True)), Contract.objects.all())


class ConditionTestCase(TestCase):
    """009-FR-001, 009-FR-002, 009-FR-003, 009-FR-005: the shared condition."""

    def setUp(self):
        super().setUp()
        build_fixture(self)

    def match(self, lookup, *values):
        return names(Contract.objects.filter(party_name_condition(lookup, list(values))))

    def test_contains_both_party_types(self):
        self.assertEqual(self.match('icontains', 'acme'), {'Support A', 'Support Old'})
        self.assertEqual(self.match('icontains', 'carrier'), CARRIERS)

    def test_exact_is_case_sensitive_and_iexact_is_not(self):
        self.assertEqual(self.match('exact', 'Acme Telecom'), {'Support A', 'Support Old'})
        self.assertEqual(self.match('exact', 'acme telecom'), set())
        self.assertEqual(self.match('iexact', 'acme telecom'), {'Support A', 'Support Old'})

    def test_any_of_several_names(self):
        self.assertEqual(self.match('exact', 'Acme Telecom', 'Globex Carrier'),
                         {'Support A', 'Support Old', 'Support G', 'Acme framework'})

    def test_same_primary_key_does_not_cross_party_types(self):
        """009-FR-005: Initech (circuit provider) has the primary key of Acme (service provider)."""
        self.assertEqual(self.acme.pk, self.initech.pk)
        self.assertNotIn('Support I', self.match('icontains', 'acme'))
        self.assertNotIn('Support A', self.match('icontains', 'initech'))
        self.assertEqual(self.match('icontains', 'initech'), {'Support I'})

    def test_same_name_on_both_types(self):
        self.assertEqual(self.match('exact', 'Shared Name'), {'Shared SP', 'Shared CP'})

    def test_contract_without_party_and_deleted_party_never_match(self):
        self.assertNotIn('Orphan', self.match('icontains', ''))
        self.globex.delete()
        self.assertEqual(self.match('icontains', 'globex'), set())
        self.assertEqual(Contract.objects.filter(party_name_condition('icontains', ['globex'])).count(), 0)

    def test_each_contract_once(self):
        queryset = Contract.objects.filter(party_name_condition('icontains', ['a', 'acme', 'telecom']))
        self.assertEqual(queryset.count(), len({c.pk for c in queryset}))


class QuickSearchTestCase(TestCase):
    """009-US1: the contract list quick search."""

    user_permissions = ['netbox_contract.view_contract']

    def setUp(self):
        super().setUp()
        build_fixture(self)

    def search(self, text):
        return names(fs(q=text).qs)

    def test_service_provider_name(self):
        """009-US1-1."""
        self.assertIn('Support A', self.search('acme'))

    def test_circuit_provider_name(self):
        """009-US1-2."""
        self.assertIn('Support G', self.search('globex'))
        self.assertEqual(self.search('carrier'), CARRIERS)

    def test_own_name_and_party_name_both_listed_once(self):
        """009-US1-3."""
        result = fs(q='acme').qs
        self.assertEqual(sorted(result.values_list('name', flat=True)), ['Acme framework', 'Support A'])

    def test_only_active_contracts(self):
        """009-US1-4: 009-FR-004."""
        self.assertNotIn('Support Old', self.search('acme'))

    def test_contract_without_party(self):
        """009-US1-5."""
        self.assertEqual(self.search('orphan'), {'Orphan'})
        self.assertNotIn('Orphan', self.search('acme'))

    def test_upper_case_text(self):
        self.assertEqual(self.search('ACME'), {'Support A', 'Acme framework'})

    def test_several_parties(self):
        self.assertEqual(self.search('carrier'), CARRIERS)

    def test_empty_text_leaves_the_list_unchanged(self):
        self.assertEqual(names(fs(q='').qs), names(Contract.objects.all()))

    def test_renamed_provider_is_found_at_once(self):
        self.acme.name = 'Zenith Telecom'
        self.acme.save()
        self.assertEqual(self.search('zenith'), {'Support A'})
        self.assertEqual(self.search('acme'), {'Acme framework'})

    def test_existing_fields_still_match(self):
        """009-SC-004: name, external reference and comments."""
        Contract.objects.filter(name='Support G').update(external_reference='REF-42', comments='needs renewal')
        self.assertEqual(self.search('ref-42'), {'Support G'})
        self.assertEqual(self.search('renewal'), {'Support G'})
        self.assertEqual(self.search('support g'), {'Support G'})

    def test_list_view_search(self):
        response = self.client.get(reverse('plugins:netbox_contract:contract_list'), {'q': 'globex'})
        self.assertHttpStatus(response, 200)
        self.assertContains(response, 'Support G')
        self.assertNotContains(response, 'Support A')

    def test_query_count_does_not_grow(self):
        """009-SC-003: the same number of queries with 3 and with 30 contracts and providers."""
        url = reverse('plugins:netbox_contract:contract_list')
        self.client.get(url, {'q': 'carrier'})  # warm caches (content types, permissions)
        with CaptureQueriesContext(connection) as few:
            self.client.get(url, {'q': 'carrier'})
        for i in range(30):
            provider = Provider.objects.create(pk=SHARED_ID + 10 + i, name=f'Bulk Carrier {i}', slug=f'bulk-{i}')
            new_contract(f'Bulk {i}', provider)
        with CaptureQueriesContext(connection) as many:
            self.client.get(url, {'q': 'carrier'})
        self.assertEqual(len(few), len(many))


class FilterSetTestCase(TestCase):
    """009-US2: the party-name filter on the filterset and the list view."""

    user_permissions = ['netbox_contract.view_contract']

    def setUp(self):
        super().setUp()
        build_fixture(self)

    def names(self, **params):
        return names(fs(**params).qs)

    def test_exact_both_types(self):
        """009-US2-1."""
        self.assertEqual(self.names(external_party_name='Acme Telecom'), {'Support A', 'Support Old'})
        self.assertEqual(self.names(external_party_name='Globex Carrier'), {'Support G', 'Acme framework'})

    def test_exact_is_case_sensitive_ie_and_ic_are_not(self):
        self.assertEqual(self.names(external_party_name='acme telecom'), set())
        self.assertEqual(self.names(external_party_name__ie='acme telecom'), {'Support A', 'Support Old'})
        self.assertEqual(self.names(external_party_name__ic='ACME'), {'Support A', 'Support Old'})

    def test_several_names_any_of(self):
        self.assertEqual(
            self.names(external_party_name=['Acme Telecom', 'Initech Carrier']),
            {'Support A', 'Support Old', 'Support I'},
        )

    def test_contains_matches_several_parties(self):
        self.assertEqual(self.names(external_party_name__ic='carrier'), CARRIERS)

    def test_same_name_on_both_types(self):
        """009-US2-3."""
        self.assertEqual(self.names(external_party_name='Shared Name'), {'Shared SP', 'Shared CP'})

    def test_does_not_restrict_the_status(self):
        """009-US2-4."""
        self.assertIn('Support Old', self.names(external_party_name__ic='acme'))

    def test_negated_filter_keeps_contracts_without_party(self):
        """009-US2-6."""
        result = self.names(external_party_name__n='Acme Telecom')
        self.assertNotIn('Support A', result)
        self.assertNotIn('Support Old', result)
        self.assertIn('Support G', result)
        self.assertIn('Orphan', result)

    def test_empty_value_is_ignored(self):
        self.assertEqual(self.names(external_party_name=''), names(Contract.objects.all()))
        self.assertEqual(self.names(external_party_name__ic=''), names(Contract.objects.all()))

    def test_combines_with_other_filters(self):
        """009-FR-009."""
        self.assertEqual(
            self.names(external_party_name__ic='acme', status=StatusChoices.STATUS_CANCELED), {'Support Old'}
        )
        self.assertEqual(
            self.names(external_party_name__ic='carrier', service_provider_id=self.carrier_sp.pk), {'Support C'}
        )

    def test_id_filters_are_unchanged(self):
        """009-US2-5: 009-FR-010."""
        self.assertEqual(self.names(service_provider_id=self.acme.pk), {'Support A', 'Support Old'})
        self.assertEqual(self.names(provider_id=self.initech.pk), {'Support I'})

    def test_list_view_address(self):
        url = reverse('plugins:netbox_contract:contract_list')
        response = self.client.get(url, {'external_party_name__ic': 'initech'})
        self.assertHttpStatus(response, 200)
        self.assertContains(response, 'Support I')
        self.assertNotContains(response, 'Support A')

    def test_query_count_does_not_grow(self):
        """009-SC-003."""
        url = reverse('plugins:netbox_contract:contract_list')
        params = {'external_party_name__ic': 'carrier'}
        self.client.get(url, params)
        with CaptureQueriesContext(connection) as few:
            self.client.get(url, params)
        for i in range(30):
            provider = Provider.objects.create(pk=SHARED_ID + 10 + i, name=f'Bulk Carrier {i}', slug=f'bulk-{i}')
            new_contract(f'Bulk {i}', provider)
        with CaptureQueriesContext(connection) as many:
            self.client.get(url, params)
        self.assertEqual(len(few), len(many))


class FilterFormTestCase(TestCase):
    """009-FR-006: the filter form."""

    user_permissions = ['netbox_contract.view_contract']

    def test_field_is_in_the_parties_section(self):
        form = ContractFilterForm()
        self.assertIn('external_party_name', form.fields)
        parties = [fieldset for fieldset in form.fieldsets if str(fieldset.name) == 'Parties'][0]
        self.assertIn('external_party_name', parties.items)

    def test_field_is_rendered_and_keeps_its_value(self):
        response = self.client.get(reverse('plugins:netbox_contract:contract_list'), {'external_party_name': 'Acme'})
        self.assertHttpStatus(response, 200)
        self.assertContains(response, 'id_external_party_name')

    def test_modifier_dropdown(self):
        """The lookup modifiers are offered when the `__ic`, `__ie` and `__n` filters exist (009-D2)."""
        widget = ContractFilterForm().fields['external_party_name'].widget
        self.assertTrue(hasattr(widget, 'lookups'), type(widget))


class RestTestCase(APITestCase):
    """009-FR-007: the REST contracts endpoint."""

    model = Contract

    def setUp(self):
        super().setUp()
        build_fixture(self)
        # the REST serializer cannot render a contract without party (existing behaviour, out of scope here)
        Contract.objects.filter(name='Orphan').delete()
        self.add_permissions('netbox_contract.view_contract')

    def names(self, **params):
        response = self.client.get(self._get_list_url(), params, **self.header)
        self.assertHttpStatus(response, 200)
        return {c['name'] for c in response.json()['results']}

    def test_same_contracts_as_the_list_view(self):
        for params in (
            {'external_party_name': 'Acme Telecom'},
            {'external_party_name__ic': 'carrier'},
            {'external_party_name__ie': 'acme telecom'},
            {'external_party_name__n': 'Acme Telecom'},
        ):
            with self.subTest(params=params):
                self.assertEqual(self.names(**params), names(fs(**params).qs))

    def test_fields_are_unchanged(self):
        response = self.client.get(self._get_list_url(), {'external_party_name': 'Acme Telecom'}, **self.header)
        result = response.json()['results'][0]
        self.assertIn('external_party_object', result)
        self.assertNotIn('external_party_name', result)

    def test_object_permission_still_limits_the_result(self):
        self.remove_permissions('netbox_contract.view_contract')
        add_constrained_permission(self.user, 'netbox_contract.view_contract', {'name': 'Support A'})
        self.assertEqual(self.names(external_party_name__ic='acme'), {'Support A'})

    def test_user_without_provider_permission_finds_contracts(self):
        """009-FR-011, 009-D5: the provider names are only used for matching."""
        self.assertEqual(self.names(external_party_name__ic='acme'), {'Support A', 'Support Old'})

    def test_query_count_does_not_grow(self):
        """009-SC-003."""
        self.names(external_party_name__ic='carrier')
        with CaptureQueriesContext(connection) as few:
            self.names(external_party_name__ic='carrier')
        for i in range(30):
            provider = Provider.objects.create(pk=SHARED_ID + 10 + i, name=f'Bulk Carrier {i}', slug=f'bulk-{i}')
            new_contract(f'Bulk {i}', provider)
        with CaptureQueriesContext(connection) as many:
            self.names(external_party_name__ic='carrier')
        self.assertEqual(len(few), len(many))


class GraphQLFilterTestCase(GraphQLTestCase):
    """009-FR-008: the GraphQL contract list filter, for lookups equivalent to the REST ones."""

    def setUp(self):
        super().setUp()
        build_fixture(self)
        self.superuser()

    def names(self, lookup):
        data = self.data('{ contract_list(filters: {external_party_name: {' + lookup + '}}) { name } }')
        return {c['name'] for c in data['contract_list']}

    def test_i_contains_is_the_ic_filter(self):
        self.assertEqual(self.names('i_contains: "carrier"'), names(fs(external_party_name__ic='carrier').qs))
        self.assertEqual(self.names('i_contains: "ACME"'), {'Support A', 'Support Old'})

    def test_exact_is_the_exact_filter(self):
        self.assertEqual(self.names('exact: "Acme Telecom"'), names(fs(external_party_name='Acme Telecom').qs))
        self.assertEqual(self.names('exact: "acme telecom"'), set())

    def test_i_exact_is_the_ie_filter(self):
        self.assertEqual(self.names('i_exact: "acme telecom"'), names(fs(external_party_name__ie='acme telecom').qs))

    def test_other_lookups(self):
        self.assertEqual(self.names('starts_with: "Acme"'), {'Support A', 'Support Old'})
        self.assertEqual(self.names('in_list: ["Acme Telecom", "Initech Carrier"]'),
                         {'Support A', 'Support Old', 'Support I'})

    def test_same_primary_key_does_not_cross_party_types(self):
        self.assertEqual(self.names('i_contains: "initech"'), {'Support I'})

    def test_combines_with_another_filter(self):
        data = self.data(
            '{ contract_list(filters: {external_party_name: {i_contains: "acme"}, name: {exact: "Support A"}}) '
            '{ name } }'
        )
        self.assertEqual([c['name'] for c in data['contract_list']], ['Support A'])

    def test_filter_nested_in_a_contract_line_filter(self):
        """The filter works through a relation (the `prefix` of the filter method)."""
        line = make_line(Contract.objects.get(name='Support A'), monthly(), 100, description='Acme fee')
        make_line(Contract.objects.get(name='Support G'), monthly(), 50, description='Globex fee')
        data = self.data(
            '{ contract_line_list(filters: {contract: {external_party_name: {i_contains: "acme"}}}) { id } }'
        )
        self.assertEqual(data['contract_line_list'], [{'id': str(line.pk)}])


class GlobalSearchTestCase(TestCase):
    """009-FR-012: NetBox's global search does not index the party name."""

    def test_party_name_is_not_indexed(self):
        build_fixture(self)
        contract = Contract.objects.get(name='Support A')
        content_type = ContentType.objects.get_for_model(Contract)

        def cached():
            return ' '.join(
                str(value) for value in CachedValue.objects.filter(
                    object_type=content_type, object_id=contract.pk
                ).values_list('value', flat=True)
            ).lower()

        self.assertNotIn('acme telecom', cached())
        self.acme.name = 'Zenith Telecom'
        self.acme.save()
        self.assertNotIn('zenith', cached())
