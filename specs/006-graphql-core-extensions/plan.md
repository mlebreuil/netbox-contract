# Implementation Plan: Contracts reachable from core objects in GraphQL

**Branch**: `318-assess-against-netbox-4-7-4` | **Date**: 2026-10-29 | **Spec**: [spec.md](spec.md)

**Depends on**: [008-netbox-47-baseline](../008-netbox-47-baseline/spec.md) (minimum NetBox 4.7.0).

## Summary

Use NetBox 4.7's plugin GraphQL extension points to add, on the core types of the models in `supported_models` that have a GraphQL type (default: device, site, rack, circuit, virtual circuit, virtual machine, cluster), a `contract_assignments` field and two list filters, `has_contracts` and `has_active_contract`. A `GenericRelation` added to those core models at start-up lets the field be prefetched (constant query count) and lets the filters use a subquery. Consequence accepted in the clarifications: deleting such an object now deletes its assignments.

## Technical Context

**Language/Version**: Python 3.12 to 3.14, Django 6.1 (NetBox 4.7.4)

**Primary Dependencies**: NetBox 4.7 `graphql_extensions` plugin hook (`type_extensions`, `filter_extensions`), strawberry-graphql(-django), `RestrictedPrefetch`; no new dependency

**Storage**: no schema change; `GenericRelation` creates no column. No migration (checked with `makemigrations --check`).

**Testing**: GraphQL view tests via `APIViewTestCases.GraphQLTestCase`-style requests, a query-count test, permission tests

**Project Type**: NetBox plugin

**Performance Goals**: constant number of queries for a list with contracts (SC-003)

**Constraints**: no core GraphQL import at module level (circular import); names unique; start-up must survive a supported model without a GraphQL type (log and skip)

**Scale/Scope**: 7 default models, 1 new module, a few lines in `__init__.py`'s `ready()`, docs, tests

## Constitution Check

| Principle | Assessment |
|-----------|------------|
| I. NetBox-native | Pass: uses the official extension hook. |
| II. Tested behaviour | Pass. Tests first for every scenario, permissions, query count, unchanged existing queries. |
| III. Lint-clean | Pass. |
| IV. Data safety | **Attention**: the relation introduces cascade deletion of assignments when a core object is deleted. Accepted by the owner (clarification 2026-10-29); this feature's own upgrade steps modify or remove no existing row (the duplicate merge belongs to specification 004); orphans are removed only by the explicit, dry-run-by-default command `cleanup_orphan_assignments` (reports every row, never touches an assignment whose type cannot be judged); announced under Breaking Changes. Test: deleting a device removes its assignments, deleting a contract removes assignments but not the device. |
| V. Backward-compatible interfaces | Pass for GraphQL/REST/web (additive); the deletion behaviour is the one stated exception (FR-012). |
| VI. Simplicity | Pass with note: one module and one relation per model, no custom resolver framework. |
| VII. Documented change | Pass: `docs/api.md`, a docs page for the command, `CHANGELOG.md` (Enhancements + Breaking Changes). |

## Project Structure

```text
specs/006-graphql-core-extensions/
├── plan.md  research.md  data-model.md  quickstart.md
└── contracts/graphql-schema.md

netbox_contract/
├── graphql_extensions.py        # new: type + filter extensions
├── orphans.py                   # new: find_orphan_assignments()
├── management/commands/cleanup_orphan_assignments.py   # new
├── __init__.py                  # config: graphql_extensions, ready(): GenericRelation
├── models.py                    # unchanged
├── tests/test_graphql_extensions.py   # new
└── tests/test_orphan_cleanup.py       # new
docs/api.md
CHANGELOG.md
```

## Complexity Tracking

| Item | Why needed | Simpler alternative rejected because |
|------|------------|--------------------------------------|
| `GenericRelation` added to core models at start-up | Gives constant-query prefetch and a clean `Exists` filter | A per-object resolver issues one query per device (fails SC-003); a manual prefetch map duplicates what the ORM provides. Cost: cascade deletion, accepted. |
