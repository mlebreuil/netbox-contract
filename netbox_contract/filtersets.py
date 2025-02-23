import django_filters
from django.db.models import Q
from netbox.filtersets import NetBoxModelFilterSet
from tenancy.filtersets import TenancyFilterSet

from .models import (
    AccountingDimension,
    AccountingDimensionStatusChoices,
    Contract,
    ContractAssignment,
    CurrencyChoices,
    InternalEntityChoices,
    Invoice,
    InvoiceLine,
    ServiceProvider,
    StatusChoices,
)


class ContractFilterSet(NetBoxModelFilterSet, TenancyFilterSet):
    status = django_filters.MultipleChoiceFilter(choices=StatusChoices, null_value=None)
    internal_partie = django_filters.MultipleChoiceFilter(
        choices=InternalEntityChoices, null_value=None
    )
    currency = django_filters.MultipleChoiceFilter(
        choices=CurrencyChoices, null_value=None
    )

    class Meta:
        model = Contract
        fields = (
            'id',
            'name',
            'external_reference',
            'start_date',
            'end_date',
            'initial_term',
            'parent',
        )

    def search(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value)
            | Q(external_reference__icontains=value)
            | Q(comments__icontains=value),
            Q(status__iexact='Active'),
        )


class InvoiceFilterSet(NetBoxModelFilterSet):
    currency = django_filters.MultipleChoiceFilter(
        choices=CurrencyChoices, null_value=None
    )

    class Meta:
        model = Invoice
        fields = (
            'id',
            'number',
            'template',
            'date',
            'contracts',
            'period_start',
            'period_end',
            'amount',
        )

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
    currency = django_filters.MultipleChoiceFilter(
        choices=CurrencyChoices, null_value=None
    )

    class Meta:
        model = InvoiceLine
        fields = ('id', 'invoice', 'accounting_dimensions')

    def search(self, queryset, name, value):
        return queryset.filter(
            Q(comments__icontains=value) | Q(invoice__number__icontains=value)
        )


class AccountingDimensionFilterSet(NetBoxModelFilterSet):
    status = django_filters.MultipleChoiceFilter(
        choices=AccountingDimensionStatusChoices, null_value=None
    )

    class Meta:
        model = AccountingDimension
        fields = ('name', 'value')

    def search(self, queryset, name, value):
        return queryset.filter(Q(comments__icontains=value) | Q(name__icontains=value))
