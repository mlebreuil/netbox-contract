# Changelog

## [Unreleased]

## Version 2

### Version 2.5.0

> [!WARNING]
> This version requires Netbox 4.6.0 or later.

* [#278](https://github.com/mlebreuil/netbox-contract/issues/278) Contract lines replace the contract costs and the invoice templates.
  * New models **Unit** (billing method one-time, recurring or usage-based, and the months one unit price covers) and **Contract line** (description, quantity, unit price, unit, currency, dates and accounting dimensions), with list, detail, edit, bulk import, bulk edit and bulk delete screens, and the REST API endpoints `units/` and `contract-lines/`.
  * Contracts get a **billable** flag and three computed values: total contract value, yearly value and yearly billable value (which includes the lines of non-billable descendants).
  * The invoice add screen proposes the amount from the contract lines, and creating an invoice generates its invoice lines from them. Invoice lines get a reference to their contract line and a quantity, unit and unit price; their amount is calculated from it.
  * Currency consistency: contract lines, invoices and invoice lines must have the currency of their contract or invoice; a non-billable child has the currency of its parent. The new read-only custom script "Report currency mismatches" lists existing mismatches without changing them.
  * Upgrade: the migration converts the monthly, yearly and non-recurring costs and the invoice templates into contract lines (units "One-time", "Monthly", "Yearly") and prints a report. It can be run again with `python manage.py convert_contract_lines`. Every existing contract is billable. Invoices and invoice lines are not changed.
  * Deprecated, kept and hidden by default: the contract fields `mrc`, `yrc` and `nrc` and the invoice templates (never deleted, shown with a "deprecated" badge). The new plugin setting `show_deprecated_fields` (default `False`) shows them again. They remain in the bulk import and the REST API.
  * CI runs the tests against the NetBox v4.6.10 tag.
  * The unit price or quantity of a recurring or usage-based line can be amended from a date ("Amend" button, REST `POST contract-lines/{id}/amend/`): the line ends the day before and a new line replaces it, invoiced periods keep their price, and the required reason is recorded in the change log.
  * Invoice lines carry their own unit and unit price, taken from the contract line by default and editable as long as the invoice is not posted (for example a discount on one invoice); the amount is calculated from quantity x unit price. Migration 0047 copies the unit and unit price of the contract line into existing lines without changing their amounts.
  * The new invoice screen previews the lines that will be generated, with their amounts and total, and lets you change their quantities, unit prices and accounting dimensions, or add lines without contract line, before saving; the invoice and its lines are created in one step.
  * Posted invoices are locked: their amounts, period and contracts, and the amounts of their lines, can no longer change, and lines can no longer be added or deleted (accounting dimensions, comments and tags remain editable; the status can change back to Draft).
  * Invoice lines have a readable name (`<invoice number> line <id>`) in search results, the change log and reports.

* [#307](https://github.com/mlebreuil/netbox-contract/issues/307) Fixes found in the NetBox 4.6 review.
  * The Contracts tab of assigned objects (sites, devices, circuits, ...) is shown to users with the view contract assignment permission; it was shown to superusers only, because it checked a permission of a non-existent `contracts` app.
  * The REST endpoints `serviceproviders/`, `contracttype/`, `accountingdimension/` and `contractassignment/` apply their filters (`name`, `q`, `tag`, `contract`, ...); they ignored them and always returned the whole list.
  * The OpenAPI schema documents `external_party_object` (contracts, and the contract nested in contract lines and assignments) and `content_object` (contract assignments) as objects instead of strings. The plugin no longer depends on `drf_yasg`, which NetBox does not use.
  * The invoice line add form pre-fills the unit price and currency only from an invoice the user may view, and no longer fails with a server error when the `invoice` parameter is unknown or not a number.
  * The **Amend** button of contract lines is shown only to users with both the add and change contract line permissions, which the amendment requires; users with the change permission alone saw it and got a "forbidden" page.

* [#308](https://github.com/mlebreuil/netbox-contract/issues/308) Aligned with the NetBox 4.6 plugin conventions.
  * Invoice lines, accounting dimensions, contract types and contract assignments get the **Journal** tab, like the other objects. Every screen of the plugin is registered the NetBox way, so other plugins can add tabs and actions to any plugin object; page addresses do not change.
  * Filter forms offer NetBox's lookup modifiers (contains, starts with, is not, is empty, ...).
  * Add, edit, bulk edit and filter forms group their fields into sections (for contracts: Contract, Parties, Dates and terms, Billing, Tenancy).
  * The invoice and invoice line add screens support NetBox's quick add and partial refresh. Values given in the page address (for example `?date=`) are kept by the invoice pre-fill instead of being replaced, and editing an existing invoice no longer shows today's date in place of its date.
  * The contract type description is a plain text field in the filter, bulk edit and import forms, and can be cleared in bulk.
  * Invoice line tables (list, invoice page) show the linked **ID** by default, so a line can be opened; no other column linked to it. Users who saved their own column choice add it from "Configure Table".
  * The translations are refreshed and the new texts of 2.5.0 are translated into French.
  * For plugin developers: the template shown at the bottom of assigned objects moved to `netbox_contract/inc/contract_assignments_bottom.html`, and the unused `contract_list_bottom.html` was removed.

#### Behaviour changes

For existing users and API clients:

* A new invoice can no longer be linked to more than one contract. Existing invoices linked to several contracts stay as they are and can be edited, but no contract can be added to them. These rules also apply to bulk edits of invoices, whose Template field is offered only when `show_deprecated_fields` is `True`.
* A new invoice must have the currency of its contract, and cannot be created for a non-billable contract.
* Creating an invoice (web interface or `POST invoices/`) now generates its invoice lines from the contract lines, and is refused when the invoice amount is lower than their total. Invoice lines are not generated when an invoice is edited or imported.
* The copy of invoice template lines onto a new invoice is removed. Invoice templates are no longer used to pre-fill invoices; the pre-fill uses the contract lines instead of `mrc` and `yrc`.
* Contract lines are locked once their contract has an invoice (any status) or once an invoice line references them: a new contract must be created. Their accounting dimensions, comments and tags remain editable, and their price or quantity can be amended from a date after the last invoiced period. The billing method and months of a unit used by such lines are locked too.
* The billable flag of a contract cannot change once the contract, one of its parents or one of its children has invoices. The currency of a contract cannot change once it has invoices or invoice lines; without invoices, its contract lines follow the new currency.
* The amount of every invoice line is quantity x unit price and can no longer be typed, as in most ERPs; the unit price is required and the quantity defaults to 1. An import or API call that gives only an amount still works: the amount becomes the unit price with quantity 1. Migration 0049 gives existing lines a unit price without changing any amount.
* A contract whose lines (or those of its child contracts) are on posted invoices can no longer be deleted.
* Changing the currency of a contract also changes its non-billable descendants of the same currency, unless one of them has invoices.
* New invoices are Draft by default (previously Posted), in the web interface and the REST API; imports still set the status given in the file.
* Posted invoices are locked: their amount, currency, period and contracts cannot change, lines cannot be added or deleted, and the unit, unit price, quantity and amount of their lines cannot change. Set an invoice back to Draft to correct it.
* The contract cost fields, new invoice templates and the invoice template section of the contract page are hidden unless `show_deprecated_fields` is `True`; templates remain reachable from the invoice list. The mandatory and hidden field settings ignore a deprecated field that is not shown (with a warning in the log) instead of failing.
* The custom scripts `create_invoice_template` and `create_invoice_lines` are removed: they read fields that no longer exist and are superseded by the conversion.
* API clients that passed filters to `serviceproviders/`, `contracttype/`, `accountingdimension/` or `contractassignment/` now get the filtered list instead of every object.
* Non-superusers with the view contract assignment permission now see the Contracts tab.
* The invoice add form keeps the values given in its address (for example `?date=` or `?period_start=`); previously the values proposed from the contract, and today's date, replaced them.

### Version v2.4.7

* [#303](https://github.com/mlebreuil/netbox-contract/issues/303) Gracefully skip `supported_models` entries that don't resolve to a registered Django model instead of raising an unhandled `LookupError` during app startup (which previously crashed *every* management command, including `migrate`). This most commonly affects models created dynamically by other plugins (e.g. `netbox_custom_objects` custom object types), whose registration order relative to `netbox_contract` is not guaranteed. A clear error is now logged (`netbox.plugins.netbox_contract`) naming the offending entry, and the rest of the plugin continues to load normally.

### Version 2.4.6

* [#300](https://github.com/mlebreuil/netbox-contract/issues/300) Expose missing model fields (slug, comments, color, notice_period, documents, status, tags, custom_fields) via API serializers.

### Version 2.4.5
* [292](https://github.com/mlebreuil/netbox-contract/issues/292) bug fix. Contract detail show internal party value instead of label.

* [294](https://github.com/mlebreuil/netbox-contract/issues/294) Add `contract_assignments_display` plugin setting (`tab`, `inline`, `both`) for contract assignment UI. The tab view allows customization of the contracts list table columns.

### Version 2.4.4
* [288](https://github.com/mlebreuil/netbox-contract/issues/288) Add the possibility to assign contract any object type. By default the following objects types: 'circuits.circuit', 'circuits.virtualcircuit', 'dcim.site', 'dcim.device', 'dcim.rack', 'virtualization.virtualmachine', 'virtualization.cluster', 'ipam.ipaddress', 'ipam.prefix'. This list can be overriden within the PLUGINS_CONFIG configuration parameter. Check the README file or [documentation](https://mlebreuil.github.io/netbox-contract/) for more information.

### Version 2.4.3

* [282](https://github.com/mlebreuil/netbox-contract/issues/282) Add the possibility to assign contract to clusters and racks.
* [276](https://github.com/mlebreuil/netbox-contract/issues/276) Add the possibility to update the provider in bulk for contracts.
* [275](https://github.com/mlebreuil/netbox-contract/issues/275) Add the possibility to filter contract by provider an service provider. Remove the default value for the currency and internal party fields in the contract search form.
* [274](https://github.com/mlebreuil/netbox-contract/issues/274) List contracts on providers and service providers pages

### Version 2.4.2

* [272](https://github.com/mlebreuil/netbox-contract/issues/272) Add missing contract_type fields to the api.


### Version 2.4.1

* [257](https://github.com/mlebreuil/netbox-contract/issues/257) Add the possibility to filter invoices by accounting dimensions.
* [267](https://github.com/mlebreuil/netbox-contract/issues/267) Add status field to invoices.
* [263](https://github.com/mlebreuil/netbox-contract/issues/263) Enable contract assignment to virtual circuits.
* [258](https://github.com/mlebreuil/netbox-contract/issues/258) Fix assignement of contacts to service providers.
* [261](https://github.com/mlebreuil/netbox-contract/issues/261) Fix spelling of word "party".

### Version 2.4.0

> [!WARNING]
> This version requires Netbox 4.3.0 or later

* [253](https://github.com/mlebreuil/netbox-contract/pull/253) Implement Netbox 4.3 compatibility

### Version 2.3.3

* [250](https://github.com/mlebreuil/netbox-contract/pull/250) Add contacts to contract.
* [248](https://github.com/mlebreuil/netbox-contract/pull/248) Add contact filtering on service provider.
* [245](https://github.com/mlebreuil/netbox-contract/pull/245) Add contract-type model.

### Version 2.3.2

* [234](https://github.com/mlebreuil/netbox-contract/issues/234) As part of the preparation of the [plugin for certification](https://github.com/netbox-community/netbox/wiki/Plugin-Certification-Program), this version includes standard Netbox unittest for model views. Correction to data import are also present as well.

### Version 2.3.1

* [219](https://github.com/mlebreuil/netbox-contract/issues/219) Fix - netbox 4.2 non editable field for gfk

### Version 2.3.0

> [!WARNING]
> Accounting dimension json field removed. It is deprecated since v2.2.0. Refer to the [documentation](https://mlebreuil.github.io/netbox-contract/accounting_dimensions/)

* [206](https://github.com/mlebreuil/netbox-contract/issues/206) remove deprecated json accounting dimention field
* Add background color to status
* Script - fix check_contract_end with empty end date
* minor fix

### Version 2.2.11

* [202](https://github.com/mlebreuil/netbox-contract/issues/202) Fix django.template.exceptions when trying to open device detail.

### Version 2.2.10

* [198](https://github.com/mlebreuil/netbox-contract/issues/198) Add internationalization support and french translation.
* [196](https://github.com/mlebreuil/netbox-contract/issues/196) Add notice field to contract. Add an example custom script to report contract nearing cancelation notice.
* minor fix and cleanup

### Version 2.2.8

* [167](https://github.com/mlebreuil/netbox-contract/issues/167) Add selector to object dynamic selection box.
* [193](https://github.com/mlebreuil/netbox-contract/pull/193) Set the first currency in the choiceset as default currency.

### Version 2.2.7

* fix migration dependency

### Version 2.2.6

* [186](https://github.com/mlebreuil/netbox-contract/issues/186) Code compatibility fix for Netbox 4.1

### Version 2.2.5

* Generally improve filtering options
* [178](https://github.com/mlebreuil/netbox-contract/issues/178) Add the possibility to filter on invoice number, and contract name through the API.
* [176](https://github.com/mlebreuil/netbox-contract/issues/176) Order accounting dimensions in tables alphabetically.
* [171](https://github.com/mlebreuil/netbox-contract/issues/171) It is now possible to define madatory accounting dimension by specifying their names in the 'mandatory_dimensions' list in the plugin settings. (see the "Customize the plugin" paragraph in the README.md file)

### Version 2.2.4

* [166](https://github.com/mlebreuil/netbox-contract/issues/166) Review the Contract view to include invoice template details and lines.
* [161](https://github.com/mlebreuil/netbox-contract/issues/161) Change the invoice block title if the invoice is a template.
* [160](https://github.com/mlebreuil/netbox-contract/issues/160) Add more fields to the invoice and contract bulk edit forms.
* [165](https://github.com/mlebreuil/netbox-contract/issues/165) Fix Invoice and invoiceline creation through api. 

### Version 2.2.3

* Fix accounting dimensions access through Dynamic Object Fields
* Fix invoice creation from contract. 
* Add scripts to convert accounting dimensions in the json fields of contract and invoices to invoice template, invoicelines and dimensions objects.

### Version 2.2.2

* [154](https://github.com/mlebreuil/netbox-contract/issues/154) Fix edit and delete bulk operations on dimensions and invoice lines.
* [153](https://github.com/mlebreuil/netbox-contract/issues/153) Enforce uniquness of accounting dimensions.
* Adds a status ( Active or Inactive ) to accounitng dimensions.
* [151](https://github.com/mlebreuil/netbox-contract/issues/151) Fix accounting line and dimensions search.

### Version 2.2.1

* [142](https://github.com/mlebreuil/netbox-contract/issues/142) Gives the option to enter contract yearly recuring costs instead of only monthly recuring costs.
Corresponding value is used to calculate the invoices amount without rounding approximations.
* [148](https://github.com/mlebreuil/netbox-contract/issues/148) Update tables format to match the new Netbox UI design.

### Version 2.2.0

* [140](https://github.com/mlebreuil/netbox-contract/issues/140) Add the "Invoice line" and "Accounting dimension" models. In order to simplify invoices creation, it is possible to selsct one invoice as the template for each contract; Its accounting lines will automatically be copied to the new invoices for the contract. The amount of the first line will be updated so that the sum of the amount for each invoice line match the invoice amount.

### Version 2.1.2

* [127](https://github.com/mlebreuil/netbox-contract/issues/135) Fix service provider creation issue
* Fix contract assignement issue

### Version 2.1.0

* Netbox v4 compatibility. Netbox4.0.2 become a minimum requirement 

### Version 2.0.14

* [127](https://github.com/mlebreuil/netbox-contract/issues/127) Fix contract filtering
* Fix contact assignement.

### Version 2.0.13

* [123](https://github.com/mlebreuil/netbox-contract/issues/123) prepare plugin to [Netbox 4.0 migration](https://docs.netbox.dev/en/feature/plugins/development/migration-v4/).
* [125](https://github.com/mlebreuil/netbox-contract/issues/125) Cleanup direct reference to Circuits in the Contract model. Correct database inconsistencies related to the ContractAssignment object renaming.

### Version 2.0.11

* [115](https://github.com/mlebreuil/netbox-contract/issues/115) API correction for contract external party
* [117](https://github.com/mlebreuil/netbox-contract/issues/117) Tenant and accounting dimensions optional
* [119](https://github.com/mlebreuil/netbox-contract/issues/119) Add a Yearly recuring cost, read only, calculated field for contract
* [15](https://github.com/mlebreuil/netbox-contract/issues/105) Quick serach limited to active contracts

### Version 2.0.10

* [107](https://github.com/mlebreuil/netbox-contract/issues/107) Add the contacts tab to the service provider detail view.
* [111](https://github.com/mlebreuil/netbox-contract/issues/111) Correct assignment spelling.

### Version 2.0.9

* [42](https://github.com/mlebreuil/netbox-contract/issues/42) Allow the selection of either providers or Service providers as contract third party.
* Removed all reference to the direct assignement of circuits to contracts
* [88](https://github.com/mlebreuil/netbox-contract/issues/88) Add a placeholder value to the accounting dimensions jsonfield. This placeholder vale con be configured as part of the PLUGINS_CONFIG parameter in the configuration.py file (see above)
* [89](https://github.com/mlebreuil/netbox-contract/issues/89) add the posibility to link contracts to sites and virtual machines.
* [99](https://github.com/mlebreuil/netbox-contract/issues/99) list child contracts in on the parent view.

### Version 2.0.8

* [#91](https://github.com/mlebreuil/netbox-contract/issues/91) Replace deprecated ( in netbox version 3.6) MultipleChoiceField.  
* [48](https://github.com/mlebreuil/netbox-contract/issues/48) Allow other plugin to inject visual in contract and invoice forms.  
* [89] (https://github.com/mlebreuil/netbox-contract/issues/89) Add contract assignement to virtual machines.

### Version 2.0.7

* [#85](https://github.com/mlebreuil/netbox-contract/issues/85) Fix missing fields contract and invoice import and export forms.

### Version 2.0.6

* [#80](https://github.com/mlebreuil/netbox-contract/issues/80) Fix missing fields in the API.

### Version 2.0.5

* [#75](https://github.com/mlebreuil/netbox-contract/issues/74) Fix contract assignement for service providers.
* [#73](https://github.com/mlebreuil/netbox-contract/issues/73) Add comment field to contract import form
* [#72](https://github.com/mlebreuil/netbox-contract/issues/72) Add fields to the contract assignement bottom tables
* Remove the 'add' actions from the contract assignment list view

### Version 2.0.4

* Add bulk update capability for contract assignement
* [#63](https://github.com/mlebreuil/netbox-contract/issues/63) Correct an API issue on the invoice object.
* [#64](https://github.com/mlebreuil/netbox-contract/issues/64) Add hierarchy to contract; New parent field created.
* [#65](https://github.com/mlebreuil/netbox-contract/issues/65) Add end date to contact import form.
* Removed the possibility of add or modify circuits to contracts. The field becomes read only and will be removed in next major release.
* Make accounting dimensions optional.

### Version 2.0.3

* [#60](https://github.com/mlebreuil/netbox-contract/issues/60) Update contract quick search to also filter on fields "External reference" and "Comments".
* [#49](https://github.com/mlebreuil/netbox-contract/issues/49) Manage permissions.

### Version 2.0.2

Add support for Netbox 3.5 which become the minimum version supported to accomodate the removal of NetBoxModelCSVForm class (replaced by NetBoxModelImportForm) .

### Version 2.0.1

Add support contract assignement panel to devices.

### Version 2.0.0

Add a new contract asignement model to allow the assignement of contract not only to Circuits. The support for the direct Contract to Circuit relation will be removed in version 2.1.0 . In Order to migrate existing relations contract_migration.py script is provided and can be run from the django shell.

