"""Generic-object selector on the assignment form and the contract external party (spec 004)."""

from urllib.parse import parse_qs, urlparse

from circuits.models import Provider
from dcim.models import Device, DeviceRole, DeviceType, Manufacturer, Site
from django.contrib.contenttypes.models import ContentType
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from utilities.testing import TestCase

from netbox_contract import forms
from netbox_contract.constants import ASSIGNEMENT_MODELS, SERVICE_PROVIDER_MODELS
from netbox_contract.models import Contract, ContractAssignment, ServiceProvider
from netbox_contract.tests.helpers import add_constrained_permission, make_contract, make_provider
from netbox_contract.views import AddContractAssignment

ADD_URL = 'plugins:netbox_contract:contractassignment_add'
CONTRACT_ADD_URL = 'plugins:netbox_contract:contract_add'


def ct(model):
    return ContentType.objects.get_for_model(model).pk


def make_device(name='Device 1', site=None):
    manufacturer = Manufacturer.objects.get_or_create(name='Manufacturer', slug='manufacturer')[0]
    device_type = DeviceType.objects.get_or_create(manufacturer=manufacturer, model='Model', slug='model')[0]
    role = DeviceRole.objects.get_or_create(name='Role', slug='role')[0]
    site = site or Site.objects.get_or_create(name='Site 1', slug='site-1')[0]
    return Device.objects.create(name=name, device_type=device_type, role=role, site=site)


def selector(device, prefix='content_object'):
    return {f'{prefix}_content_type': ct(Device), f'{prefix}_object_id': device.pk}


class AssignmentFormTestCase(TestCase):
    user_permissions = ['netbox_contract.add_contractassignment', 'netbox_contract.view_contract', 'dcim.view_device']

    @classmethod
    def setUpTestData(cls):
        cls.device = make_device('Selectable device')
        cls.other = make_device('Other device')
        cls.contract = make_contract(name='Selector contract')

    def post(self, data, query=''):
        return self.client.post(reverse(ADD_URL) + query, data)

    def test_pre_filled_by_the_add_link_and_returns_to_the_object(self):
        return_url = self.device.get_absolute_url()
        url = f'{reverse(ADD_URL)}?{self.device_query()}&return_url={return_url}'
        response = self.client.get(url)
        self.assertHttpStatus(response, 200)
        self.assertContains(response, 'Selectable device')
        response = self.client.post(url, {**selector(self.device), 'contract': self.contract.pk})
        self.assertRedirects(response, return_url, fetch_redirect_response=False)
        assignment = ContractAssignment.objects.get(contract=self.contract)
        self.assertEqual(assignment.content_object, self.device)

    def device_query(self):
        return f'content_object_content_type={ct(Device)}&content_object_object_id={self.device.pk}'

    def test_add_link_uses_the_selector_names(self):
        url = AddContractAssignment.get_url(self.device)
        query = parse_qs(urlparse(url).query)
        self.assertEqual(query['content_object_content_type'], [str(ct(Device))])
        self.assertEqual(query['content_object_object_id'], [str(self.device.pk)])
        self.assertNotIn('content_type', query)

    def test_inline_table_link_uses_the_selector_names(self):
        self.add_permissions('dcim.view_device')
        response = self.client.get(self.device.get_absolute_url())
        self.assertContains(response, 'content_object_content_type=')
        self.assertContains(response, f'content_object_object_id={self.device.pk}')

    def test_old_query_names_still_preselect(self):
        response = self.client.get(f'{reverse(ADD_URL)}?content_type={ct(Device)}&object_id={self.device.pk}')
        self.assertHttpStatus(response, 200)
        self.assertContains(response, 'Selectable device')

    def test_new_query_names_win_over_old_ones(self):
        query = f'{self.device_query()}&content_type={ct(Device)}&object_id={self.other.pk}'
        response = self.client.get(f'{reverse(ADD_URL)}?{query}')
        self.assertContains(response, 'Selectable device')
        self.assertNotContains(response, 'Other device')

    def test_object_types_follow_supported_models(self):
        field = forms.ContractAssignmentForm().fields['content_object']
        self.assertEqual(
            set(field.content_type_queryset.values_list('pk', flat=True)),
            set(ContentType.objects.filter(ASSIGNEMENT_MODELS).values_list('pk', flat=True)),
        )
        self.assertIn(ct(Device), set(field.content_type_queryset.values_list('pk', flat=True)))

    def test_the_form_has_no_raw_object_id_field(self):
        form = forms.ContractAssignmentForm()
        self.assertNotIn('object_id', form.fields)
        self.assertNotIn('content_type', form.fields)
        self.assertTrue(form.fields['content_object'].required)

    def test_object_outside_the_view_permission_is_refused(self):
        self.remove_permissions('dcim.view_device')
        add_constrained_permission(self.user, 'dcim.view_device', {'pk': self.device.pk})
        response = self.post({**selector(self.other), 'contract': self.contract.pk})
        self.assertHttpStatus(response, 200)
        self.assertFalse(ContractAssignment.objects.exists())
        response = self.post({**selector(self.device), 'contract': self.contract.pk})
        self.assertHttpStatus(response, 302)

    def test_type_without_object_is_refused_with_the_type_name(self):
        response = self.post({'content_object_content_type': ct(Device), 'contract': self.contract.pk})
        self.assertHttpStatus(response, 200)
        self.assertContains(response, 'Please select a device.')
        self.assertFalse(ContractAssignment.objects.exists())

    def test_object_without_type_is_refused(self):
        response = self.post({'content_object_object_id': self.device.pk, 'contract': self.contract.pk})
        self.assertHttpStatus(response, 200)
        self.assertContains(response, 'Both an object type and an object must be specified.')
        self.assertFalse(ContractAssignment.objects.exists())

    def test_edit_shows_the_current_object_and_saves(self):
        assignment = ContractAssignment.objects.create(contract=self.contract, content_object=self.device)
        self.add_permissions('netbox_contract.change_contractassignment')
        url = reverse('plugins:netbox_contract:contractassignment_edit', args=[assignment.pk])
        self.assertContains(self.client.get(url), 'Selectable device')
        response = self.client.post(url, {**selector(self.other), 'contract': self.contract.pk})
        self.assertHttpStatus(response, 302)
        assignment.refresh_from_db()
        self.assertEqual(assignment.content_object, self.other)

    def test_changing_the_type_clears_the_object(self):
        assignment = ContractAssignment.objects.create(contract=self.contract, content_object=self.device)
        self.add_permissions('netbox_contract.change_contractassignment', 'dcim.view_site')
        url = reverse('plugins:netbox_contract:contractassignment_edit', args=[assignment.pk])
        response = self.client.get(
            f'{url}?content_object_content_type={ct(Site)}&content_object_object_id=',
            headers={'HX-Request': 'true'},
        )
        self.assertHttpStatus(response, 200)
        self.assertNotContains(response, 'Selectable device')

    def test_clone_returns_the_selector_names(self):
        assignment = ContractAssignment.objects.create(contract=self.contract, content_object=self.device)
        clone = assignment.clone()
        self.assertEqual(clone['content_object_content_type'], ct(Device))
        self.assertEqual(clone['content_object_object_id'], self.device.pk)
        self.assertEqual(clone['contract'], self.contract.pk)
        self.assertNotIn('content_type', clone)
        self.assertNotIn('object_id', clone)

    def test_add_another_keeps_the_object(self):
        response = self.post(
            {**selector(self.device), 'contract': self.contract.pk, '_addanother': '1'}, query=f'?{self.device_query()}'
        )
        self.assertHttpStatus(response, 302)
        query = parse_qs(urlparse(response['Location']).query)
        self.assertEqual(query['content_object_content_type'], [str(ct(Device))])
        self.assertEqual(query['content_object_object_id'], [str(self.device.pk)])

    def test_htmx_refresh_renders_the_form(self):
        response = self.client.get(
            f'{reverse(ADD_URL)}?content_object_content_type={ct(Device)}', headers={'HX-Request': 'true'}
        )
        self.assertHttpStatus(response, 200)
        self.assertContains(response, 'content_object_object_id')


class ExternalPartyFormTestCase(TestCase):
    user_permissions = [
        'netbox_contract.add_contract',
        'netbox_contract.change_contract',
        'netbox_contract.view_contract',
        'netbox_contract.view_serviceprovider',
        'circuits.view_provider',
    ]

    @classmethod
    def setUpTestData(cls):
        cls.service_provider = ServiceProvider.objects.create(name='Chosen service provider', slug='chosen-sp')
        cls.provider = Provider.objects.create(name='Chosen circuit provider', slug='chosen-cp')

    def data(self, **kwargs):
        data = {
            'name': 'Selector contract',
            'internal_party': 'default',
            'status': 'active',
            'start_date': '2025-01-01',
            'end_date': '2025-12-31',
            'currency': 'usd',
            'invoice_frequency': 1,
            'initial_term': 12,
            'renewal_term': 12,
            'notice_period': 90,
            'billable': True,
            'external_party_object_content_type': ct(ServiceProvider),
            'external_party_object_object_id': self.service_provider.pk,
        }
        data.update(kwargs)
        return data

    def test_new_contract_defaults_to_the_service_provider_type(self):
        response = self.client.get(reverse(CONTRACT_ADD_URL))
        self.assertHttpStatus(response, 200)
        form = response.context['form']
        self.assertEqual(form['external_party_object'].initial[0], ct(ServiceProvider))

    def test_external_party_types_follow_the_allowed_providers(self):
        field = forms.ContractForm().fields['external_party_object']
        self.assertEqual(
            set(field.content_type_queryset.values_list('pk', flat=True)),
            set(ContentType.objects.filter(SERVICE_PROVIDER_MODELS).values_list('pk', flat=True)),
        )

    def test_create_with_a_service_provider(self):
        response = self.client.post(reverse(CONTRACT_ADD_URL), self.data())
        self.assertHttpStatus(response, 302)
        contract = Contract.objects.get(name='Selector contract')
        self.assertEqual(contract.external_party_object, self.service_provider)

    def test_create_with_a_circuit_provider(self):
        data = self.data(
            external_party_object_content_type=ct(Provider), external_party_object_object_id=self.provider.pk
        )
        response = self.client.post(reverse(CONTRACT_ADD_URL), data)
        self.assertHttpStatus(response, 302)
        contract = Contract.objects.get(name='Selector contract')
        self.assertEqual(contract.external_party_object, self.provider)

    def test_external_party_is_required(self):
        data = self.data()
        del data['external_party_object_content_type']
        del data['external_party_object_object_id']
        response = self.client.post(reverse(CONTRACT_ADD_URL), data)
        self.assertHttpStatus(response, 200)
        self.assertFalse(Contract.objects.filter(name='Selector contract').exists())

    def test_edit_shows_and_changes_the_external_party(self):
        contract = make_contract(name='Edited contract')
        url = reverse('plugins:netbox_contract:contract_edit', args=[contract.pk])
        self.assertContains(self.client.get(url), make_provider().name)
        data = self.data(name='Edited contract')
        response = self.client.post(url, data)
        self.assertHttpStatus(response, 302)
        contract.refresh_from_db()
        self.assertEqual(contract.external_party_object, self.service_provider)

    def test_switching_the_type_clears_the_provider(self):
        contract = make_contract(name='Edited contract')
        url = reverse('plugins:netbox_contract:contract_edit', args=[contract.pk])
        response = self.client.get(
            f'{url}?external_party_object_content_type={ct(ServiceProvider)}&external_party_object_object_id=',
            headers={'HX-Request': 'true'},
        )
        self.assertHttpStatus(response, 200)
        self.assertNotContains(response, make_provider().name)

    def test_the_page_does_not_list_every_provider(self):
        def page_queries():
            with CaptureQueriesContext(connection) as queries:
                response = self.client.get(reverse(CONTRACT_ADD_URL))
            self.assertHttpStatus(response, 200)
            return response, len(queries)

        ServiceProvider.objects.bulk_create(
            ServiceProvider(name=f'Bulk provider {n}', slug=f'bulk-{n}') for n in range(10)
        )
        _, few = page_queries()
        ServiceProvider.objects.bulk_create(
            ServiceProvider(name=f'Bulk provider {n}', slug=f'bulk-{n}') for n in range(10, 5000)
        )
        response, many = page_queries()
        self.assertNotContains(response, 'Bulk provider 4999')
        self.assertEqual(few, many)


class UnchangedInterfacesTestCase(TestCase):
    """Bulk edit of contracts keeps its own external party fields (specification FR-009)."""

    def test_bulk_edit_form_fields(self):
        fields = forms.ContractBulkEditForm().fields
        self.assertIn('external_party_object_type', fields)
        self.assertIn('external_party_object', fields)
