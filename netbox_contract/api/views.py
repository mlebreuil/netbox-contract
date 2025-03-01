from django.db.models import Case, F, When
from django.db.models.functions import Round
from netbox.api.viewsets import NetBoxModelViewSet

from .. import filtersets, models
from .serializers import (
    AccountingDimensionSerializer,
    ContractAssignmentSerializer,
    ContractSerializer,
    ContractTypeSerializer,
    InvoiceLineSerializer,
    InvoiceSerializer,
    ServiceProviderSerializer,
)


class ContractViewSet(NetBoxModelViewSet):
    queryset = models.Contract.objects.prefetch_related('parent', 'tags').annotate(
        calculated_rc=Round(
            Case(When(yrc__gt=0, then=F('yrc') / 12), default=F('mrc') * 12),
            precision=2,
        )
    )
    serializer_class = ContractSerializer
    filterset_class = filtersets.ContractFilterSet


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
    queryset = models.InvoiceLine.objects.prefetch_related(
        'invoice', 'accounting_dimensions', 'tags'
    )
    serializer_class = InvoiceLineSerializer
    filterset_class = filtersets.InvoiceLineFilterSet


class AccountingDimensionViewSet(NetBoxModelViewSet):
    queryset = models.AccountingDimension.objects.prefetch_related('tags')
    serializer_class = AccountingDimensionSerializer


class ContractTypeViewSet(NetBoxModelViewSet):
    queryset = models.ContractType.objects.prefetch_related('tags')
    serializer_class = ContractTypeSerializer
