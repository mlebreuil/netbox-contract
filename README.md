# Contract plugin

NetBox plugin to manage contracts.


* Free software: MIT
* Documentation: https://mlebreuil.github.io/netbox-contract/

## Features

The plugin adds contracts and invoices model to NetBox.  
It allows to link contract with objects.  
And link invoice templates and invoices with contracts.  
Invoice lines can be linked to each invoice / invoice template.  
Accounting dimensions can be linked with invoice lines.  

## Compatibility

| NetBox Version | Plugin Version |
|----------------|----------------|
|     4.1        |      2.2       |
|     4.2        |      2.3       |
|     4.3        |      2.4       |

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
    }
}

```

* top_level_menu : If "Contracts" appears under the "Plugins" menu item or on its own
* default_accounting_dimensions: The accounting dimensions which will appear in the field' background when empty. Note that accounting dimensions are now managed as individual objects. The use of this field is deprecated.  
* mandatory_contract_fields, mandatory_invoice_fields: Fields which are not required by default and can be set as such. The list of fields is at the bottom of the contract import form.
* hidden_contract_fields, hidden_invoice_fields: List of fields to be hidden. Fields should not be required to be hidden.

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

### Run database migrations

```bash
(venv) $ cd /opt/netbox/netbox/
(venv) $ python3 manage.py migrate
```
