"""A contract is assigned to an object only once (specs/004-generic-object-selector, User Story 4)."""

import io
from contextlib import redirect_stdout
from importlib import import_module

from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.db import IntegrityError, connection, transaction
from django.urls import reverse
from extras.models import Bookmark, JournalEntry, Tag
from utilities.testing import APITestCase, TestCase

from netbox_contract.models import ContractAssignment
from netbox_contract.tests.helpers import make_contract
from netbox_contract.tests.test_assignment_selector import make_device, selector

ADD_URL = 'plugins:netbox_contract:contractassignment_add'
migration = import_module('netbox_contract.migrations.0054_merge_duplicate_assignments')


def drop_unique_rule():
    """Let a test create the duplicates an older release allowed (rolled back with the test)."""
    constraint = next(c for c in ContractAssignment._meta.constraints if c.name == 'netbox_contract_unique_assignment')
    with connection.schema_editor() as editor:
        editor.remove_constraint(ContractAssignment, constraint)


class DuplicateRuleTestCase(TestCase):
    user_permissions = [
        'netbox_contract.add_contractassignment',
        'netbox_contract.change_contractassignment',
        'netbox_contract.view_contract',
        'dcim.view_device',
    ]

    @classmethod
    def setUpTestData(cls):
        cls.device = make_device('Assigned device')
        cls.other = make_device('Other device')
        cls.contract = make_contract(name='Duplicate contract')
        cls.second_contract = make_contract(name='Second contract')
        cls.assignment = ContractAssignment.objects.create(contract=cls.contract, content_object=cls.device)

    def test_form_refuses_the_same_pair(self):
        response = self.client.post(reverse(ADD_URL), {**selector(self.device), 'contract': self.contract.pk})
        self.assertHttpStatus(response, 200)
        self.assertContains(response, 'Duplicate contract is already assigned to Assigned device.')
        self.assertEqual(ContractAssignment.objects.count(), 1)

    def test_different_pairs_are_accepted(self):
        for device, contract in ((self.other, self.contract), (self.device, self.second_contract)):
            response = self.client.post(reverse(ADD_URL), {**selector(device), 'contract': contract.pk})
            self.assertHttpStatus(response, 302)
        self.assertEqual(ContractAssignment.objects.count(), 3)

    def test_edit_without_changing_the_pair_saves(self):
        url = reverse('plugins:netbox_contract:contractassignment_edit', args=[self.assignment.pk])
        self.add_permissions('extras.view_tag')
        tag = Tag.objects.create(name='Edited', slug='edited')
        tag.object_types.set([ContentType.objects.get_for_model(ContractAssignment)])
        response = self.client.post(
            url, {**selector(self.device), 'contract': self.contract.pk, 'tags': [tag.pk]}
        )
        self.assertHttpStatus(response, 302)
        self.assertEqual(list(self.assignment.tags.all()), [tag])

    def test_edit_onto_an_existing_pair_is_refused(self):
        moved = ContractAssignment.objects.create(contract=self.contract, content_object=self.other)
        url = reverse('plugins:netbox_contract:contractassignment_edit', args=[moved.pk])
        response = self.client.post(url, {**selector(self.device), 'contract': self.contract.pk})
        self.assertHttpStatus(response, 200)
        self.assertContains(response, 'is already assigned to')
        moved.refresh_from_db()
        self.assertEqual(moved.content_object, self.other)

    def test_csv_import_refuses_the_same_pair(self):
        self.add_permissions('netbox_contract.add_contractassignment')
        csv = f'content_type,object_id,contract\ndcim.device,{self.device.pk},{self.contract.pk}'
        response = self.client.post(
            reverse('plugins:netbox_contract:contractassignment_bulk_import'),
            {'data': csv, 'format': 'csv', 'csv_delimiter': 'auto'},
        )
        self.assertHttpStatus(response, 200)
        self.assertContains(response, 'is already assigned to')
        self.assertEqual(ContractAssignment.objects.count(), 1)

    def test_database_rejects_the_same_pair(self):
        with self.assertRaisesMessage(IntegrityError, 'netbox_contract_unique_assignment'):
            with transaction.atomic():
                ContractAssignment.objects.bulk_create(
                    [ContractAssignment(contract=self.contract, content_object=self.device)]
                )


class DuplicateRuleApiTestCase(APITestCase):
    user_permissions = ['netbox_contract.add_contractassignment', 'netbox_contract.view_contractassignment']

    def test_rest_refuses_the_same_pair(self):
        device = make_device('Rest device')
        contract = make_contract(name='Rest contract')
        ContractAssignment.objects.create(contract=contract, content_object=device)
        url = reverse('plugins-api:netbox_contract-api:contractassignment-list')
        data = {'contract': contract.pk, 'content_type': 'dcim.device', 'object_id': device.pk}
        response = self.client.post(url, data, format='json', **self.header)
        self.assertHttpStatus(response, 400)
        self.assertIn('is already assigned to', str(response.data))
        self.assertEqual(ContractAssignment.objects.count(), 1)


class MergeDuplicatesTestCase(TestCase):
    """The merge of the upgrade step; the unique rule is dropped inside the test to create old-style duplicates."""

    def setUp(self):
        super().setUp()
        drop_unique_rule()
        self.device = make_device('Merged device')
        self.contract = make_contract(name='Merged contract')
        self.assignment_type = ContentType.objects.get_for_model(ContractAssignment)

    def duplicates(self, count=3):
        device_type = ContentType.objects.get_for_model(self.device)
        return ContractAssignment.objects.bulk_create(
            [
                ContractAssignment(contract=self.contract, content_type=device_type, object_id=self.device.pk)
                for _ in range(count)
            ]
        )

    def run_merge(self):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            lines = migration.merge_duplicates(apps)
        return lines, buffer.getvalue()

    def test_nothing_to_merge(self):
        ContractAssignment.objects.create(contract=self.contract, content_object=self.device)
        lines, printed = self.run_merge()
        self.assertEqual((lines, printed), ([], ''))
        self.assertEqual(ContractAssignment.objects.count(), 1)

    def test_oldest_is_kept_and_receives_everything(self):
        first, second, third = self.duplicates()
        tags = [Tag.objects.create(name=name, slug=name) for name in ('a', 'b', 'c')]
        first.tags.add(tags[0])
        second.tags.add(tags[0], tags[1])
        third.tags.add(tags[2])
        entry = JournalEntry.objects.create(
            assigned_object_type=self.assignment_type, assigned_object_id=third.pk, comments='kept note'
        )
        Bookmark.objects.create(object_type=self.assignment_type, object_id=first.pk, user=self.user)
        Bookmark.objects.create(object_type=self.assignment_type, object_id=second.pk, user=self.user)
        ContractAssignment.objects.filter(pk=first.pk).update(custom_field_data={'owner': '', 'site': 'A'})
        ContractAssignment.objects.filter(pk=second.pk).update(custom_field_data={'owner': 'Marc', 'site': 'B'})

        lines, printed = self.run_merge()

        self.assertEqual(list(ContractAssignment.objects.values_list('pk', flat=True)), [first.pk])
        first.refresh_from_db()
        self.assertEqual({tag.name for tag in first.tags.all()}, {'a', 'b', 'c'})
        entry.refresh_from_db()
        self.assertEqual(entry.assigned_object_id, first.pk)
        self.assertEqual(Bookmark.objects.filter(object_id=first.pk).count(), 1)
        self.assertEqual(first.custom_field_data, {'owner': 'Marc', 'site': 'A'})
        report = '\n'.join(lines)
        self.assertIn(f'kept #{first.pk}', report)
        self.assertIn(f'#{second.pk}', report)
        self.assertIn(f'#{third.pk}', report)
        self.assertIn('custom field "site" differs', report)
        self.assertIn("'B'", report)
        self.assertIn('journal entries', report)
        self.assertIn(report.splitlines()[0], printed)

    def test_second_run_changes_nothing(self):
        self.duplicates()
        self.run_merge()
        lines, printed = self.run_merge()
        self.assertEqual((lines, printed), ([], ''))
        self.assertEqual(ContractAssignment.objects.count(), 1)
