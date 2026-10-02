---

description: "Task list for issue #309, Adopt NetBox 4.6 plugin features"
---

# Tasks: Adopt NetBox 4.6 plugin features

**Input**: Design documents from `specs/003-netbox-46-plugin-features/`: [plan.md](plan.md), [spec.md](spec.md),
[research.md](research.md), [data-model.md](data-model.md), [contracts/](contracts/), [quickstart.md](quickstart.md)

**Tests**: required (Constitution II, FR-020). Each story's tests are written first, in its own module, and MUST fail
before the story's implementation. The only exception is a test marked "guard", which passes before and after.

**Organization**: one phase per user story in the spec's priority order. Each story can be tested on its own. Its
cross-story touch points are listed under Dependencies.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependency on an incomplete task)
- **[Story]**: user story of spec.md (US1-US5)

Commands (from `CLAUDE.md`):
- Tests run from `/workspaces/netbox/netbox` with
  `NETBOX_CONFIGURATION=netbox.configuration_testing venv/bin/python netbox/manage.py test <label> --keepdb`.
- Lint with `ruff check` in the plugin repository.
- Query-count baselines are re-recorded with `UPDATE_QUERY_COUNTS=1`, serially, and only with a stated reason.

---

## Phase 1: Setup

**Purpose**: baseline and shared test scaffolding

- [ ] T001 Run the whole suite (`netbox_contract.tests`), `ruff check` and `makemigrations netbox_contract --check --dry-run` on the branch before any change, and note the result (all green expected) in the commit message of T002
- [ ] T002 Add to `netbox_contract/tests/helpers.py`:
  - `make_user_with_permissions(*perms, constraints=None)`, which creates a user and one `ObjectPermission` per `(model, actions)` pair, with optional constraints;
  - `invoiced_recurring_line()`, which returns a monthly line on a contract that has a Posted invoice.

  Both are used by US1-US4.

---

## Phase 2: Foundational

**Purpose**: the contract line lock and successor annotations that US1 (Amend in tables) and US2 (per-line actions)
both read (research D4).

- [ ] T003 Write `netbox_contract/tests/test_amend_permission.py::LineAnnotationsTestCase` first. `ContractLine.objects.with_lock_state()` sets `is_locked_line` (true when an invoice line references the line, or when its contract has an invoice) and `has_successor` (true when another line `replaces` it). Each value must equal `bool(line.lock_message())` and `line.replaced_by.exists()`, on four lines: unlocked, locked by contract invoice, referenced by an invoice line, and replaced
- [ ] T004 Implement `with_lock_state()` as a queryset method (`ContractLineQuerySet.as_manager()` on `ContractLine.objects`, keeping `RestrictedQuerySet` as base) in `netbox_contract/models.py`. Use two `Exists(...)` annotations, and make `can_be_amended` read `has_successor` when the annotation is present
- [ ] T005 Use `with_lock_state()` in `ContractLineListView.queryset` (`netbox_contract/views.py`) and `ContractLineViewSet.queryset` (`netbox_contract/api/views.py`). Run `test_views`/`test_api`. If the `contractline:*` query counts change, re-record them with the reason "lock-state annotations for per-line actions (#309 D4)"

**Checkpoint**: annotations available; no visible change yet.

---

## Phase 3: User Story 1 - Amend permission action (Priority: P1) 🎯 MVP

**Goal**: amending needs view + the `amend` action on that line (object-level). The button appears on the line page,
in contract line tables and on the edit page (research D6, D4).

**Independent Test**: a user with view + amend only can amend through the page and the REST API. A user with
add + change but not amend cannot.

### Tests for User Story 1 (write first, must fail)

- [ ] T006 [US1] `netbox_contract/tests/test_amend_permission.py::PermissionRegistrationTestCase`:
  - `'amend'` is in `registry['model_actions']['netbox_contract.contractline']`, with the help text "Amend the price or quantity of an invoiced contract line";
  - the ObjectPermission add form lists it for the contract line object type (US1-1).
- [ ] T007 [US1] Same module, `AmendUITestCase`, with `invoiced_recurring_line()`:
  - view + amend user: Amend button on the line page, GET/POST `contractline_amend` succeed, a successor exists (US1-2);
  - add + change + view user: no button on the line page, in the contract's lines table response or on the edit page, and `contractline_amend` answers 403 (US1-4);
  - amend constrained to `{"contract": <other>}`: no button and 403/404 for this line (US1-5);
  - a one-time line, an unlocked line and a replaced line show no button (US1-6);
  - superuser sees it (US1-7);
  - amend without view: refused (edge case);
  - a contract line list with an amendable and a non-amendable line shows the button only on the first (edge case).
- [ ] T008 [US1] Same module, `AmendAPITestCase`: `POST contract-lines/{id}/amend/`:
  - view + amend with a write token → 201 (US1-3);
  - add + change + view without amend → 403 (US1-4);
  - amend outside the view constraints → 404;
  - read-only token → 403 (contracts/rest-api.md table).
- [ ] T009 [US1] Run the module; confirm every new test fails for the expected reason (no `amend` action, add + change still accepted)

### Implementation for User Story 1

- [ ] T010 [US1] Add `permissions = [('amend', 'Amend the price or quantity of an invoiced contract line')]` to `ContractLine.Meta` in `netbox_contract/models.py`, and create `netbox_contract/migrations/0050_contractline_amend_permission.py` (`AlterModelOptions`) with `makemigrations` (DEVELOPER on)
- [ ] T011 [US1] In `netbox_contract/views.py`:
  - `ContractLineAmendView.get_required_permission()` returns `'netbox_contract.amend_contractline'`;
  - `has_permission()` requires that, plus `netbox_contract.view_contractline`;
  - the object comes from `ContractLine.objects.restrict(user, 'view').restrict(user, 'amend')`;
  - the add + change check is removed.
- [ ] T012 [US1] In `netbox_contract/api/views.py`, give `ContractLineViewSet`:
  - `get_permissions()`, which returns `[AmendPermission()]` for `self.action == 'amend'`. `AmendPermission` is authenticated, and a token must be write-enabled. Define it in the same file.
  - an `amend()` handler that rebuilds the queryset with `models.ContractLine.objects.restrict(user, 'view').restrict(user, 'amend')` (404 when absent), raises `PermissionDenied` when `not user.has_perm('netbox_contract.amend_contractline')`, and drops the `add_contractline` check.
- [ ] T013 [P] [US1] Create `netbox_contract/object_actions.py` with `AmendContractLine(ObjectAction)`:
  - `name='amend'`, `label=_('Amend')`, `template_name='netbox_contract/buttons/amend.html'`, `permissions_required = {'amend'}` (the button declares its permission, as the constitution requires);
  - `render()` also returns `''` unless `obj.can_be_amended` and `context['request'].user.has_perm('netbox_contract.amend_contractline', obj)`.

  Also create the template `netbox_contract/templates/netbox_contract/buttons/amend.html` (the `mdi-cash-sync` primary button).
- [ ] T014 [P] [US1] Create `netbox_contract/templatetags/__init__.py` and `netbox_contract/templatetags/contract_tags.py` with the `can_amend` filter (`line|can_amend:user`, same rule as T013). Use it in `netbox_contract/templates/netbox_contract/contractline_edit.html` in place of `perms.netbox_contract.change_contractline and perms.netbox_contract.add_contractline`
- [ ] T015 [US1] In `netbox_contract/views.py`, set `ContractLineView.actions = (CloneObject, EditObject, DeleteObject, AmendContractLine)`, and remove the `extra_controls` block from `netbox_contract/templates/netbox_contract/contractline.html`
- [ ] T016 [US1] In `netbox_contract/tables.py`:
  - add `ContractLineActionsColumn(columns.ActionsColumn)`. Its `render()` drops `delete` when the record is locked (`is_locked_line` annotation, else `bool(record.lock_message())`), and prepends the Amend button when `record.can_be_amended` and `user.has_perm('netbox_contract.amend_contractline', record)`;
  - use it as `ContractLineListTable.actions`;
  - remove `AMEND_BUTTON`, `ContractLineContractTable` and `ContractLineLockedContractTable`, and switch `ContractView` to `ContractLineListTable` until US2 replaces the table.
- [ ] T017 [US1] Adapt `netbox_contract/tests/test_issue_307.py` (Amend button rule: add + change → amend) and `netbox_contract/tests/test_amendments.py` (REST permission fixtures use amend). Run `test_amend_permission`, `test_amendments`, `test_issue_307`, `test_locking` (adapt its locked-table class assertions to the per-line column), `test_views`, and `ruff check`
- [ ] T018 [US1] Update `docs/contract_lines.md` ("Amending ...": the **amend** action of object permissions replaces add + change, and is checked per line). Add the US1 bullets to the #309 entry in `CHANGELOG.md` (create the entry under 2.5.0) and to "Behaviour changes"

**Checkpoint**: US1 complete and shippable alone.

---

## Phase 4: User Story 2 - Detail pages built from NetBox's standard panels (Priority: P2)

**Goal**: nine `ObjectView`s with `SimpleLayout`. Related tables come from the list views. No attribute or table
markup is left in templates (research D1-D5, [contracts/detail-pages.md](contracts/detail-pages.md)).

**Independent Test**: each detail page shows the same attributes, tables, buttons and messages as before, under the
same settings and permissions.

### Tests for User Story 2 (write first, must fail)

- [ ] T019 [US2] `netbox_contract/tests/test_detail_layouts.py::LayoutTestCase`:
  - each of the nine detail views has a `layout` that is a `SimpleLayout`. Fails today.
  - each page renders with status 200, as a superuser, for one object per model (guard part).
- [ ] T020 [P] [US2] Same module, `ContractPageTestCase`:
  - every attribute of contracts/detail-pages.md with its value and links (US2-1);
  - `hidden_contract_fields=['tenant','notice_period']` hides them (US2-2, `mock.patch.dict`);
  - deprecated costs and the template panel only with `show_deprecated_fields`, and the template is not queried when it is off (`assertNumQueries` difference or query log) (US2-3);
  - values panel, including "Not available", within a fixed query count (US2-4);
  - locked message and no add-line button on an invoiced contract; button with `?contract=<pk>` otherwise (US2-5);
  - four `ObjectsTablePanel`s whose `hx-get` URLs carry `contract_id`, `contract`, `parent` and `contracts` + `template=False`, each with the `exclude_columns` of research D4 (`contract`, `contract`, `parent`, `contracts`) (edge case "column choices"), the invoice add button with `?contracts=<pk>`, and no table panel for a user without view on invoices (US2-6);
  - a contract whose external party was deleted, or with no contract type, renders a placeholder (edge case).
- [ ] T021 [P] [US2] Same module, `OtherPagesTestCase`:
  - invoice: attributes, `hidden_invoice_fields`, posted message, deprecated template panel, contracts table via `invoice_id`, lines table via `invoice` with `exclude_columns=invoice`, add-line button absent when posted;
  - contract line: lock message, replaces/replaced-by links, invoiced-at-conversion checkmark;
  - invoice line, unit (lines table via `unit_id`), accounting dimension, contract type, service provider (contracts via `service_provider_id`), contract assignment: the attributes of contracts/detail-pages.md (US2-7);
  - a contract line page opened by a user without view on its contract still renders (edge case).
- [ ] T022 [P] [US2] Same module, `TableActionsTestCase`: GET the contract line list filtered by `contract_id` (the URL the panel loads) for an invoiced contract with an amendable recurring line and a one-time line, as a user with change + delete + amend. The recurring line offers Edit + Amend, the one-time line Edit only, and neither offers Delete. For a contract without invoices, lines offer Edit + Delete (US2-8). A list mixing locked and unlocked lines offers Delete only on the unlocked ones (edge case)
- [ ] T023 [P] [US2] Same module, `PluginContentTestCase`: register a test `PluginTemplateExtension` for `netbox_contract.contract` with `left_page`, `right_page` and `full_width_page` (in `netbox_contract/tests/plugin_content.py`, registered in `setUpClass` and removed in `tearDownClass`). Its three markers appear on the contract page (US2-9)
- [ ] T024 [US2] Same module, `ContractFilterTestCase`: `contracts/?invoice_id=<pk>` (UI list and REST) returns exactly the invoice's contracts (research D5)
- [ ] T025 [US2] Run the module; confirm the failures are the expected ones (no `layout`, no `invoice_id` filter, no left/full-width plugin content)

### Implementation for User Story 2

- [ ] T026 [US2] Add `invoice_id = django_filters.ModelMultipleChoiceFilter(field_name='invoices', queryset=Invoice.objects.all(), label=_('Invoice (ID)'))` to `ContractFilterSet` in `netbox_contract/filtersets.py`
- [ ] T027 [US2] Create `netbox_contract/panels.py`:
  - `SettingsAttributesPanel(ObjectAttributesPanel)` with `hidden_setting`, which excludes the listed names at render time from `settings.PLUGINS_CONFIG['netbox_contract']`;
  - `DeprecatedPanel` mixin with `should_render` on `show_deprecated_fields`;
  - `AddContractLine(AddObject)`, which renders `''` when the contract has invoices.
- [ ] T028 [P] [US2] Create the fragments under `netbox_contract/templates/netbox_contract/panels/`: `contract_values.html`, `lines_locked.html`, `line_lock.html`, `invoice_posted.html` and `invoice_template.html`. Move the texts unchanged from the old templates, so the translation msgids are kept
- [ ] T029 [US2] In `netbox_contract/panels.py`, declare the attribute panels of contracts/detail-pages.md for the nine models:
  - `ContractPanel` (with `GenericForeignKeyAttr('external_party_object', linkify=True)`, and `TemplatedAttr` for terms with units and for documents);
  - `DeprecatedCostsPanel`, `InvoicePanel`, `DeprecatedTemplatePanel`, `ContractLinePanel`, `InvoiceLinePanel`, `UnitPanel`, `AccountingDimensionPanel`, `ContractTypePanel`, `ServiceProviderPanel`, `ContractAssignmentPanel`;
  - the `TemplatePanel`s of T028.
- [ ] T030 [US2] In `netbox_contract/views.py`, set `layout = SimpleLayout(...)` on `ContractView`, `InvoiceView`, `ContractLineView`, `InvoiceLineView`, `UnitView`, `AccountingDimensionView`, `ContractTypeView`, `ServiceProviderView` and `ContractAssignmentView`, as in contracts/detail-pages.md:
  - use `ObjectsTablePanel` with the filters and `exclude_columns` of research D4;
  - remove the tables from `get_extra_context`. `ContractView` keeps `contract_values`, `lines_locked` and the deprecated template table only when `show_deprecated_fields` is on. `ContractLineView` keeps `lock_message`. `InvoiceView` keeps nothing extra.
- [ ] T031 [US2] Reduce `netbox_contract/templates/netbox_contract/contract.html` and `contractline.html` to `{% extends 'generic/object.html' %}` plus their `breadcrumbs` block. Delete `invoice.html`, `invoiceline.html`, `unit.html`, `serviceprovider.html`, `contracttype.html`, `accountingdimension.html` and `contractassignment.html`, and set `template_name = 'generic/object.html'` on those seven views
- [ ] T032 [US2] Remove from `netbox_contract/tables.py` the tables only used by deleted page code (`ContractProviderBottomTable`, `ContractListBottomTable`, `ContractAssignmentContractTable` if unused elsewhere: check with `grep`)
- [ ] T033 [US2] Adapt `netbox_contract/tests/test_deprecated.py`: deprecated badges per row become the "Deprecated costs" and deprecated template panels. Run `test_detail_layouts`, `test_deprecated`, `test_views`, `test_conventions`, `test_locking`, and, for FR-008 (edit, preview and amend screens unchanged), `test_prefill`, `test_invoice_preview` and `test_amendments`, then `ruff check`. Re-record query counts only if a list view changed, with the reason
- [ ] T034 [US2] Add the US2 bullets to `CHANGELOG.md` #309:
  - standard NetBox panels;
  - configurable related tables (#294);
  - per-line actions, with no Delete on locked lines;
  - left and full-width plugin content;
  - "Deprecated costs" panel.

  Check `docs/contract.md`, `docs/invoice.md` and `docs/contract_lines.md` wherever they describe page sections

**Checkpoint**: US1 + US2 work. The other stories have no dependency on US2.

---

## Phase 5: User Story 3 - Standard nested objects in the REST API, with the shrink announced (Priority: P2)

**Goal**: the nested invoice, accounting dimensions and contract line `replaces` use NetBox's brief mechanism with
identical output, and every model declares explicit `brief_fields` (which only gain fields). The nested contract and
invoice `contracts` stay unchanged and are announced as deprecated (research D7,
[contracts/rest-api.md](contracts/rest-api.md)).

**Independent Test**: no REST response loses a field compared with today, three hand-written nested serializers are
gone, and the changelog and docs list every field to be removed later.

### Tests for User Story 3 (write first)

- [ ] T035 [P] [US3] `netbox_contract/tests/test_nested_api.py::NestedSnapshotTestCase` (guard, written before any serializer change). Record, as literal expected values in the test, the keys and value types of:
  - assignment `contract`, contract line `contract` and contract `parent` (24 keys, `contract_type` an integer) (US3-1);
  - invoice `contracts` items (full contract) (US3-2);
  - invoice line `invoice` (`id, url, display, number`) and `accounting_dimensions` items (`id, url, display, name, value`) (US3-3).

  Passes before and after.
- [ ] T036 [P] [US3] Same module, `ReplacesTestCase`: the contract line `replaces` holds exactly the brief contract line set of contracts/rest-api.md. Fails today, because the hand-written set lacks `contract`, `unit` and `currency` (US3-3)
- [ ] T037 [P] [US3] Same module, `NestedWriteTestCase` (guard):
  - create/update an assignment and a contract line with `"contract": <id>` and with `"contract": {"name": "C-1"}`, and an invoice line with `"invoice": <id>` (US3-4);
  - a dict matching nothing, or two contracts → 400 (edge case);
  - `parent` set to `null`.
- [ ] T038 [P] [US3] Same module, `BriefTestCase`. For each of the nine endpoints, `?brief=true` returns exactly the "Brief fields in 2.5.0" set of contracts/rest-api.md. That is a superset of today's output, and every declared brief field is a serializer field (US3-5). The invoice line set (`id`, `currency` added) and the contract line set (dates added) fail today. The contract type and service provider additions are asserted in T056/T057 (US5)
- [ ] T039 [P] [US3] Same module, `SchemaTestCase` (OpenAPI generator, as `test_issue_307` does). Assert:
  - `BriefInvoice`, `BriefAccountingDimension` and `BriefContractLine` exist with the properties listed above, and `NestedInvoice`, `NestedAccountingDimension` and `NestedContractLine` do not;
  - `NestedContract` keeps its 24 properties, with "Deprecated" in the help text of the fields to be removed;
  - `external_party_object` and `content_object` are `object` (US3-6).
- [ ] T040 [P] [US3] Same module, `DeprecationNoticeTestCase`. Read `CHANGELOG.md` and `docs/api.md` from the repository root, and assert that every field of the "Deprecations announced in 2.5.0" table of contracts/rest-api.md is named in both, under the #309 entry's "Deprecations" list and the docs section (US3-7, FR-012a)
- [ ] T041 [US3] Run the module. T035 and T037 must pass (guards); T036, T038, T039 and T040 must fail for the expected reasons

### Implementation for User Story 3

- [ ] T042 [US3] In `netbox_contract/api/serializers.py`:
  - remove `NestedInvoiceSerializer`, `NestedAccountingDimensionSerializer` and `NestedContractLineSerializer`;
  - use `InvoiceSerializer(nested=True, fields=('id', 'url', 'display', 'number'), required=False)` for invoice line `invoice`, `SerializedPKRelatedField(serializer=AccountingDimensionSerializer, nested=True, ...)` for both `accounting_dimensions`, and `ContractLineSerializer(nested=True, read_only=True, ...)` for `replaces`;
  - order the classes so dependencies come first (`replaces` refers to its own class, so attach it after the class body);
  - keep `NestedContractSerializer`, with the docstring of research D7 and "Deprecated: will be removed from the nested contract, read contracts/{id}/" help texts on the 19 fields;
  - keep invoice `contracts` unchanged.
- [ ] T043 [US3] Set `brief_fields` on all nine serializers to the "Brief fields in 2.5.0" column of contracts/rest-api.md. Contract type `slug` and service provider `description` are added by US5 (T063)
- [ ] T044 [US3] Adapt the `brief_fields` lists in `netbox_contract/tests/test_api.py`. Run `test_nested_api` (except T040), `test_api`, `test_issue_307`, `test_prefill`, `test_posted` and `ruff check`. Query counts must not change; if they do, find out why before re-recording
- [ ] T045 [US3] Add to the #309 entry of `CHANGELOG.md`:
  - "Behaviour changes": the renamed OpenAPI components, the brief additions, and the invalid invoice line `name` declaration removed;
  - "Deprecations": every field of the contracts/rest-api.md deprecation table, per location, with "read `contracts/{id}/` instead", to be removed by a later release.

  In `docs/api.md`, add "Nested objects and `brief=true`" (2.5.0 sets) and "Deprecated nested fields" (same table). T040 then passes

**Checkpoint**: US3 shippable. It is independent of US1, US2 and US4.

---

## Phase 6: User Story 4 - GraphQL API (Priority: P3)

**Goal**: the nine models are in NetBox's GraphQL API, with stored fields and relations, permissions applied, and
deprecated fields marked (research D8, [contracts/graphql.md](contracts/graphql.md)).

**Independent Test**: query each type by id and as a filtered list, with and without view permission.

### Tests for User Story 4 (write first, must fail)

- [ ] T046 [US4] In `netbox_contract/tests/test_api.py`, switch the nine API test cases to `APIViewTestCases.APIViewTestCase`. Add `create_data`, `bulk_update_data` and `brief_fields` where missing (`ContractAPITestCase` and the custom `APITestCase` classes become full cases), and set `graphql_base_name` only where the default (verbose name with underscores) differs from contracts/graphql.md. The GraphQL part fails today (`GraphQLTypeNotFound`)
- [ ] T047 [P] [US4] `netbox_contract/tests/test_graphql.py`:
  - `contract_list(filters: {status: ...})` returns the matching contracts with `contract_type`, `lines`, `invoices`, `assignments`, `parent` and `childs` (US4-1);
  - a user without view on invoices gets `[]`, and a constrained permission limits results (US4-3);
  - `external_party_object` on a service provider contract and on a circuit provider contract, and `content_object` of a device assignment, resolve with their type (US4-4);
  - an assignment to a model outside the union resolves to `null`, with `content_type` and `object_id` set (contracts/graphql.md);
  - the schema marks `mrc`, `yrc`, `nrc` and `template` deprecated (US4-5);
  - querying `yearly_contract_value` returns a GraphQL error (edge case);
  - `contract_list { external_party_object { ... } }` and `contract_assignment_list { content_object { ... } }` run in the same number of queries for 2 and for 10 objects (`CaptureQueriesContext`; plan performance goal for generic relations).
- [ ] T048 [US4] Run both modules; confirm the expected failures

### Implementation for User Story 4

- [ ] T049 [P] [US4] Create `netbox_contract/graphql/__init__.py` and `netbox_contract/graphql/filters.py`. Add one `@strawberry_django.filter_type(models.<Model>, lookups=True)` class per model, based on `NetBoxModelFilter` (contract type and service provider are switched to the organizational and primary bases in T064), covering the stored fields with core lookups (`StrFilterLookup`, `ComparisonFilterLookup`, `DateFilterLookup`, choice enums)
- [ ] T050 [US4] Create `netbox_contract/graphql/types.py` with `ContractType`, `ContractLineType`, `ContractTypeType`, `ContractAssignmentType`, `InvoiceType`, `InvoiceLineType`, `UnitType`, `AccountingDimensionType` and `ServiceProviderType`:
  - `@strawberry_django.type(models.<Model>, fields='__all__', filters=..., pagination=True)`, on `NetBoxObjectType`;
  - `deprecation_reason` on `mrc`, `yrc`, `nrc` and `template`;
  - unions `ContractExternalPartyType` and `ContractAssignmentObjectType`, resolved with `build_gfk_prefetch` (research D8).
- [ ] T051 [US4] Create `netbox_contract/graphql/schema.py` with `NetBoxContractQuery` (single and `_list` field per model, named as in contracts/graphql.md) and `schema = [NetBoxContractQuery]`. Check that NetBox loads it (`/graphql/` introspection lists `contract_list`)
- [ ] T052 [US4] Run `test_graphql`, `test_api` and `ruff check`. Re-record query counts only if the API list tests change, with the reason
- [ ] T053 [US4] Add the US4 bullets to `CHANGELOG.md` #309 (GraphQL API; stored fields only; union limits for `supported_models`). In `docs/api.md`, add a "GraphQL" section with example queries, the absence of computed values (use REST), and the assignment union limit

**Checkpoint**: US4 shippable. If US5 is not done, contract type and service provider types are plain `NetBoxObjectType` until T064.

---

## Phase 7: User Story 5 - Contract types and service providers as standard NetBox objects (Priority: P3)

**Goal**: `ContractType(OrganizationalModel)` and `ServiceProvider(PrimaryModel)` across the full stack, with a
lossless, reported migration (research D9, D10, [data-model.md](data-model.md)).

**Independent Test**: migrate a database with contract types (colliding names, one 350-character description) and
service providers, then check slugs, descriptions, comments and owner in pages, forms, import, filters, REST and
GraphQL.

### Tests for User Story 5 (write first, must fail)

- [ ] T054 [P] [US5] `netbox_contract/tests/test_base_classes.py::TextHelpersTestCase` for `netbox_contract/text.py`:
  - `unique_slug('Support & Licences', set())` == `'support-licences'`;
  - a collision gives `-2`, then `-3`;
  - `unique_slug('&&&', set())` == `'contract-type'` (edge case);
  - `shorten_description` keeps 200-character text, cuts a 350-character text at the last space within 199 characters plus `…` (length ≤ 200), and cuts text without spaces at 199 plus `…` (edge case);
  - `plan_contract_type_changes(rows, taken)`, on plain `(pk, name, slug, description)` tuples:
    - "Maintenance" → slug `maintenance`; two names with the same slug get unique slugs, and both appear in the report (US5-1, US5-2);
    - a 350-character description gets the shortened text, its full text becomes the comments, and the report names the type (US5-3);
    - rows that already have a slug and a short description produce no change and no report line (US5-7, idempotence).
- [ ] T055 [P] [US5] Same module, `MigrationTestCase(TransactionTestCase)`, with `django.db.migrations.executor.MigrationExecutor` and historical models (not the current model, whose unique `slug` forbids several empty values):
  1. migrate `netbox_contract` to `0050`, then create three contract types with the historical model: "Maintenance", two names giving the same slug, and one with a 350-character description;
  2. migrate to `0051`: slugs filled and unique, the description shortened, and the full text in `comments` (US5-1, US5-2, US5-3);
  3. migrate back to `0050`: the 350-character description is restored exactly (US5-7, lossless reverse);
  4. migrate forward again: the same result as step 2, with no duplicated text in `comments` (US5-7).

  Restore the latest migration state in `tearDown`.
- [ ] T056 [P] [US5] Same module, `ContractTypeTestCase`:
  - REST create with only `name` → 201 with a derived slug, and with an explicit slug it is kept (US5-4);
  - form and CSV import without slug succeed;
  - `description` over 200 → 400 / form error;
  - `comments` and `owner` are editable, bulk-editable, importable (`owner` column), filterable (`?owner_id=`) and shown on the page (US5-6).
- [ ] T057 [P] [US5] Same module, `ServiceProviderTestCase`:
  - description and owner are editable through form, bulk edit, import, REST and filters, and shown on the page;
  - the existing name, slug, portal URL, comments and contacts are unchanged after the change (US5-5, US5-6);
  - no owner defined anywhere → empty owner, forms valid (edge case).
- [ ] T058 [US5] Run the module; confirm the expected failures (`ImportError` on `text`, missing fields)

### Implementation for User Story 5

- [ ] T059 [US5] Create `netbox_contract/text.py` with `unique_slug(name, taken)`, `shorten_description(text, limit=200)` and `plan_contract_type_changes(rows, taken)` (returns the per-row slug, description and comments changes plus the report lines), as in research D9 and D10. They are pure functions with no Django model import
- [ ] T060 [US5] In `netbox_contract/models.py`:
  - `ContractType(OrganizationalModel)` keeps `color`. Redeclare `slug = models.SlugField(max_length=100, unique=True, blank=True, verbose_name=_('slug'))`, and drop the local `name`/`description` (inherited: `name` "CharField(100, unique)", `description` "CharField(200, blank)"). `clean()` and `save()` set an empty slug with `unique_slug(self.name, <slugs of other types>)`.
  - `ServiceProvider(ContactsMixin, PrimaryModel)` keeps `name`, `slug` and `portal_url`, and inherits `description` "CharField(200, blank)" and `owner` (`comments` is now inherited).
- [ ] T061 [US5] Create `netbox_contract/migrations/0051_contracttype_organizational.py`. Generate it with `makemigrations`, then edit it into:
  1. add `slug` null;
  2. add `comments` and `owner`;
  3. `RunPython(fill_slugs_and_shorten_descriptions, restore_descriptions)`. The forward function applies `plan_contract_type_changes` and prints the report. The reverse puts the full text from `comments` back into `description` wherever `shorten_description(comments) == description` (`description` is already a `TextField` again at that point of the reverse);
  4. alter `slug` to unique not null;
  5. alter `description` to `CharField(200)`.

  Add a docstring saying that the reverse restores moved descriptions, and drops comments typed after the upgrade with their column. Then create `netbox_contract/migrations/0052_serviceprovider_primary.py` (add `description` and `owner`). Run `makemigrations --check`
- [ ] T062 [US5] Switch the stack to the core bases:
  - `netbox_contract/forms.py`: `OrganizationalModelForm` (slug `SlugField(required=False)`), `OrganizationalModelBulkEditForm`, `OrganizationalModelImportForm` (slug optional), `OrganizationalModelFilterSetForm`, and the `PrimaryModel*` equivalents for service providers, with `owner` and `description` placed in their fieldsets;
  - `netbox_contract/filtersets.py`: `OrganizationalModelFilterSet` and `PrimaryModelFilterSet`, with the `slug` and `description` filters;
  - `netbox_contract/tables.py`: `OrganizationalModelTable` and `PrimaryModelTable`, with `owner` not in `default_columns`;
  - `netbox_contract/search.py`: contract type `description` and `slug`.
- [ ] T063 [US5] In `netbox_contract/api/serializers.py`:
  - `ContractTypeSerializer(OrganizationalModelSerializer)` with `slug`, `comments` and `owner` in `fields`, `extra_kwargs={'slug': {'required': False}}`, and `brief_fields` with `slug`;
  - `ServiceProviderSerializer(PrimaryModelSerializer)` with `description` and `owner`, and `brief_fields` with `description` (completes T043).
- [ ] T064 [US5] If US4 is done, switch `ContractTypeType` to `OrganizationalObjectType` and `ServiceProviderType` to `PrimaryObjectType` in `netbox_contract/graphql/types.py`, and the filters to `OrganizationalModelFilter` and `PrimaryModelFilter` in `graphql/filters.py`. If US2 is done, add slug, owner and description to `ContractTypePanel` and `ServiceProviderPanel` in `netbox_contract/panels.py`
- [ ] T065 [US5] Run `test_base_classes`, `test_api`, `test_views`, `test_graphql` (if present), `test_conventions` and `ruff check`. Re-record the `contracttype:*` and `serviceprovider:*` query counts only if they change (reason: "owner relation of the core base classes, #309 D9")
- [ ] T066 [US5] Add the US5 bullets to `CHANGELOG.md` #309 "Behaviour changes":
  - slug derived on upgrade, with the report;
  - long descriptions shortened and moved to comments;
  - description limited to 200 characters;
  - new owner and description fields.

  Document the contract type and service provider fields in `docs/contract.md` (or the page that lists contract types and providers)

**Checkpoint**: all stories complete.

---

## Phase 8: Polish & Cross-Cutting Concerns

- [ ] T067 Refresh translations: `makemessages -l en -l fr` from `netbox_contract/` (NetBox `manage.py`, test configuration). Translate the new and fuzzy French entries in `netbox_contract/locale/fr/LC_MESSAGES/django.po`, then `msgfmt` both catalogs. Check that msgids moved from the deleted templates keep their translations
- [ ] T068 [P] Update `CLAUDE.md`:
  - Architecture: detail pages via `layout` + `panels.py`; per-line contract line actions and `with_lock_state()`; amend permission action and `object_actions.py`; nested `brief_fields`; `graphql/` package;
  - Tests: the API tests now use `APIViewTestCase`; remove "the plugin has no GraphQL".
- [ ] T069 [P] Review `README.md`: requirements unchanged (NetBox 4.6.0). Mention GraphQL only if the README lists features
- [ ] T070 Run the full quickstart: `ruff check`, `makemigrations --check`, `migrate`, the whole `netbox_contract.tests` suite (including `test_prefill`, `test_invoice_preview` and `test_amendments` for FR-008), then the manual dev-server checks 1-6 of [quickstart.md](quickstart.md)
- [ ] T071 Keep `spec.md`, `research.md` and this file in step with what was implemented (CLAUDE.md workflow rule). Mark tasks `[X]` and record any deviation in research.md

---

## Dependencies & Execution Order

- **Setup (T001-T002)** → **Foundational (T003-T005)** → stories.
- **US1** depends on the Foundational phase only.
- **US2** depends on US1 for the per-line actions column (T016) and on the Foundational annotations.
- **US3** is independent: Setup only.
- **US4** is independent: Setup only. T046 changes `test_api.py`, which T044 (US3) also touches, so run them in
  sequence.
- **US5** is independent for its core. T063 completes US3's brief sets, and T064 adjusts US4 types and US2 panels when
  those stories are done.
- **Polish** comes after the stories that ship.

Within each story: tests first and failing, then models, migrations and helpers, then views and serializers, then
docs and changelog.

## Parallel Opportunities

- US1: T013 and T014 (different files) after T010-T012.
- US2: the test classes T020-T023 in parallel (same module, independent classes; write them in one sitting); T028 in
  parallel with T027.
- US3: T035-T040 in parallel.
- US4: T049 in parallel with T047.
- US5: T054-T057 in parallel.
- Across stories, once Phase 2 is done: US3, US4 and the US5 core (T054-T062) can proceed in parallel with US1 and
  US2. They touch different modules, except `test_api.py`, `api/serializers.py` and `CHANGELOG.md`; merge those by
  hand.

## Implementation Strategy

1. **MVP**: Setup, Foundational, then US1. This gives the amend permission, which has the most security weight.
   Validate it with `test_amend_permission`.
2. Add US2 (pages), then US3 (REST), each validated by its module and the full suite.
3. Add US4 (GraphQL) and US5 (base classes).
4. Polish, then one pull request to `develop`: the feature ships whole in 2.5.0 (Constitution VII). The stories are
   commits, not separate releases.
