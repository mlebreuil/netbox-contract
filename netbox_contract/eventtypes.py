from django.utils.translation import gettext_lazy as _
from netbox.events import EventType, EVENT_TYPE_KIND_WARNING

EventType(
    name='contract_notice_approaching',
    text=_('Contract notice period approaching'),
    kind=EVENT_TYPE_KIND_WARNING
).register()
