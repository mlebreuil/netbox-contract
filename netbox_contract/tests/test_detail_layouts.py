"""Issue #309, user story 2: detail pages built from declarative layouts (spec 003, contracts/detail-pages.md)."""

import html
import re
from datetime import date
from unittest import mock
from urllib.parse import parse_qs, urlsplit

from dcim.models import Site
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from netbox.plugins import PluginTemplateExtension
from netbox.registry import registry
from netbox.ui.layout import SimpleLayout
from tenancy.models import Tenant
from utilities.testing import TestCase

from netbox_contract import views
from netbox_contract.models import (
    AccountingDimension,
    Contract,
    ContractAssignment,
    ContractType,
    Invoice,
    InvoiceStatusChoices,
    ServiceProvider,
)
from netbox_contract.tests.helpers import (
    make_contract,
    make_invoice,
    make_invoice_line,
    make_line,
    monthly,
    one_time,
)

DRAFT = InvoiceStatusChoices.STATUS_DRAFT
DETAIL_VIEWS = (
    views.ContractView, views.InvoiceView, views.ContractLineView, views.InvoiceLineView, views.UnitView,
    views.AccountingDimensionView, views.ContractTypeView, views.ServiceProviderView, views.ContractAssignmentView,
)
HX_GET = re.compile(r'hx-get="([^"]+)"')


def table_panels(response):
    """The HTMX tables of a page, as {list path: query parameters}."""
    panels = {}
    for url in HX_GET.findall(response.content.decode()):
        parts = urlsplit(html.unescape(url))
        if 'embedded' in parse_qs(parts.query):
            panels.setdefault(parts.path, []).append({k: v[0] for k, v in parse_qs(parts.query).items()})
    return panels


def attribute_row(label):
    return f'<th scope="row">{label}</th>'


def plugin_settings(**values):
    return mock.patch.dict(settings.PLUGINS_CONFIG['netbox_contract'], values)


class DetailPageTestCase(TestCase):
    """Common fixture: one object of each type, viewed as a superuser unless a test says otherwise."""

    def setUp(self):
        super().setUp()
        self.user.is_superuser = True
        self.user.save()
        self.contract_type = ContractType.objects.create(name='Maintenance', description='Yearly maintenance')
        self.tenant = Tenant.objects.create(name='Tenant A', slug='tenant-a')
        self.parent = make_contract(name='Parent contract')
        self.contract = make_contract(
            name='Main contract', contract_type=self.contract_type, tenant=self.tenant, parent=self.parent,
            external_reference='EXT-42', documents='https://docs.example.com/main',
        )
        self.child = make_contract(name='Child contract', parent=self.contract, billable=False)
        self.line = make_line(self.contract, monthly(), 100, description='Monthly fee')
        self.dimension = AccountingDimension.objects.create(name='Cost center', value='CC1')
        self.line.accounting_dimensions.add(self.dimension)
        self.invoice = make_invoice(self.contract, number='INV-1', amount=100, status=DRAFT)
        self.invoice_line = make_invoice_line(self.invoice, contract_line=self.line, quantity=1)
        self.site = Site.objects.create(name='Site 1', slug='site-1')
        self.assignment = ContractAssignment.objects.create(
            content_type=ContentType.objects.get_for_model(Site), object_id=self.site.pk, contract=self.contract
        )
        self.provider = ServiceProvider.objects.create(name='Telco', slug='telco', portal_url='https://telco.example')

    def get(self, obj):
        response = self.client.get(obj.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        return response


class LayoutTestCase(DetailPageTestCase):
    """T019: every detail view declares a SimpleLayout, and every page renders."""

    def test_views_declare_a_layout(self):
        for view in DETAIL_VIEWS:
            with self.subTest(view=view.__name__):
                self.assertIsInstance(view.layout, SimpleLayout)

    def test_pages_render(self):
        for obj in (self.contract, self.invoice, self.line, self.invoice_line, self.line.unit, self.dimension,
                    self.contract_type, self.provider, self.assignment):
            with self.subTest(model=obj._meta.model_name):
                self.get(obj)


class ContractPageTestCase(DetailPageTestCase):
    """T020: the contract page (US2-1 to US2-6)."""

    def test_attributes(self):
        """US2-1."""
        response = self.get(self.contract)
        for label in ('Name', 'Contract type', 'External party', 'Status', 'External reference', 'Internal party',
                      'Tenant', 'Start date', 'End date', 'Initial term', 'Renewal term', 'Notice period',
                      'Currency', 'Invoice frequency', 'Parent', 'Documents'):
            with self.subTest(label=label):
                self.assertContains(response, attribute_row(label))
        for link in (self.contract_type.get_absolute_url(), self.parent.get_absolute_url(),
                     self.contract.external_party_object.get_absolute_url(), 'https://docs.example.com/main'):
            self.assertContains(response, f'href="{link}"')
        self.assertContains(response, '12 month')
        self.assertContains(response, '90 days')
        self.assertContains(response, 'EXT-42')

    def test_no_documents_row_without_documents(self):
        self.assertNotContains(self.get(self.parent), attribute_row('Documents'))

    def test_hidden_fields(self):
        """US2-2."""
        with plugin_settings(hidden_contract_fields=['tenant', 'notice_period']):
            response = self.get(self.contract)
        self.assertNotContains(response, attribute_row('Tenant'))
        self.assertNotContains(response, attribute_row('Notice period'))
        self.assertContains(response, attribute_row('Initial term'))

    def test_deprecated_fields(self):
        """US2-3: deprecated costs and the template panel only with show_deprecated_fields; no template lookup."""
        make_invoice(self.contract, number='_invoice_template_Main contract', template=True, status=DRAFT,
                     period_start=None, period_end=None)
        with plugin_settings(show_deprecated_fields=False), CaptureQueriesContext(connection) as queries:
            response = self.get(self.contract)
        self.assertNotContains(response, 'Deprecated costs')
        self.assertNotContains(response, '_invoice_template_Main contract')
        self.assertFalse([q for q in queries.captured_queries if '"template" = true' in q['sql'].lower()
                          or '"template" = %s' in q['sql'].lower()])
        with plugin_settings(show_deprecated_fields=True):
            response = self.get(self.contract)
        self.assertContains(response, 'Deprecated costs')
        self.assertContains(response, attribute_row('Monthly recuring costs'))
        self.assertContains(response, '_invoice_template_Main contract')

    def test_values(self):
        """US2-4: values panel, "Not available" for an open-ended total, a fixed number of queries."""
        response = self.get(self.contract)
        for label in ('Billable', 'Total contract value', 'Yearly value', 'Yearly billable value'):
            self.assertContains(response, attribute_row(label))
        open_ended = make_contract(name='Open ended', end_date=None)
        make_line(open_ended, monthly(), 10, end_date=None)
        self.assertContains(self.get(open_ended), 'Not available')

        def count(contract):
            with CaptureQueriesContext(connection) as queries:
                self.get(contract)
            return len(queries)
        small = make_contract(name='Small')
        make_line(small, monthly(), 1)
        big = make_contract(name='Big')
        for i in range(6):
            make_line(big, monthly(), i + 1, description=f'Line {i}')
        self.assertEqual(count(small), count(big))

    def test_lines_locked(self):
        """US2-5: locked message and no add button on an invoiced contract; add button otherwise."""
        add_url = reverse('plugins:netbox_contract:contractline_add')
        response = self.get(self.contract)
        self.assertContains(response, 'This contract has invoices')
        self.assertNotContains(response, f'{add_url}?contract={self.contract.pk}')  # the menu has its own add link
        response = self.get(self.parent)
        self.assertNotContains(response, 'This contract has invoices')
        self.assertContains(response, f'{add_url}?contract={self.parent.pk}')

    def test_tables(self):
        """US2-6, and the column each table leaves out (edge case "column choices")."""
        panels = table_panels(self.get(self.contract))
        lines = panels[reverse('plugins:netbox_contract:contractline_list')][0]
        self.assertEqual(lines['contract_id'], str(self.contract.pk))
        self.assertEqual(lines['exclude_columns'], 'contract')
        assignments = panels[reverse('plugins:netbox_contract:contractassignment_list')][0]
        self.assertEqual(assignments['contract'], str(self.contract.pk))
        self.assertEqual(assignments['exclude_columns'], 'contract')
        children = panels[reverse('plugins:netbox_contract:contract_list')][0]
        self.assertEqual(children['parent'], str(self.contract.pk))
        self.assertEqual(children['exclude_columns'], 'parent')
        invoices = panels[reverse('plugins:netbox_contract:invoice_list')][0]
        self.assertEqual(invoices['contracts'], str(self.contract.pk))
        self.assertEqual(invoices['template'], 'False')
        self.assertEqual(invoices['exclude_columns'], 'contracts')
        add_invoice = f'{reverse("plugins:netbox_contract:invoice_add")}?contracts={self.contract.pk}'
        self.assertContains(self.get(self.contract), add_invoice)

    def test_tables_follow_view_permissions(self):
        """US2-6: a table of objects the user may not view is not shown."""
        self.user.is_superuser = False
        self.user.save()
        self.add_permissions('netbox_contract.view_contract', 'netbox_contract.view_contractline')
        panels = table_panels(self.get(self.contract))
        self.assertIn(reverse('plugins:netbox_contract:contractline_list'), panels)
        self.assertNotIn(reverse('plugins:netbox_contract:invoice_list'), panels)

    def test_missing_related_objects(self):
        """Edge case: no contract type, and an external party that no longer exists."""
        contract = make_contract(name='Orphan')
        Contract.objects.filter(pk=contract.pk).update(external_party_object_id=999999)
        self.get(contract)


class OtherPagesTestCase(DetailPageTestCase):
    """T021: the other detail pages (US2-7)."""

    def test_invoice(self):
        response = self.get(self.invoice)
        for label in ('Number', 'Date', 'Status', 'Period start', 'Period end', 'Currency', 'Amount',
                      'Invoice lines total'):
            with self.subTest(label=label):
                self.assertContains(response, attribute_row(label))
        panels = table_panels(response)
        contracts = panels[reverse('plugins:netbox_contract:contract_list')][0]
        self.assertEqual(contracts['invoice_id'], str(self.invoice.pk))
        lines = panels[reverse('plugins:netbox_contract:invoiceline_list')][0]
        self.assertEqual(lines['invoice'], str(self.invoice.pk))
        self.assertEqual(lines['exclude_columns'], 'invoice')
        add_line = f'{reverse("plugins:netbox_contract:invoiceline_add")}?invoice={self.invoice.pk}'
        self.assertContains(response, add_line)
        self.assertNotContains(response, 'This invoice is posted')

    def test_posted_invoice(self):
        posted = make_invoice(self.parent, number='INV-P', amount=10)
        response = self.get(posted)
        self.assertContains(response, 'This invoice is posted')
        self.assertNotContains(response, f'{reverse("plugins:netbox_contract:invoiceline_add")}?invoice={posted.pk}')

    def test_invoice_hidden_fields(self):
        with plugin_settings(hidden_invoice_fields=['date']):
            self.assertNotContains(self.get(self.invoice), attribute_row('Date'))

    def test_invoice_template(self):
        template = make_invoice(self.parent, number='_invoice_template_Parent', template=True, status=DRAFT,
                                period_start=None, period_end=None)
        response = self.get(template)
        self.assertContains(response, 'Invoice templates are deprecated')
        self.assertNotContains(response, attribute_row('Period start'))

    def test_contract_line(self):
        replaced = make_line(self.parent, monthly(), 50, description='Old terms', end_date=date(2025, 6, 30))
        successor = make_line(self.parent, monthly(), 55, description='New terms', start_date=date(2025, 7, 1),
                              replaces=replaced)
        response = self.get(replaced)
        for label in ('Contract', 'Description', 'Quantity', 'Unit', 'Unit price', 'Start date', 'End date',
                      'Accounting dimensions', 'Total value', 'Yearly value', 'Replaces', 'Replaced by',
                      'Invoiced at conversion'):
            with self.subTest(label=label):
                self.assertContains(response, attribute_row(label))
        self.assertContains(response, f'href="{successor.get_absolute_url()}"')
        self.assertContains(self.get(successor), f'href="{replaced.get_absolute_url()}"')
        self.assertContains(self.get(self.line), self.line.lock_message())

    def test_contract_line_without_contract_permission(self):
        """Edge case: the line page renders for a user who may not view its contract."""
        self.user.is_superuser = False
        self.user.save()
        self.add_permissions('netbox_contract.view_contractline')
        self.get(self.line)

    def test_invoice_line(self):
        response = self.get(self.invoice_line)
        for label in ('Invoice', 'Contract line', 'Quantity', 'Unit', 'Unit price', 'Amount', 'Currency',
                      'Accounting dimensions'):
            with self.subTest(label=label):
                self.assertContains(response, attribute_row(label))
        self.assertContains(response, f'href="{self.invoice.get_absolute_url()}"')
        self.assertContains(response, f'href="{self.line.get_absolute_url()}"')

    def test_unit(self):
        unit = self.line.unit
        response = self.get(unit)
        for label in ('Name', 'Description', 'Billing method', 'Months covered by one unit price'):
            self.assertContains(response, attribute_row(label))
        lines = table_panels(response)[reverse('plugins:netbox_contract:contractline_list')][0]
        self.assertEqual(lines['unit_id'], str(unit.pk))
        self.assertEqual(lines['exclude_columns'], 'unit')

    def test_accounting_dimension(self):
        response = self.get(self.dimension)
        for label in ('Name', 'Value', 'Status'):
            self.assertContains(response, attribute_row(label))

    def test_contract_type(self):
        response = self.get(self.contract_type)
        for label in ('Name', 'Description', 'Color'):
            self.assertContains(response, attribute_row(label))

    def test_service_provider(self):
        contract = make_contract(name='Provider contract')
        Contract.objects.filter(pk=contract.pk).update(
            external_party_object_type=ContentType.objects.get_for_model(ServiceProvider),
            external_party_object_id=self.provider.pk,
        )
        response = self.get(self.provider)
        for label in ('Name', 'Slug', 'Portal URL'):
            self.assertContains(response, attribute_row(label))
        self.assertContains(response, 'href="https://telco.example"')
        contracts = table_panels(response)[reverse('plugins:netbox_contract:contract_list')][0]
        self.assertEqual(contracts['service_provider_id'], str(self.provider.pk))

    def test_contract_assignment(self):
        response = self.get(self.assignment)
        for label in ('Contract', 'Object'):
            self.assertContains(response, attribute_row(label))
        self.assertContains(response, f'href="{self.contract.get_absolute_url()}"')
        self.assertContains(response, f'href="{self.site.get_absolute_url()}"')


class TableActionsTestCase(TestCase):
    """T022: contract line actions decided per line in the list the contract page loads (US2-8)."""

    def setUp(self):
        super().setUp()
        self.add_permissions(
            'netbox_contract.view_contractline', 'netbox_contract.change_contractline',
            'netbox_contract.delete_contractline', 'netbox_contract.amend_contractline',
        )
        self.invoiced = make_contract(name='Invoiced')
        self.recurring = make_line(self.invoiced, monthly(), 100, description='Recurring')
        self.setup_fee = make_line(self.invoiced, one_time(), 50, description='Setup')
        make_invoice(self.invoiced, number='INV-1', amount=150)
        self.open = make_contract(name='Open')
        self.open_line = make_line(self.open, one_time(), 20, description='Open setup')

    def actions(self, line, content):
        return {
            action: reverse(f'plugins:netbox_contract:contractline_{action}', args=[line.pk]) in content
            for action in ('edit', 'amend', 'delete')
        }

    def list_content(self, **params):
        query = '&'.join(f'{k}={v}' for k, v in params.items())
        response = self.client.get(f'{reverse("plugins:netbox_contract:contractline_list")}?{query}')
        self.assertEqual(response.status_code, 200)
        return response.content.decode()

    def test_invoiced_contract(self):
        content = self.list_content(contract_id=self.invoiced.pk)
        self.assertEqual(self.actions(self.recurring, content), {'edit': True, 'amend': True, 'delete': False})
        self.assertEqual(self.actions(self.setup_fee, content), {'edit': True, 'amend': False, 'delete': False})

    def test_contract_without_invoice(self):
        content = self.list_content(contract_id=self.open.pk)
        self.assertEqual(self.actions(self.open_line, content), {'edit': True, 'amend': False, 'delete': True})

    def test_mixed_list(self):
        """Edge case: a list across contracts offers Delete only on the unlocked lines."""
        content = self.list_content()
        self.assertFalse(self.actions(self.recurring, content)['delete'])
        self.assertTrue(self.actions(self.open_line, content)['delete'])


class MarkerContent(PluginTemplateExtension):
    models = ['netbox_contract.contract']

    def left_page(self):
        return '<p>marker-left</p>'

    def right_page(self):
        return '<p>marker-right</p>'

    def full_width_page(self):
        return '<p>marker-full</p>'


class PluginContentTestCase(DetailPageTestCase):
    """T023: the three plugin content areas (US2-9)."""

    def setUp(self):
        super().setUp()
        extensions = registry['plugins']['template_extensions']['netbox_contract.contract']
        extensions.append(MarkerContent)
        self.addCleanup(extensions.remove, MarkerContent)

    def test_areas(self):
        response = self.get(self.contract)
        for marker in ('marker-left', 'marker-right', 'marker-full'):
            self.assertContains(response, marker)


class ContractFilterTestCase(DetailPageTestCase):
    """T024: contracts of an invoice (research D5)."""

    def test_ui_list(self):
        response = self.client.get(f'{reverse("plugins:netbox_contract:contract_list")}?invoice_id={self.invoice.pk}')
        self.assertContains(response, self.contract.get_absolute_url())
        self.assertNotContains(response, self.child.get_absolute_url())  # the parent is linked by the Parent column

    def test_rest(self):
        self.user.is_superuser = True
        self.user.save()
        url = reverse('plugins-api:netbox_contract-api:contract-list')
        response = self.client.get(f'{url}?invoice_id={self.invoice.pk}')
        self.assertEqual([item['id'] for item in response.json()['results']], [self.contract.pk])
        other = make_invoice(self.parent, number='INV-2', amount=1, status=DRAFT)
        self.assertEqual(Invoice.objects.filter(contracts=self.parent).count(), 1)
        response = self.client.get(f'{url}?invoice_id={other.pk}')
        self.assertEqual([item['id'] for item in response.json()['results']], [self.parent.pk])
