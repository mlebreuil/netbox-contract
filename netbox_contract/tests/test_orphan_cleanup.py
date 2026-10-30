"""Spec 006, user story 4: cleaning up the assignments whose object no longer exists."""

from io import StringIO

from dcim.models import Site
from django.contrib.contenttypes.models import ContentType
from django.core.management import call_command
from django.test import TestCase

from netbox_contract.models import ContractAssignment
from netbox_contract.orphans import find_orphan_assignments
from netbox_contract.tests.helpers import make_contract


class OrphanCleanupTestCase(TestCase):
    def setUp(self):
        self.contract = make_contract(name='C1')
        self.site_ok = Site.objects.create(name='ok', slug='ok')
        self.ct = ContentType.objects.get_for_model(Site)
        self.valid = ContractAssignment.objects.create(contract=self.contract, content_type=self.ct,
                                                       object_id=self.site_ok.pk)
        self.orphans = []
        for name in ('gone1', 'gone2'):
            site = Site.objects.create(name=name, slug=name)
            self.orphans.append(
                ContractAssignment.objects.create(contract=self.contract, content_type=self.ct, object_id=site.pk)
            )
            # Mimic the old behaviour: the object is deleted, its assignment stays
            Site.objects.filter(pk=site.pk)._raw_delete(Site.objects.db)

    def run_command(self, *args):
        out = StringIO()
        call_command('cleanup_orphan_assignments', *args, stdout=out)
        return out.getvalue()

    def test_dry_run_reports_and_deletes_nothing(self):
        output = self.run_command()
        for orphan in self.orphans:
            self.assertIn(str(orphan.pk), output)
            self.assertIn(str(orphan.object_id), output)
        self.assertIn('C1', output)
        self.assertEqual(ContractAssignment.objects.count(), 3)

    def test_apply_deletes_exactly_the_orphans(self):
        output = self.run_command('--apply')
        self.assertIn('2', output)
        self.assertEqual(list(ContractAssignment.objects.all()), [self.valid])
        self.assertEqual(find_orphan_assignments().orphans, [])
        self.run_command('--apply')
        self.assertEqual(ContractAssignment.objects.count(), 1)

    def test_content_type_without_model_is_listed_and_kept(self):
        stale = ContentType.objects.create(app_label='removed_app', model='thing')
        row = ContractAssignment.objects.create(contract=self.contract, content_type=stale, object_id=1)
        output = self.run_command()
        self.assertIn('removed_app', output)
        result = find_orphan_assignments()
        self.assertEqual(result.cannot_judge, [row])
        self.run_command('--apply')
        self.assertTrue(ContractAssignment.objects.filter(pk=row.pk).exists())
