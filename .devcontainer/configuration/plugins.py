# Add your plugins and plugin settings here.
# Of course uncomment this file out.

# To learn how to build images with your required plugins
# See https://github.com/netbox-community/netbox-docker/wiki/Using-Netbox-Plugins

PLUGINS = [
    'netbox_contract',  # Loads demo data
]

PLUGINS_CONFIG = {
    'netbox_contract': {
        'top_level_menu': True,
        'mandatory_contract_fields': [],
        'hidden_contract_fields': [],
        'mandatory_invoice_fields': [],
        'hidden_invoice_fields': [],
    }
}

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
        ('active', 'Active', 'green'),
        ('canceled', 'Canceled', 'red'),
    ),
}
