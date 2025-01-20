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
        # 'default_accounting_dimensions':{
        #     "account": "",
        #     "project": "",
        #     "cost center": "TO"
        # },
        'mandatory_contract_fields': [],
        'hidden_contract_fields': [],
        'mandatory_invoice_fields': [],
        'hidden_invoice_fields': [],
    }
}

FIELD_CHOICES = {
    'netbox_contract.Contract.internal_partie': (
        ('entity1', 'Entity 1', 'green'),
        ('entity2', 'Entity 2', 'yellow'),
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
