"""Match contracts by the name of their external party (feature 009, issue #333).

The external party of a contract is a generic foreign key (type and ID), which cannot be searched through a join.
The condition below selects, for each party type, the providers whose name satisfies a lookup and keeps the contracts
that point to one of them. The contract quick search, the party-name filter of the list view and REST API and the
GraphQL filter all use it, so that they return the same contracts (009-SC-002).
"""

from circuits.models import Provider
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q

from .models import ServiceProvider

# The party types a contract can have today.
PARTY_MODELS = (ServiceProvider, Provider)


def party_name_condition(lookup, values, prefix=''):
    """A `Q` on contracts: the external party's name satisfies `name__<lookup>` for any of the values.

    `lookup` is a Django lookup name (`icontains`, `exact`, `iexact`, ...). `prefix` is the path to the contract when
    the condition is applied from a related model (for example `contract__`), as nested GraphQL filters do.

    A contract matches through the provider of its own party type only, never through a provider of the other type
    that has the same ID (009-FR-005). A contract without a party, or whose party no longer exists, matches nothing,
    and so does an empty list of values. Providers are reached through `IN (subquery)`, so each contract is selected
    once (009-FR-003).
    """
    nothing = Q(**{f'{prefix}pk__in': []})
    if not values:
        return nothing
    condition = nothing
    for model in PARTY_MODELS:
        names = Q()
        for value in values:
            names |= Q(**{f'name__{lookup}': value})
        condition |= Q(
            **{
                f'{prefix}external_party_object_type': ContentType.objects.get_for_model(model),
                f'{prefix}external_party_object_id__in': model.objects.filter(names).values('pk'),
            }
        )
    return condition
