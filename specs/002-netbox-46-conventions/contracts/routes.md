# Contract: plugin routes (unchanged)

Public interface kept by FR-003. Every route name below, in the `plugins:netbox_contract:` namespace, MUST resolve
to the same address and view after the change. The list was taken from `netbox_contract/urls.py` on `develop`
(commit 29c3df7) and is the fixture of the route test (research D8).

Routes added by this feature (not in the list, registered by NetBox for every model once the detail include exists):
`<model>_journal` for all nine models; `invoiceline`, `accountingdimension`, `contracttype` and `contractassignment`
also gain every other feature view NetBox registers for them.

Extra routes that already exist through `register_model_view` and stay: `contractline_amend` (`contract-lines/<pk>/amend/`),
`contract_journal`, `invoice_journal`, `unit_journal`, `contractline_journal`, `serviceprovider_journal`, and the
`<model>_contracts` tabs on assignable NetBox models.

| Route name | Address | View |
|---|---|---|
| `serviceprovider_list` | `serviceproviders/` | `ServiceProviderListView` |
| `serviceprovider_add` | `serviceproviders/add/` | `ServiceProviderEditView` |
| `serviceprovider_bulk_import` | `serviceproviders/import/` | `ServiceProviderBulkImportView` |
| `serviceprovider_bulk_edit` | `serviceproviders/edit/` | `ServiceProviderBulkEditView` |
| `serviceprovider_bulk_delete` | `serviceproviders/delete/` | `ServiceProviderBulkDeleteView` |
| `serviceprovider` | `serviceproviders/<int:pk>/` | `ServiceProviderView` |
| `serviceprovider_edit` | `serviceproviders/<int:pk>/edit/` | `ServiceProviderEditView` |
| `serviceprovider_delete` | `serviceproviders/<int:pk>/delete/` | `ServiceProviderDeleteView` |
| `serviceprovider_changelog` | `serviceproviders/<int:pk>/changelog/` | `ObjectChangeLogView (NetBox)` |
| `contract_list` | `contracts/` | `ContractListView` |
| `contract_add` | `contracts/add/` | `ContractEditView` |
| `contract_bulk_import` | `contracts/import/` | `ContractBulkImportView` |
| `contract_bulk_edit` | `contracts/edit/` | `ContractBulkEditView` |
| `contract_bulk_delete` | `contracts/delete/` | `ContractBulkDeleteView` |
| `contract` | `contracts/<int:pk>/` | `ContractView` |
| `contract_edit` | `contracts/<int:pk>/edit/` | `ContractEditView` |
| `contract_delete` | `contracts/<int:pk>/delete/` | `ContractDeleteView` |
| `contract_changelog` | `contracts/<int:pk>/changelog/` | `ObjectChangeLogView (NetBox)` |
| `unit_list` | `units/` | `UnitListView` |
| `unit_add` | `units/add/` | `UnitEditView` |
| `unit_bulk_import` | `units/import/` | `UnitBulkImportView` |
| `unit_bulk_edit` | `units/edit/` | `UnitBulkEditView` |
| `unit_bulk_delete` | `units/delete/` | `UnitBulkDeleteView` |
| `unit` | `units/<int:pk>/` | `UnitView` |
| `unit_edit` | `units/<int:pk>/edit/` | `UnitEditView` |
| `unit_delete` | `units/<int:pk>/delete/` | `UnitDeleteView` |
| `unit_changelog` | `units/<int:pk>/changelog/` | `ObjectChangeLogView (NetBox)` |
| `contractline_list` | `contract-lines/` | `ContractLineListView` |
| `contractline_add` | `contract-lines/add/` | `ContractLineEditView` |
| `contractline_bulk_import` | `contract-lines/import/` | `ContractLineBulkImportView` |
| `contractline_bulk_edit` | `contract-lines/edit/` | `ContractLineBulkEditView` |
| `contractline_bulk_delete` | `contract-lines/delete/` | `ContractLineBulkDeleteView` |
| `contractline` | `contract-lines/<int:pk>/` | `ContractLineView` |
| `contractline_edit` | `contract-lines/<int:pk>/edit/` | `ContractLineEditView` |
| `contractline_delete` | `contract-lines/<int:pk>/delete/` | `ContractLineDeleteView` |
| `contractline_changelog` | `contract-lines/<int:pk>/changelog/` | `ObjectChangeLogView (NetBox)` |
| `invoice_list` | `invoices/` | `InvoiceListView` |
| `invoice_add` | `invoices/add/` | `InvoiceEditView` |
| `invoice_lines_preview` | `invoices/lines-preview/` | `InvoiceLinesPreviewView` |
| `invoice_bulk_import` | `invoices/import/` | `InvoiceBulkImportView` |
| `invoice_bulk_edit` | `invoices/edit/` | `InvoiceBulkEditView` |
| `invoice_bulk_delete` | `invoices/delete/` | `InvoiceBulkDeleteView` |
| `invoice` | `invoices/<int:pk>/` | `InvoiceView` |
| `invoice_edit` | `invoices/<int:pk>/edit/` | `InvoiceEditView` |
| `invoice_delete` | `invoices/<int:pk>/delete/` | `InvoiceDeleteView` |
| `invoice_changelog` | `invoices/<int:pk>/changelog/` | `ObjectChangeLogView (NetBox)` |
| `contractassignment_list` | `assignments/` | `ContractAssignmentListView` |
| `contractassignment_add` | `assignments/add/` | `ContractAssignmentEditView` |
| `contractassignment_bulk_import` | `assignments/import/` | `ContractAssignmentBulkImportView` |
| `contractassignment_bulk_edit` | `assignments/edit/` | `ContractAssignmentBulkEditView` |
| `contractassignment_bulk_delete` | `assignments/delete/` | `ContractAssignmentBulkDeleteView` |
| `contractassignment` | `assignments/<int:pk>/` | `ContractAssignmentView` |
| `contractassignment_edit` | `assignments/<int:pk>/edit/` | `ContractAssignmentEditView` |
| `contractassignment_delete` | `assignments/<int:pk>/delete/` | `ContractAssignmentDeleteView` |
| `contractassignment_changelog` | `assignments/<int:pk>/changelog/` | `ObjectChangeLogView (NetBox)` |
| `invoiceline_list` | `invoiceline/` | `InvoiceLineListView` |
| `invoiceline_add` | `invoiceline/add/` | `InvoiceLineEditView` |
| `invoiceline_bulk_import` | `invoiceline/import/` | `InvoiceLineBulkImportView` |
| `invoiceline_bulk_edit` | `invoiceline/edit/` | `InvoiceLineBulkEditView` |
| `invoiceline_bulk_delete` | `invoiceline/delete/` | `InvoiceLineBulkDeleteView` |
| `invoiceline` | `invoiceline/<int:pk>/` | `InvoiceLineView` |
| `invoiceline_edit` | `invoiceline/<int:pk>/edit/` | `InvoiceLineEditView` |
| `invoiceline_delete` | `invoiceline/<int:pk>/delete/` | `InvoiceLineDeleteView` |
| `invoiceline_changelog` | `invoiceline/<int:pk>/changelog/` | `ObjectChangeLogView (NetBox)` |
| `accountingdimension_list` | `accountingdimension/` | `AccountingDimensionListView` |
| `accountingdimension_add` | `accountingdimension/add/` | `AccountingDimensionEditView` |
| `accountingdimension_bulk_import` | `accountingdimension/import/` | `AccountingDimensionBulkImportView` |
| `accountingdimension_bulk_edit` | `accountingdimension/edit/` | `AccountingDimensionBulkEditView` |
| `accountingdimension_bulk_delete` | `accountingdimension/delete/` | `AccountingDimensionBulkDeleteView` |
| `accountingdimension` | `accountingdimension/<int:pk>/` | `AccountingDimensionView` |
| `accountingdimension_edit` | `accountingdimension/<int:pk>/edit/` | `AccountingDimensionEditView` |
| `accountingdimension_delete` | `accountingdimension/<int:pk>/delete/` | `AccountingDimensionDeleteView` |
| `accountingdimension_changelog` | `accountingdimension/<int:pk>/changelog/` | `ObjectChangeLogView (NetBox)` |
| `contracttype_list` | `contracttype/` | `ContractTypeListView` |
| `contracttype_add` | `contracttype/add/` | `ContractTypeEditView` |
| `contracttype` | `contracttype/<int:pk>/` | `ContractTypeView` |
| `contracttype_edit` | `contracttype/<int:pk>/edit/` | `ContractTypeEditView` |
| `contracttype_bulk_edit` | `contracttype/edit/` | `ContractTypeBulkEditView` |
| `contracttype_delete` | `contracttype/<int:pk>/delete/` | `ContractTypeDeleteView` |
| `contracttype_bulk_delete` | `contracttype/delete/` | `ContractTypeBulkDeleteView` |
| `contracttype_bulk_import` | `contracttype/import/` | `ContractTypeBulkImportView` |
| `contracttype_changelog` | `contracttype/<int:pk>/changelog/` | `ObjectChangeLogView (NetBox)` |
