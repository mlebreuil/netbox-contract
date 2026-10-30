# Tasks: Choose related objects with a search selector

**Input**: `specs/004-generic-object-selector/` (plan.md, spec.md, research.md R1-R9, data-model.md, contracts/forms-and-urls.md, quickstart.md)

**Migration**: US4 adds migration `0054` (the only one of 004 to 008).

**Tests**: required and written first (constitution II); each test task must be seen failing before its implementation task.

**Depends on**: 008 done (green baseline on NetBox 4.7.4).

**Test command**: `cd ../netbox && NETBOX_CONFIGURATION=netbox.configuration_testing venv/bin/python netbox/manage.py test netbox_contract.tests.test_assignment_selector netbox_contract.tests.test_views --keepdb`

## Phase 1: Setup

- [X] T001 Create `netbox_contract/tests/test_assignment_selector.py` with the shared fixtures (a device, a site, a circuit provider, a service provider, a contract, a user with view-only permission on devices, a user constrained to one device, a `supported_models` override helper).

## Phase 2: Foundational

- [X] T002 Update the posted names in the existing form-data of `netbox_contract/tests/test_views.py`: contract (about lines 90-91) to `external_party_object_content_type` / `external_party_object_object_id`; assignment (about lines 571-578) to `content_object_content_type` / `content_object_object_id`. Run: these tests fail now (expected, before the change).

**Checkpoint**: failing tests describe the new form contract.

## Phase 3: User Story 1 - Assign a contract by choosing the object (P1) 🎯 MVP

**Goal**: the assignment form uses the selector. **Independent test**: add an assignment to a device through the Contracts tab, then through the assignments list with a typed search.

### Tests first
- [X] T003 [US1] In `test_assignment_selector.py` add failing tests: (a) the Add link on a device Contracts tab opens the form with the device chosen and saving returns to the device page (FR-004); (b) old query names `content_type` / `object_id` also pre-select (R3); new names win when both present; (c) types offered equal `supported_models` that exist and are exposed in the REST API (FR-002, R6); (d) a user constrained to one device cannot choose another (FR-003); (e) type without object, and object without type, are refused with a message naming the type (FR-006); (f) edit shows the current type and object, changing the type clears the object (FR-005); (g) clone of an assignment returns `content_object_content_type`, `content_object_object_id`, `contract` (FR-012 of spec); (h) see User Story 4 for duplicates.

### Implementation
- [X] T004 [US1] `netbox_contract/forms.py` `ContractAssignmentForm` (about lines 799-823): derive from `GenericObjectFormMixin` before `NetBoxModelForm`; declare `content_object = GenericObjectChoiceField(content_type_queryset=ContentType.objects.filter(ASSIGNEMENT_MODELS) minus types without a REST list endpoint, required=True)`; put it in the fieldset in place of `content_type`/`object_id`; `Meta.fields` keeps only the real form fields (`contract`, `tags`). Constraint (data-model.md): both parts present or both absent.
- [X] T005 [US1] In the same form's `__init__` map legacy initial keys `content_type`/`object_id` to `content_object_content_type`/`content_object_object_id` when the new ones are absent (R3).
- [X] T006 [P] [US1] `netbox_contract/models.py` (about line 252): `ContractAssignment.clone_fields = ('content_object', 'contract')`.
- [X] T007 [P] [US1] `netbox_contract/views.py`: `AddContractAssignment.get_url` (about lines 242-250) and `ContractAssignmentEditView.get_extra_addanother_params` (about lines 190-207) use the new parameter names; delete the unreachable `ContractAssignmentEditView.alter_object` (R4).
- [X] T008 [P] [US1] `netbox_contract/templates/netbox_contract/inc/contract_assignments_bottom.html` (line 11): build the Add link with the new parameter names.
- [X] T009 [US1] Run `test_assignment_selector` and `test_views` assignment cases: green.

**Checkpoint**: US1 works and is testable alone.

## Phase 4: User Story 2 - Choose the external party by searching (P2)

**Goal**: the contract form uses the selector for the external party. **Independent test**: create then edit a contract with each provider type.

### Tests first
- [X] T010 [US2] Add failing tests: new contract opens with the type "service provider" selected (R5); choose a circuit provider by search and save; edit shows type and provider, switching the type clears the provider (FR-008); the form no longer loads every provider into the page: with 5,000 service providers created by `bulk_create()`, the page contains none of their names and costs the same number of queries as with 10 (SC-002); contract without external party remains saveable if the field was optional before (check current form rule and keep it).

### Implementation
- [X] T011 [US2] `ContractForm` (about lines 110-222): derive from `GenericObjectFormMixin`; replace the hand-built `external_party_object_type` / `external_party_object` pair and the related `__init__` logic by `external_party_object = GenericObjectChoiceField(content_type_queryset=ContentType.objects.filter(SERVICE_PROVIDER_MODELS))` in the "Parties" fieldset; seed the default type in `__init__` for an unbound new form (R5); update `Meta.fields`.
- [X] T012 [US2] `netbox_contract/views.py`: delete the `ContractEditView.alter_object` POST workaround (about lines 410-437).
- [X] T013 [US2] Run the contract form tests in `test_views.py` and `test_assignment_selector.py`: green.

**Checkpoint**: US1 and US2 independent.

## Phase 5: User Story 3 - Nothing else changes (P3)

- [X] T014 (existing import, REST, GraphQL and bulk edit tests run unchanged and pass; added a bulk edit form test) [US3] Add tests asserting unchanged behaviour: CSV import of assignments and contracts (same columns), contract bulk edit (its own external-party fields untouched), REST create/update of both models, GraphQL assignment query, filters; run the existing `test_api`, `test_graphql`, `test_views` unchanged except T002.
- [X] T015 [US3] Verify FR-013: the form still renders under quick add and under partial refresh (HTMX re-render of the type field) in a rendering test; fix anything the selector requires (`hx_target_id` matches `FieldSet(html_id=...)` if used).

## Phase 6: User Story 4 - A contract is assigned to an object only once (P2)

**Goal**: no duplicate pair, existing ones merged. **Independent test**: repeat an assignment in form, import and REST; migrate a database with duplicates.

### Tests first (`netbox_contract/tests/test_assignment_duplicates.py`)
- [X] T016 [US4] Failing tests: the form shows an error naming contract and object (and does not end in a database error); CSV import row and REST create/update are refused with the same message; edit without changing the pair saves; moving onto an existing pair is refused; same contract on two objects and two contracts on one object are accepted (FR-014, scenarios 1-3, 5).
- [X] T017 [US4] Failing merge tests (`merge_duplicates` called directly on rows inserted with `bulk_create()`, in a plain `TestCase`, as spec 003 had to do because NetBox's database cannot run a `TransactionTestCase` or a real migrate-back; restore the latest migration state in `tearDown` if the migration executor is used at all): three duplicates with different tags, a journal entry on a removed row, the same user's bookmark on two rows, empty and conflicting custom fields. Expect: one row (lowest id) with the union of tags, the journal entry moved, one bookmark, empty fields filled, conflicting values listed with both values in the report, removed rows gone, change-log entries kept; a second call changes nothing; a database without duplicates produces no report (FR-016, FR-017).
- [X] T018 [US4] Failing test: a raw insert of the same triple raises the integrity error named `netbox_contract_unique_assignment` (FR-015).

### Implementation
- [X] T019 [US4] `netbox_contract/models.py` `ContractAssignment`: add `clean()` raising the duplicate `ValidationError` (message of `contracts/forms-and-urls.md`; exclude `self.pk`; skip when contract or object missing) and `Meta.constraints = [UniqueConstraint(fields=['contract', 'content_type', 'object_id'], name='netbox_contract_unique_assignment')]` (R10).
- [X] T020 [US4] Create `netbox_contract/migrations/0054_contractassignment_unique.py`: `RunPython(merge_duplicates, noop)` then `AddConstraint`; put `merge_duplicates(apps, schema_editor)` in a module-level function so T017 can call it; declare the dependency on the `extras` migration that provides the models it touches (read how `0051`/`0052` declare dependencies and an earlier `RunPython` migration first). Rules and report format: `research.md` R10. Report to stdout and to the `netbox_contract` logger.
- [X] T021 [US4] Run T016-T018; `makemigrations netbox_contract --check --dry-run` reports no change.
- [X] T022 [P] [US4] `docs/contract.md`: one paragraph on the duplicate rule and on the upgrade merge report; `docs/api.md`: the REST create and update of an assignment now answer 400 for a duplicate pair, with the message. `CHANGELOG.md`: Breaking Changes (duplicate assignments are refused by form, import and REST; existing duplicates are merged at upgrade; removed duplicates are not restored on downgrade).

## Phase 7: Polish

- [X] T023 [P] `docs/contract.md`: describe the selectors; note that a supported model must be exposed in the REST API (R7); README `supported_models` line if present.
- [X] T024 [P] `netbox_contract/locale/fr`: run `makemessages -l fr`, translate new labels, `compilemessages`.
- [X] T025 [P] `CHANGELOG.md` Enhancements: selector for assignments and external party (by kind of change, not by issue).
- [ ] T026 (deferred: no screenshot in `utils/docs_screenshots` shows a form, so none changes with this feature; the complete regeneration on NetBox 4.7.4, with a `SHOTS` entry for the selector form if wanted, is done at the end of 007) Regenerate the screenshots of pages this change alters with `utils/docs_screenshots/make_screenshots.sh contract contract_linked_objects` (add a SHOTS entry if the docs now show the selector form), look at the images, keep only meaningful changes.
- [X] T027 (automated checks only: lint, no pending migration, full suite 1057 tests OK; the manual steps of `quickstart.md` were not run in a browser) `ruff check`, `makemigrations --check --dry-run` (no change), full suite, `quickstart.md` manual steps 1-7 and the duplicate steps.
- [X] T028 Stage the files for the owner to commit; do not bypass the pre-commit hook.

## Dependencies and order

008 → T001 → T002 → US1 (T003 → T004 → T005; T006..T008 parallel after T004) → US2 (T010 → T011 → T012) → US3 → US4 → Polish. US4 depends on T004 (selector form) only for the form-level test; its model and migration work can start earlier. US2 is independent of US1 once T002 exists, but both edit `forms.py` and `views.py`, so they are done in sequence. T023-T025 parallel.

## Implementation strategy

MVP = US1. Ship US1, US2 and US4 together in 2.6.0 (the migration of US4 cannot be released alone without its changelog Breaking Changes entry).
