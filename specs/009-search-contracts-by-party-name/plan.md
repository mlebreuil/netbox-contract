# Implementation Plan: Search contracts by external party name

**Branch**: `333-search-contracts-by-party-name` | **Date**: 2026-11-11 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/009-search-contracts-by-party-name/spec.md` (issue #333, proposals 1 and 2).

## Summary

A contract's external party is a generic foreign key (type + ID), so its name cannot be reached by a join. For each party type (service provider, circuit provider) a subquery selects the providers whose name satisfies the text, combined with the contract's party type; the two are OR-ed. One small module builds that condition and is shared by the quick search, the list/REST filterset and the GraphQL filter, so the three interfaces cannot disagree (009-SC-002). The quick search adds the condition to its existing OR and keeps its Active-only restriction. A new filter `external_party_name` (with the lookup modifiers `__ic`, `__ie`, `__n`) is added to the filterset and the filter form, and an `external_party_name` string filter to the GraphQL contract filter. No model change, no migration.

## Technical Context

**Language/Version**: Python 3.12 to 3.14, Django 6.1 (NetBox 4.7.4)

**Primary Dependencies**: NetBox `NetBoxModelFilterSet`, `MultiValueCharFilter`, strawberry-django filters; no new dependency

**Storage**: none; no migration (`makemigrations --check` must stay clean)

**Testing**: Django tests through NetBox's test runner: filterset tests, list view, REST and GraphQL tests, query-count baseline

**Target Platform**: NetBox plugin (4.7+)

**Project Type**: NetBox plugin

**Performance Goals**: the contract list keeps a fixed query count; the party-name match is a subquery inside the one list query (009-SC-003)

**Constraints**: ID filters, fields and REST/GraphQL outputs unchanged (009-FR-010); global search unchanged (009-FR-012)

**Scale/Scope**: 1 new module, 3 edited modules (`filtersets.py`, `forms.py`, `graphql/filters.py`), 1 new test module, docs, changelog, French translation of one label, 4 global documents

## Constitution Check

| Principle | Assessment |
|-----------|------------|
| I. NetBox-native | Pass: standard filterset filters, filter-form field, strawberry filter. Lookup modifiers follow NetBox's `field__lookup` naming. |
| II. Tested behaviour | Pass, tests first: each acceptance scenario and edge case of the spec (see Tests below). The query-count baseline is checked, and re-recorded only if the list view count changes, with a stated reason. |
| III. Lint-clean | Pass, through the pre-commit hook. |
| IV. Data safety | Pass: read-only feature, no migration. |
| V. Backward-compatible interfaces | Pass: filters are additive; `service_provider_id`, `provider_id` and all outputs unchanged. |
| VI. Simplicity | Pass: no dependency; the condition builder is a small module without view dependencies (database access only through the two provider querysets). |
| VII. Documented change | Pass: `docs/contract.md`, `docs/api.md`, `CHANGELOG.md`, French translation (see Global documents and tasks). README unchanged (no setting or requirement). |
| VIII. Traceable specifications | Pass: identifiers qualified `009-`; code cites `009-FR-nnn`; global documents updated. |
| IX. Human accountability | Pass: issue and pull request text are drafted only on request, as drafts. |

No Complexity Tracking entry.

## Global documents

| Document | Changed? | What changes |
|---|---|---|
| data-model.md | no | Nothing stored (009-FR-010). |
| contracts/rest-api.md | yes | `contracts/` filters `external_party_name` and its modifiers (009-FR-007, 009-D2). |
| contracts/graphql.md | yes | `ContractFilter.external_party_name` (009-FR-008, 009-D4). |
| contracts/ui.md | yes | Contract filter form: `external_party_name` in the Parties section; quick search covers the party name (009-FR-001, 009-FR-002, 009-FR-006). |
| contracts/routes.md | no | No route added or renamed. |
| contracts/operations.md | no | |
| behaviours.md | yes | Rule: contracts are found by the name of their external party (009-FR-001 to 009-FR-009). |

`registry.md` is regenerated (`python utils/spec_ids.py registry`).

## Project Structure

### Documentation (this feature)

```text
specs/009-search-contracts-by-party-name/
├── spec.md  plan.md  research.md  data-model.md  quickstart.md
├── checklists/requirements.md
├── contracts/filters.md
└── tasks.md             # /speckit-tasks
```

### Source code

```text
netbox_contract/
├── external_party.py         # new: party_name_condition(lookup, values) shared by the three interfaces
├── filtersets.py             # ContractFilterSet: search(), external_party_name and modifiers
├── forms.py                  # ContractFilterForm: external_party_name in the Parties fieldset
├── graphql/filters.py        # ContractFilter.external_party_name
├── locale/fr/LC_MESSAGES/    # label of the new filter field
└── tests/test_party_name.py  # new
docs/contract.md, docs/api.md, CHANGELOG.md
specs/_global/...             # four documents above + registry.md
```

**Structure Decision**: the plugin's standard layout; one new module because the condition is needed by `filtersets.py` and `graphql/filters.py` (009-D1).
