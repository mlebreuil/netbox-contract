from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from netbox.api.viewsets import NetBoxModelViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from users.models import Token

from .. import filtersets, models
from ..services import amendments
from .serializers import (
    AccountingDimensionSerializer,
    ContractAssignmentSerializer,
    ContractLineAmendmentSerializer,
    ContractLineSerializer,
    ContractSerializer,
    ContractTypeSerializer,
    InvoiceLineSerializer,
    InvoiceSerializer,
    ServiceProviderSerializer,
    UnitSerializer,
)


class ContractViewSet(NetBoxModelViewSet):
    queryset = models.Contract.objects.prefetch_related(
        'parent', 'tags', 'external_party_object', 'parent__external_party_object'
    ).annotate(
        yearly_value=models.yearly_value_annotation()
    )
    serializer_class = ContractSerializer
    filterset_class = filtersets.ContractFilterSet

    def get_serializer(self, *args, **kwargs):
        # The contract values are computed once for a detail and for the whole page of a list
        if args and 'data' not in kwargs:
            instances = list(args[0]) if kwargs.get('many') else [args[0]]
            if all(isinstance(instance, models.Contract) for instance in instances):
                kwargs['context'] = {
                    **self.get_serializer_context(), 'contract_values': models.contract_values(instances)
                }
                if kwargs.get('many'):
                    args = (instances, *args[1:])
        return super().get_serializer(*args, **kwargs)


class InvoiceViewSet(NetBoxModelViewSet):
    queryset = models.Invoice.objects.prefetch_related('contracts', 'tags')
    serializer_class = InvoiceSerializer
    filterset_class = filtersets.InvoiceFilterSet


class ServiceProviderViewSet(NetBoxModelViewSet):
    queryset = models.ServiceProvider.objects.prefetch_related('tags')
    serializer_class = ServiceProviderSerializer
    filterset_class = filtersets.ServiceProviderFilterSet


class ContractAssignmentViewSet(NetBoxModelViewSet):
    queryset = models.ContractAssignment.objects.prefetch_related('contract', 'tags')
    serializer_class = ContractAssignmentSerializer
    filterset_class = filtersets.ContractAssignmentFilterSet


class InvoiceLineViewSet(NetBoxModelViewSet):
    queryset = models.InvoiceLine.objects.prefetch_related(
        'invoice', 'accounting_dimensions', 'tags'
    )
    serializer_class = InvoiceLineSerializer
    filterset_class = filtersets.InvoiceLineFilterSet


class AccountingDimensionViewSet(NetBoxModelViewSet):
    queryset = models.AccountingDimension.objects.prefetch_related('tags')
    serializer_class = AccountingDimensionSerializer
    filterset_class = filtersets.AccountingDimensionFilterSet


class ContractTypeViewSet(NetBoxModelViewSet):
    queryset = models.ContractType.objects.prefetch_related('tags')
    serializer_class = ContractTypeSerializer
    filterset_class = filtersets.ContractTypeFilterSet


class UnitViewSet(NetBoxModelViewSet):
    queryset = models.Unit.objects.prefetch_related('tags')
    serializer_class = UnitSerializer
    filterset_class = filtersets.UnitFilterSet


class AmendPermission(BasePermission):
    """
    Gate of the amend action: an authenticated user, with a write-enabled token when a token is used. The object
    permissions (view and amend on the line) are checked by the action itself, because NetBox maps every POST to the
    "add" permission (research D6).
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return not isinstance(request.auth, Token) or request.auth.write_enabled


class ContractLineViewSet(NetBoxModelViewSet):
    queryset = models.ContractLine.objects.select_related('contract', 'unit', 'replaces').prefetch_related(
        'accounting_dimensions', 'tags'
    )
    serializer_class = ContractLineSerializer
    filterset_class = filtersets.ContractLineFilterSet

    def get_permissions(self):
        if self.action == 'amend':
            return [AmendPermission()]
        return super().get_permissions()

    @extend_schema(request=ContractLineAmendmentSerializer, responses={201: ContractLineSerializer})
    @action(detail=True, methods=['post'])
    def amend(self, request, pk=None):
        """End this line and create the line that replaces it with a new unit price or quantity (FR-030)."""
        if not request.user.has_perm('netbox_contract.amend_contractline'):
            raise PermissionDenied()
        # Amending is an "amend" operation, not the "add" BaseViewSet restricts POST requests to
        lines = models.ContractLine.objects.restrict(request.user, 'view').restrict(request.user, 'amend')
        line = get_object_or_404(lines, pk=pk)
        data = ContractLineAmendmentSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        try:
            new = amendments.amend_contract_line(line, **data.validated_data)
        except amendments.AmendmentError as e:
            raise ValidationError({
                'non_field_errors' if field == '__all__' else field: message for field, message in e.errors.items()
            })
        return Response(ContractLineSerializer(new, context={'request': request}).data, status=status.HTTP_201_CREATED)
