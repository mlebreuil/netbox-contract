# Changelog

## [Unreleased]

## Version 2

### Version 2.5.0

> [!WARNING]
> This version requires NetBox 4.6.0 or later. Read the **Breaking Changes** below before upgrading: the upgrade converts the contract costs and invoice templates into contract lines, and changes how invoices are created and locked.

#### Breaking Changes

* A new invoice can no longer be linked to more than one contract. Existing invoices linked to several contracts stay as they are and can be edited, but no contract can be added to them. These rules also apply to bulk edits of invoices, whose Template field is offered only when `show_deprecated_fields` is `True`. ([#278](https://github.com/mlebreuil/netbox-contract/issues/278))
* A new invoice must have the currency of its contract, and cannot be created for a non-billable contract. ([#278](https://github.com/mlebreuil/netbox-contract/issues/278))
* Creating an invoice (web interface or `POST invoices/`) now generates its invoice lines from the contract lines, and is refused when the invoice amount is lower than their total. Invoice lines are not generated when an invoice is edited or imported. ([#278](https://github.com/mlebreuil/netbox-contract/issues/278))
* The copy of invoice template lines onto a new invoice is removed. Invoice templates are no longer used to pre-fill invoices; the pre-fill uses the contract lines instead of `mrc` and `yrc`. ([#278](https://github.com/mlebreuil/netbox-contract/issues/278))
* New invoices are Draft by default (previously Posted), in the web interface and the REST API; imports still set the status given in the file. ([#278](https://github.com/mlebreuil/netbox-contract/issues/278))
* Posted invoices are locked: their amount, currency, period and contracts cannot change, lines cannot be added or deleted, and the unit, unit price, quantity and amount of their lines cannot change. Set an invoice back to Draft to correct it. ([#278](https://github.com/mlebreuil/netbox-contract/issues/278))
* The amount of every invoice line is quantity x unit price and can no longer be typed, as in most ERPs; the unit price is required and the quantity defaults to 1. An import or API call that gives only an amount still works: the amount becomes the unit price with quantity 1. Migration 0049 gives existing lines a unit price without changing any amount. ([#278](https://github.com/mlebreuil/netbox-contract/issues/278))
* Contract lines are locked once their contract has an invoice (any status) or once an invoice line references them: a new contract must be created. Their accounting dimensions, comments and tags remain editable, and their price or quantity can be amended from a date after the last invoiced period. The billing method and months of a unit used by such lines are locked too. ([#278](https://github.com/mlebreuil/netbox-contract/issues/278))
* The billable flag of a contract cannot change once the contract, one of its parents or one of its children has invoices. The currency of a contract cannot change once it has invoices or invoice lines; without invoices, its contract lines follow the new currency. Changing the currency of a contract also changes its non-billable descendants of the same currency, unless one of them has invoices. ([#278](https://github.com/mlebreuil/netbox-contract/issues/278))
* A contract whose lines (or those of its child contracts) are on posted invoices can no longer be deleted. ([#278](https://github.com/mlebreuil/netbox-contract/issues/278))
* The contract cost fields, new invoice templates and the invoice template section of the contract page are hidden unless `show_deprecated_fields` is `True`; templates remain reachable from the invoice list. The mandatory and hidden field settings ignore a deprecated field that is not shown (with a warning in the log) instead of failing. ([#278](https://github.com/mlebreuil/netbox-contract/issues/278))
* The custom scripts `create_invoice_template` and `create_invoice_lines` are removed: they read fields that no longer exist and are superseded by the conversion. ([#278](https://github.com/mlebreuil/netbox-contract/issues/278))
* API clients that passed filters to `serviceproviders/`, `contracttype/`, `accountingdimension/` or `contractassignment/` now get the filtered list instead of every object. ([#307](https://github.com/mlebreuil/netbox-contract/issues/307))
* Amending a contract line requires the new **amend** permission action. The add and change contract line permissions (required since [#307](https://github.com/mlebreuil/netbox-contract/issues/307)) are no longer enough; administrators grant the new action to the users who amend lines. This applies to the screen and to the REST action `POST contract-lines/{id}/amend/`. ([#309](https://github.com/mlebreuil/netbox-contract/issues/309))
* The related tables of detail pages show the default columns of their lists (for example the contract lines of a contract show the contract line list columns, without the contract). Users who want other columns choose them on the list with **Configure Table**. ([#309](https://github.com/mlebreuil/netbox-contract/issues/309))
* On the contract page, the deprecated costs (`mrc`, `yrc`, `nrc`, shown with `show_deprecated_fields`) are grouped in a **Deprecated costs** panel. The invoice page applies the `hidden_invoice_fields` setting, which it ignored until now. ([#309](https://github.com/mlebreuil/netbox-contract/issues/309))
* Contract type descriptions are limited to 200 characters, as on core objects: a longer description is refused (form, import, REST API). On upgrade, every contract type gets a slug derived from its name, made unique with `-2`, `-3`, ... when needed, and a longer description is shortened at a word boundary (ending with "…") with its full text moved to the new comments; the migration prints every slug it made unique and every description it moved. Migrating back restores the moved descriptions. ([#309](https://github.com/mlebreuil/netbox-contract/issues/309))
* Code that creates contract types with `bulk_create()` must give a slug, since `bulk_create()` does not call `save()`, which derives it. ([#309](https://github.com/mlebreuil/netbox-contract/issues/309))
* OpenAPI schema: the components `NestedInvoice`, `NestedAccountingDimension` and `NestedContractLine` are replaced by `BriefInvoice`, `BriefAccountingDimension` and `BriefContractLine`, with the same properties (on NetBox 4.6.10 or later; earlier 4.6 releases document the accounting dimension lists with the `AccountingDimension` component). Clients generated from the schema must be regenerated; the responses are unchanged. ([#309](https://github.com/mlebreuil/netbox-contract/issues/309))

#### New Features

##### Contract Lines and Units ([#278](https://github.com/mlebreuil/netbox-contract/issues/278))

Contract lines replace the contract costs (`mrc`, `yrc`, `nrc`) and the invoice templates. The new **Unit** model defines a billing method (one-time, recurring or usage-based) and the number of months one unit price covers; a **Contract line** has a description, quantity, unit price, unit, currency, start and end dates and accounting dimensions. Both have list, detail, edit, bulk import, bulk edit and bulk delete screens.

Contracts get a **billable** flag and three computed values: total contract value, yearly value and yearly billable value (which includes the lines of non-billable descendants).

On upgrade, a data migration converts the monthly, yearly and non-recurring costs and the invoice templates into contract lines (units "One-time", "Monthly", "Yearly") and prints a report. It can be run again with `python manage.py convert_contract_lines`. Every existing contract is billable. Invoices and invoice lines are not changed.

##### Invoices Generated from Contract Lines ([#278](https://github.com/mlebreuil/netbox-contract/issues/278))

The invoice add screen proposes the amount from the contract lines and previews the invoice lines that will be generated, with their amounts and total. Their quantities, unit prices and accounting dimensions can be changed, and lines without contract line added, before saving; the invoice and its lines are created in one step.

Invoice lines reference their contract line and carry their own quantity, unit and unit price, taken from the contract line by default and editable as long as the invoice is not posted (for example a discount on one invoice). Their amount is calculated as quantity x unit price. Migration 0047 copies the unit and unit price of the contract line into existing lines without changing their amounts.

##### Contract Line Amendments ([#278](https://github.com/mlebreuil/netbox-contract/issues/278), [#309](https://github.com/mlebreuil/netbox-contract/issues/309))

The unit price or quantity of a recurring or usage-based line can be amended from a date (**Amend** button, or `POST contract-lines/{id}/amend/`): the line ends the day before and a new line replaces it, invoiced periods keep their price, and the required reason is recorded in the change log. Amending has its own **amend** permission action (migration 0050), which can be limited with constraints; the **Amend** button is shown on the line page, in contract line tables and on the edit page only for the lines the user may amend.

##### Currency Consistency and Posted Invoice Locking ([#278](https://github.com/mlebreuil/netbox-contract/issues/278))

Contract lines, invoices and invoice lines must have the currency of their contract or invoice, and a non-billable child contract has the currency of its parent. The new read-only custom script "Report currency mismatches" lists existing mismatches without changing them.

Posted invoices are locked: their amounts, period and contracts, and the amounts of their lines, can no longer change, and lines can no longer be added or deleted. Accounting dimensions, comments and tags remain editable, and the status can change back to Draft.

##### GraphQL API ([#309](https://github.com/mlebreuil/netbox-contract/issues/309))

Contracts, contract lines, contract types, contract assignments, invoices, invoice lines, units, accounting dimensions and service providers can be queried and filtered in NetBox's GraphQL API, with permissions applied. It has the stored fields and relations; the computed contract and line values stay in the REST API, and an assigned object is resolved for the models of the default `supported_models` setting (see the API documentation).

#### Enhancements

* [#278](https://github.com/mlebreuil/netbox-contract/issues/278) - Invoice lines have a readable name (`<invoice number> line <id>`) in search results, the change log and reports
* [#308](https://github.com/mlebreuil/netbox-contract/issues/308) - Add the **Journal** tab to invoice lines, accounting dimensions, contract types and contract assignments
* [#308](https://github.com/mlebreuil/netbox-contract/issues/308) - Filter forms offer NetBox's lookup modifiers (contains, starts with, is not, is empty, ...)
* [#308](https://github.com/mlebreuil/netbox-contract/issues/308) - Add, edit, bulk edit and filter forms group their fields into sections (for contracts: Contract, Parties, Dates and terms, Billing, Tenancy)
* [#308](https://github.com/mlebreuil/netbox-contract/issues/308) - The invoice and invoice line add screens support NetBox's quick add and partial refresh; values given in the page address (for example `?date=` or `?period_start=`) are kept by the invoice pre-fill instead of being replaced
* [#308](https://github.com/mlebreuil/netbox-contract/issues/308) - The contract type description is a plain text field in the filter, bulk edit and import forms, and can be cleared in bulk
* [#308](https://github.com/mlebreuil/netbox-contract/issues/308) - Invoice line tables (list, invoice page) show the linked **ID** by default, so a line can be opened; users who saved their own column choice add it from **Configure Table**
* [#308](https://github.com/mlebreuil/netbox-contract/issues/308) - Refresh the translations and translate the new texts of 2.5.0 into French
* [#309](https://github.com/mlebreuil/netbox-contract/issues/309) - The detail pages of the nine object types are built from NetBox's standard panels; their related tables are the tables of the corresponding lists filtered to the object, so their columns can be chosen with **Configure Table** on the list ([#294](https://github.com/mlebreuil/netbox-contract/issues/294))
* [#309](https://github.com/mlebreuil/netbox-contract/issues/309) - Contract line tables decide their actions line by line: a locked line offers no Delete, and an amendable line offers Amend
* [#309](https://github.com/mlebreuil/netbox-contract/issues/309) - Add the contract list filter `invoice_id` (UI and REST API): the contracts of an invoice
* [#309](https://github.com/mlebreuil/netbox-contract/issues/309) - Contract types become NetBox organizational objects, with a **slug**, **comments** and an **owner**; service providers become NetBox primary objects, with a **description** and an **owner** (migrations 0051 and 0052). Both can be filtered by owner, and the owner can be set in bulk and imported. A contract type's slug is derived from its name when it is not given

#### Bug Fixes

* [#307](https://github.com/mlebreuil/netbox-contract/issues/307) - The Contracts tab of assigned objects (sites, devices, circuits, ...) is shown to users with the view contract assignment permission; it was shown to superusers only, because it checked a permission of a non-existent `contracts` app
* [#307](https://github.com/mlebreuil/netbox-contract/issues/307) - The REST endpoints `serviceproviders/`, `contracttype/`, `accountingdimension/` and `contractassignment/` ignored their filters (`name`, `q`, `tag`, `contract`, ...) and always returned the whole list
* [#307](https://github.com/mlebreuil/netbox-contract/issues/307) - The OpenAPI schema documents `external_party_object` (contracts, and the contract nested in contract lines and assignments) and `content_object` (contract assignments) as objects instead of strings
* [#307](https://github.com/mlebreuil/netbox-contract/issues/307) - The invoice line add form pre-fills the unit price and currency only from an invoice the user may view, and no longer fails with a server error when the `invoice` parameter is unknown or not a number
* [#307](https://github.com/mlebreuil/netbox-contract/issues/307) - The **Amend** button of contract lines was shown to users with the change permission alone, who then got a "forbidden" page
* [#308](https://github.com/mlebreuil/netbox-contract/issues/308) - Editing an existing invoice showed today's date in place of its date

#### Plugins

* [#308](https://github.com/mlebreuil/netbox-contract/issues/308) - Every screen of the plugin is registered with `register_model_view`, so other plugins can add tabs and actions to any plugin object; page addresses do not change
* [#309](https://github.com/mlebreuil/netbox-contract/issues/309) - Other plugins can add content to the left, right and full-width areas of every plugin page
* [#309](https://github.com/mlebreuil/netbox-contract/issues/309) - The template shown at the bottom of assigned objects moved to `netbox_contract/inc/contract_assignments_bottom.html`, and the unused `contract_list_bottom.html` was removed

#### Deprecations

* [#278](https://github.com/mlebreuil/netbox-contract/issues/278) - The contract fields `mrc`, `yrc` and `nrc` and the invoice templates are deprecated. They are kept (never deleted, shown with a "deprecated" badge) and hidden by default; the new plugin setting `show_deprecated_fields` (default `False`) shows them again. They remain in the bulk import and the REST API
* [#309](https://github.com/mlebreuil/netbox-contract/issues/309) - REST API fields, to be removed by a later release (see the API documentation; read `contracts/{id}/` or `invoices/{id}/` instead):
    * Nested contract (`contract` of assignments and contract lines, `parent` of contracts): `contract_type`, `external_party_object_type`, `external_party_object_id`, `external_party_object`, `external_reference`, `internal_party`, `tenant`, `start_date`, `end_date`, `initial_term`, `renewal_term`, `notice_period`, `currency`, `mrc`, `yrc`, `nrc`, `invoice_frequency`, `comments`, `documents`; it will keep `id`, `url`, `display`, `name` and `status`
    * `contracts` of an invoice become brief contracts: the fields above and `billable`, `total_contract_value`, `yearly_contract_value`, `yearly_billable_value`, `parent`, `tags`, `custom_fields`, `created`, `last_updated` will be removed
    * `contracts/?brief=true`: `contract_type`, `external_party_object_type`, `external_party_object_id`, `external_party_object`, `external_reference`, `internal_party`, `tenant`, `start_date`, `end_date`, `initial_term`, `renewal_term`, `currency`, `mrc`, `yrc`, `nrc`, `invoice_frequency`, `billable`, `comments`, `parent`
    * `invoices/?brief=true`: `date`, `template`, `contracts`, `period_start`, `period_end`, `currency`, `amount`, `comments`

#### Other Changes

* [#278](https://github.com/mlebreuil/netbox-contract/issues/278) - CI runs the tests against the NetBox v4.6.10 tag
* [#307](https://github.com/mlebreuil/netbox-contract/issues/307) - The plugin no longer depends on `drf_yasg`, which NetBox does not use

#### REST API Changes

* Added the following endpoints:
    * `GET/POST /api/plugins/contracts/units/`
    * `GET/PUT/PATCH/DELETE /api/plugins/contracts/units/<id>/`
    * `GET/POST /api/plugins/contracts/contract-lines/`
    * `GET/PUT/PATCH/DELETE /api/plugins/contracts/contract-lines/<id>/`
    * `POST /api/plugins/contracts/contract-lines/<id>/amend/`
* `netbox_contract.Contract`
    * Add the `billable` boolean field
    * Add the read-only `total_contract_value`, `yearly_contract_value` and `yearly_billable_value` fields
    * Add the `invoice_id` filter
    * `mrc`, `yrc` and `nrc` are deprecated
* `netbox_contract.ContractType`
    * Add the `slug`, `comments` and `owner` fields
    * The brief representation gains `slug` and `description`
* `netbox_contract.ServiceProvider`
    * Add the `description` and `owner` fields
    * The brief representation gains `slug` and `description`
* `netbox_contract.Invoice`
    * New invoices default to the `draft` status
    * `template` is deprecated
    * The nested invoice uses NetBox's brief representation (same fields)
* `netbox_contract.InvoiceLine`
    * Add the `contract_line`, `quantity`, `unit` and `unit_price` fields; `amount` is calculated
    * The brief representation gains `id` and `currency` and no longer declares the non-existent `name`
* `netbox_contract.ContractLine`
    * The brief representation (also used for the replaced line, `replaces`) includes `start_date` and `end_date`
* `netbox_contract.AccountingDimension`
    * The nested accounting dimensions use NetBox's brief representation (same fields)

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

