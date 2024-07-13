from django.db.models import Q
from netbox.filtersets import NetBoxModelFilterSet

from .models import (
    AccountingDimension,
    Contract,
    ContractAssignment,
    Invoice,
    InvoiceLine,
    ServiceProvider,
)


class ContractFilterSet(NetBoxModelFilterSet):
    class Meta:
        model = Contract
        fields = ('id', 'internal_partie', 'status', 'parent')

    def search(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value)
            | Q(external_reference__icontains=value)
            | Q(comments__icontains=value),
            Q(status__iexact='Active'),
        )


class InvoiceFilterSet(NetBoxModelFilterSet):
    class Meta:
        model = Invoice
        fields = ('id', 'contracts')

    def search(self, queryset, name, value):
        return queryset.filter(
            Q(number__icontains=value) | Q(contracts__name__icontains=value)
        )


class ServiceProviderFilterSet(NetBoxModelFilterSet):
    class Meta:
        model = ServiceProvider
        fields = ('id', 'name')

    def search(self, queryset, name, value):
        return queryset.filter(name__icontains=value)


class ContractAssignmentFilterSet(NetBoxModelFilterSet):
    class Meta:
        model = ContractAssignment
        fields = ('id', 'contract')

    def search(self, queryset, name, value):
        return queryset.filter(Q(contract__name__icontains=value))


class InvoiceLineFilterSet(NetBoxModelFilterSet):
    class Meta:
        model = InvoiceLine
        fields = ('id', 'invoice')

    def search(self, queryset, name, value):
        return queryset.filter(
            Q(comments__icontains=value) | Q(invoice__name__icontains=value)
        )


class AccountingDimensionFilterSet(NetBoxModelFilterSet):
    class Meta:
        model = AccountingDimension
        fields = ('name', 'value')

    def search(self, queryset, name, value):
        return queryset.filter(
            Q(comments__icontains=value) | Q(invoice__name__icontains=value)
        )
