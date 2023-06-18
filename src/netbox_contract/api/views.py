from netbox.api.viewsets import NetBoxModelViewSet

from .. import filtersets, models
from .serializers import ContractSerializer, InvoiceSerializer, ServiceProviderSerializer, ContractAssignementSerializer

class ContractViewSet(NetBoxModelViewSet):
    queryset = models.Contract.objects.prefetch_related(
        'parent','circuit','tags'
        )
    serializer_class = ContractSerializer

class InvoiceViewSet(NetBoxModelViewSet):
    queryset = models.Invoice.objects.prefetch_related(
        'contracts', 'tags'
    )
    serializer_class = InvoiceSerializer
    filterset_class = filtersets.InvoiceFilterSet

class ServiceProviderViewSet(NetBoxModelViewSet):
    queryset = models.ServiceProvider.objects.prefetch_related('tags')
    serializer_class = ServiceProviderSerializer

class ContractAssignementViewSet(NetBoxModelViewSet):
    queryset = models.ContractAssignement.objects.prefetch_related('contract','tags')
    serializer_class = ContractAssignementSerializer
