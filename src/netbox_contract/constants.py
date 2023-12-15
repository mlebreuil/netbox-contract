from django.db.models import Q

SERVICE_PROVIDER_MODELS = Q(
    Q(app_label='circuits', model__in=('provider',))
    | Q(app_label='netbox_contract', model__in=('serviceprovider',))
)
