"""Sorting the generic-relation columns of the assignment tables must not fail (#317)."""

from django.urls import reverse
from utilities.testing import TestCase

from netbox_contract.models import ContractAssignment
from netbox_contract.tests.helpers import make_contract
from netbox_contract.tests.test_assignment_selector import make_device


class SortGenericColumnsTestCase(TestCase):
    user_permissions = [
        'netbox_contract.view_contractassignment',
        'netbox_contract.view_contract',
        'dcim.view_device',
    ]

    @classmethod
    def setUpTestData(cls):
        cls.device = make_device('Sorted device')
        cls.contract = make_contract(name='Sorted contract')
        ContractAssignment.objects.create(contract=cls.contract, content_object=cls.device)

    def test_device_contracts_tab_sorts_by_partner(self):
        url = reverse('dcim:device_contracts', args=[self.device.pk])
        for sort in ('contract__external_party_object', '-contract__external_party_object'):
            with self.subTest(sort=sort):
                self.assertHttpStatus(self.client.get(f'{url}?sort={sort}'), 200)

    def test_assignment_list_sorts_by_partner_and_object(self):
        url = reverse('plugins:netbox_contract:contractassignment_list')
        for sort in ('contract__external_party_object', 'content_object'):
            with self.subTest(sort=sort):
                self.assertHttpStatus(self.client.get(f'{url}?sort={sort}'), 200)

    def test_contract_list_sorts_by_external_party(self):
        url = reverse('plugins:netbox_contract:contract_list')
        self.add_permissions('netbox_contract.view_contract')
        self.assertHttpStatus(self.client.get(f'{url}?sort=external_party_object'), 200)
