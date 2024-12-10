# Contract pluggin
## Overview
The pluggin adds contracts and invoices model to Netbox.  
It allows to register contract with objects.  
Add invoices to contracts. 

Check the [documentation](https://mlebreuil.github.io/netbox-contract/) for additional information 

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

Internal partie reference the legal entity of your organization that is a partie to the contract.  
The first currency will also be the default currency for contracts.  

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
