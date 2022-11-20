from netbox.api.routers import NetBoxRouter
from . import views

app_name = 'contracts'

router = NetBoxRouter()
router.register('contracts', views.ContractViewSet)
router.register('invoices', views.InvoiceViewSet)

urlpatterns = router.urls