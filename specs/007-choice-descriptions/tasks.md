# Tasks: Descriptions under status and billing method options

**Input**: `specs/007-choice-descriptions/` (plan.md, spec.md, research.md R1-R6, data-model.md, contracts/choices.md, quickstart.md)

**Tests**: required and written first (constitution II).

**Depends on**: 008 done.

**Test command**: `cd ../netbox && NETBOX_CONFIGURATION=netbox.configuration_testing venv/bin/python netbox/manage.py test netbox_contract.tests.test_choice_descriptions --keepdb`

## Phase 1: Setup

- [ ] T001 Read `netbox_contract/models.py` (`StatusChoices` line 73, `InvoiceStatusChoices` 118, `BillingMethodChoices` 132), `netbox_contract/forms.py` (ContractForm, ContractFilterForm about line 268, InvoiceForm, InvoiceFilterForm about line 627, UnitForm, UnitFilterForm about line 1078, ContractLineFilterForm about line 1198) and the 4.7.4 `utilities/choices.py` / `utilities/forms/fields` to confirm the `Choice` signature and the `data-description` attribute (R1, R2).
- [ ] T002 Create `netbox_contract/tests/test_choice_descriptions.py` with helpers: render a form field and return `{value: data-description}`; set `FIELD_CHOICES` through `override_settings`/plugin settings.

## Phase 2: Foundational

- [ ] T003 Write the failing data tests: every built-in choice of the three sets has a non-empty description; values, labels and colours equal the lists of the previous release (copy them into the test as literals); `colors` map unchanged; REST `OPTIONS`/serializer output has no description key and unchanged choices (FR-006).

## Phase 3: User Story 1 - Know what Draft and Posted mean (P1) 🎯 MVP

**Independent test**: open the invoice form status list.

### Tests first
- [ ] T004 [US1] Failing tests: `InvoiceForm` and `InvoiceFilterForm` status options carry the descriptions of research R3 (Posted states what it locks: amount, currency, period, contracts, amounts of lines); the filter form multi-select renders them too; an option without description renders without error (FR-008).

### Implementation
- [ ] T005 [US1] `models.py`: define `InvoiceStatusChoices` with `Choice(value, label, color, description=_('...'))` using the R3 wording (colours and values unchanged).
- [ ] T006 [US1] `forms.py`: declare `InvoiceForm.status` with `utilities.forms.fields.ChoiceField` and `InvoiceFilterForm.status` with `MultipleChoiceField` (or `ChoiceField` if single, matching today) over `InvoiceStatusChoices.CHOICES` (R2). Run T003-T004.

## Phase 4: User Story 2 - Understand the billing method of a unit (P2)

- [ ] T007 [US2] Failing tests: `UnitForm.billing_method`, `UnitFilterForm` and `ContractLineFilterForm` billing method options carry the R3 descriptions (one-time, recurring, usage-based), consistent with the invoicing rules in `docs/`.
- [ ] T008 [US2] `BillingMethodChoices` with `Choice(...)` descriptions; declare the three form fields with NetBox's `ChoiceField` / `MultipleChoiceField`. Run T007.

## Phase 5: User Story 3 - Contract status and administrator choices (P3)

- [ ] T009 [US3] Failing tests: contract status descriptions on `ContractForm` and `ContractFilterForm` (line about 268, currently a plain Django field); `FIELD_CHOICES` extend case (built-in options keep descriptions, an added option without description renders); replace case (only the configured options, descriptions shown when given, none required) (FR-007).
- [ ] T010 [US3] `StatusChoices` with descriptions; declare `ContractForm.status` and `ContractFilterForm.status` with NetBox fields. Run T009.

## Phase 6: Translations and polish

- [ ] T011 Failing test first: every built-in description has a French translation different from its English source (R4). Then `makemessages -l fr` in `netbox_contract/`, translate the eight strings, `compilemessages`; run the test.
- [ ] T012 [P] `docs/invoice.md`, `docs/contract.md`, `docs/contract_lines.md` (wherever the statuses and billing methods are explained): mention that the options show a description; add the `FIELD_CHOICES` example with a `description` entry (FR-009).
- [ ] T013 [P] `CHANGELOG.md` Enhancements: descriptions under status and billing method options.
- [ ] T014 Regenerate screenshots: first `utils/docs_screenshots/make_screenshots.sh invoice contract contract_line invoice_line` for the pages changed here, then, as the last UI change of 2.6.0, regenerate the complete set with `utils/docs_screenshots/make_screenshots.sh` on NetBox 4.7.4; look at every image and keep only meaningful changes.
- [ ] T015 `ruff check`, `makemigrations --check --dry-run` (no change), full suite, `quickstart.md` manual steps (including French).
- [ ] T016 Stage the files for the owner to commit; do not bypass the pre-commit hook.

## Dependencies and order

008 → T001 → T002 → T003 → US1 → US2 → US3 → T011 → Polish. US1-US3 touch `models.py` and `forms.py`, so run in sequence. T012 and T013 parallel.

## Implementation strategy

MVP = US1 (the invoice Draft/Posted description). All three ship in 2.6.0.
