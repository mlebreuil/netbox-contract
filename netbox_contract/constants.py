from django.db.models import Q

SERVICE_PROVIDER_MODELS = Q(
    Q(app_label='circuits', model__in=('provider',))
    | Q(app_label='netbox_contract', model__in=('serviceprovider',))
)

SERVICE_PROVIDER_TYPES = (
    'provider',
    'serviceprovider',
)

ASSIGNEMENT_MODELS = Q(
    Q(app_label='circuits', model__in=('circuit',))
    | Q(app_label='circuits', model__in=('virtualcircuit',))
    | Q(app_label='dcim', model__in=('site',))
    | Q(app_label='dcim', model__in=('device',))
    | Q(app_label='dcim', model__in=('rack',))
    | Q(app_label='virtualization', model__in=('virtualmachine',))
    | Q(app_label='virtualization', model__in=('cluster',))
)
