"""
Contracts reachable from the core objects in GraphQL (spec 006).

NetBox imports this module while the plugins initialise, before its own GraphQL types exist: no core GraphQL module
may be imported here, core and plugin types are only reached through strawberry.lazy() annotations.
"""

import logging
from typing import TYPE_CHECKING, Annotated

import strawberry
import strawberry_django
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db.models import Exists, OuterRef, Q
from utilities.querysets import RestrictedPrefetch

from .models import Contract, ContractAssignment, StatusChoices

if TYPE_CHECKING:
    from .graphql.types import ContractAssignmentType

logger = logging.getLogger('netbox.plugins.netbox_contract')

# The models of the `supported_models` setting that have a core GraphQL type
CORE_GRAPHQL_MODELS = (
    'circuits.circuit',
    'circuits.virtualcircuit',
    'dcim.site',
    'dcim.device',
    'dcim.rack',
    'virtualization.virtualmachine',
    'virtualization.cluster',
)


def covered_models():
    """The `supported_models` entries the extensions apply to; the others are skipped with a log line."""
    covered = []
    for label in settings.PLUGINS_CONFIG['netbox_contract'].get('supported_models') or []:
        label = label.lower()
        if label in CORE_GRAPHQL_MODELS:
            covered.append(label)
        else:
            logger.info('netbox_contract: %s has no core GraphQL type, contracts are not added to it', label)
    return covered


def viewable_assignments(user, **filters):
    """The assignments the user may see, whose contract the user may see as well."""
    return ContractAssignment.objects.restrict(user, 'view').filter(
        contract__in=Contract.objects.restrict(user, 'view'), **filters
    )


@strawberry.type
class ContractAssignmentsTypeExtension:
    models = covered_models()

    @strawberry_django.field(
        prefetch_related=lambda info: RestrictedPrefetch(
            'contract_assignments',
            info.context.request.user,
            'view',
            queryset=ContractAssignment.objects.filter(
                contract__in=Contract.objects.restrict(info.context.request.user, 'view')
            ).select_related('contract'),
        ),
    )
    def contract_assignments(
        self,
    ) -> list[Annotated['ContractAssignmentType', strawberry.lazy('netbox_contract.graphql.types')]]:
        return self.contract_assignments.all()


def _exists(info, queryset, prefix, active):
    user = info.context.request.user
    contracts = Contract.objects.restrict(user, 'view')
    if active:
        contracts = contracts.filter(status=StatusChoices.STATUS_ACTIVE)
    assignments = ContractAssignment.objects.restrict(user, 'view').filter(
        content_type=ContentType.objects.get_for_model(queryset.model),
        object_id=OuterRef(f'{prefix}pk'),
        contract__in=contracts,
    )
    return Q(Exists(assignments))


@strawberry.type
class ContractAssignmentsFilterExtension:
    models = covered_models()

    @strawberry_django.filter_field()
    def has_contracts(self, info: strawberry.Info, value: bool, queryset, prefix) -> Q:
        match = _exists(info, queryset, prefix, active=False)
        return match if value else ~match

    @strawberry_django.filter_field()
    def has_active_contract(self, info: strawberry.Info, value: bool, queryset, prefix) -> Q:
        match = _exists(info, queryset, prefix, active=True)
        return match if value else ~match


type_extensions = [ContractAssignmentsTypeExtension]
filter_extensions = [ContractAssignmentsFilterExtension]
