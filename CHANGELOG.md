# Changelog

## [Unreleased]


## Version 2

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

* [115](https://github.com/mlebreuil/netbox-contract/issues/115) API correction for contract external partie
* [117](https://github.com/mlebreuil/netbox-contract/issues/117) Tenant and accounting dimensions optional
* [119](https://github.com/mlebreuil/netbox-contract/issues/119) Add a Yearly recuring cost, read only, calculated field for contract
* [15](https://github.com/mlebreuil/netbox-contract/issues/105) Quick serach limited to active contracts

### Version 2.0.10

* [107](https://github.com/mlebreuil/netbox-contract/issues/107) Add the contacts tab to the service provider detail view.
* [111](https://github.com/mlebreuil/netbox-contract/issues/111) Correct assignment spelling.

### Version 2.0.9

* [42](https://github.com/mlebreuil/netbox-contract/issues/42) Allow the selection of either providers or Service providers as contract third partie.
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

