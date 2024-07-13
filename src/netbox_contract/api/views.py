from django.db.models import F
from netbox.api.viewsets import NetBoxModelViewSet

from .. import filtersets, models
from .serializers import (
    AccountingDimensionSerializer,
    ContractAssignmentSerializer,
    ContractSerializer,
    InvoiceLineSerializer,
    InvoiceSerializer,
    ServiceProviderSerializer,
)


class ContractViewSet(NetBoxModelViewSet):
    queryset = models.Contract.objects.prefetch_related('parent', 'tags').annotate(
        yrc=F('mrc') * 12
    )
    serializer_class = ContractSerializer


class InvoiceViewSet(NetBoxModelViewSet):
    queryset = models.Invoice.objects.prefetch_related('contracts', 'tags')
    serializer_class = InvoiceSerializer
    filterset_class = filtersets.InvoiceFilterSet


class ServiceProviderViewSet(NetBoxModelViewSet):
    queryset = models.ServiceProvider.objects.prefetch_related('tags')
    serializer_class = ServiceProviderSerializer


class ContractAssignmentViewSet(NetBoxModelViewSet):
    queryset = models.ContractAssignment.objects.prefetch_related('contract', 'tags')
    serializer_class = ContractAssignmentSerializer


class InvoiceLineViewSet(NetBoxModelViewSet):
    queryset = models.InvoiceLine.objects.prefetch_related('invoice', 'tags')
    serializer_class = InvoiceLineSerializer


class AccountingDimensionViewSet(NetBoxModelViewSet):
    queryset = models.AccountingDimension.objects.prefetch_related('tags')
    serializer_class = AccountingDimensionSerializer
