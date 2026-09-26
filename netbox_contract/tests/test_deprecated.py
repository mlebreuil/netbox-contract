"""Deprecated cost fields and invoice templates after the upgrade (FR-014, FR-015, SC-007, US2)."""

from decimal import Decimal
from unittest import mock

from circuits.models import Provider
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from rest_framework import status
from utilities.testing import TestCase

from netbox_contract.models import Contract, Invoice, InvoiceLine
from netbox_contract.tests.custom import APITestCase
from netbox_contract.tests.helpers import make_contract, make_provider

PLUGIN_SETTINGS = settings.PLUGINS_CONFIG['netbox_contract']


class DeprecatedFieldsViewTestCase(TestCase):
    def setUp(self):
        super().setUp()
        self.user.is_superuser = True
        self.user.save()
        self.contract = make_contract(mrc=Decimal('123.45'), nrc=Decimal('678.90'))

    def get_contract_page(self):
        return self.client.get(reverse('plugins:netbox_contract:contract', args=[self.contract.pk])).content.decode()

    def get_contract_form(self):
        return self.client.get(reverse('plugins:netbox_contract:contract_edit', args=[self.contract.pk]))

    def test_hidden_by_default(self):
        form = self.get_contract_form().context['form']
        for field in ('mrc', 'yrc', 'nrc'):
            self.assertNotIn(field, form.fields)
        content = self.get_contract_page()
        self.assertNotIn('123.45', content)
        self.assertNotIn('678.90', content)

    def test_shown_with_setting(self):
        with mock.patch.dict(PLUGIN_SETTINGS, {'show_deprecated_fields': True}):
            form = self.get_contract_form().context['form']
            for field in ('mrc', 'yrc', 'nrc'):
                self.assertIn(field, form.fields)
            content = self.get_contract_page()
        self.assertIn('123.45', content)
        self.assertIn('678.90', content)
        self.assertIn('deprecated', content.lower())

    def test_saving_the_form_keeps_deprecated_values(self):
        provider = make_provider()
        data = {
            'name': 'Renamed',
            'external_party_object_type': ContentType.objects.get_for_model(Provider).pk,
            'external_party_object': provider.pk,
            'internal_party': 'default',
            'status': 'active',
            'currency': 'usd',
            'notice_period': 90,
            'invoice_frequency': 1,
            'billable': True,
        }
        response = self.client.post(reverse('plugins:netbox_contract:contract_edit', args=[self.contract.pk]), data)
        self.assertEqual(response.status_code, 302, response.content.decode()[-2000:])
        self.contract.refresh_from_db()
        self.assertEqual(self.contract.name, 'Renamed')
        self.assertEqual(self.contract.mrc, Decimal('123.45'))
        self.assertEqual(self.contract.nrc, Decimal('678.90'))

    def test_settings_naming_deprecated_fields_do_not_crash(self):
        with (
            mock.patch.dict(PLUGIN_SETTINGS, {'mandatory_contract_fields': ['mrc'], 'hidden_contract_fields': ['yrc']}),
            self.assertLogs('netbox.plugins.netbox_contract', level='WARNING'),
        ):
            response = self.get_contract_form()
        self.assertEqual(response.status_code, 200)

    def test_contract_list_hides_deprecated_columns(self):
        url = reverse('plugins:netbox_contract:contract_list')
        response = self.client.get(url)
        column_names = [column.name for column in response.context['table'].columns.iterall()]
        for field in ('mrc', 'yrc', 'nrc'):
            self.assertNotIn(field, column_names)
        with mock.patch.dict(PLUGIN_SETTINGS, {'show_deprecated_fields': True}):
            response = self.client.get(url)
        column_names = [column.name for column in response.context['table'].columns.iterall()]
        for field in ('mrc', 'yrc', 'nrc'):
            self.assertIn(field, column_names)

    def test_template_invoice_badge_and_panel(self):
        template = Invoice.objects.create(number='_invoice_template_Contract', template=True, amount=0)
        template.contracts.add(self.contract)
        InvoiceLine.objects.create(invoice=template, amount=Decimal(10), currency='usd')
        content = self.get_contract_page()
        self.assertIn(template.get_absolute_url(), content)
        self.assertIn('Invoice templates (kept for reference)', content)
        response = self.client.get(template.get_absolute_url())
        self.assertIn('deprecated', response.content.decode().lower())

    def test_new_template_offered_only_with_setting(self):
        response = self.client.get(reverse('plugins:netbox_contract:invoice_add'))
        self.assertNotIn('template', response.context['form'].fields)
        self.assertFalse(response.context['form'].fields['number'].help_text)
        self.assertNotIn('_invoice_template_', response.content.decode())
        with mock.patch.dict(PLUGIN_SETTINGS, {'show_deprecated_fields': True}):
            response = self.client.get(reverse('plugins:netbox_contract:invoice_add'))
        self.assertIn('template', response.context['form'].fields)

    def test_import_accepts_deprecated_and_billable_columns(self):
        csv = (
            'name,external_party_object_type,external_party_object_id,internal_party,status,currency,'
            'mrc,yrc,nrc,invoice_frequency,billable\n'
            'Imported,circuits.provider,Provider A,default,active,usd,10,,5,1,false'
        )
        response = self.client.post(
            reverse('plugins:netbox_contract:contract_bulk_import'),
            {'data': csv, 'format': 'csv', 'csv_delimiter': 'auto'},
        )
        self.assertEqual(response.status_code, 302, response.content.decode()[-3000:])
        imported = Contract.objects.get(name='Imported')
        self.assertEqual(imported.mrc, Decimal(10))
        self.assertEqual(imported.nrc, Decimal(5))
        self.assertFalse(imported.billable)


class DeprecatedFieldsAPITestCase(APITestCase):
    model = Contract

    def test_api_accepts_and_returns_deprecated_fields(self):
        self.add_permissions('netbox_contract.add_contract', 'netbox_contract.view_contract')
        provider = make_provider()
        data = {
            'name': 'API contract',
            'external_party_object_type': 'circuits.provider',
            'external_party_object_id': provider.pk,
            'internal_party': 'default',
            'status': 'active',
            'currency': 'usd',
            'mrc': '100.00',
            'nrc': '20.00',
        }
        response = self.client.post(self._get_list_url(), data, format='json', **self.header)
        self.assertHttpStatus(response, status.HTTP_201_CREATED)
        self.assertEqual(Decimal(response.data['mrc']), Decimal(100))
        self.assertEqual(Decimal(response.data['nrc']), Decimal(20))
        self.assertIn('yrc', response.data)
        self.assertTrue(response.data['billable'])
