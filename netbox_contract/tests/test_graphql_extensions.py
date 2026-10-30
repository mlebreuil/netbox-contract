"""Spec 006: contracts reachable from core objects in GraphQL (field, filters, cascade)."""

from dcim.models import Device, DeviceRole, DeviceType, Manufacturer
from django.contrib.contenttypes.models import ContentType
from django.db import connection
from django.test.utils import CaptureQueriesContext

from netbox_contract.models import Contract, ContractAssignment
from netbox_contract.tests.helpers import add_constrained_permission
from netbox_contract.tests.test_graphql import GraphQLTestCase

LIST = '{ device_list { name contract_assignments { contract { name status end_date } } } }'
NAMES = '{ device_list(filters: {%s}) { name } }'


def make_device(name, site):
    manufacturer = Manufacturer.objects.get_or_create(name='Acme', slug='acme')[0]
    device_type = DeviceType.objects.get_or_create(manufacturer=manufacturer, model='Box', slug='box')[0]
    role = DeviceRole.objects.get_or_create(name='Router', slug='router')[0]
    return Device.objects.create(name=name, site=site, device_type=device_type, role=role)


def assign(contract, obj):
    return ContractAssignment.objects.create(
        contract=contract, content_type=ContentType.objects.get_for_model(obj), object_id=obj.pk
    )


class ExtensionTestCase(GraphQLTestCase):
    def setUp(self):
        super().setUp()
        self.d_none = make_device('d-none', self.site)
        self.d_canceled = make_device('d-canceled', self.site)
        self.d_active = make_device('d-active', self.site)
        self.d_both = make_device('d-both', self.site)
        assign(self.cancelled, self.d_canceled)
        assign(self.contract, self.d_active)
        assign(self.cancelled, self.d_both)
        assign(self.contract, self.d_both)

    def devices(self, filters):
        return sorted(d['name'] for d in self.data(NAMES % filters)['device_list'])

    def by_name(self, query=LIST):
        return {d['name']: d['contract_assignments'] for d in self.data(query)['device_list']}

    # US1
    def test_device_with_two_contracts(self):
        self.superuser()
        assignments = self.by_name()
        self.assertEqual(assignments['d-none'], [])
        names = sorted(a['contract']['name'] for a in assignments['d-both'])
        self.assertEqual(names, ['Active', 'Cancelled'])
        active = next(a for a in assignments['d-active'])
        self.assertEqual(active['contract']['status'], 'active')
        self.assertIn('end_date', active['contract'])

    def test_user_without_contract_permission_gets_empty_list(self):
        self.add_permissions('dcim.view_device')
        self.assertTrue(all(v == [] for v in self.by_name().values()))

    def test_hidden_contract_is_left_out(self):
        self.add_permissions('dcim.view_device', 'netbox_contract.view_contractassignment')
        add_constrained_permission(self.user, 'netbox_contract.view_contract', {'pk': self.contract.pk})
        assignments = self.by_name()
        self.assertEqual([a['contract']['name'] for a in assignments['d-both']], ['Active'])
        self.assertEqual(assignments['d-canceled'], [])

    def test_field_only_on_supported_types(self):
        self.superuser()
        with_field = set()
        for name in ('DeviceType', 'SiteType', 'RackType', 'CircuitType', 'VirtualCircuitType',
                     'VirtualMachineType', 'ClusterType', 'TenantType', 'ManufacturerType'):
            data = self.data(f'{{ __type(name: "{name}") {{ fields {{ name }} }} }}')['__type']
            if data and 'contract_assignments' in {f['name'] for f in data['fields']}:
                with_field.add(name)
        self.assertEqual(with_field, {
            'DeviceType', 'SiteType', 'RackType', 'CircuitType', 'VirtualCircuitType', 'VirtualMachineType',
            'ClusterType',
        })

    def test_query_count_does_not_grow_with_the_list(self):
        self.superuser()
        query = '{ device_list { name contract_assignments { contract { name } } } }'
        self.data(query)  # fills the content type cache
        with CaptureQueriesContext(connection) as small:
            self.data(query)
        for i in range(20):
            device = make_device(f'bulk-{i}', self.site)
            assign(self.contract, device)
        with CaptureQueriesContext(connection) as large:
            self.data(query)
        self.assertEqual(len(small), len(large))

    # FR-012: deleted with their object
    def test_assignments_deleted_with_their_object(self):
        before = ContractAssignment.objects.count()
        self.d_both.delete()
        self.assertEqual(ContractAssignment.objects.count(), before - 2)
        self.assertTrue(Contract.objects.filter(pk=self.contract.pk).exists())
        self.d_none.delete()

    def test_assignments_deleted_with_their_contract(self):
        self.cancelled.delete()
        self.assertTrue(Device.objects.filter(pk=self.d_canceled.pk).exists())
        self.assertFalse(ContractAssignment.objects.filter(object_id=self.d_canceled.pk).exists())

    # US2
    def test_has_contracts(self):
        self.superuser()
        self.assertEqual(self.devices('has_contracts: true'), ['d-active', 'd-both', 'd-canceled'])
        self.assertEqual(self.devices('has_contracts: false'), ['d-none'])

    def test_has_active_contract(self):
        self.superuser()
        self.assertEqual(self.devices('has_active_contract: true'), ['d-active', 'd-both'])
        self.assertEqual(self.devices('has_active_contract: false'), ['d-canceled', 'd-none'])

    def test_filters_combine_with_others(self):
        self.superuser()
        self.assertEqual(self.devices('has_active_contract: false, name: {exact: "d-none"}'), ['d-none'])
        self.assertEqual(self.devices('has_contracts: true, name: {exact: "d-none"}'), [])

    def test_filters_without_contract_permission(self):
        self.add_permissions('dcim.view_device')
        self.assertEqual(self.devices('has_contracts: true'), [])
        self.assertEqual(len(self.devices('has_contracts: false')), 4)

    def test_hidden_active_contract_does_not_count(self):
        self.add_permissions('dcim.view_device', 'netbox_contract.view_contractassignment')
        add_constrained_permission(self.user, 'netbox_contract.view_contract', {'pk': self.cancelled.pk})
        self.assertEqual(self.devices('has_active_contract: true'), [])
        self.assertEqual(self.devices('has_contracts: true'), ['d-both', 'd-canceled'])

    # US3
    def test_core_type_without_new_field_is_unchanged(self):
        self.superuser()
        data = self.data('{ device_list { name site { name } } }')['device_list']
        self.assertEqual(len(data), 4)
