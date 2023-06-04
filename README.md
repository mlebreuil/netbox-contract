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

Customize the location of the plugin's menu:


```python
# configuration.py
PLUGINS_CONFIG = {
    'netbox_contract': {
        'top_level_menu': True
    }
}

```

Customize the internal partie field.  
Internal partie reference the legal entity of your organization that is a partie to the contract.  

```python
# configuration.py
FIELD_CHOICES = {
    'netbox_contract.Contract.internal_partie': (
        ('Nagravision SARL', 'Nagravision SARL', 'green'),
        ('Nagra USA', 'Nagra USA', 'green'),
        ('Nagra India', 'Nagra India', 'green'),
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

Add support for Netbox 3.5 whcih become the minimum version supported to accoodate the removal of NetBoxModelCSVForm class (replaced by NetBoxModelImportForm) .
