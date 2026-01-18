from django.db.models import Q
from django.conf import settings

plugin_settings = settings.PLUGINS_CONFIG['netbox_contract']

ASSIGNEMENT_TYPES = plugin_settings.get('supported_models')

SERVICE_PROVIDER_TYPES = (
    'circuits.provider',
    'netbox_contract.serviceprovider',
)

# ASSIGNEMENT_TYPES = (
#     'circuits.circuit',
#     'circuits.virtualcircuit',
#     'dcim.site',
#     'dcim.device',
#     'dcim.rack',
#     'virtualization.virtualmachine',
#     'virtualization.cluster',
#     'ipam.ipaddress',
#     'ipam.prefix',
# )


def build_models_q(model_strings):
    """Build a Q object from a list of 'app_label.model' strings."""
    q = Q()
    for model_string in model_strings:
        app_label, model = model_string.split('.')
        q |= Q(app_label=app_label, model=model)
    return q


ASSIGNEMENT_MODELS = build_models_q(ASSIGNEMENT_TYPES)
SERVICE_PROVIDER_MODELS = build_models_q(SERVICE_PROVIDER_TYPES)
