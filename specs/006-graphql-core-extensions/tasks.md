# Tasks: Contracts reachable from core objects in GraphQL

**Input**: `specs/006-graphql-core-extensions/` (plan.md, spec.md, research.md R1-R8, data-model.md, contracts/graphql-schema.md, quickstart.md)

**Tests**: required and written first (constitution II).

**Depends on**: 008 done.

**Test command**: `cd ../netbox && NETBOX_CONFIGURATION=netbox.configuration_testing venv/bin/python netbox/manage.py test netbox_contract.tests.test_graphql_extensions netbox_contract.tests.test_orphan_cleanup netbox_contract.tests.test_graphql --keepdb`

## Phase 1: Setup

- [X] T001 Read `netbox_contract/graphql/types.py` (`ContractAssignmentType`, `ASSIGNABLE_MODELS`) and NetBox 4.7.4 `netbox/plugins/__init__.py` plus `docs/plugins/development/graphql-api.md` for the exact attribute name and signature of `graphql_extensions`, the type extension mixin (`models = [...]`) and the filter extension; note any difference from `research.md` R1 in that file before coding.
- [X] T002 Create `netbox_contract/tests/test_graphql_extensions.py` and `netbox_contract/tests/test_orphan_cleanup.py` with fixtures: three devices (no contract, one canceled contract, one active contract), a site, a user without contract permission, a user constrained to one contract, a helper to post a GraphQL query as a user with a token.

## Phase 2: Foundational

- [X] T003 Add `netbox_contract/graphql_extensions.py` with empty `type_extensions = []` and `filter_extensions = []`, register it in `netbox_contract/__init__.py` (`graphql_extensions`), and check NetBox starts and the existing `test_graphql` passes (SC-005 baseline).

**Checkpoint**: the hook is wired, nothing else changed.

## Phase 3: User Story 1 - Read the contracts of an object (P1) 🎯 MVP

**Goal**: `contract_assignments` field on the covered core types. **Independent test**: query a device with two contracts.

### Tests first
- [X] T004 [US1] Failing tests: device with two contracts returns both with contract name, status, end date; device with none returns an empty list; a user without contract view permission gets an empty list; a constrained user gets only permitted contracts; the field exists on exactly the types of `supported_models` that have a GraphQL type and on no other type (schema introspection); a supported model without a GraphQL type is skipped and NetBox starts; names do not collide with another extending plugin (FR-008).
- [X] T005 [US1] Failing test: the query count for a list of 2 devices with contracts equals that for 20 devices (SC-003).
- [X] T006 [US1] Failing tests: deleting a device deletes its assignments, deleting a contract deletes its assignments but not the device, deleting an object that has no assignment works (FR-012).

### Implementation
- [X] T007 [US1] In `graphql_extensions.py` build, from `supported_models` ∩ core models with a GraphQL type, a type-extension mixin adding `contract_assignments: list[ContractAssignmentType]` resolved from the prefetched relation with `RestrictedPrefetch` limited to `ContractAssignment` viewable by the user (R3); no core GraphQL import at module level.
- [X] T008 [US1] In `netbox_contract/__init__.py` `ready()` add the `GenericRelation` `contract_assignments` (unique `related_query_name`, only if the attribute is absent) to each covered model (R4). Confirm `makemigrations --check` shows nothing.
- [X] T009 [US1] Run T004-T006 until green; fix N+1 if T005 fails.

## Phase 4: User Story 2 - Find objects with or without a contract (P2)

**Independent test**: three devices, each filter.

### Tests first
- [X] T010 [US2] Failing tests: `has_contracts` true/false; `has_active_contract` true/false (status active only, dates ignored); a user without contract permission sees every object as without contract; a hidden active contract does not count; combined with `site`, `status`, `name` filters (FR-004, FR-005).

### Implementation
- [X] T011 [US2] Add the filter extension with `has_contracts` and `has_active_contract` using `Exists(ContractAssignment.objects.restrict(user, 'view').filter(content_type=..., object_id=OuterRef('pk')))`, the second also restricting `Contract` to viewable and `status='active'` (R5). Run T010.

## Phase 5: User Story 3 - Existing clients unaffected (P3)

- [X] T012 [US3] Run the unchanged existing `test_graphql`, `test_api`, `test_views`; add one test that queries a core type without the new field and gets identical output; add a test that two extensions on `dcim.device` load together (FR-008).

## Phase 6: User Story 4 - Clean up orphan assignments (P3)

### Tests first
- [X] T013 [US4] Failing tests in `test_orphan_cleanup.py`: two orphans and one valid assignment (create then delete the object with the relation temporarily bypassed, e.g. `QuerySet._raw_delete`, to mimic old behaviour) → default run reports the two (contract, type, former id) and deletes nothing; `--apply` deletes exactly the two in one transaction; second run reports none; assignment with a content type that has no installed model is listed separately and kept in both modes; exit code 0.

### Implementation
- [X] T014 [US4] Create `netbox_contract/orphans.py` with `find_orphan_assignments()` returning orphans and "cannot judge" rows (R8), and `netbox_contract/management/commands/cleanup_orphan_assignments.py` (`--apply`, dry-run default, `transaction.atomic`, report format of `contracts/graphql-schema.md`). Run T013.

## Phase 7: Polish

- [X] T015 [P] `docs/api.md` GraphQL section: field, both filters, permission behaviour, the example query of the contract; new docs section for the cleanup command (dry-run default, `--apply`, "cannot judge" list), linked from the docs index if there is a maintenance page.
- [X] T016 [P] `CHANGELOG.md`: Enhancements (GraphQL field and filters, cleanup command), Breaking Changes (assignments are deleted with their object; run the command once after upgrading to remove old orphans).
- [ ] T017 `ruff check`, `makemigrations --check --dry-run` (no change), full suite, `quickstart.md` manual steps including the delete check and the command.
- [ ] T018 Stage the files for the owner to commit; do not bypass the pre-commit hook.

## Dependencies and order

008 → T001 → T002 → T003 → US1 → US2 (needs the relation of T008) → US3 → US4 (needs the relation only for the cascade semantic; independent otherwise) → Polish. T015 and T016 parallel.

## Implementation strategy

MVP = US1. US2 follows because it builds on the same relation. US4 and the Breaking Changes note must ship in the same release as the cascade.
