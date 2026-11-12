"""The create_demo_data command (issue #322): demo scenarios for development."""

from decimal import Decimal
from io import StringIO

from dcim.models import Site
from django.core.management import CommandError, call_command
from django.test import TestCase, override_settings
from extras.models import Tag

from netbox_contract.demo import SCENARIOS, TAG_SLUG
from netbox_contract.models import (
    BillingMethodChoices,
    Contract,
    ContractAssignment,
    ContractLine,
    Invoice,
    InvoiceLine,
    InvoiceStatusChoices,
    Unit,
)


def run(*args):
    out = StringIO()
    call_command('create_demo_data', *args, stdout=out)
    return out.getvalue()


def counts():
    return {
        model.__name__: model.objects.count()
        for model in (Contract, ContractLine, Invoice, InvoiceLine, ContractAssignment, Unit)
    }


@override_settings(DEVELOPER=True)
class CreateDemoDataTestCase(TestCase):
    def test_runs_on_an_empty_database(self):
        run()
        names = set(Contract.objects.values_list('name', flat=True))
        self.assertTrue({'Demo: recurring lines', 'Demo: amendments', 'Demo: open-ended'} <= names)
        self.assertGreaterEqual(Contract.objects.count(), len(SCENARIOS))

    def test_covers_the_feature(self):
        run()
        methods = set(Unit.objects.values_list('billing_method', flat=True))
        self.assertEqual(methods, {choice[0] for choice in BillingMethodChoices.CHOICES})
        statuses = set(Invoice.objects.filter(template=False).values_list('status', flat=True))
        self.assertEqual(statuses, {choice[0] for choice in InvoiceStatusChoices.CHOICES})
        self.assertTrue(Contract.objects.filter(end_date__isnull=True).exists())
        self.assertTrue(Contract.objects.filter(parent__isnull=False, billable=False).exists())
        self.assertTrue(Contract.objects.filter(parent__isnull=False, billable=True).exists())
        self.assertTrue(ContractLine.objects.filter(replaces__isnull=False).exists())
        # legacy data: deprecated costs and a template, without contract lines
        legacy = Contract.objects.filter(name__startswith='Demo: legacy')
        self.assertTrue(legacy.exists())
        self.assertFalse(ContractLine.objects.filter(contract__in=legacy).exists())
        self.assertTrue(Invoice.objects.filter(template=True).exists())
        self.assertTrue(InvoiceLine.objects.filter(accounting_dimensions__isnull=False).exists())

    def test_amounts_come_from_the_lines(self):
        run()
        invoice = Invoice.objects.get(number='DEMO-REC-2025-01')
        self.assertEqual(invoice.status, InvoiceStatusChoices.STATUS_POSTED)
        # 1000 + 4 x 45.50 monthly, and the yearly 1200 for one month
        self.assertEqual(invoice.total_invoicelines_amount, Decimal('1282.00'))
        self.assertEqual(invoice.amount, invoice.total_invoicelines_amount)

    def test_everything_is_tagged(self):
        run()
        tag = Tag.objects.get(slug=TAG_SLUG)
        for model in (Contract, ContractLine, Invoice, InvoiceLine, Unit):
            self.assertFalse(model.objects.exclude(tags=tag).exists(), model.__name__)

    def test_is_idempotent(self):
        run()
        before = counts()
        output = run()
        self.assertEqual(counts(), before)
        self.assertIn('Skipped', output)

    def test_reset_recreates_the_data(self):
        run()
        before = counts()
        output = run('--reset')
        self.assertEqual(counts(), before)
        self.assertIn('Deleted', output)

    def test_reset_keeps_other_data(self):
        other = Contract.objects.create(name='Mine', internal_party='default', status='active', currency='usd',
                                        external_party_object_type_id=1, external_party_object_id=1)
        run()
        run('--reset')
        self.assertTrue(Contract.objects.filter(pk=other.pk).exists())

    def test_assigns_netbox_objects_found_by_criteria(self):
        site = Site.objects.create(name='Demo site', slug='demo-site')
        run()
        self.assertTrue(ContractAssignment.objects.filter(object_id=site.pk).exists())

    @override_settings(DEVELOPER=False)
    def test_refuses_without_developer_mode(self):
        with self.assertRaises(CommandError):
            run()
        self.assertFalse(Contract.objects.exists())
