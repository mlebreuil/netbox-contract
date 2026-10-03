from django.urls import include, path
from utilities.urls import get_model_urls

from . import views

# Every view of a model is registered with register_model_view (views.py); NetBox adds the changelog and journal views.
MODEL_PREFIXES = (
    ('serviceprovider', 'serviceproviders'),
    ('contract', 'contracts'),
    ('unit', 'units'),
    ('contractline', 'contract-lines'),
    ('invoice', 'invoices'),
    ('contractassignment', 'assignments'),
    ('invoiceline', 'invoiceline'),
    ('accountingdimension', 'accountingdimension'),
    ('contracttype', 'contracttype'),
)

urlpatterns = [
    path('invoices/lines-preview/', views.InvoiceLinesPreviewView.as_view(), name='invoice_lines_preview'),
]

for model_name, prefix in MODEL_PREFIXES:
    urlpatterns += [
        path(f'{prefix}/', include(get_model_urls('netbox_contract', model_name, detail=False))),
        path(f'{prefix}/<int:pk>/', include(get_model_urls('netbox_contract', model_name))),
    ]
