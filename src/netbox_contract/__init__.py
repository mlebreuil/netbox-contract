from extras.plugins import PluginConfig

class ContractsConfig(PluginConfig):
    name = 'netbox_contract'
    verbose_name = 'Netbox contract'
    description = 'Contract management plugin for Netbox'
    version = '1.0.3'
    author = 'Marc Lebreuil'
    author_email = 'marc@famillelebreuil.net'
    base_url = 'contract'
    required_settings = []
    default_settings = {
    }

config = ContractsConfig
