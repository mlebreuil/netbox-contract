from django.utils.translation import gettext as _
from netbox.events import EventType, EVENT_TYPE_KIND_WARNING
from netbox.plugins import PluginConfig


class ContractsConfig(PluginConfig):
    name = 'netbox_contract'
    verbose_name = 'Netbox contract'
    description = 'Contract management plugin for Netbox'
    version = '2.4.1'
    author = 'Marc Lebreuil'
    author_email = 'marc@famillelebreuil.net'
    base_url = 'contracts'
    min_version = '4.3.0'
    required_settings = []
    default_settings = {
        'top_level_menu': False,
        'mandatory_contract_fields': [],
        'hidden_contract_fields': [],
        'mandatory_invoice_fields': [],
        'hidden_invoice_fields': [],
        'mandatory_dimensions': [],
        'days_before_notice_notification': 30,
    }

    def ready(self):
        super().ready()

        EventType('contract_notice', _('Contract notice period approaching'), kind=EVENT_TYPE_KIND_WARNING).register()

        from .jobs import ContractEventTrigger as ContractEventTrigger


config = ContractsConfig
