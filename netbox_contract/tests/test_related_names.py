"""Reverse names of the foreign keys to core models carry the app label (issue #329).

Another plugin can add its own ``contracts`` reverse name to a core model; the prefix keeps the two apart.
"""

from django.test import TestCase
from tenancy.models import Tenant

from netbox_contract.models import Contract
from netbox_contract.tests.helpers import make_contract


class TenantReverseNameTestCase(TestCase):
    def test_tenant_reverse_name_is_prefixed(self):
        tenant = Tenant.objects.create(name='Tenant', slug='tenant')
        contract = make_contract(tenant=tenant)

        self.assertEqual(Contract._meta.get_field('tenant').remote_field.related_name, 'netbox_contract_contracts')
        self.assertEqual(list(tenant.netbox_contract_contracts.all()), [contract])

    def test_tenant_has_no_unprefixed_contracts_name(self):
        self.assertFalse(hasattr(Tenant, 'contracts'))
