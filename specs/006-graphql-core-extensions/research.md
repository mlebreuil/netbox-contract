# Research: GraphQL core extensions

Source: NetBox 4.7.4 `netbox/plugins/__init__.py`, `netbox/graphql`, `docs/plugins/development/graphql-api.md`. No NEEDS CLARIFICATION remains.

## R1 - Hook
- **Decision**: declare `graphql_extensions = [...]` module path in `PluginConfig`, a module `graphql_extensions.py` exposing `type_extensions` and `filter_extensions` lists; each extension is a mixin class with `models = ['dcim.device', ...]`.
- **Rationale**: official 4.7 API. The module must not import core GraphQL modules at import time.

## R2 - Models covered
- **Decision**: default `supported_models` list intersected with models that have a core GraphQL type, evaluated when the extensions are built from the settings. A model without a type is skipped with a log line (NetBox raises `ImproperlyConfigured` if asked to extend it).
- **Rationale**: spec FR-002 and edge case.

## R3 - Field
- **Decision**: field `contract_assignments` returning `list[ContractAssignmentType]` (the plugin's existing type, which already exposes the contract), resolved from a prefetched relation restricted to the user's view permission with `RestrictedPrefetch`.
- **Rationale**: reuses the existing type, so the contract fields available are exactly the ones of the plugin's GraphQL API today. The name is plugin-specific to avoid clashes (FR-008).
- **Alternatives**: expose contracts directly (rejected: loses the per-assignment link); a field per model (rejected: one mixin works for all).

## R4 - Relation for prefetch and subquery
- **Decision**: in `ready()`, for each covered model add `GenericRelation(ContractAssignment, content_type_field='content_type', object_id_field='object_id', related_query_name='netbox_contract_assignment_<model>')` as `contract_assignments`, only when the attribute does not already exist.
- **Rationale**: lets Django prefetch generic relations in one query and gives a join path for filters. `related_query_name` is unique per model.
- **Consequence**: Django's collector deletes related assignments when the object is deleted (cascade) - decided in the clarifications. The upgrade leaves existing orphan rows untouched; R8 removes them on request.
- **Alternatives**: no relation and a manual `Prefetch` on `object_id__in` (rejected: breaks the query-count criterion and duplicates logic); database trigger (rejected: not NetBox-native).

## R5 - Filters
- **Decision**: `has_contracts: bool` and `has_active_contract: bool`, implemented with `Exists(ContractAssignment.objects.restrict(user, 'view').filter(content_type=<model ct>, object_id=OuterRef('pk')))`, the second adding `contract__status='active'`. The user comes from the request in the filter context; with no authenticated user, no contract counts.
- **Rationale**: spec FR-003 to FR-005 (only viewable contracts; active = status only). Using `Exists` avoids duplicates a join would create.
- **Restriction detail**: the subquery also restricts `Contract` for the active filter so a hidden active contract does not count.

## R6 - Tests
- **Decision**: new `tests/test_graphql_extensions.py`: schema contains the field and filters on the 7 types and not on other types; scenarios of US1 and US2; user without contract permission; constrained permission; `assertNumQueries`-style check equal for 2 and 20 devices; existing plugin GraphQL tests unchanged; deletion cascade test; unsupported model skipped.
- **Rationale**: constitution II.

## R7 - Documentation
- **Decision**: `docs/api.md` GraphQL section gets the field, both filters, permission note and one example query; `CHANGELOG.md` Enhancements (field, filters) and Breaking Changes (assignments deleted with the object).

## R8 - Orphan cleanup command
- **Decision**: management command `cleanup_orphan_assignments` (next to `convert_contract_lines`), dry-run by default, `--apply` deletes in one transaction. Orphan test: for each content type present in the assignments, the model class resolves and `model.objects.filter(pk__in=ids)` misses the identifier. Assignments whose content type has no model class are listed under a separate "cannot judge" heading and never deleted. Output: totals per object type and one line per orphan (assignment id, contract, type, former identifier). Idempotent.
- **Rationale**: constitution IV forbids silent deletion of user data and requires reporting judgement calls; an automatic data migration would delete without a chance to review. The command logic lives in a function (`find_orphan_assignments`) so tests and the command share it, as `conversion.py` does.
- **Alternatives**: data migration (rejected, silent); doing nothing (rejected by the owner, 2026-10-29).
