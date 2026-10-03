from typing import TYPE_CHECKING, Annotated

import strawberry
import strawberry_django
from netbox.graphql.filters import NetBoxModelFilter, OrganizationalModelFilter, PrimaryModelFilter
from strawberry.scalars import ID
from strawberry_django import BaseFilterLookup, DateFilterLookup, FilterLookup, StrFilterLookup
from tenancy.graphql.filter_mixins import ContactFilterMixin, TenancyFilterMixin

from .. import models

if TYPE_CHECKING:
    from core.graphql.filters import ContentTypeFilter
    from netbox.graphql.filter_lookups import FloatLookup, IntegerLookup

    from .enums import *

__all__ = (
    'AccountingDimensionFilter',
    'ContractAssignmentFilter',
    'ContractFilter',
    'ContractLineFilter',
    'ContractTypeFilter',
    'InvoiceFilter',
    'InvoiceLineFilter',
    'ServiceProviderFilter',
    'UnitFilter',
)

LAZY = 'netbox_contract.graphql.filters'
LAZY_ENUMS = 'netbox_contract.graphql.enums'
LAZY_LOOKUPS = 'netbox.graphql.filter_lookups'


@strawberry_django.filter_type(models.ContractType, lookups=True)
class ContractTypeFilter(OrganizationalModelFilter):
    color: StrFilterLookup | None = strawberry_django.filter_field()


@strawberry_django.filter_type(models.ServiceProvider, lookups=True)
class ServiceProviderFilter(ContactFilterMixin, PrimaryModelFilter):
    name: StrFilterLookup | None = strawberry_django.filter_field()
    slug: StrFilterLookup | None = strawberry_django.filter_field()
    portal_url: StrFilterLookup | None = strawberry_django.filter_field()


@strawberry_django.filter_type(models.AccountingDimension, lookups=True)
class AccountingDimensionFilter(NetBoxModelFilter):
    name: StrFilterLookup | None = strawberry_django.filter_field()
    value: StrFilterLookup | None = strawberry_django.filter_field()
    status: BaseFilterLookup[Annotated['AccountingDimensionStatusEnum', strawberry.lazy(LAZY_ENUMS)]] | None = (
        strawberry_django.filter_field()
    )


@strawberry_django.filter_type(models.Unit, lookups=True)
class UnitFilter(NetBoxModelFilter):
    name: StrFilterLookup | None = strawberry_django.filter_field()
    description: StrFilterLookup | None = strawberry_django.filter_field()
    billing_method: BaseFilterLookup[Annotated['BillingMethodEnum', strawberry.lazy(LAZY_ENUMS)]] | None = (
        strawberry_django.filter_field()
    )
    months: Annotated['IntegerLookup', strawberry.lazy(LAZY_LOOKUPS)] | None = strawberry_django.filter_field()


@strawberry_django.filter_type(models.Contract, lookups=True)
class ContractFilter(ContactFilterMixin, TenancyFilterMixin, NetBoxModelFilter):
    name: StrFilterLookup | None = strawberry_django.filter_field()
    contract_type: Annotated['ContractTypeFilter', strawberry.lazy(LAZY)] | None = strawberry_django.filter_field()
    contract_type_id: ID | None = strawberry_django.filter_field()
    external_party_object_type: Annotated['ContentTypeFilter', strawberry.lazy('core.graphql.filters')] | None = (
        strawberry_django.filter_field()
    )
    external_party_object_id: ID | None = strawberry_django.filter_field()
    external_reference: StrFilterLookup | None = strawberry_django.filter_field()
    internal_party: StrFilterLookup | None = strawberry_django.filter_field()
    status: BaseFilterLookup[Annotated['ContractStatusEnum', strawberry.lazy(LAZY_ENUMS)]] | None = (
        strawberry_django.filter_field()
    )
    start_date: DateFilterLookup | None = strawberry_django.filter_field()
    end_date: DateFilterLookup | None = strawberry_django.filter_field()
    initial_term: Annotated['IntegerLookup', strawberry.lazy(LAZY_LOOKUPS)] | None = strawberry_django.filter_field()
    renewal_term: Annotated['IntegerLookup', strawberry.lazy(LAZY_LOOKUPS)] | None = strawberry_django.filter_field()
    notice_period: Annotated['IntegerLookup', strawberry.lazy(LAZY_LOOKUPS)] | None = (
        strawberry_django.filter_field()
    )
    currency: StrFilterLookup | None = strawberry_django.filter_field()
    invoice_frequency: Annotated['IntegerLookup', strawberry.lazy(LAZY_LOOKUPS)] | None = (
        strawberry_django.filter_field()
    )
    documents: StrFilterLookup | None = strawberry_django.filter_field()
    parent: Annotated['ContractFilter', strawberry.lazy(LAZY)] | None = strawberry_django.filter_field()
    parent_id: ID | None = strawberry_django.filter_field()
    billable: FilterLookup[bool] | None = strawberry_django.filter_field()


@strawberry_django.filter_type(models.ContractAssignment, lookups=True)
class ContractAssignmentFilter(NetBoxModelFilter):
    content_type: Annotated['ContentTypeFilter', strawberry.lazy('core.graphql.filters')] | None = (
        strawberry_django.filter_field()
    )
    object_id: ID | None = strawberry_django.filter_field()
    contract: Annotated['ContractFilter', strawberry.lazy(LAZY)] | None = strawberry_django.filter_field()
    contract_id: ID | None = strawberry_django.filter_field()


@strawberry_django.filter_type(models.ContractLine, lookups=True)
class ContractLineFilter(NetBoxModelFilter):
    contract: Annotated['ContractFilter', strawberry.lazy(LAZY)] | None = strawberry_django.filter_field()
    contract_id: ID | None = strawberry_django.filter_field()
    description: StrFilterLookup | None = strawberry_django.filter_field()
    quantity: Annotated['FloatLookup', strawberry.lazy(LAZY_LOOKUPS)] | None = strawberry_django.filter_field()
    unit_price: Annotated['FloatLookup', strawberry.lazy(LAZY_LOOKUPS)] | None = strawberry_django.filter_field()
    unit: Annotated['UnitFilter', strawberry.lazy(LAZY)] | None = strawberry_django.filter_field()
    unit_id: ID | None = strawberry_django.filter_field()
    currency: StrFilterLookup | None = strawberry_django.filter_field()
    start_date: DateFilterLookup | None = strawberry_django.filter_field()
    end_date: DateFilterLookup | None = strawberry_django.filter_field()
    accounting_dimensions: Annotated['AccountingDimensionFilter', strawberry.lazy(LAZY)] | None = (
        strawberry_django.filter_field()
    )
    replaces: Annotated['ContractLineFilter', strawberry.lazy(LAZY)] | None = strawberry_django.filter_field()
    replaces_id: ID | None = strawberry_django.filter_field()
    invoiced_at_conversion: FilterLookup[bool] | None = strawberry_django.filter_field()


@strawberry_django.filter_type(models.Invoice, lookups=True)
class InvoiceFilter(NetBoxModelFilter):
    number: StrFilterLookup | None = strawberry_django.filter_field()
    template: FilterLookup[bool] | None = strawberry_django.filter_field()
    status: BaseFilterLookup[Annotated['InvoiceStatusEnum', strawberry.lazy(LAZY_ENUMS)]] | None = (
        strawberry_django.filter_field()
    )
    date: DateFilterLookup | None = strawberry_django.filter_field()
    contracts: Annotated['ContractFilter', strawberry.lazy(LAZY)] | None = strawberry_django.filter_field()
    period_start: DateFilterLookup | None = strawberry_django.filter_field()
    period_end: DateFilterLookup | None = strawberry_django.filter_field()
    currency: StrFilterLookup | None = strawberry_django.filter_field()
    amount: Annotated['FloatLookup', strawberry.lazy(LAZY_LOOKUPS)] | None = strawberry_django.filter_field()
    documents: StrFilterLookup | None = strawberry_django.filter_field()


@strawberry_django.filter_type(models.InvoiceLine, lookups=True)
class InvoiceLineFilter(NetBoxModelFilter):
    invoice: Annotated['InvoiceFilter', strawberry.lazy(LAZY)] | None = strawberry_django.filter_field()
    invoice_id: ID | None = strawberry_django.filter_field()
    contract_line: Annotated['ContractLineFilter', strawberry.lazy(LAZY)] | None = strawberry_django.filter_field()
    contract_line_id: ID | None = strawberry_django.filter_field()
    unit: Annotated['UnitFilter', strawberry.lazy(LAZY)] | None = strawberry_django.filter_field()
    unit_id: ID | None = strawberry_django.filter_field()
    unit_price: Annotated['FloatLookup', strawberry.lazy(LAZY_LOOKUPS)] | None = strawberry_django.filter_field()
    quantity: Annotated['FloatLookup', strawberry.lazy(LAZY_LOOKUPS)] | None = strawberry_django.filter_field()
    currency: StrFilterLookup | None = strawberry_django.filter_field()
    amount: Annotated['FloatLookup', strawberry.lazy(LAZY_LOOKUPS)] | None = strawberry_django.filter_field()
    accounting_dimensions: Annotated['AccountingDimensionFilter', strawberry.lazy(LAZY)] | None = (
        strawberry_django.filter_field()
    )
