# Implementation Plan: Align with NetBox 4.6 plugin conventions

**Branch**: `308-align-with-netbox-4-6-plugin-conventions` | **Date**: 2026-09-30 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/002-netbox-46-conventions/spec.md` (GitHub issue #308)

## Summary

Bring the plugin's views, URLs, filtersets and forms onto the NetBox 4.6 plugin conventions, with no change to data,
REST API, settings or import columns, in the not-yet-released 2.5.0 (patch-level change, see D9). The approach: register every view of the nine models
with `register_model_view` and reduce `urls.py` to `get_model_urls` includes (which brings the Journal tab to the four
models that lack it), register the nine filtersets with `register_filterset` (lookup modifiers on filter forms), add
`fieldsets` to model, bulk-edit and filter forms while keeping fields hidden by settings out of them, feed the invoice
and invoice line pre-fill through `request.GET` and call core `ObjectEditView.get()` (quick add and HTMX partials),
move the root template under `templates/netbox_contract/inc/` and delete the unused one, and look up the deprecated
invoice template on the contract page only when deprecated fields are shown. Details:
[research.md](research.md), [data-model.md](data-model.md), [contracts/](contracts/), [quickstart.md](quickstart.md).

## Technical Context

**Language/Version**: Python 3.12 or newer (CI matrix 3.12, 3.13, 3.14)

**Primary Dependencies**: NetBox 4.6 (`min_version = '4.6.0'`; CI pinned to `v4.6.10`), Django, django-filter,
django-tables2 as shipped with NetBox; no new dependency

**Storage**: PostgreSQL through the Django ORM; no schema or data change

**Testing**: NetBox test runner (`manage.py test netbox_contract.tests`); new module `tests/test_conventions.py`;
existing `test_views.py` (`PrimaryObjectViewTestCase`), `test_prefill.py`, `test_issue_307.py` as regression nets;
ruff for lint

**Target Platform**: NetBox plugin on Linux servers (self-hosted NetBox 4.6)

**Project Type**: NetBox plugin (Django app, web UI plus REST API)

**Performance Goals**: list view query counts unchanged (`tests/query_counts.json`); the contract page does one to
two fewer queries when deprecated fields are hidden

**Constraints**: all 82 existing route names and addresses kept (FR-003); no REST, setting, import column or data
change (FR-013); the #307 permission restriction on pre-fill kept; no use of APIs announced for removal in 4.7

**Scale/Scope**: 9 models; files touched: `urls.py`, `views.py`, `filtersets.py`, `forms.py`,
`template_content.py`, 2 templates, `locale/*`, `CHANGELOG.md`, `docs/`, `CLAUDE.md`;
1 new test module

## Constitution Check

Checked against `.specify/memory/constitution.md` version 1.0.0 (Principles I-VII), before Phase 0 and again after
Phase 1:

| Principle | Status | Evidence |
|---|---|---|
| I. NetBox-native plugin | Met | the feature is the alignment itself: `register_model_view`/`get_model_urls` (D1), `register_filterset` (D2), `FieldSet` (D3), core `ObjectEditView.get()` (D5); every API used exists in 4.6 and none is announced for removal |
| II. Tested behaviour | Met | `test_conventions.py` written first, failing before the change, covering every scenario and edge case (quickstart scenario map); query-count baselines re-recorded only with a stated reason (D8) |
| III. Lint-clean | Met | `ruff check` after each story; no rule disabled |
| IV. Data safety and migrations | Met | no model change; `makemigrations --check` in the validation steps; the deleted template is not data and not a public interface |
| V. Backward-compatible interfaces | Met | route names and addresses kept and tested (contracts/routes.md); filter query strings unchanged; REST API, settings and import columns untouched; the two visible changes are listed as behaviour changes |
| VI. Simplicity | Met | no dependency; removes about 300 lines of hand-written routes and two copies of core `get()`; the fieldset filtering is a small helper next to `apply_field_settings` |
| VII. Documented change | Met | CHANGELOG 2.5.0 section (#308 entry) with "Changed" and "Behaviour changes", docs checked where forms are described, `CLAUDE.md` architecture note updated; patch version per clarification Q4 |

Re-check after design: no violation, so no entry in Complexity Tracking.

## Decisions taken with the maintainer

1. **Invoice template section hidden** on the contract page when `show_deprecated_fields` is off (Q1, D7).
2. **All views registered** through `register_model_view`, `urls.py` reduced to includes (Q2, D1).
3. **`contract_list_bottom.html` deleted**, `contract_assignments_bottom.html` moved (Q3, D6).
4. **Patch-level release** (Q4): shipped in the unreleased 2.5.0 as a #308 entry (D9, confirmed by the maintainer).
5. **The address wins** for pre-filled values on the invoice and invoice line add screens (Q5, D5).
6. **Contract type description clearable in bulk** (D4) and **French section titles** translated by Claude (D6), both accepted.

Points to watch during implementation:
- A form with `fieldsets` renders only listed fields: a forgotten field disappears silently. The generic
  "every visible field in exactly one section" test guards this; write it first.
- `add` and `edit` are stacked on the same edit view class (as core does); `ContractAssignmentEditView.alter_object`
  and `get_extra_addanother_params` must keep working for `add` (URL kwargs stay empty for list-level routes).
- `invoice_lines_preview` must stay a hand-written path in the `invoices/` prefix; place it before the include.
- Pre-fill precedence: a value in the query string wins on both screens (`setdefault`, D5, clarification Q5); for
  invoices this is a behaviour change covered by a test and the changelog.

## Project Structure

### Documentation (this feature)

```text
specs/002-netbox-46-conventions/
├── spec.md
├── plan.md              # this file
├── research.md          # Phase 0: decisions D1-D9
├── data-model.md        # Phase 1: no schema change; routes per model
├── quickstart.md        # Phase 1: validation commands and scenario map
├── contracts/
│   ├── routes.md        # the 82 route names kept (test fixture)
│   └── forms.md         # form sections, filter modifiers, edit screen responses
├── checklists/requirements.md
└── tasks.md             # created by /speckit-tasks
```

### Source Code (repository root)

```text
netbox_contract/
├── urls.py                     # one detail=False and one detail include per model + invoice_lines_preview
├── views.py                    # register_model_view on every view (D1); InvoiceEditView/InvoiceLineEditView get() via super() (D5); ContractView invoice template only with deprecated fields (D7)
├── filtersets.py               # @register_filterset on the nine filtersets (D2)
├── forms.py                    # fieldsets on model, bulk-edit and filter forms; hidden/deprecated names removed from fieldsets; contract type description CharField (D3, D4)
├── template_content.py         # template path netbox_contract/inc/contract_assignments_bottom.html (D6)
├── templates/
│   ├── contract_assignments_bottom.html     # moved →
│   ├── contract_list_bottom.html            # deleted
│   └── netbox_contract/inc/contract_assignments_bottom.html
├── locale/{en,fr}/LC_MESSAGES/django.{po,mo}   # references refreshed
└── tests/
    └── test_conventions.py     # NEW (D8)
CHANGELOG.md, docs/, CLAUDE.md  # D9
```

**Structure Decision**: the existing single-plugin layout is kept; no new module other than the test module.

## Complexity Tracking

No constitution violation to justify.
