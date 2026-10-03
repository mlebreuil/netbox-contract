"""
Issue #309, user story 5: contract types and service providers on NetBox's organizational and primary base classes
(spec 003, research D9 and D10, data-model.md).
"""

from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase as DjangoTestCase
from django.urls import reverse
from rest_framework import status
from users.models import Owner
from utilities.testing import TestCase

from netbox_contract.models import ContractType, ServiceProvider
from netbox_contract.tests.custom import APITestCase

LONG_TEXT = ' '.join(['Maintenance of the network equipment and of the related software licences'] * 5)  # > 350
APP = 'netbox_contract'
BEFORE = (APP, '0050_contractline_amend_permission')
AFTER = (APP, '0051_contracttype_organizational')


class TextHelpersTestCase(DjangoTestCase):
    """T054: the pure helpers of netbox_contract/text.py."""

    def test_unique_slug(self):
        from netbox_contract.text import unique_slug

        self.assertEqual(unique_slug('Support & Licences', set()), 'support-licences')
        self.assertEqual(unique_slug('Maintenance', {'maintenance'}), 'maintenance-2')
        self.assertEqual(unique_slug('Maintenance', {'maintenance', 'maintenance-2'}), 'maintenance-3')
        self.assertEqual(unique_slug('&&&', set()), 'contract-type')  # edge case: nothing to slugify

    def test_shorten_description(self):
        from netbox_contract.text import shorten_description

        exact = 'x' * 200
        self.assertEqual(shorten_description(exact), exact)
        short = shorten_description(LONG_TEXT)
        self.assertLessEqual(len(short), 200)
        self.assertTrue(short.endswith('…'))
        self.assertTrue(LONG_TEXT.startswith(short[:-1]))
        self.assertEqual(LONG_TEXT[len(short) - 1], ' ')  # cut at a word boundary
        no_space = 'y' * 350
        self.assertEqual(shorten_description(no_space), 'y' * 199 + '…')  # edge case: no space

    def test_plan_contract_type_changes(self):
        from netbox_contract.text import plan_contract_type_changes

        rows = [
            (1, 'Maintenance', '', 'Short'),
            (2, 'Maintenance!', '', ''),
            (3, 'Licences', '', LONG_TEXT),
            (4, 'Support', 'support', 'Already done'),
        ]
        changes, report = plan_contract_type_changes(rows, taken={'support'})
        self.assertEqual(changes[1], {'slug': 'maintenance'})
        self.assertEqual(changes[2], {'slug': 'maintenance-2'})
        self.assertEqual(changes[3]['slug'], 'licences')
        self.assertTrue(changes[3]['description'].endswith('…'))
        self.assertEqual(changes[3]['comments'], LONG_TEXT)
        self.assertNotIn(4, changes)  # US5-7: nothing to do twice
        self.assertEqual(len(report), 2)
        self.assertIn('Maintenance!', report[0])
        self.assertIn('maintenance-2', report[0])
        self.assertIn('Licences', report[1])
        self.assertEqual(plan_contract_type_changes([(4, 'Support', 'support', 'Done')], taken=set()), ({}, []))


class MigrationTestCase(DjangoTestCase):
    """
    T055: migration 0051 forward, back and forward again on historical models (US5-1, US5-2, US5-3, US5-7).
    PostgreSQL runs the schema changes inside the test transaction, so its rollback restores the schema. (A
    TransactionTestCase cannot flush NetBox's database, which has foreign keys between apps.)
    """

    def migrate(self, target):
        executor = MigrationExecutor(connection)
        executor.migrate([target])
        return MigrationExecutor(connection).loader.project_state([target]).apps

    def test_forward_back_forward(self):
        apps = self.migrate(BEFORE)
        HistoricalType = apps.get_model(APP, 'ContractType')
        # bulk_create: no post_save signal (NetBox's search cache expects the current fields)
        HistoricalType.objects.bulk_create([
            HistoricalType(name='Maintenance', description='Short'),
            HistoricalType(name='Maintenance!', description=''),
            HistoricalType(name='Licences', description=LONG_TEXT),
        ])

        apps = self.migrate(AFTER)
        types = {t.name: t for t in apps.get_model(APP, 'ContractType').objects.all()}
        self.assertEqual(types['Maintenance'].slug, 'maintenance')
        self.assertEqual(types['Maintenance!'].slug, 'maintenance-2')
        self.assertEqual(types['Licences'].comments, LONG_TEXT)
        self.assertTrue(types['Licences'].description.endswith('…'))
        self.assertLessEqual(len(types['Licences'].description), 200)

        apps = self.migrate(BEFORE)
        types = {t.name: t for t in apps.get_model(APP, 'ContractType').objects.all()}
        self.assertEqual(types['Licences'].description, LONG_TEXT)  # lossless reverse

        apps = self.migrate(AFTER)
        licences = apps.get_model(APP, 'ContractType').objects.get(name='Licences')
        self.assertEqual(licences.comments, LONG_TEXT)  # moved once, not duplicated


class ContractTypeTestCase(APITestCase):
    """T056: slug, description limit, comments and owner of contract types (US5-4, US5-6)."""

    model = ContractType

    def setUp(self):
        super().setUp()
        self.user.is_superuser = True
        self.user.save()
        self.owner = Owner.objects.create(name='Network team')

    def post(self, data):
        return self.client.post(reverse('plugins-api:netbox_contract-api:contracttype-list'), data, format='json',
                                **self.header)

    def test_rest_slug_optional(self):
        response = self.post({'name': 'Support & Licences'})
        self.assertHttpStatus(response, status.HTTP_201_CREATED)
        self.assertEqual(response.data['slug'], 'support-licences')
        response = self.post({'name': 'Hosting', 'slug': 'hosting-custom'})
        self.assertHttpStatus(response, status.HTTP_201_CREATED)
        self.assertEqual(response.data['slug'], 'hosting-custom')
        response = self.post({'name': 'Support and licences'})
        self.assertHttpStatus(response, status.HTTP_201_CREATED)
        self.assertEqual(response.data['slug'], 'support-and-licences')

    def test_rest_description_limit_comments_owner(self):
        self.assertHttpStatus(self.post({'name': 'Long', 'description': 'z' * 201}), status.HTTP_400_BAD_REQUEST)
        response = self.post({'name': 'Owned', 'comments': 'Notes', 'owner': self.owner.pk})
        self.assertHttpStatus(response, status.HTTP_201_CREATED)
        self.assertEqual(response.data['comments'], 'Notes')
        self.assertEqual(response.data['owner']['id'], self.owner.pk)
        url = reverse('plugins-api:netbox_contract-api:contracttype-list')
        response = self.client.get(f'{url}?owner_id={self.owner.pk}', **self.header)
        self.assertEqual([item['name'] for item in response.data['results']], ['Owned'])
        response = self.client.get(f'{url}?brief=true', **self.header)
        self.assertEqual(set(response.data['results'][0]), {'id', 'url', 'display', 'name', 'slug', 'description'})


class ContractTypeUITestCase(TestCase):
    """T056: form, import, bulk edit and page."""

    def setUp(self):
        super().setUp()
        self.user.is_superuser = True
        self.user.save()
        self.owner = Owner.objects.create(name='Network team')

    def test_form_without_slug(self):
        response = self.client.post(reverse('plugins:netbox_contract:contracttype_add'), {
            'name': 'Hosting', 'color': '9e9e9e', 'owner': self.owner.pk,
        })
        self.assertEqual(response.status_code, 302)
        contract_type = ContractType.objects.get(name='Hosting')
        self.assertEqual(contract_type.slug, 'hosting')
        self.assertEqual(contract_type.owner, self.owner)
        self.assertContains(self.client.get(contract_type.get_absolute_url()), 'Network team')

    def test_import_without_slug(self):
        response = self.client.post(reverse('plugins:netbox_contract:contracttype_bulk_import'), {
            'data': 'name,color,owner\nImported,9e9e9e,Network team', 'format': 'csv', 'csv_delimiter': ',',
        })
        self.assertIn(response.status_code, (200, 302))
        imported = ContractType.objects.get(name='Imported')
        self.assertEqual((imported.slug, imported.owner), ('imported', self.owner))

    def test_bulk_edit_owner(self):
        contract_type = ContractType.objects.create(name='Bulk')
        response = self.client.post(reverse('plugins:netbox_contract:contracttype_bulk_edit'), {
            'pk': [contract_type.pk], 'owner': self.owner.pk, '_apply': True,
        })
        self.assertEqual(response.status_code, 302)
        contract_type.refresh_from_db()
        self.assertEqual(contract_type.owner, self.owner)


class ServiceProviderTestCase(APITestCase):
    """T057: description and owner of service providers (US5-5, US5-6)."""

    model = ServiceProvider

    def setUp(self):
        super().setUp()
        self.user.is_superuser = True
        self.user.save()
        self.owner = Owner.objects.create(name='Vendor management')
        self.provider = ServiceProvider.objects.create(
            name='Telco', slug='telco', portal_url='https://telco.example', comments='Main carrier'
        )

    def test_description_and_owner(self):
        url = reverse('plugins-api:netbox_contract-api:serviceprovider-detail', args=[self.provider.pk])
        response = self.client.patch(url, {'description': 'Carrier', 'owner': self.owner.pk}, format='json',
                                     **self.header)
        self.assertHttpStatus(response, status.HTTP_200_OK)
        self.provider.refresh_from_db()
        self.assertEqual((self.provider.description, self.provider.owner), ('Carrier', self.owner))
        self.assertEqual(
            (self.provider.name, self.provider.slug, self.provider.portal_url, self.provider.comments),
            ('Telco', 'telco', 'https://telco.example', 'Main carrier'),
        )
        list_url = reverse('plugins-api:netbox_contract-api:serviceprovider-list')
        response = self.client.get(f'{list_url}?owner_id={self.owner.pk}', **self.header)
        self.assertEqual([item['name'] for item in response.data['results']], ['Telco'])
        response = self.client.get(f'{list_url}?brief=true', **self.header)
        self.assertEqual(set(response.data['results'][0]), {'id', 'url', 'display', 'name', 'slug', 'description'})
        self.client.force_login(self.user)
        page = self.client.get(self.provider.get_absolute_url())
        self.assertContains(page, 'Carrier')
        self.assertContains(page, 'Vendor management')

    def test_form_without_owner(self):
        """Edge case: no owner defined anywhere; the forms do not require one."""
        Owner.objects.all().delete()
        self.client.force_login(self.user)
        response = self.client.post(reverse('plugins:netbox_contract:serviceprovider_add'), {
            'name': 'New', 'slug': 'new', 'description': 'Described',
        })
        self.assertEqual(response.status_code, 302, response.context['form'].errors if response.context else '')
        self.assertEqual(ServiceProvider.objects.get(slug='new').description, 'Described')
