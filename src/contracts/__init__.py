from extras.plugins import PluginConfig

class ContractsConfig(PluginConfig):
    name = 'netbox-contracts'
    verbose_name = 'Netbox contracts'
    description = 'Contract management plugin for Netbox'
    version = '1.0'
    author = 'Marc Lebreuil'
    author_email = 'marc@famillelebreuil.net'
    base_url = 'contracts'
    required_settings = []
    default_settings = {
    }

config = ContractsConfig
