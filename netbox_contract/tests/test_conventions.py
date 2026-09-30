"""Alignment with the NetBox 4.6 plugin conventions (issue #308, specs/002-netbox-46-conventions)."""

from dcim.models import Site
from django.contrib.contenttypes.models import ContentType
from django.urls import resolve, reverse
from extras.models import JournalEntry
from utilities.testing import TestCase

from netbox_contract.models import (
    AccountingDimension,
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
