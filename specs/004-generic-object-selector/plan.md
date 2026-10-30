# Implementation Plan: Choose related objects with a search selector

**Branch**: `318-assess-against-netbox-4-7-4` | **Date**: 2026-10-29 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/004-generic-object-selector/spec.md`

**Depends on**: [008-netbox-47-baseline](../008-netbox-47-baseline/spec.md) (minimum NetBox 4.7.0, CI on v4.7.4, green baseline). Implemented after it.

## Summary

Replace the hand-built type drop-down plus raw object field of two forms with NetBox 4.7's generic-object selector (`GenericObjectChoiceField` with `GenericObjectFormMixin`):

1. the contract assignment form, today an object type drop-down plus a typed numeric object ID;
2. the contract form's external party, today a type drop-down plus a plain choice field listing every provider, filled by custom code in the form and the edit view.

The model fields, REST, GraphQL, CSV import, bulk edit and filters do not change; one migration (merge existing duplicates, then a uniqueness rule, see User Story 4). Prototyped on NetBox 4.7.4: the form validated and saved a device assignment, refused a missing object with "Please select a device.", and the generic cloning of a model with a generic foreign key returned the expected parameters. The three places that build pre-filled links (two in Python, one template) move to the selector's parameter names, and the old names keep working.

## Technical Context

**Language/Version**: Python 3.12 to 3.14, Django 6.1 (NetBox 4.7.4)

**Primary Dependencies**: NetBox 4.7 `utilities.forms.fields.GenericObjectChoiceField`, `utilities.forms.GenericObjectFormMixin`, `utilities.forms.rendering.FieldSet(html_id=...)`; no new dependency

**Storage**: columns unchanged (`ContractAssignment.content_type/object_id`, `Contract.external_party_object_type/external_party_object_id`); one new unique constraint on assignments (contract, content type, object id) with a data migration before it

**Testing**: NetBox view tests (`PrimaryObjectViewTestCase`), form unit tests, `tests/test_conventions.py` route names

**Target Platform**: NetBox 4.7.x plugin

**Project Type**: NetBox plugin

**Performance Goals**: contract form opens without loading every provider (the selector loads the current value only); list views unchanged, so `query_counts.json` unchanged

**Constraints**: no change of stored data or public interfaces (constitution IV and V); object types offered follow `supported_models`; selectable objects follow the user's view permission

**Scale/Scope**: 2 forms, 1 model rule, 1 migration, 2 edit views, 1 model attribute, 2 links, 1 template, about 6 test locations, 3 documents

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Assessment |
|-----------|------------|
| I. NetBox-native | Pass, and improved: the forms use the platform's own control, as NetBox core forms do. Requires 4.7 (specification 008). |
| II. Tested behaviour | Pass. Tests first: pre-filled link, permission limit, `supported_models` limit, edit, assignment clone, missing object, unchanged import/bulk edit/REST. Existing form-data tests change to the new parameter names, and must fail before the change. |
| III. Lint-clean | Pass; `ruff check` before commit. |
| IV. Data safety | **Attention, justified**: the uniqueness rule needs a migration that deletes redundant duplicate assignments. It is lossless (oldest kept; tags, journal entries, bookmarks, subscriptions and image attachments moved; empty custom fields filled; conflicting custom field values written to the report), reports every merge, and is re-runnable (R10). `makemigrations --check` stays clean after the migration is added. |
| V. Backward-compatible interfaces | Pass with one declared exception: REST and import now refuse a duplicate pair (a validation error on input that used to be accepted; no field or endpoint changes). Listed under Breaking Changes. REST, GraphQL, import columns, filters otherwise unchanged. The web form's POST field names change (not a public interface); old pre-fill URLs keep working. |
| VI. Simplicity | Pass. Removes custom form and view code; no dependency. |
| VII. Documented change | Pass. `docs/contract.md`, `CHANGELOG.md` (Enhancements, Breaking Changes for the duplicate rule), README unchanged unless the `supported_models` note is added (R7). |

Post-design re-check: unchanged. No Complexity Tracking entry.

## Project Structure

### Documentation (this feature)

```text
specs/004-generic-object-selector/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── forms-and-urls.md
└── tasks.md             # /speckit-tasks, not created here
```

### Source Code (repository root)

```text
netbox_contract/
├── forms.py                      # ContractAssignmentForm, ContractForm
├── views.py                      # ContractAssignmentEditView, ContractEditView, AddContractAssignment
├── models.py                     # ContractAssignment.clone_fields, clean(), UniqueConstraint
├── migrations/0054_contractassignment_unique.py   # merge duplicates, add constraint
├── templates/netbox_contract/inc/contract_assignments_bottom.html   # Add link
├── locale/fr/LC_MESSAGES/django.po                                  # new labels
└── tests/
    ├── test_views.py             # form_data names (assignment, contract)
    ├── test_assignment_selector.py   # new: pre-fill, permissions, supported_models, clone
    └── test_assignment_duplicates.py # new: refusal, merge migration, database rule
docs/contract.md
CHANGELOG.md
```

**Structure Decision**: edit the existing forms and views in place; one new test module for the behaviours the NetBox view test case does not cover.

## Complexity Tracking

| Item | Why needed | Simpler alternative rejected because |
|------|------------|--------------------------------------|
| Data migration that deletes duplicate rows | A unique rule cannot be added while duplicates exist | Failing the upgrade and asking the administrator to clean by hand is hostile; the merge moves everything attached to the removed rows and reports the rest. |
