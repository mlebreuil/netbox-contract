from decimal import Decimal
from typing import TYPE_CHECKING, Annotated

import strawberry
import strawberry_django
from circuits.models import Circuit, Provider, VirtualCircuit
from dcim.models import Device, Rack, Site
from extras.graphql.mixins import ContactsMixin
from netbox.graphql.optimization import build_gfk_prefetch
from netbox.graphql.types import NetBoxObjectType
from virtualization.models import Cluster, VirtualMachine

from .. import models
from .filters import *

if TYPE_CHECKING:
    from circuits.graphql.types import CircuitType, ProviderType, VirtualCircuitType
    from dcim.graphql.types import DeviceType, RackType, SiteType
    from netbox.graphql.types import ContentTypeType
    from tenancy.graphql.types import TenantType
    from virtualization.graphql.types import ClusterType, VirtualMachineType

__all__ = (
    'AccountingDimensionType',
    'ContractAssignmentType',
    'ContractLineType',
    'ContractType',
    'ContractTypeType',
    'InvoiceLineType',
    'InvoiceType',
    'ServiceProviderType',
    'UnitType',
)

LAZY = 'netbox_contract.graphql.types'
DEPRECATED_COST = 'Replaced by contract lines; kept for compatibility (shown with show_deprecated_fields).'

# The objects contracts are assigned to: the default `supported_models` setting. Objects of other models listed in
# the setting resolve to null; content_type and object_id still identify them (research D8).
ASSIGNABLE_MODELS = [Circuit, VirtualCircuit, Site, Device, Rack, VirtualMachine, Cluster]

# Relations are nullable when the related object may be hidden by the user's view permissions.
# Computed values (total, yearly, yearly billable) are properties, not model fields: fields='__all__' leaves them out
# and they stay REST only (FR-015a).


@strawberry_django.type(models.ContractType, fields='__all__', filters=ContractTypeFilter, pagination=True)
class ContractTypeType(NetBoxObjectType):
    color: str
    contracts: list[Annotated['ContractType', strawberry.lazy(LAZY)]]


@strawberry_django.type(models.ServiceProvider, fields='__all__', filters=ServiceProviderFilter, pagination=True)
class ServiceProviderType(ContactsMixin, NetBoxObjectType):
    pass


@strawberry_django.type(
    models.AccountingDimension, fields='__all__', filters=AccountingDimensionFilter, pagination=True
)
class AccountingDimensionType(NetBoxObjectType):
    contract_lines: list[Annotated['ContractLineType', strawberry.lazy(LAZY)]]
    invoice_lines: list[Annotated['InvoiceLineType', strawberry.lazy(LAZY)]] = strawberry_django.field(
        field_name='invoiceline_set'
    )


@strawberry_django.type(models.Unit, fields='__all__', filters=UnitFilter, pagination=True)
class UnitType(NetBoxObjectType):
    contract_lines: list[Annotated['ContractLineType', strawberry.lazy(LAZY)]]
    invoicelines: list[Annotated['InvoiceLineType', strawberry.lazy(LAZY)]]


@strawberry_django.type(
    models.Contract,
    exclude=['external_party_object_type', 'external_party_object_id'],
    filters=ContractFilter,
    pagination=True,
)
class ContractType(ContactsMixin, NetBoxObjectType):
    contract_type: Annotated['ContractTypeType', strawberry.lazy(LAZY)] | None
    tenant: Annotated['TenantType', strawberry.lazy('tenancy.graphql.types')] | None
    parent: Annotated['ContractType', strawberry.lazy(LAZY)] | None
    childs: list[Annotated['ContractType', strawberry.lazy(LAZY)]]
    lines: list[Annotated['ContractLineType', strawberry.lazy(LAZY)]]
    invoices: list[Annotated['InvoiceType', strawberry.lazy(LAZY)]]
    assignments: list[Annotated['ContractAssignmentType', strawberry.lazy(LAZY)]]
    external_party_object_type: Annotated['ContentTypeType', strawberry.lazy('netbox.graphql.types')] | None
    external_party_object_id: int | None
    mrc: Decimal | None = strawberry_django.field(deprecation_reason=DEPRECATED_COST)
    yrc: Decimal | None = strawberry_django.field(deprecation_reason=DEPRECATED_COST)
    nrc: Decimal | None = strawberry_django.field(deprecation_reason=DEPRECATED_COST)

    @strawberry_django.field(
        prefetch_related=build_gfk_prefetch('external_party_object', [models.ServiceProvider, Provider]),
        only=['external_party_object_type', 'external_party_object_id'],
    )
    def external_party_object(self) -> Annotated[
        Annotated['ServiceProviderType', strawberry.lazy(LAZY)]
        | Annotated['ProviderType', strawberry.lazy('circuits.graphql.types')],
        strawberry.union('ContractExternalPartyType'),
    ] | None:
        return self.external_party_object


@strawberry_django.type(
    models.ContractAssignment,
    exclude=['content_type', 'object_id'],
    filters=ContractAssignmentFilter,
    pagination=True,
)
class ContractAssignmentType(NetBoxObjectType):
    contract: Annotated['ContractType', strawberry.lazy(LAZY)] | None
    content_type: Annotated['ContentTypeType', strawberry.lazy('netbox.graphql.types')]
    object_id: int

    @strawberry_django.field(
        prefetch_related=build_gfk_prefetch('content_object', ASSIGNABLE_MODELS),
        only=['content_type', 'object_id'],
    )
    def content_object(self) -> Annotated[
        Annotated['CircuitType', strawberry.lazy('circuits.graphql.types')]
        | Annotated['VirtualCircuitType', strawberry.lazy('circuits.graphql.types')]
        | Annotated['SiteType', strawberry.lazy('dcim.graphql.types')]
        | Annotated['DeviceType', strawberry.lazy('dcim.graphql.types')]
        | Annotated['RackType', strawberry.lazy('dcim.graphql.types')]
        | Annotated['VirtualMachineType', strawberry.lazy('virtualization.graphql.types')]
        | Annotated['ClusterType', strawberry.lazy('virtualization.graphql.types')],
        strawberry.union('ContractAssignmentObjectType'),
    ] | None:
        obj = self.content_object
        return obj if obj is not None and type(obj) in ASSIGNABLE_MODELS else None


@strawberry_django.type(models.ContractLine, fields='__all__', filters=ContractLineFilter, pagination=True)
class ContractLineType(NetBoxObjectType):
    contract: Annotated['ContractType', strawberry.lazy(LAZY)] | None
    unit: Annotated['UnitType', strawberry.lazy(LAZY)] | None
    accounting_dimensions: list[Annotated['AccountingDimensionType', strawberry.lazy(LAZY)]]
    replaces: Annotated['ContractLineType', strawberry.lazy(LAZY)] | None
    replaced_by: list[Annotated['ContractLineType', strawberry.lazy(LAZY)]]
    invoicelines: list[Annotated['InvoiceLineType', strawberry.lazy(LAZY)]]


@strawberry_django.type(models.Invoice, fields='__all__', filters=InvoiceFilter, pagination=True)
class InvoiceType(NetBoxObjectType):
    contracts: list[Annotated['ContractType', strawberry.lazy(LAZY)]]
    invoicelines: list[Annotated['InvoiceLineType', strawberry.lazy(LAZY)]]
    template: bool = strawberry_django.field(
        deprecation_reason='Invoice templates are replaced by contract lines; kept for reference.'
    )


@strawberry_django.type(models.InvoiceLine, fields='__all__', filters=InvoiceLineFilter, pagination=True)
class InvoiceLineType(NetBoxObjectType):
    invoice: Annotated['InvoiceType', strawberry.lazy(LAZY)] | None
    contract_line: Annotated['ContractLineType', strawberry.lazy(LAZY)] | None
    unit: Annotated['UnitType', strawberry.lazy(LAZY)] | None
    accounting_dimensions: list[Annotated['AccountingDimensionType', strawberry.lazy(LAZY)]]
