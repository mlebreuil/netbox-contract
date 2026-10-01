---

description: "Task list for issue #308, Align with NetBox 4.6 plugin conventions"
---

# Tasks: Align with NetBox 4.6 plugin conventions

**Input**: Design documents from `specs/002-netbox-46-conventions/` ([plan.md](plan.md), [spec.md](spec.md),
[research.md](research.md), [data-model.md](data-model.md), [contracts/](contracts/), [quickstart.md](quickstart.md))

**Tests**: required (Constitution II, FR-014). Tests are written first in `netbox_contract/tests/test_conventions.py`,
one test class per story, and MUST fail before the story's implementation.

**Organization**: one phase per user story in priority order; each story is independently testable.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependency on an incomplete task)
- **[Story]**: user story of spec.md (US1-US5)

Commands (from `CLAUDE.md`): tests run from `/workspaces/netbox/netbox` with
`NETBOX_CONFIGURATION=netbox.configuration_testing venv/bin/python netbox/manage.py test <label> --keepdb`; lint with
`ruff check` in the plugin repository.

---

## Phase 1: Setup

**Purpose**: baseline and shared test scaffolding

- [X] T001 Run the whole suite (`netbox_contract.tests`) and `ruff check` on the branch before any change and note the result (all green expected) in the commit message of T002
- [X] T002 Create `netbox_contract/tests/test_conventions.py` with a module docstring referencing spec 002 and a `setUpTestData` fixture helper building one object of each of the nine models with `tests/helpers.py` factories (`make_contract`, `make_line`, `make_invoice` with `status=InvoiceStatusChoices.STATUS_DRAFT`, `monthly()`), plus a `ContractType`, `AccountingDimension`, `ServiceProvider`, `InvoiceLine` and a `ContractAssignment` to a `dcim.Site`

---

## Phase 2: Foundational

No blocking prerequisite: the stories touch different parts of `views.py`/`urls.py`, `filtersets.py`, `forms.py` and
can start once Phase 1 is done.

---

## Phase 3: User Story 1 - Journal and extra tabs on every plugin object (Priority: P1) 🎯 MVP

**Goal**: every view of the nine models registered with `register_model_view`, `urls.py` reduced to includes, Journal
tab on all detail pages (research D1).

**Independent Test**: open an invoice line, accounting dimension, contract type and contract assignment: Journal and
Changelog tabs shown, a journal entry can be added; every old route name resolves.

### Tests for User Story 1 (write first, must fail)

- [X] T003 [US1] In `netbox_contract/tests/test_conventions.py`, class `RouteTestCase`: for each of the 82 route names of `contracts/routes.md`, `reverse('plugins:netbox_contract:<name>', kwargs={'pk': 1} when the address has `<int:pk>`)` returns `/plugins/contracts/<address>` and `resolve()` of it returns the listed view class (`ObjectChangeLogView` for `*_changelog`); `invoice_lines_preview` included. Passes before the change too (guard for the refactor); record that in the test docstring
- [X] T004 [US1] Same file, class `JournalTabTestCase`: as a superuser, GET the detail page of each of the nine models and assert the links to `<model>_journal` and `<model>_changelog` are in the response (fails today for `invoiceline`, `accountingdimension`, `contracttype`, `contractassignment`: `NoReverseMatch` on `<model>_journal`). The Journal view is registered by NetBox core through `register_model_view`, so this also covers FR-002 and the edge case "views registered by other code work for the four models"; say so in the test docstring
- [X] T005 [US1] Same class: create a journal entry for an invoice line and assert it is listed by `plugins:netbox_contract:invoiceline_journal` (implemented with the ORM instead of a POST to core's `extras:journalentry_add`: the add form is core's, the plugin's Journal tab is what is tested)
- [X] T006 [US1] Same class: `contractline_amend` still resolves and the Amend button is on the contract line page; the `contracts` tab is still registered for `dcim.site` (`dcim:site_contracts` resolves) (US1-4)

### Implementation for User Story 1

- [X] T007 [US1] In `netbox_contract/views.py`, decorate the ServiceProvider list, add/edit (stacked `'add', detail=False` and `'edit'`), delete, bulk import (`path='import'`), bulk edit (`path='edit'`), bulk delete (`path='delete'`) views with `@register_model_view` as in research D1 (detail view already registered)
- [X] T008 [US1] Same for Contract, Unit, ContractLine and Invoice views in `netbox_contract/views.py` (detail views already registered; keep `ContractLineAmendView`)
- [X] T009 [US1] Same for ContractAssignment, InvoiceLine, AccountingDimension and ContractType views in `netbox_contract/views.py`, including `@register_model_view(Model)` on their detail views; check `ContractAssignmentEditView.alter_object` and `get_extra_addanother_params` still behave for `add` (list-level route, empty URL kwargs)
- [X] T010 [US1] Rewrite `netbox_contract/urls.py`: per model `path('<prefix>/', include(get_model_urls('netbox_contract', '<model>', detail=False)))` and `path('<prefix>/<int:pk>/', include(get_model_urls('netbox_contract', '<model>')))` with today's prefixes; keep `path('invoices/lines-preview/', views.InvoiceLinesPreviewView.as_view(), name='invoice_lines_preview')` before the invoice includes; remove all hand-written `*_changelog` paths and the `ObjectChangeLogView`/`models` imports
- [X] T011 [US1] Run `test_conventions.RouteTestCase`, `test_conventions.JournalTabTestCase`, `test_views`, `test_issue_307` and `ruff check`; all pass

**Checkpoint**: US1 complete; Journal tab on 9/9 models (SC-001), routes unchanged (SC-003).

---

## Phase 4: User Story 2 - Lookup modifiers on the plugin's filter forms (Priority: P2)

**Goal**: the nine filtersets registered (research D2).

**Independent Test**: contract list filter tab shows the modifier selector next to External reference; "contains"
filters.

### Tests for User Story 2 (write first, must fail)

- [X] T012 [US2] In `netbox_contract/tests/test_conventions.py`, class `FilterModifierTestCase`: `registry['filtersets']['netbox_contract.<model>']` is the plugin filterset for the nine models; for each filter form, one text/choice field (e.g. `ContractFilterForm.external_reference`, `InvoiceFilterForm.number`, `UnitFilterForm.name`, `AccountingDimensionFilterForm.value`, `ContractTypeFilterForm.name`, `ServiceProviderFilterForm.name`, `ContractLineFilterForm.currency`, `InvoiceLineFilterForm.currency`, `ContractAssignmentFilterForm.contract`) has a `utilities.forms.widgets.FilterModifierWidget` widget when the model's filterset supports more than one lookup for it (`len(lookups) > 1`, computed with the filterset); in addition, each of the nine filter forms has at least one field with `FilterModifierWidget`, so SC-002 is checked 9/9 (implemented as that check plus `external_reference`; the contract type, contract assignment and accounting dimension filter forms have no `tag` filter, so `tag` cannot be the common field)
- [X] T013 [US2] Same class: contracts with external references `ALPHA-FIBER-01` and `BETA-POWER-02`; GET `contract_list?external_reference__ic=FIBER` lists only the first (US2-2); GET with a query string used before the change (`?status=active&currency=usd`) returns the same contracts as the filterset applied directly (US2-3)

### Implementation for User Story 2

- [X] T014 [US2] In `netbox_contract/filtersets.py`, import `register_filterset` from `utilities.filtersets` and decorate the nine `*FilterSet` classes
- [X] T015 [US2] Run `test_conventions.FilterModifierTestCase`, `test_views`, `test_api` and `ruff check`; all pass

**Checkpoint**: modifiers on 9/9 filter forms (SC-002).

---

## Phase 5: User Story 3 - Forms grouped into sections (Priority: P2)

**Goal**: `fieldsets` on the model, bulk-edit and filter forms with the grouping of research D3; hidden and deprecated
fields removed from sections; contract type description as a `CharField` (D4). Invariants in
[contracts/forms.md](contracts/forms.md).

**Independent Test**: contract add form shows titled sections; a contract can be created with the same fields.

### Tests for User Story 3 (write first, must fail)

- [X] T016 [US3] In `netbox_contract/tests/test_conventions.py`, class `FormSectionsTestCase`: for each of the 27 model, bulk-edit and filter form classes of `netbox_contract/forms.py` (instantiated unbound; bulk-edit forms with `model` set as the views do), assert `form.fieldsets` is not empty and every visible field name (excluding hidden widgets, custom fields `cf_*`, `comments`, `changelog_message`, `owner`, `owner_group`, and the bulk-edit `add_tags`/`remove_tags`, which `generic/bulk_edit.html` renders outside the sections) appears in exactly one `FieldSet`; filter forms' first fieldset is `('q', 'filter_id', 'tag')`, or `('q', 'filter_id')` for the three filter forms without a `tag` filter; no `FieldSet` without a field present in `form.fields`
- [X] T017 [US3] Same class: with `mock.patch.dict(settings.PLUGINS_CONFIG['netbox_contract'], {'hidden_contract_fields': ['external_reference', 'documents']})`, a `ContractForm` has both as hidden inputs (optional fields: the setting never hides a required field such as `notice_period`), in no fieldset, and the rendered `contract_add` page contains each input exactly once (US3-2)
- [X] T018 [US3] Same class: `show_deprecated_fields` off → `ContractForm` (`mrc`, `yrc`, `nrc`), `InvoiceForm` and `InvoiceBulkEditForm` (`template`) have no `Deprecated` fieldset and none of those fields; on → those fields are in a `Deprecated` fieldset (US3-3). `InvoiceFilterForm` keeps its `template` filter whatever the setting (it is not removed today, FR-007), in a `Deprecated` section that is always shown; `ContractBulkEditForm` has no deprecated field and no `Deprecated` section
- [X] T019 [US3] Same class: `ContractTypeFilterForm().fields['description']`, `ContractTypeCSVForm().fields['description']` and `ContractTypeBulkEditForm().fields['description']` are `forms.CharField` with a `TextInput`-based widget (not `MarkdownWidget`), `required=False`; `ContractTypeBulkEditForm.nullable_fields == ('description',)` (US3-4)

### Implementation for User Story 3

- [X] T020 [US3] In `netbox_contract/forms.py`, add a helper `prune_fieldsets(form)` next to `apply_field_settings`: rebuild `form.fieldsets` on the instance keeping only names present in `form.fields` whose widget is not hidden, dropping empty `FieldSet`s (preserve `name`); call it at the end of `apply_field_settings` and after the deprecated-field deletions in `ContractForm`, `InvoiceForm` and `InvoiceBulkEditForm` (and any other form that deletes or hides fields)
- [X] T021 [US3] In `netbox_contract/forms.py`, add `fieldsets` to `ContractForm`, `ContractBulkEditForm` and `ContractFilterForm` per research D3 (Contract; Parties; Dates and terms; Billing; Tenancy; Deprecated / filter: Attributes; Parties; Billing; Tenant with `tenant_group_id`, `tenant_id`; Contacts with `contact`, `contact_role`, `contact_group`), section names wrapped in `_()`
- [X] T022 [US3] Same for `InvoiceForm`, `InvoiceBulkEditForm`, `InvoiceFilterForm` (filter: Attributes number, status, contracts; Billing currency, accounting dimensions; Deprecated template)
- [X] T023 [US3] Same for `InvoiceLineForm`, `InvoiceLineBulkEditForm`, `InvoiceLineFilterForm` (filter: Attributes invoice; Billing currency, accounting dimensions) and `ContractLineForm`, `ContractLineBulkEditForm`, `ContractLineFilterForm` (filter: Attributes contract; Billing currency, unit, billing method, accounting dimensions)
- [X] T024 [US3] Same for the Unit, ServiceProvider (filter Contacts section with `contact`, `contact_role`, `contact_group`), ContractType, ContractAssignment and AccountingDimension model, bulk-edit and filter forms
- [X] T025 [US3] In `netbox_contract/forms.py`, replace `description = CommentField(...)` by `forms.CharField(required=False, label=_('Description'))` in `ContractTypeFilterForm`, `ContractTypeCSVForm`, `ContractTypeBulkEditForm`; set `ContractTypeBulkEditForm.nullable_fields = ('description',)` (research D4)
- [X] T026 [US3] Run `test_conventions.FormSectionsTestCase`, `test_views` (create, edit, bulk edit, import of every model: US3-5), `test_deprecated` and `ruff check`; all pass

**Checkpoint**: sections on all forms with the same fields (SC-004).

---

## Phase 6: User Story 4 - Quick add and partial refresh on invoice and invoice line forms (Priority: P3)

**Goal**: pre-fill as form defaults under the address values, then core `ObjectEditView.get()` (research D5).

**Independent Test**: add-invoice from a contract shows the same pre-filled values; `?_quickadd=true` and an HTMX
partial request return the short forms.

### Tests for User Story 4 (write first, must fail)

- [X] T027 [US4] In `netbox_contract/tests/test_conventions.py`, class `EditViewTestCase`: GET `invoice_add?contracts=<id>&_quickadd=true` and `invoiceline_add?invoice=<id>&_quickadd=true` render `htmx/quick_add.html` with fields prefixed `quickadd-` and the pre-filled values as initial (US4-4); the same with header `HX-Request: true` (and no `HX-Boosted`) render `htmx/form.html` (US4-5)
- [X] T028 [US4] Same class: `invoice_add?contracts=<id>&date=2026-01-15` keeps `date(2026, 1, 15)` as initial date and still fills period, currency and amount from the contract (clarification Q5); `invoiceline_add?invoice=<id>&quantity=3` keeps quantity 3
- [X] T029 [US4] Same class: `invoice_edit` and `invoiceline_edit` of existing objects opened with `?contracts=`/`?invoice=` of another object show the stored values (US4-6); `invoice_add?contracts=abc` and an unknown id render without error and without pre-fill; a contract whose lines raise `InvoicingError` shows the error message and still pre-fills period and currency
- [X] T030 [P] [US4] Confirm `netbox_contract/tests/test_prefill.py`, `test_issue_307.py` and `test_invoice_preview.py` are unchanged and cover US4-1 to US4-3 (same values, restriction #307, preview); no edit to those files

### Implementation for User Story 4

- [X] T031 [US4] In `netbox_contract/views.py`, add a helper `form_with_defaults(form_class, defaults)` returning a subclass whose `__init__(self, *args, initial=None, **kwargs)` calls `super().__init__(*args, initial={**defaults, **(initial or {})}, **kwargs)`
- [X] T032 [US4] In `netbox_contract/views.py`, rewrite `InvoiceEditView.get`: for a new invoice compute `defaults` (date today, period start/end, amount from `invoicing.propose_invoice`, currency; `messages.error` on `InvoicingError`) from the contract restricted with `restrict(request.user, 'view')`, store them on `self`, set `self.form = form_with_defaults(self.form, defaults)`, return `super().get(...)`; in `get_extra_context`, on GET for a new invoice return `lines_preview = build_lines_preview({**defaults, **normalize_querydict(request.GET)}, request.user)`; remove the copied render code
- [X] T033 [US4] In `netbox_contract/views.py`, rewrite `InvoiceLineEditView.get` the same way (defaults `unit_price` = invoice amount − lines total, `quantity` 1, `currency`, from the invoice restricted with `restrict(request.user, 'view')`); remove the copied render code and imports left unused (`render`, `get_prerequisite_model`, `restrict_form_fields` if no longer used)
- [X] T034 [US4] Run `test_conventions.EditViewTestCase`, `test_prefill`, `test_issue_307`, `test_invoice_preview`, `test_generation`, `test_views` and `ruff check`; all pass

**Checkpoint**: quick add works for invoices and invoice lines (SC-006); pre-fill unchanged except "address wins".

---

## Phase 7: User Story 5 - Deprecated invoice templates hidden on contracts when deprecated fields are off (Priority: P3)

**Goal**: invoice template looked up on the contract page only with `show_deprecated_fields` on (research D7).

**Independent Test**: contract with an invoice template, setting off: no section; on: section.

### Tests for User Story 5 (write first, must fail)

- [X] T035 [US5] In `netbox_contract/tests/test_conventions.py`, class `ContractTemplateSectionTestCase`: a contract with an invoice template (`make_invoice(..., template=True)`); with `show_deprecated_fields` False, the contract page context has `invoice_template` None and the template's number is not in the response, and the page runs fewer queries than with the setting True (compare `CaptureQueriesContext` counts); with True, the section and number are shown

### Implementation for User Story 5

- [X] T036 [US5] In `netbox_contract/views.py` `ContractView.get_extra_context`, look up `invoice_template` and build `invoicelines_table` only when `plugin_settings.get('show_deprecated_fields')` is true, else both `None`
- [X] T037 [US5] Run `test_conventions.ContractTemplateSectionTestCase`, `test_deprecated`, `test_views` and `ruff check`; all pass. `test_deprecated.test_template_invoice_badge_and_panel` (#278) asserted the panel with the default setting; it now checks both settings, the one existing test changed by this feature (maintainer decision, spec clarification Q1)

**Checkpoint**: all user stories complete.

---

## Phase 8: Polish & Cross-Cutting Concerns

### Templates (FR-011, research D6; test first)

- [X] T038 In `netbox_contract/tests/test_conventions.py`, class `TemplateLocationTestCase`: no `.html` file directly under `netbox_contract/templates/` (covers the edge case "a template with the same name in another plugin does not replace them": only namespaced paths remain); with `contract_assignments_display` `both`, the page of a site with a contract assignment renders the assignments table (the contract name is in the response)
- [X] T039 Move `netbox_contract/templates/contract_assignments_bottom.html` to `netbox_contract/templates/netbox_contract/inc/contract_assignments_bottom.html` (`git mv`) and update the path in `netbox_contract/template_content.py`
- [X] T040 Delete `netbox_contract/templates/contract_list_bottom.html` (`git rm`, clarification Q3)

### Translations, documentation, release notes

- [X] T041 From `netbox_contract/`, run NetBox's `django-admin makemessages -l en -l fr` (NetBox venv, settings of the test configuration) to refresh `locale/*/LC_MESSAGES/django.po`; add French translations for the new section titles; for a title NetBox core already translates, reuse its wording from `netbox/translations/fr/LC_MESSAGES/django.po` (Tenancy → Utilisateur, Tenant → Entité, Attributes → Attributs, Contacts → Contacts), otherwise Parties → Parties, Dates and terms → Dates et conditions, Billing → Facturation, Deprecated → Obsolète, Period and amount → Période et montant, Amount → Montant, Price → Prix, Dates → Dates, Assignment → Affectation, and the model-named sections as the models are already translated; check no `msgid` is lost; run `compilemessages` to update the `.mo` files. Done as decided by the maintainer: full refresh (113 → 266 msgids) and French translation of every untranslated (120) and fuzzy (38) entry, including the #278/#307 strings; for msgids NetBox core also translates, NetBox's catalog takes precedence (e.g. Tenancy → Utilisateur), so the plugin entries use the same wording
- [X] T042 [P] In `CHANGELOG.md`, 2.5.0 section: add a `#308` entry after `#307` ("Aligned with NetBox 4.6 plugin conventions": Journal tab on every object, lookup modifiers on filter forms, form sections, quick add on invoices and invoice lines, contract type description as plain text, clearable in bulk); add to its "Behaviour changes" list: invoice template section hidden on the contract page when `show_deprecated_fields` is off; invoice pre-fill keeps values given in the page address; editing an existing invoice no longer shows today's date in place of its stored date (found while writing T029: the old copied `get()` set the date on every GET); unused `templates/contract_list_bottom.html` removed
- [X] T043 [P] Check `docs/contract.md`, `docs/invoice.md`, `docs/invoice_line.md`, `docs/contract_lines.md`, `docs/accounting_dimensions.md` where they describe forms, filters or the pre-fill (`docs/invoice.md` "Pre-fill": add that a value in the address is kept); update wording that no longer matches
- [X] T044 [P] In `CLAUDE.md`, replace "Views are mostly wired explicitly in `urls.py`; detail views use `register_model_view` + `get_model_urls`…" with the new rule (every view registered with `register_model_view`, `urls.py` only includes `get_model_urls` plus `invoice_lines_preview`; filtersets registered with `register_filterset`; forms declare `fieldsets`, pruned by `prune_fieldsets`)

### Validation

- [X] T045 Run the whole suite (`netbox_contract.tests`), `ruff check`, and `makemigrations netbox_contract --check --dry-run` (nothing pending); if a list view query-count test fails, re-record serially with `UPDATE_QUERY_COUNTS=1` and state the reason in the commit (Constitution II)
- [X] T046 Walk the manual checks of [quickstart.md](quickstart.md) in the dev NetBox (Journal tab, filter modifiers, contract form sections, add invoice from a contract, `invoiceline/add/?_quickadd=true` returning the short form). Done without a browser: the same checks run with Django's test client as a superuser against the dev NetBox database (sections on the contract add form, modifier selector on the contract list, Journal tab on a contract type, short quick-add form for an invoice line, invoice pre-fill from a contract); a visual check in the browser is left to the maintainer
- [X] T047 Update `spec.md`, `research.md` and this file if implementation deviated from them (CLAUDE.md workflow rule)

### Added after review

- [X] T048 Invoice line tables show the linked `id` column by default (maintainer request on PR #311: no other column opened the line's detail page): test `test_conventions.InvoiceLineTableTestCase` first, then `id` added to `fields` and `default_columns` of `InvoiceLineListTable` in `netbox_contract/tables.py`; CHANGELOG #308 entry

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: none; T002 before every test task
- **User stories (Phases 3-7)**: after Phase 1; independent of each other, but US1 (T007-T010) and US4/US5 (T031-T036) all edit `netbox_contract/views.py`, so run them one after the other; US3 is the only story editing `forms.py`, US2 the only one editing `filtersets.py`
- **Polish (Phase 8)**: templates (T038-T040) can start after Phase 1; translations T041 after US3 (section titles exist); T042-T044 after the stories they describe; T045-T047 last

### Within each story

Tests first and failing (except T003, a refactor guard that passes before and after), then implementation, then the
story's run task.

### Parallel opportunities

- US2 (`filtersets.py`) and US3 (`forms.py`) can proceed in parallel with US1 (`views.py`, `urls.py`), apart from
  the shared test module: add each story's test class in its own commit to avoid conflicts
- T042, T043, T044 touch different files and can run in parallel
- T030 is a read-only check

## Parallel Example

```text
# After Phase 1:
Developer A: T003-T011 (US1, views.py + urls.py)
Developer B: T012-T015 (US2, filtersets.py), then T016-T026 (US3, forms.py)
# Then sequentially on views.py: T027-T034 (US4), T035-T037 (US5)
```

## Implementation Strategy

### MVP first

Phase 1 → Phase 3 (US1): the Journal tab on every model and the URL refactor, guarded by the route test. Stop and
validate (T011).

### Incremental delivery

US1 → US2 → US3 → US4 → US5 → Polish, one commit or more per story (`308 - <what>`), each story leaving the suite green.
Everything ships together in 2.5.0 (Constitution VII: not published in pieces).

## Notes

- Commit through the pre-commit hook, never bypassed; commit messages end with the co-author line.
- `make_invoice` defaults to a Posted invoice; pass a Draft status where a test adds or edits lines.
- Plugin settings are patched with `mock.patch.dict(settings.PLUGINS_CONFIG['netbox_contract'], {...})`.
