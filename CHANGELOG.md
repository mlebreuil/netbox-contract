# Changelog

## [Unreleased]


## Version 2
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

