# Contract plugin

NetBox plugin to manage contracts.


* Free software: MIT
* Documentation: https://mlebreuil.github.io/netbox-contract/

## Features

The plugin adds contracts and invoices model to NetBox.  
It allows to link contract with objects.  
Each contract is described by contract lines (one-time, recurring or usage-based, through units).  
Invoices are linked with contracts; their amount is proposed and their invoice lines are generated from the contract lines.  
Accounting dimensions can be linked with contract lines and invoice lines.  

## Compatibility

| NetBox Version | Plugin Version |
|----------------|----------------|
|     4.1        |      2.2       |
|     4.2        |      2.3       |
|     4.3        |      2.4       |
|     4.4        |      2.4       |
|     4.5        |      2.4       |
|     4.6        |   2.4, 2.5     |
|     4.7        |      2.6       |

Version 2.6 requires NetBox 4.7 or later. NetBox 4.6 installations stay on plugin 2.5.

## Installing

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

Finally, we need to configure NetBox to enable our new plugin. In the NetBox installation directory, open `netbox/netbox/configuration.py` and locate the `PLUGINS` parameter; it should be an empty list. (If it's not yet defined, go ahead and create it.) Add the name of our plugin to this list:

```python
# configuration.py
PLUGINS = [
    'netbox_contract',
]
```

### Customize the plugin

The following configuration items can be set:

```python
# configuration.py
PLUGINS_CONFIG = {
    'netbox_contract': {
        'top_level_menu': True,
        'mandatory_contract_fields': [],
        'hidden_contract_fields': [],
        'mandatory_invoice_fields': [],
        'hidden_invoice_fields': [],
        'mandatory_dimensions': [],
        'supported_models': [
            'circuits.circuit',
            'circuits.virtualcircuit',
            'dcim.site',
            'dcim.device',
            'dcim.rack',
            'virtualization.virtualmachine',
            'virtualization.cluster',
            'ipam.ipaddress',
            'ipam.prefix',
        ],
        'contract_assignments_display': 'both',  # options: 'tab', 'inline', 'both'
        'show_deprecated_fields': False,
    }
}

```

* top_level_menu : If "Contracts" appears under the "Plugins" menu item or on its own
* supported_models: The NetBox models a contract can be assigned to. Each model must be exposed in NetBox's REST API, because the assignment form searches its objects through it. A contract can be assigned to a given object only once.
* contract_assignments_display:
  * `'tab'` - only the Contracts view tab is visible on the related object page.
  * `'inline'` - only the inline contract assignments table is shown in object detail; the Contracts tab is hidden.
  * `'both'` - both tab and inline table are shown (default behavior).
* default_accounting_dimensions: The accounting dimensions which will appear in the field' background when empty. Note that accounting dimensions are now managed as individual objects. The use of this field is deprecated.  
* mandatory_contract_fields, mandatory_invoice_fields: Fields which are not required by default and can be set as such. The list of fields is at the bottom of the contract import form.
* hidden_contract_fields, hidden_invoice_fields: List of fields to be hidden. Fields should not be required to be hidden. A deprecated field that is not shown is ignored, with a warning in the log. The legacy name `external_party_object_type` is an alias of `external_party_object`.
* show_deprecated_fields: show the deprecated contract cost fields (monthly, yearly and non-recurring costs, replaced by contract lines) in the contract form, detail page and tables, and allow creating new invoice templates. Default: `False`.

### Customize the plugin fields choices

Internal party reference the legal entity of your organization that is a party to the contract.  
The first currency will also be the default currency for contracts.  

```python
# configuration.py
FIELD_CHOICES = {
    'netbox_contract.Contract.internal_party': (
        ('default', 'Default entity', 'green'),
        ('entity1', 'Entity 1', 'green'),
        ('entity2', 'Entity 2', 'yellow'),
    ),
    'netbox_contract.Contract.currency': (
        ('usd', 'USD'),  # 1st position is the default currency
        ('eur', 'EUR'),
        ('chf', 'CHF'),
        ('pln', 'PLN'),
    ),
    'netbox_contract.Contract.status': (
        ('active', 'Active', 'green'),
        ('canceled', 'Canceled', 'red'),
    )
    'netbox_contract.Invoice.status': (
        ('draft', 'Draft', 'yellow'),
        ('posted', 'Posted', 'green'),
        ('canceled', 'Canceled', 'red'),
    )
}

```

Status and billing method options show a description under their name. The built-in options come with one. An option you add or
replace through `FIELD_CHOICES` can give its own with a dictionary entry; an option without a description is shown without one. Replacing all the options of a set, as in the example above, drops the built-in descriptions unless you give them again:

```python
FIELD_CHOICES = {
    'netbox_contract.Invoice.status+': [
        {'value': 'on_hold', 'label': 'On hold', 'color': 'orange', 'description': 'Waiting for the customer approval'},
    ],
}
```

### Run database migrations

```bash
(venv) $ cd /opt/netbox/netbox/
(venv) $ python3 manage.py migrate
```

### Upgrading to version 2.5

The migration to version 2.5 converts the monthly, yearly and non-recurring costs and the invoice templates of existing contracts into contract lines, and prints a report of the judgement calls it made (for example an invoice template whose total differs from the recurring cost). Invoices, invoice lines, invoice templates and the deprecated fields are not changed. The conversion can be run again at any time; contracts that already have contract lines are skipped:

```bash
(venv) $ python3 manage.py convert_contract_lines
```

### Upgrading to version 2.6: orphan assignments

Before version 2.6, deleting a device, site or other object left its contract assignments behind. From 2.6 the assignments are deleted with their object. The ones already left behind are not touched by the upgrade. List them, then delete them once you have looked at the list:

```bash
(venv) $ python3 manage.py cleanup_orphan_assignments          # list only, nothing is changed
(venv) $ python3 manage.py cleanup_orphan_assignments --apply  # delete the listed assignments
```

The report gives the number per object type and, for each assignment, its contract, the object type and the former identifier. Assignments whose object type is no longer installed are listed separately and are never deleted. Running the command again lists nothing once it is clean.

The custom script "Report currency mismatches" (in `scripts/netbox-contract.py`) lists existing records whose currency does not match their contract or invoice, without changing them.
