from netbox.plugins import PluginConfig


class ContractsConfig(PluginConfig):
    name = 'netbox_contract'
    verbose_name = 'Netbox contract'
    description = 'Contract management plugin for Netbox'
    version = '2.6.0'
    author = 'Marc Lebreuil'
    author_email = 'marc@famillelebreuil.net'
    base_url = 'contracts'
    graphql_schema = 'graphql.schema.schema'
    min_version = '4.7.0'
    required_settings = []
    default_settings = {
        'top_level_menu': False,
        'mandatory_contract_fields': [],
        'hidden_contract_fields': [],
        'mandatory_invoice_fields': [],
        'hidden_invoice_fields': [],
        'mandatory_dimensions': [],
        'supported_models': [
            'circuits.circuit',
            'circuits.virtualcircuit',
            'dcim.site',
            'dcim.device',
            'dcim.rack',
            'virtualization.virtualmachine',
            'virtualization.cluster',
        ],
        'contract_assignments_display': 'both',  # options: 'tab', 'inline', 'both'
        'show_deprecated_fields': False,
    }

    def ready(self):
        super().ready()
        from . import signals  # noqa: F401

        add_contract_assignments_relation()


def add_contract_assignments_relation():
    """
    Give the objects contracts can be assigned to a `contract_assignments` relation: GraphQL prefetches and filters
    through it, and Django deletes the assignments of an object with the object (spec 006, research R4).
    """
    from django.apps import apps
    from django.contrib.contenttypes.fields import GenericRelation

    from .models import ContractAssignment

    for label in plugin_supported_models():
        try:
            model = apps.get_model(label)
        except (LookupError, ValueError):
            continue
        if hasattr(model, 'contract_assignments'):
            continue
        relation = GenericRelation(
            ContractAssignment,
            content_type_field='content_type',
            object_id_field='object_id',
            related_query_name=f'netbox_contract_assignment_{model._meta.model_name}',
        )
        relation.contribute_to_class(model, 'contract_assignments')


def plugin_supported_models():
    from django.conf import settings

    return settings.PLUGINS_CONFIG['netbox_contract'].get('supported_models') or []


config = ContractsConfig
