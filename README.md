# Contract pluggin
## Overview
The pluggin adds contracts and invoices model to Netbox.  
It allows to register contract with objects.  
Add invoices to contracts.  

## Installation

### Activate venv
To ensure our plugin is accessible to the NetBox installation, we first need to activate the Python [virtual environment](https://docs.python.org/3/library/venv.html) that was created when we installed NetBox. To do this, determine the virtual environment's path (this will be `/opt/netbox/venv/` if you use the documentation's defaults) and activate it:

```bash
$ source /opt/netbox/venv/bin/activate
```

### Install the package 

```bash
$ python3 -m pip install netbox-contract
```

### Configure NetBox

Finally, we need to configure NetBox to enable our new plugin. Over in the NetBox installation path, open `netbox/netbox/configuration.py` and look for the `PLUGINS` parameter; this should be an empty list. (If it's not yet defined, go ahead and create it.) Add the name of our plugin to this list:

```python
# configuration.py
PLUGINS = [
    'netbox_contract',
]
```

### Customize the plugin

The following configurationitems can be set:

```python
# configuration.py
PLUGINS_CONFIG = {
    'netbox_contract': {
        'top_level_menu': True,
        'default_accounting_dimensions':{
            "account": "", 
            "project": "", 
            "cost center": ""
        },
        'mandatory_contract_fields': ['accounting_dimensions'],
        'hidden_contract_fields': [],
        'mandatory_invoice_fields': ['accounting_dimensions'],
        'hidden_invoice_fields': [],
    }
}

```

* top_level_menu : If "Contracts" appears under the "Plugins" menu item or on its own
* default_accounting_dimensions: The accounting dimensions which will appear in the field' background when empty.
* mandatory_contract_fields, mandatory_invoice_fields: Fields which are not required by default and can be set as such. The list of fields is at the bottom of the contract import form.
* hidden_contract_fields, hidden_invoice_fields: List of fields to be hidden. Fields should not be required to be hidden.

### Customize the plugin fields choices

Internal partie reference the legal entity of your organization that is a partie to the contract.  

```python
# configuration.py
FIELD_CHOICES = {
    'netbox_contract.Contract.internal_partie': (
        ('Nagravision SARL', 'Nagravision SARL', 'green'),
        ('Nagra USA', 'Nagra USA', 'green'),
        ('Nagra India', 'Nagra India', 'green'),
    ),
    'netbox_contract.Contract.currency': (
        ('usd', 'USD'),
        ('eur', 'EUR'),
        ('chf', 'CHF'),
        ('pln', 'PLN'),
    ),
    'netbox_contract.Contract.status': (
        ('Active', 'Active', 'green'),
        ('Cancled', 'Canceled', 'red'),
    )
}

```

### Run database migrations

```bash
(venv) $ cd /opt/netbox/netbox/
(venv) $ python3 manage.py migrate
```

## release notes

### version 2.0.0

Add a new contract asignement model to allow the assignement of contract not only to Circuits. The support for the direct Contract to Circuit relation will be removed in version 2.1.0 . In Order to migrate existing relations contract_migration.py script is provided and can be run from the django shell.

#### version 2.0.1

Add support contract assignement panel to devices.

#### version 2.0.2

Add support for Netbox 3.5 which become the minimum version supported to accomodate the removal of NetBoxModelCSVForm class (replaced by NetBoxModelImportForm) .

#### version 2.0.3

* [#60](https://github.com/mlebreuil/netbox-contract/issues/60) Update contract quick search to also filter on fields "External reference" and "Comments".
* [#49](https://github.com/mlebreuil/netbox-contract/issues/49) Manage permissions.

#### version 2.0.4

* Add bulk update capability for contract assignement
* [#63](https://github.com/mlebreuil/netbox-contract/issues/63) Correct an API issue on the invoice object.
* [#64](https://github.com/mlebreuil/netbox-contract/issues/64) Add hierarchy to contract; New parent field created.
* [#65](https://github.com/mlebreuil/netbox-contract/issues/65) Add end date to contact import form.
* Removed the possibility of add or modify circuits to contracts. The field becomes read only and will be removed in next major release.
* Make accounting dimensions optional.

#### version 2.0.5

* [#75](https://github.com/mlebreuil/netbox-contract/issues/74) Fix contract assignement for service providers.
* [#73](https://github.com/mlebreuil/netbox-contract/issues/73) Add comment field to contract import form
* [#72](https://github.com/mlebreuil/netbox-contract/issues/72) Add fields to the contract assignement bottom tables
* Remove the 'add' actions from the contract assignment list view

#### version 2.0.6
* [#80](https://github.com/mlebreuil/netbox-contract/issues/80) Fix missing fields in the API.

#### version 2.0.7
* [#85](https://github.com/mlebreuil/netbox-contract/issues/85) Fix missing fields contract and invoice import and export forms.

#### version 2.0.8
* [#91](https://github.com/mlebreuil/netbox-contract/issues/91) Replace deprecated ( in netbox version 3.6) MultipleChoiceField.  
* [48](https://github.com/mlebreuil/netbox-contract/issues/48) Allow other plugin to inject visual in contract and invoice forms.  
* [89] (https://github.com/mlebreuil/netbox-contract/issues/89) Add contract assignement to virtual machines.

#### version 2.0.9
* [42](https://github.com/mlebreuil/netbox-contract/issues/42) Allow the selection of either providers or Service providers as contract third partie.
* Removed all reference to the direct assignement of circuits to contracts
* [88](https://github.com/mlebreuil/netbox-contract/issues/88) Add a placeholder value to the accounting dimensions jsonfield. This placeholder vale con be configured as part of the PLUGINS_CONFIG parameter in the configuration.py file (see above)
* [89](https://github.com/mlebreuil/netbox-contract/issues/89) add the posibility to link contracts to sites and virtual machines.
* [99](https://github.com/mlebreuil/netbox-contract/issues/99) list child contracts in on the parent view.
#### version 2.0.10
* [107](https://github.com/mlebreuil/netbox-contract/issues/107) Add the contacts tab to the service provider detail view.
* [111](https://github.com/mlebreuil/netbox-contract/issues/111) Correct assignment spelling.
#### version 2.0.11
* [115](https://github.com/mlebreuil/netbox-contract/issues/115) API correction for contract external partie
* [117](https://github.com/mlebreuil/netbox-contract/issues/117) Tenant and accounting dimensions optional
* [119](https://github.com/mlebreuil/netbox-contract/issues/119) Add a Yearly recuring cost, read only, calculated field for contract
* [15](https://github.com/mlebreuil/netbox-contract/issues/105) Quick serach limited to active contracts
#### version 2.0.13
* [123](https://github.com/mlebreuil/netbox-contract/issues/123) prepare plugin to [Netbox 4.0 migration](https://docs.netbox.dev/en/feature/plugins/development/migration-v4/).
* [125](https://github.com/mlebreuil/netbox-contract/issues/125) Cleanup direct reference to Circuits in the Contract model. Correct database inconsistencies related to the ContractAssignment object renaming.

#### version 2.0.14

* [127](https://github.com/mlebreuil/netbox-contract/issues/127) Fix contract filtering
* Fix contact assignement.
