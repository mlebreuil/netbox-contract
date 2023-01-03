# Contract pluggin
## Overview
The pluggin adds contracts and invoices model to Netbox.  
It allows to register contract with objects.  
Add invoices to contracts.  

## Installation
### get the source file  
download the file at:  
"https://github.com/mlebreuil/netbox-contract/archive/refs/tags/{{ contract_version }}.tar.gz"   

### Activate venv
To ensure our plugin is accessible to the NetBox installation, we first need to activate the Python [virtual environment](https://docs.python.org/3/library/venv.html) that was created when we installed NetBox. To do this, determine the virtual environment's path (this will be `/opt/netbox/venv/` if you use the documentation's defaults) and activate it:

```bash
$ source /opt/netbox/venv/bin/activate
```

### Install the package 

```bash
$ python3 -m pip install https://github.com/mlebreuil/netbox-contract/archive/refs/tags/v1.0.0.tar.gz
```

### Configure NetBox

Finally, we need to configure NetBox to enable our new plugin. Over in the NetBox installation path, open `netbox/netbox/configuration.py` and look for the `PLUGINS` parameter; this should be an empty list. (If it's not yet defined, go ahead and create it.) Add the name of our plugin to this list:

```python
# configuration.py
PLUGINS = [
    'contracts',
]
```
### Run database migrations

```bash
(venv) $ cd /opt/netbox/netbox/
(venv) $ python3 manage.py migrate
```