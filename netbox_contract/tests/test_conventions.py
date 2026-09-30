"""Alignment with the NetBox 4.6 plugin conventions (issue #308, specs/002-netbox-46-conventions)."""

import inspect
from datetime import date
from pathlib import Path
from unittest import mock

from dcim.models import Site
from django import forms as django_forms
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.messages import get_messages
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import resolve, reverse
from extras.models import JournalEntry
from netbox.forms import NetBoxModelBulkEditForm, NetBoxModelFilterSetForm, NetBoxModelForm, NetBoxModelImportForm
from netbox.registry import registry
from utilities.forms.widgets import FilterModifierWidget, MarkdownWidget
from utilities.testing import TestCase

from netbox_contract import filtersets, forms
from netbox_contract.models import (
    AccountingDimension,
    Contract,
    ContractAssignment,
    ContractType,
    InvoiceStatusChoices,
    ServiceProvider,
)
from netbox_contract.tests.helpers import make_contract, make_invoice, make_invoice_line, make_line, monthly

# Route names, addresses and views before the change (contracts/routes.md); pk 1 where the address has one
ROUTES = (
    ('serviceprovider_list', 'serviceproviders/', 'ServiceProviderListView'),
    ('serviceprovider_add', 'serviceproviders/add/', 'ServiceProviderEditView'),
    ('serviceprovider_bulk_import', 'serviceproviders/import/', 'ServiceProviderBulkImportView'),
    ('serviceprovider_bulk_edit', 'serviceproviders/edit/', 'ServiceProviderBulkEditView'),
    ('serviceprovider_bulk_delete', 'serviceproviders/delete/', 'ServiceProviderBulkDeleteView'),
    ('serviceprovider', 'serviceproviders/1/', 'ServiceProviderView'),
    ('serviceprovider_edit', 'serviceproviders/1/edit/', 'ServiceProviderEditView'),
    ('serviceprovider_delete', 'serviceproviders/1/delete/', 'ServiceProviderDeleteView'),
    ('serviceprovider_changelog', 'serviceproviders/1/changelog/', 'ObjectChangeLogView'),
    ('contract_list', 'contracts/', 'ContractListView'),
    ('contract_add', 'contracts/add/', 'ContractEditView'),
    ('contract_bulk_import', 'contracts/import/', 'ContractBulkImportView'),
    ('contract_bulk_edit', 'contracts/edit/', 'ContractBulkEditView'),
    ('contract_bulk_delete', 'contracts/delete/', 'ContractBulkDeleteView'),
    ('contract', 'contracts/1/', 'ContractView'),
    ('contract_edit', 'contracts/1/edit/', 'ContractEditView'),
    ('contract_delete', 'contracts/1/delete/', 'ContractDeleteView'),
    ('contract_changelog', 'contracts/1/changelog/', 'ObjectChangeLogView'),
    ('unit_list', 'units/', 'UnitListView'),
    ('unit_add', 'units/add/', 'UnitEditView'),
    ('unit_bulk_import', 'units/import/', 'UnitBulkImportView'),
    ('unit_bulk_edit', 'units/edit/', 'UnitBulkEditView'),
    ('unit_bulk_delete', 'units/delete/', 'UnitBulkDeleteView'),
    ('unit', 'units/1/', 'UnitView'),
    ('unit_edit', 'units/1/edit/', 'UnitEditView'),
    ('unit_delete', 'units/1/delete/', 'UnitDeleteView'),
    ('unit_changelog', 'units/1/changelog/', 'ObjectChangeLogView'),
    ('contractline_list', 'contract-lines/', 'ContractLineListView'),
    ('contractline_add', 'contract-lines/add/', 'ContractLineEditView'),
    ('contractline_bulk_import', 'contract-lines/import/', 'ContractLineBulkImportView'),
    ('contractline_bulk_edit', 'contract-lines/edit/', 'ContractLineBulkEditView'),
    ('contractline_bulk_delete', 'contract-lines/delete/', 'ContractLineBulkDeleteView'),
    ('contractline', 'contract-lines/1/', 'ContractLineView'),
    ('contractline_edit', 'contract-lines/1/edit/', 'ContractLineEditView'),
    ('contractline_delete', 'contract-lines/1/delete/', 'ContractLineDeleteView'),
    ('contractline_changelog', 'contract-lines/1/changelog/', 'ObjectChangeLogView'),
    ('invoice_list', 'invoices/', 'InvoiceListView'),
    ('invoice_add', 'invoices/add/', 'InvoiceEditView'),
    ('invoice_lines_preview', 'invoices/lines-preview/', 'InvoiceLinesPreviewView'),
    ('invoice_bulk_import', 'invoices/import/', 'InvoiceBulkImportView'),
    ('invoice_bulk_edit', 'invoices/edit/', 'InvoiceBulkEditView'),
    ('invoice_bulk_delete', 'invoices/delete/', 'InvoiceBulkDeleteView'),
    ('invoice', 'invoices/1/', 'InvoiceView'),
    ('invoice_edit', 'invoices/1/edit/', 'InvoiceEditView'),
    ('invoice_delete', 'invoices/1/delete/', 'InvoiceDeleteView'),
    ('invoice_changelog', 'invoices/1/changelog/', 'ObjectChangeLogView'),
    ('contractassignment_list', 'assignments/', 'ContractAssignmentListView'),
    ('contractassignment_add', 'assignments/add/', 'ContractAssignmentEditView'),
    ('contractassignment_bulk_import', 'assignments/import/', 'ContractAssignmentBulkImportView'),
    ('contractassignment_bulk_edit', 'assignments/edit/', 'ContractAssignmentBulkEditView'),
    ('contractassignment_bulk_delete', 'assignments/delete/', 'ContractAssignmentBulkDeleteView'),
    ('contractassignment', 'assignments/1/', 'ContractAssignmentView'),
    ('contractassignment_edit', 'assignments/1/edit/', 'ContractAssignmentEditView'),
    ('contractassignment_delete', 'assignments/1/delete/', 'ContractAssignmentDeleteView'),
    ('contractassignment_changelog', 'assignments/1/changelog/', 'ObjectChangeLogView'),
    ('invoiceline_list', 'invoiceline/', 'InvoiceLineListView'),
    ('invoiceline_add', 'invoiceline/add/', 'InvoiceLineEditView'),
    ('invoiceline_bulk_import', 'invoiceline/import/', 'InvoiceLineBulkImportView'),
    ('invoiceline_bulk_edit', 'invoiceline/edit/', 'InvoiceLineBulkEditView'),
    ('invoiceline_bulk_delete', 'invoiceline/delete/', 'InvoiceLineBulkDeleteView'),
    ('invoiceline', 'invoiceline/1/', 'InvoiceLineView'),
    ('invoiceline_edit', 'invoiceline/1/edit/', 'InvoiceLineEditView'),
    ('invoiceline_delete', 'invoiceline/1/delete/', 'InvoiceLineDeleteView'),
    ('invoiceline_changelog', 'invoiceline/1/changelog/', 'ObjectChangeLogView'),
    ('accountingdimension_list', 'accountingdimension/', 'AccountingDimensionListView'),
    ('accountingdimension_add', 'accountingdimension/add/', 'AccountingDimensionEditView'),
    ('accountingdimension_bulk_import', 'accountingdimension/import/', 'AccountingDimensionBulkImportView'),
    ('accountingdimension_bulk_edit', 'accountingdimension/edit/', 'AccountingDimensionBulkEditView'),
    ('accountingdimension_bulk_delete', 'accountingdimension/delete/', 'AccountingDimensionBulkDeleteView'),
    ('accountingdimension', 'accountingdimension/1/', 'AccountingDimensionView'),
    ('accountingdimension_edit', 'accountingdimension/1/edit/', 'AccountingDimensionEditView'),
    ('accountingdimension_delete', 'accountingdimension/1/delete/', 'AccountingDimensionDeleteView'),
    ('accountingdimension_changelog', 'accountingdimension/1/changelog/', 'ObjectChangeLogView'),
    ('contracttype_list', 'contracttype/', 'ContractTypeListView'),
    ('contracttype_add', 'contracttype/add/', 'ContractTypeEditView'),
    ('contracttype', 'contracttype/1/', 'ContractTypeView'),
    ('contracttype_edit', 'contracttype/1/edit/', 'ContractTypeEditView'),
    ('contracttype_bulk_edit', 'contracttype/edit/', 'ContractTypeBulkEditView'),
    ('contracttype_delete', 'contracttype/1/delete/', 'ContractTypeDeleteView'),
    ('contracttype_bulk_delete', 'contracttype/delete/', 'ContractTypeBulkDeleteView'),
    ('contracttype_bulk_import', 'contracttype/import/', 'ContractTypeBulkImportView'),
    ('contracttype_changelog', 'contracttype/1/changelog/', 'ObjectChangeLogView'),
)


def make_objects():
    """One object of each of the nine plugin models, keyed by model name."""
    contract = make_contract(name='Conventions contract')
    line = make_line(contract, monthly(), '100')
    invoice = make_invoice(contract, number='CONV-1', status=InvoiceStatusChoices.STATUS_DRAFT, amount=100)
    site = Site.objects.create(name='Conventions site', slug='conventions-site')
    return {
        'contract': contract,
        'contractline': line,
        'unit': line.unit,
        'invoice': invoice,
        'invoiceline': make_invoice_line(invoice, amount=100),
        'contracttype': ContractType.objects.create(name='Conventions type'),
        'accountingdimension': AccountingDimension.objects.create(name='Cost center', value='CC1'),
        'serviceprovider': ServiceProvider.objects.create(name='Conventions provider', slug='conventions-provider'),
        'contractassignment': ContractAssignment.objects.create(
            content_type=ContentType.objects.get_for_model(Site), object_id=site.pk, contract=contract
        ),
    }


class RouteTestCase(TestCase):
    """
    Every route name of the plugin keeps its address and view (FR-003, SC-003). This is a guard for the URL
    refactor: it passes before and after the change.
    """

    def test_routes_are_unchanged(self):
        for name, address, view in ROUTES:
            with self.subTest(route=name):
                kwargs = {'pk': 1} if '/1/' in address else {}
                url = reverse(f'plugins:netbox_contract:{name}', kwargs=kwargs)
                self.assertEqual(url, f'/plugins/contracts/{address}')
                self.assertEqual(resolve(url).func.view_class.__name__, view)


class JournalTabTestCase(TestCase):
    """
    The detail page of every plugin model shows the Journal and Changelog tabs (FR-001, SC-001, US1-1). The
    Journal view is registered by NetBox core through register_model_view, so this also shows that views
    registered by other code attach to the four models wired by hand before (FR-002 and its edge case).
    """

    @classmethod
    def setUpTestData(cls):
        cls.objects = make_objects()

    def setUp(self):
        super().setUp()
        self.user.is_superuser = True
        self.user.save()

    def test_journal_and_changelog_tabs(self):
        for model_name, obj in self.objects.items():
            with self.subTest(model=model_name):
                response = self.client.get(obj.get_absolute_url())
                self.assertHttpStatus(response, 200)
                for tab in ('journal', 'changelog'):
                    url = reverse(f'plugins:netbox_contract:{model_name}_{tab}', kwargs={'pk': obj.pk})
                    self.assertContains(response, url)

    def test_journal_entry_listed_on_its_tab(self):
        line = self.objects['invoiceline']
        JournalEntry.objects.create(assigned_object=line, created_by=self.user, comments='Checked with finance')
        response = self.client.get(reverse('plugins:netbox_contract:invoiceline_journal', kwargs={'pk': line.pk}))
        self.assertHttpStatus(response, 200)
        self.assertContains(response, 'Checked with finance')

    def test_existing_extra_views_kept(self):
        line = self.objects['contractline']
        amend_url = reverse('plugins:netbox_contract:contractline_amend', kwargs={'pk': line.pk})
        self.assertContains(self.client.get(line.get_absolute_url()), amend_url)
        site_pk = self.objects['contractassignment'].object_id
        self.assertEqual(resolve(reverse('dcim:site_contracts', kwargs={'pk': site_pk})).url_name, 'site_contracts')


FILTERSETS = (
    ('contract', filtersets.ContractFilterSet, forms.ContractFilterForm),
    ('contractline', filtersets.ContractLineFilterSet, forms.ContractLineFilterForm),
    ('contracttype', filtersets.ContractTypeFilterSet, forms.ContractTypeFilterForm),
    ('contractassignment', filtersets.ContractAssignmentFilterSet, forms.ContractAssignmentFilterForm),
    ('invoice', filtersets.InvoiceFilterSet, forms.InvoiceFilterForm),
    ('invoiceline', filtersets.InvoiceLineFilterSet, forms.InvoiceLineFilterForm),
    ('unit', filtersets.UnitFilterSet, forms.UnitFilterForm),
    ('accountingdimension', filtersets.AccountingDimensionFilterSet, forms.AccountingDimensionFilterForm),
    ('serviceprovider', filtersets.ServiceProviderFilterSet, forms.ServiceProviderFilterForm),
)


class FilterModifierTestCase(TestCase):
    """The filter forms offer NetBox's lookup modifiers (FR-004, FR-005, SC-002, US2)."""

    def test_filtersets_registered(self):
        for model_name, filterset, _form in FILTERSETS:
            with self.subTest(model=model_name):
                self.assertIs(registry['filtersets'].get(f'netbox_contract.{model_name}'), filterset)

    def test_every_filter_form_offers_modifiers(self):
        for model_name, _filterset, form_class in FILTERSETS:
            with self.subTest(model=model_name):
                form = form_class()
                modified = [name for name, field in form.fields.items()
                            if isinstance(field.widget, FilterModifierWidget)]
                # Not always 'tag': the contract type, assignment and dimension filter forms have no tag filter
                self.assertTrue(modified)
        form = forms.ContractFilterForm()
        self.assertIsInstance(form.fields['external_reference'].widget, FilterModifierWidget)

    def test_contains_modifier_filters_the_list(self):
        wanted = make_contract(name='Fiber', external_reference='ALPHA-FIBER-01')
        make_contract(name='Power', external_reference='BETA-POWER-02')
        self.add_permissions('netbox_contract.view_contract')
        response = self.client.get(f"{reverse('plugins:netbox_contract:contract_list')}?external_reference__ic=FIBER")
        self.assertHttpStatus(response, 200)
        self.assertEqual([contract.pk for contract in response.context['table'].data], [wanted.pk])

    def test_existing_query_strings_unchanged(self):
        make_contract(name='Dollars', currency='usd')
        make_contract(name='Euros', currency='eur')
        self.add_permissions('netbox_contract.view_contract')
        response = self.client.get(f"{reverse('plugins:netbox_contract:contract_list')}?status=active&currency=usd")
        expected = filtersets.ContractFilterSet({'status': ['active'], 'currency': ['usd']}, Contract.objects.all()).qs
        listed = {contract.pk for contract in response.context['table'].data}
        self.assertEqual(listed, set(expected.values_list('pk', flat=True)))


# Fields NetBox renders outside the form sections
OUTSIDE_SECTIONS = {
    'comments', 'changelog_message', 'background_job', 'add_tags', 'remove_tags', 'owner', 'owner_group',
}


def plugin_forms():
    """The model, bulk-edit and filter form classes of the plugin (import forms have no sections)."""
    bases = (NetBoxModelForm, NetBoxModelBulkEditForm, NetBoxModelFilterSetForm)
    return [
        cls for _name, cls in inspect.getmembers(forms, inspect.isclass)
        if cls.__module__ == forms.__name__ and issubclass(cls, bases) and not issubclass(cls, NetBoxModelImportForm)
    ]


def section_names(form):
    return [name for fieldset in form.fieldsets for name in fieldset.items]


class FormSectionsTestCase(TestCase):
    """Forms group their fields into titled sections, with the same fields as before (FR-006 to FR-008, US3)."""

    def test_every_visible_field_in_exactly_one_section(self):
        classes = plugin_forms()
        self.assertEqual(len(classes), 27)
        for form_class in classes:
            with self.subTest(form=form_class.__name__):
                form = form_class()
                self.assertTrue(form.fieldsets)
                names = section_names(form)
                visible = [
                    name for name, field in form.fields.items()
                    if not field.widget.is_hidden and not name.startswith('cf_') and name not in OUTSIDE_SECTIONS
                ]
                for name in visible:
                    self.assertEqual(names.count(name), 1, name)
                for name in names:
                    self.assertIn(name, visible)
                for fieldset in form.fieldsets:
                    self.assertTrue(fieldset.items)
                if isinstance(form, NetBoxModelFilterSetForm):
                    expected = ('q', 'filter_id', 'tag') if 'tag' in form.fields else ('q', 'filter_id')
                    self.assertEqual(tuple(form.fieldsets[0].items), expected)

    def test_hidden_contract_fields_are_in_no_section(self):
        # Optional fields only: the setting never hides a required field
        hidden = ['external_reference', 'documents']
        with mock.patch.dict(settings.PLUGINS_CONFIG['netbox_contract'], {'hidden_contract_fields': hidden}):
            form = forms.ContractForm()
            for name in hidden:
                self.assertTrue(form.fields[name].widget.is_hidden)
                self.assertNotIn(name, section_names(form))
            self.add_permissions('netbox_contract.add_contract')
            response = self.client.get(reverse('plugins:netbox_contract:contract_add'))
        content = response.content.decode()
        for name in hidden:
            self.assertEqual(content.count(f'name="{name}"'), 1, name)

    def deprecated_sections(self, form_class):
        return [fieldset for fieldset in form_class().fieldsets if str(fieldset.name) == 'Deprecated']

    def test_deprecated_section_follows_the_setting(self):
        deprecated = {
            forms.ContractForm: ['mrc', 'yrc', 'nrc'],
            forms.InvoiceForm: ['template'],
            forms.InvoiceBulkEditForm: ['template'],
        }
        with mock.patch.dict(settings.PLUGINS_CONFIG['netbox_contract'], {'show_deprecated_fields': False}):
            for form_class in deprecated:
                with self.subTest(form=form_class.__name__, setting=False):
                    self.assertEqual(self.deprecated_sections(form_class), [])
            # The invoice filter form never removed its template filter
            self.assertEqual(len(self.deprecated_sections(forms.InvoiceFilterForm)), 1)
        with mock.patch.dict(settings.PLUGINS_CONFIG['netbox_contract'], {'show_deprecated_fields': True}):
            for form_class, names in deprecated.items():
                with self.subTest(form=form_class.__name__, setting=True):
                    sections = self.deprecated_sections(form_class)
                    self.assertEqual(len(sections), 1)
                    self.assertEqual(list(sections[0].items), names)
        self.assertEqual(self.deprecated_sections(forms.ContractBulkEditForm), [])

    def test_contract_type_description_is_plain_text(self):
        for form_class in (forms.ContractTypeFilterForm, forms.ContractTypeCSVForm, forms.ContractTypeBulkEditForm):
            with self.subTest(form=form_class.__name__):
                field = form_class().fields['description']
                # The filter form wraps the widget with the lookup modifier selector
                widget = getattr(field.widget, 'original_widget', field.widget)
                self.assertIsInstance(widget, django_forms.TextInput)
                self.assertNotIsInstance(widget, MarkdownWidget)
                self.assertFalse(field.required)
        self.assertEqual(tuple(forms.ContractTypeBulkEditForm.nullable_fields), ('description',))


class EditViewTestCase(TestCase):
    """The invoice and invoice line edit screens answer like core edit views (FR-009, FR-010, SC-006, US4)."""

    @classmethod
    def setUpTestData(cls):
        cls.contract = make_contract(name='Edit views contract')
        make_line(cls.contract, monthly(), '100')
        cls.invoice = make_invoice(cls.contract, number='EDIT-1', status=InvoiceStatusChoices.STATUS_DRAFT,
                                   amount=300, period_start=date(2024, 12, 1), period_end=date(2024, 12, 31))

    def setUp(self):
        super().setUp()
        self.user.is_superuser = True
        self.user.save()

    def get(self, name, query='', **kwargs):
        url = reverse(f'plugins:netbox_contract:{name}', kwargs=kwargs)
        return self.client.get(f'{url}?{query}' if query else url, **getattr(self, 'headers', {}))

    def template_names(self, response):
        return [template.name for template in response.templates]

    def test_quick_add(self):
        response = self.get('invoice_add', f'contracts={self.contract.pk}&_quickadd=true')
        self.assertIn('htmx/quick_add.html', self.template_names(response))
        form = response.context['form']
        self.assertEqual(form.prefix, 'quickadd')
        self.assertEqual(form.initial['period_start'], date(2025, 1, 1))
        response = self.get('invoiceline_add', f'invoice={self.invoice.pk}&_quickadd=true')
        self.assertIn('htmx/quick_add.html', self.template_names(response))
        self.assertEqual(response.context['form'].initial['quantity'], 1)

    def test_htmx_partial(self):
        self.headers = {'HTTP_HX_REQUEST': 'true'}
        for name, query in (('invoice_add', f'contracts={self.contract.pk}'),
                            ('invoiceline_add', f'invoice={self.invoice.pk}')):
            with self.subTest(view=name):
                response = self.get(name, query)
                self.assertIn('htmx/form.html', self.template_names(response))
                self.assertNotIn('generic/object_edit.html', self.template_names(response))

    def test_address_values_win(self):
        initial = self.get('invoice_add', f'contracts={self.contract.pk}&date=2026-01-15').context['form'].initial
        self.assertEqual(str(initial['date']), '2026-01-15')
        self.assertEqual(initial['period_start'], date(2025, 1, 1))
        self.assertEqual(initial['currency'], 'usd')
        initial = self.get('invoiceline_add', f'invoice={self.invoice.pk}&quantity=3').context['form'].initial
        self.assertEqual(str(initial['quantity']), '3')
        self.assertEqual(initial['currency'], 'usd')

    def test_no_prefill_on_edit(self):
        other = make_contract(name='Other contract', currency='eur')
        initial = self.get('invoice_edit', f'contracts={other.pk}', pk=self.invoice.pk).context['form'].initial
        self.assertEqual(initial['date'], self.invoice.date)
        self.assertEqual(initial['period_start'], date(2024, 12, 1))
        self.assertEqual(initial['currency'], 'usd')
        line = make_invoice_line(self.invoice, amount=100)
        other_invoice = make_invoice(other, number='EDIT-2', status=InvoiceStatusChoices.STATUS_DRAFT, amount=999)
        initial = self.get('invoiceline_edit', f'invoice={other_invoice.pk}', pk=line.pk).context['form'].initial
        self.assertEqual(initial['currency'], 'usd')

    def test_invalid_or_unknown_contract(self):
        for value in ('abc', '999999'):
            with self.subTest(contracts=value):
                response = self.get('invoice_add', f'contracts={value}')
                self.assertHttpStatus(response, 200)
                self.assertIsNone(response.context['form'].initial.get('period_start'))

    def test_invoicing_error_keeps_the_rest_of_the_prefill(self):
        child = make_contract(name='Not billable', parent=self.contract, billable=False)
        response = self.get('invoice_add', f'contracts={child.pk}')
        messages = [str(message) for message in get_messages(response.wsgi_request)]
        self.assertTrue(any('not billable' in message for message in messages), messages)
        initial = response.context['form'].initial
        self.assertEqual(initial['period_start'], date(2025, 1, 1))
        self.assertEqual(initial['currency'], 'usd')
        self.assertIsNone(initial.get('amount'))


class ContractTemplateSectionTestCase(TestCase):
    """The deprecated invoice template is looked up on the contract page only when deprecated fields are shown."""

    @classmethod
    def setUpTestData(cls):
        cls.contract = make_contract(name='Templated contract')
        make_invoice(cls.contract, number='TEMPLATE-NUMBER-1', status=InvoiceStatusChoices.STATUS_DRAFT, template=True)

    def setUp(self):
        super().setUp()
        self.user.is_superuser = True
        self.user.save()

    def get_page(self, show_deprecated):
        with mock.patch.dict(settings.PLUGINS_CONFIG['netbox_contract'], {'show_deprecated_fields': show_deprecated}):
            with CaptureQueriesContext(connection) as queries:
                response = self.client.get(self.contract.get_absolute_url())
        self.assertHttpStatus(response, 200)
        return response, len(queries)

    def test_section_follows_the_setting(self):
        hidden, hidden_queries = self.get_page(False)
        self.assertIsNone(hidden.context['invoice_template'])
        self.assertNotContains(hidden, 'TEMPLATE-NUMBER-1')
        shown, shown_queries = self.get_page(True)
        self.assertEqual(shown.context['invoice_template'].number, 'TEMPLATE-NUMBER-1')
        self.assertContains(shown, 'TEMPLATE-NUMBER-1')
        self.assertLess(hidden_queries, shown_queries)


class TemplateLocationTestCase(TestCase):
    """
    Plugin templates live under templates/netbox_contract/ (FR-011). This covers the edge case "a template with the
    same name in another plugin does not replace them": only namespaced template paths remain.
    """

    def test_no_template_at_the_root(self):
        root = Path(forms.__file__).parent / 'templates'
        self.assertEqual(sorted(path.name for path in root.glob('*.html')), [])

    def test_inline_assignments_on_an_assigned_object(self):
        site = Site.objects.create(name='Inline site', slug='inline-site')
        contract = make_contract(name='Inline contract')
        ContractAssignment.objects.create(
            content_type=ContentType.objects.get_for_model(Site), object_id=site.pk, contract=contract
        )
        self.add_permissions(
            'dcim.view_site', 'netbox_contract.view_contract', 'netbox_contract.view_contractassignment'
        )
        with mock.patch.dict(settings.PLUGINS_CONFIG['netbox_contract'], {'contract_assignments_display': 'both'}):
            response = self.client.get(site.get_absolute_url())
        self.assertHttpStatus(response, 200)
        self.assertContains(response, 'Inline contract')
