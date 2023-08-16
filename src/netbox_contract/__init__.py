from extras.plugins import PluginConfig

class ContractsConfig(PluginConfig):
    name = 'netbox_contract'
    verbose_name = 'Netbox contract'
    description = 'Contract management plugin for Netbox'
    version = '2.0.6'
    author = 'Marc Lebreuil'
    author_email = 'marc@famillelebreuil.net'
    base_url = 'contracts'
    min_version = "3.5.0"
    required_settings = []
    default_settings = {
        'top_level_menu': False,
    }

config = ContractsConfig
