"""Spec 005: breadcrumb trails declared in the layouts of the four detail views (contracts/breadcrumbs.md)."""

import html
import re
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from utilities.testing import TestCase

from netbox_contract import views
from netbox_contract.models import Contract, ServiceProvider
from netbox_contract.tests.helpers import (
    make_contract,
    make_invoice,
    make_invoice_line,
    make_line,
    make_provider,
    monthly,
)

LIST = 'plugins:netbox_contract:'
CRUMBS = re.compile(r'<ol class="breadcrumb".*?</ol>', re.S)
ITEM = re.compile(r'<li class="breadcrumb-item">(.*?)</li>', re.S)
LINK = re.compile(r'<a href="([^"]*)"[^>]*>(.*?)</a>', re.S)
TEMPLATES = Path(views.__file__).parent / 'templates' / 'netbox_contract'


def trail(response):
    """The breadcrumb trail of a page as [(text, href or None), ...]."""
    ol = CRUMBS.search(response.content.decode()).group(0)
    entries = []
    for item in ITEM.findall(ol):
        link = LINK.search(item)
        if link:
            entries.append((html.unescape(link.group(2).strip()), html.unescape(link.group(1))))
        else:
            entries.append((html.unescape(re.sub(r'<[^>]+>', '', item).strip()), None))
    return entries


def query(href):
    return {k: v[0] for k, v in parse_qs(urlsplit(href).query).items()}


class BreadcrumbTestCase(TestCase):
    def setUp(self):
        super().setUp()
        self.user.is_superuser = True
        self.user.save()
        self.sp = ServiceProvider.objects.create(name='Telco', slug='telco')
        self.circuit_provider = make_provider()
        self.contract = make_contract(name='Circuit contract')
        self.sp_contract = make_contract(name='Telco contract')
        Contract.objects.filter(pk=self.sp_contract.pk).update(
            external_party_object_type=ContentType.objects.get_for_model(ServiceProvider),
            external_party_object_id=self.sp.pk,
        )
        self.sp_contract.refresh_from_db()
        self.orphan_contract = make_contract(name='Free contract')
        Contract.objects.filter(pk=self.orphan_contract.pk).update(
            external_party_object_type=None, external_party_object_id=None
        )
        self.orphan_contract.refresh_from_db()
        self.line = make_line(self.contract, monthly(), 100, description='Monthly fee')
        self.invoice = make_invoice(self.contract, number='INV-1')
        self.invoice.contracts.add(self.sp_contract)
        self.invoice_line = make_invoice_line(self.invoice, contract_line=self.line, quantity=1)
        self.empty_invoice = make_invoice(None, number='INV-0')

    def trail(self, obj, suffix=''):
        response = self.client.get(obj.get_absolute_url() + suffix)
        self.assertEqual(response.status_code, 200)
        return trail(response)

    # US1: contract
    def test_contract_trail_circuit_provider(self):
        entries = self.trail(self.contract)
        self.assertEqual(entries[0], ('Contracts', reverse(LIST + 'contract_list')))
        self.assertEqual([t for t, _ in entries[1:]], ['Provider A'])
        self.assertEqual(query(entries[1][1]), {'provider_id': str(self.circuit_provider.pk)})

    def test_contract_trail_service_provider(self):
        entries = self.trail(self.sp_contract)
        self.assertEqual([t for t, _ in entries[1:]], ['Telco'])
        self.assertEqual(query(entries[1][1]), {'service_provider_id': str(self.sp.pk)})

    def test_contract_trail_without_party(self):
        entries = self.trail(self.orphan_contract)
        self.assertEqual(len(entries), 1)

    # US1: contract line, invoice line
    def test_contract_line_trail(self):
        entries = self.trail(self.line)
        self.assertEqual(entries[0], ('Contract Lines', reverse(LIST + 'contractline_list')))
        self.assertEqual(entries[1][0], 'Circuit contract')
        self.assertEqual(query(entries[1][1]), {'contract_id': str(self.contract.pk)})

    def test_invoice_line_trail(self):
        entries = self.trail(self.invoice_line)
        self.assertEqual(entries[0], ('Invoice Lines', reverse(LIST + 'invoiceline_list')))
        self.assertEqual(entries[1][0], 'INV-1')
        self.assertEqual(query(entries[1][1]), {'invoice': str(self.invoice.pk)})

    # Each link opens a list that contains the object
    def test_links_open_lists_containing_the_object(self):
        cases = [
            (self.contract, 1, 'Circuit contract'),
            (self.sp_contract, 1, 'Telco contract'),
            (self.line, 1, 'Monthly fee'),
            (self.invoice_line, 1, 'INV-1'),
            (self.invoice, 1, 'INV-1'),
        ]
        for obj, index, expected in cases:
            with self.subTest(obj=str(obj)):
                href = self.trail(obj)[index][1]
                response = self.client.get(href)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, expected)

    # US1: tabs show the same trail
    def test_tab_pages_show_the_same_trail(self):
        for obj in (self.contract, self.line, self.invoice, self.invoice_line):
            with self.subTest(obj=str(obj)):
                for tab in ('changelog/', 'journal/'):
                    self.assertEqual(self.trail(obj, tab), self.trail(obj))

    # FR-008: shown whatever the permissions on the target
    def test_view_only_user_sees_entries(self):
        self.user.is_superuser = False
        self.user.save()
        self.add_permissions('netbox_contract.view_contract')
        entries = self.trail(self.contract)
        self.assertEqual(entries[1][0], 'Provider A')

    # US2
    def test_invoice_trail_one_entry_per_contract(self):
        entries = self.trail(self.invoice)
        self.assertEqual(entries[0], ('Invoices', reverse(LIST + 'invoice_list')))
        self.assertEqual(len(entries), 3)
        contract_entries = entries[1:]
        self.assertEqual([t for t, _ in contract_entries], ['Circuit contract', 'Telco contract'])
        self.assertEqual(
            [query(h) for _, h in contract_entries],
            [{'contracts': str(self.contract.pk)}, {'contracts': str(self.sp_contract.pk)}],
        )

    def test_invoice_without_contract_has_no_contract_entry(self):
        self.assertEqual(len(self.trail(self.empty_invoice)), 1)

    # US3
    def test_page_templates_are_removed(self):
        for name in ('contract.html', 'contractline.html', 'invoice.html', 'invoiceline.html'):
            self.assertFalse((TEMPLATES / name).exists(), name)
