import django_filters
from circuits.models import Provider
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from netbox.filtersets import NetBoxModelFilterSet
from tenancy.filtersets import ContactModelFilterSet, TenancyFilterSet
from utilities.filtersets import register_filterset

from .models import (
    AccountingDimension,
    AccountingDimensionStatusChoices,
    BillingMethodChoices,
    Contract,
    ContractAssignment,
    ContractLine,
    ContractType,
    CurrencyChoices,
    InternalEntityChoices,
    Invoice,
    InvoiceLine,
    InvoiceStatusChoices,
    ServiceProvider,
    StatusChoices,
    Unit,
)


@register_filterset
class ContractFilterSet(ContactModelFilterSet, NetBoxModelFilterSet, TenancyFilterSet):
    status = django_filters.MultipleChoiceFilter(choices=StatusChoices, null_value=None)
    internal_party = django_filters.MultipleChoiceFilter(
        choices=InternalEntityChoices, null_value=None
    )
    currency = django_filters.MultipleChoiceFilter(
        choices=CurrencyChoices, null_value=None
    )
    contract_type = django_filters.ModelMultipleChoiceFilter(
        field_name='contract_type__name', to_field_name='name', queryset=ContractType.objects.all()
    )

    service_provider_id = django_filters.NumberFilter(
        field_name='external_party_object_id',
        method='filter_by_service_provider',
        label='Service provider'
    )

    provider_id = django_filters.NumberFilter(
        field_name='external_party_object_id',
        method='filter_by_circuit_provider',
        label='Circuit provider'
    )

    class Meta:
        model = Contract
        fields = (
            'id',
            'name',
            'status',
            'internal_party',
            'currency',
            'contract_type',
            'external_party_object_id',
            'external_reference',
            'parent',
            'billable',
        )

    def search(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value)
            | Q(external_reference__icontains=value)
            | Q(comments__icontains=value),
            Q(status__iexact='Active'),
        )

    def filter_by_service_provider(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            external_party_object_id=value,
            external_party_object_type=ContentType.objects.get_for_model(ServiceProvider)
        )

    def filter_by_circuit_provider(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            external_party_object_id=value,
            external_party_object_type=ContentType.objects.get_for_model(Provider)
        )


@register_filterset
class InvoiceFilterSet(NetBoxModelFilterSet):
    status = django_filters.MultipleChoiceFilter(choices=InvoiceStatusChoices, null_value=None)
    currency = django_filters.MultipleChoiceFilter(
        choices=CurrencyChoices, null_value=None
    )
    accounting_dimensions = django_filters.ModelChoiceFilter(
        field_name='invoicelines__accounting_dimensions',
        queryset=AccountingDimension.objects.all(),
        label='Accounting Dimension'
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


@register_filterset
class ServiceProviderFilterSet(ContactModelFilterSet, NetBoxModelFilterSet):
    class Meta:
        model = ServiceProvider
        fields = ('id', 'name')

    def search(self, queryset, name, value):
        return queryset.filter(name__icontains=value)


@register_filterset
class ContractTypeFilterSet(NetBoxModelFilterSet):
    class Meta:
        model = ContractType
        fields = ('name', 'description', 'color')

    def search(self, queryset, name, value):
        return queryset.filter(name__icontains=value)


@register_filterset
class ContractAssignmentFilterSet(NetBoxModelFilterSet):
    class Meta:
        model = ContractAssignment
        fields = ('id', 'contract')

    def search(self, queryset, name, value):
        return queryset.filter(Q(contract__name__icontains=value))


@register_filterset
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


@register_filterset
class AccountingDimensionFilterSet(NetBoxModelFilterSet):
    status = django_filters.MultipleChoiceFilter(
        choices=AccountingDimensionStatusChoices, null_value=None
    )

    class Meta:
        model = AccountingDimension
        fields = ('name', 'value')

    def search(self, queryset, name, value):
        return queryset.filter(Q(comments__icontains=value) | Q(name__icontains=value))


@register_filterset
class UnitFilterSet(NetBoxModelFilterSet):
    billing_method = django_filters.MultipleChoiceFilter(choices=BillingMethodChoices, null_value=None)

    class Meta:
        model = Unit
        fields = ('id', 'name', 'description', 'months')

    def search(self, queryset, name, value):
        return queryset.filter(Q(name__icontains=value) | Q(description__icontains=value))


@register_filterset
class ContractLineFilterSet(NetBoxModelFilterSet):
    contract_id = django_filters.ModelMultipleChoiceFilter(
        field_name='contract', queryset=Contract.objects.all(), label='Contract (ID)'
    )
    unit_id = django_filters.ModelMultipleChoiceFilter(
        field_name='unit', queryset=Unit.objects.all(), label='Unit (ID)'
    )
    unit = django_filters.ModelMultipleChoiceFilter(
        field_name='unit__name', to_field_name='name', queryset=Unit.objects.all(), label='Unit (name)'
    )
    billing_method = django_filters.MultipleChoiceFilter(
        field_name='unit__billing_method', choices=BillingMethodChoices, label='Billing method'
    )
    currency = django_filters.MultipleChoiceFilter(choices=CurrencyChoices, null_value=None)
    accounting_dimensions = django_filters.ModelMultipleChoiceFilter(
        queryset=AccountingDimension.objects.all(), label='Accounting dimension (ID)'
    )
    invoice_id = django_filters.NumberFilter(
        method='filter_by_invoice',
        label='Invoice (ID): lines of its contract and of their non-billable descendants',
    )

    class Meta:
        model = ContractLine
        fields = ('id', 'description', 'quantity', 'unit_price', 'start_date', 'end_date', 'invoiced_at_conversion')

    def search(self, queryset, name, value):
        return queryset.filter(
            Q(description__icontains=value) | Q(comments__icontains=value) | Q(contract__name__icontains=value)
        )

    def filter_by_invoice(self, queryset, name, value):
        invoice = Invoice.objects.filter(pk=value).first()
        if invoice is None:
            return queryset.none()
        contract_ids = {
            contract.pk for invoice_contract in invoice.contracts.all() for contract in invoice_contract.billing_scope()
        }
        return queryset.filter(contract__in=contract_ids)
