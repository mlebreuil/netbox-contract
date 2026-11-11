# Research: Search contracts by external party name

Sources: NetBox 4.7.4 `netbox/netbox/filtersets.py` (`get_additional_lookups`), `utilities/forms/mixins.py` (`FilterModifierMixin`), the plugin's `filtersets.py`, `graphql/filters.py` and `graphql_extensions.py` (006-D5). No NEEDS CLARIFICATION remains; 009-D5 and 009-D4 list what implementation must confirm.

## 009-D1. One shared condition, one subquery per party type
- **Decision**: `external_party.party_name_condition(lookup, values)` returns a `Q`: `(external_party_object_type = <service provider type> AND external_party_object_id IN (service providers whose name satisfies the lookup)) OR (... circuit provider type ... Provider ...)`. `lookup` is a Django lookup name (`icontains`, `exact`, `iexact`). The quick search, the filterset and the GraphQL filter call it.
- **Rationale**: the generic foreign key has no join path; a subquery keeps the work in the one list query, so the query count does not grow with the number of contracts (009-SC-003). Testing the type with the ID is what keeps a service provider and a circuit provider with the same ID apart (009-FR-005). One builder means the three interfaces return the same contracts (009-SC-002). A `Q` with `IN (subquery)` returns each contract once, with no `distinct()` (009-FR-003).
- **Alternatives**: `GenericRelation` from the providers to contracts (rejected: adds a relation to a core model and a migration-free but invasive `ready()` hook, as 006-D4 did for a different need); annotating the party name on the queryset (rejected: needs a join per type and breaks the `.restrict()`/count behaviour of the list); an index table (rejected: stale on rename, the very problem of proposal 3).

## 009-D2. Filter names and lookups
- **Decision**: `external_party_name` (exact match on any of the given names, multi-value like NetBox's `name` filter), `external_party_name__ic` (contains, case-insensitive), `external_party_name__ie` (exact, case-insensitive), `external_party_name__n` (does not match: contracts whose party name is not one of the given, including contracts with no party). They are declared explicitly as `MultiValueCharFilter`s with a method, because NetBox's `get_additional_lookups` skips filters that have a `method`.
- **Rationale**: NetBox users expect these modifiers on a name filter and the filter form shows the modifier drop-down only for fields whose `field__lookup` filters exist (`FilterModifierMixin`, `_verify_lookups_with_filterset`); the set is the three that make sense for a name. The quick search uses contains-insensitive (009-FR-003). The name follows `external_reference` and `external_party_object_*` of the model, and the new filter sits next to `service_provider_id` and `provider_id` (009-FR-006).
- **Alternatives**: two filters, one per type (rejected: the user does not know the type, 009-US2-3); `q` only (rejected: proposal 2 asks for a filter); every NetBox modifier (`isw`, `iew`, `nic`, `empty`, ...) (rejected: more surface for no stated need; they can be added later without breaking anything).
- **Open point**: whether `FilterModifierMixin` shows the modifier drop-down for a method-based filter. Test it in the tasks; if it does not, the form shows a plain text box and the modifiers stay available in the address and the REST API.

## 009-D3. Quick search
- **Decision**: `ContractFilterSet.search` ORs `party_name_condition('icontains', value)` with its three existing conditions; the Active-only `status__iexact='Active'` stays ANDed as today (009-FR-004).
- **Rationale**: smallest change satisfying 009-FR-001 to 009-FR-004. The quick search keeps its current, restrictive meaning; changing it is a separate request (spec Assumptions).
- **Alternatives**: a second queryset branch with `union` (rejected: loses chaining with other filters).

## 009-D4. GraphQL filter
- **Decision**: `ContractFilter.external_party_name` takes the plugin's string lookup type like `name` and `external_reference`, implemented as a `@strawberry_django.filter_field()` method (the pattern of 006-D5: `info`, `value`, `queryset`, `prefix`) that applies the supported lookups (`exact`, `i_exact`, `contains`, `i_contains`, `starts_with`, `i_starts_with`, `ends_with`, `i_ends_with`, `in_list`) through `party_name_condition`; several given lookups combine with AND.
- **Rationale**: same shape as the other string filters of the schema, so clients use one idiom (009-FR-008); the prefix keeps the filter correct when `ContractFilter` is nested (for example from a contract line or an assignment filter).
- **Open point**: confirm in implementation how the strawberry-django 4.7 lookup type exposes `NOT`/`OR` and the regex lookups; unsupported ones are ignored for this field and documented. If a custom method cannot take the lookup type, fall back to a plain `str` meaning "contains, case-insensitive" and document it.
- **Alternatives**: filter on `external_party_object` itself (rejected: a union type has no filter); a plain string only (kept as the fallback).

## 009-D5. Permissions
- **Decision**: the provider subqueries are not restricted to the providers the user may view. The result is still limited to the contracts the user may view (the list's, REST's and GraphQL's own restriction), and a provider's name is never added to the output (009-FR-011).
- **Rationale**: a contract the user can view already shows its party's name in the list, detail page, REST and GraphQL, so matching on it reveals nothing more. Restricting the subquery would hide contracts the user is allowed to see whenever they lack permission on providers, which is the surprising direction.
- **Open point**: confirm with the maintainer at review; the opposite choice is one `.restrict(user, 'view')` per subquery and costs a user argument on the builder.

## 009-D6. Tests
- **Decision**: new `tests/test_party_name.py`: quick search for both party types, case, once-only listing, other-field matches kept, non-Active excluded, contract without a party, same-ID service provider and circuit provider, empty text; the filter in the filterset, the list view address, REST and GraphQL with the same data, each modifier, combination with the status filter and with `service_provider_id`; rename takes effect; deleted party; ID filters unchanged; a query-count check equal for few and many contracts. The existing `query_counts.json` is verified, not re-recorded unless it changes (Constitution II).
- **Rationale**: each acceptance scenario and edge case is covered (Constitution II). Tests are written first and must fail before the change.

## 009-D7. Documentation and translation
- **Decision**: `docs/contract.md` (searching and filtering contracts by party name), `docs/api.md` (REST filter, GraphQL filter and one example), `CHANGELOG.md` Enhancements entry linked to #333 in the format of the latest release, French translation of the filter label (`makemessages` then `msgfmt`).
- **Rationale**: Constitution VII.
