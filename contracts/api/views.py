from netbox.api.viewsets import NetBoxModelViewSet

from .. import filtersets, models
from .serializers import ContractSerializer, InvoiceSerializer

class ContractViewSet(NetBoxModelViewSet):
    queryset = models.Contract.objects.prefetch_related('circuits','tags')
    serializer_class = ContractSerializer

class InvoiceViewSet(NetBoxModelViewSet):
    queryset = models.Invoice.objects.prefetch_related(
        'contract', 'tags'
    )
    serializer_class = InvoiceSerializer
    filterset_class = filtersets.InvoiceFilterSet
