# Tasks: Contract lines, billing natures and currency consistency

**Input**: Design documents from `specs/001-contract-lines-billing/` (spec.md, plan.md, research.md, data-model.md, contracts/, quickstart.md)

**Prerequisites**: plan.md and spec.md (required); the other documents are used as noted in each task.

**Tests**: Requested by the specification (FR-027, FR-028, SC-005): existing tests are updated and new tests cover every scenario and edge case. Test tasks come first in each story and must fail before the implementation task that makes them pass.

**Organization**: Tasks are grouped by user story. The release is a single one (2.5.0); the story order below is the build order.

## Format: `- [ ] [ID] [P?] [Story?] Description with file path`

- **[P]**: can run in parallel (different files, no dependency on an unfinished task)
- **[US1]..[US6]**: the user story of spec.md the task belongs to
- All paths are relative to the repository root. `tests/` means `netbox_contract/tests/`.
- Run tests from the NetBox 4.6 checkout: `python netbox/manage.py test netbox_contract.tests --keepdb`; lint with `ruff check`.

---

## Phase 1: Setup

- [ ] T001 Confirm the development environment: a NetBox 4.6 checkout with this repository installed in editable mode, PostgreSQL and Redis running; run the existing suite once and note that it passes before any change.
- [ ] T002 [P] Pin CI to NetBox 4.6 in `.github/workflows/lint-tests.yaml`: add `ref:` with the newest `v4.6.x` tag (verify the tag exists) to the "Checkout netbox" step, and check which Python versions NetBox 4.6 supports before touching the `3.12/3.13/3.14` matrix (FR-028).
- [ ] T003 [P] Set `min_version = '4.6.0'` (no `max_version`) and `version = '2.5.0'` in `netbox_contract/__init__.py`, set `version = "2.5.0"` in `pyproject.toml`, and add the default setting `'show_deprecated_fields': False` to `default_settings` (FR-026, contracts/ui-and-settings.md).
- [ ] T004 [P] Create the new package folders with empty `__init__.py`: `netbox_contract/services/`, `netbox_contract/management/`, `netbox_contract/management/commands/`.

---

## Phase 2: Foundational (blocks all user stories)

- [ ] T005 Add the new models and fields in `netbox_contract/models.py` exactly as in data-model.md. `Unit`: name `CharField(100)` unique, description `TextField` blank, `billing_method` `CharField` choices `one_time`/`recurring`/`usage`, `months` `PositiveSmallIntegerField` null, comments `TextField` blank. `ContractLine`: `contract` FK cascade related name `lines`; description `CharField(200)`; `quantity` `DecimalField(12, 4)` default 1; `unit_price` `DecimalField(12, 2)`; `unit` FK `PROTECT`; `currency` `CharField(3)` with `CurrencyChoices`; `start_date`/`end_date` `DateField` null; `accounting_dimensions` M2M blank; comments; ordering contract, start date, description; `get_absolute_url`. `Contract.billable` `BooleanField` default `True`. `InvoiceLine.contract_line` FK `ContractLine` null `SET_NULL`; `InvoiceLine.quantity` `DecimalField(12, 4)` null.
- [ ] T006 Generate the schema migration `netbox_contract/migrations/0044_units_contract_lines_billable.py` with `makemigrations`, review it (defaults, `PROTECT`/`SET_NULL`, existing contracts get `billable = true`), and check `makemigrations --check` reports nothing pending.
- [ ] T007 [P] Write `netbox_contract/calculations.py` with no database access: `months_between(start, end)` (whole months inclusive of the end day plus leftover days divided by the days of the month in which the range ends), `recurring_invoice_amount(quantity, unit_price, unit_months, period_start, period_end, line_start, line_end)` (FR-018), `line_total_value(...)`, `line_yearly_value(...)` (quantity x unit price x 12 / unit months, recurring only), `usage_amount(quantity, unit_price)` and `invoice_line_amount(...)` (research D7). All results rounded once at the end to two decimals with `ROUND_HALF_UP`.
- [ ] T008 [P] Write `tests/test_calculations.py` (plain `SimpleTestCase`, no database) with hand-computed cases: spec US3 scenario 1 (total 1,900, yearly 1,200), US5 scenarios 1-3 (300, 30, 60), quarterly/yearly units, open-ended dates (total not available), zero and negative quantities and prices, rounding to two decimals, invoice period partly covered at start and at end, usage amount 10 x 20 = 200 and 12 x 20 = 240 (SC-004).

**Checkpoint**: models, migration and calculation engine exist; user stories can start.

---

## Phase 3: User Story 1 - Describe a contract line by line (P1) - MVP

**Goal**: units and contract lines can be created, listed, shown, edited, imported and served by the API, with dates defaults and the lock once the contract is invoiced.

**Independent Test**: create a contract with three lines (one-time, monthly, usage-based) through the UI and the API; each keeps its nature, dates and dimensions; a contract with an invoice refuses new, changed or deleted lines.

### Tests for User Story 1 (write first, they must fail)

- [ ] T009 [P] [US1] In `tests/test_views.py` add `UnitTestCase` and `ContractLineTestCase` (same pattern as the existing `ContractTestCase`: `ModelViewTestCase, ViewTestCases.PrimaryObjectViewTestCase`, `setUpTestData`, `form_data`, `csv_data`, `csv_update_data`, `bulk_edit_data`), and update `ContractTestCase`, `InvoiceTestCase`, `InvoiceLineTestCase` form data for the new fields (`billable`, `contract_line`, `quantity`).
- [ ] T010 [P] [US1] Write `tests/test_contract_lines.py` covering US1 scenarios 1-8 and edge cases: dates default to the contract's (scenario 1), recurring unit of 12 months (2), several dimensions (3), line currency defaults to the contract's (4), values update on edit and delete (5, 7), a `Unit` with `recurring` needs `months` of at least 1 and other billing methods must have none, dates outside the contract's dates are refused with the contract's dates in the message including the open-ended cases (start missing, end missing), end before start, changing contract dates so that lines fall outside is refused (FR-002a).
- [ ] T011 [P] [US1] Write `tests/test_locking.py` (FR-029, FR-001a): add, change and delete of a contract line are refused with the "new contract must be created" message once the contract has an invoice of status Draft, Posted or Canceled (each status); allowed before any invoice; deleting the contract itself still cascades to its lines; deleting a used unit is refused; changing `billing_method` or `months` of a unit used by an invoiced contract is refused, and allowed when only non-invoiced contracts use it (US1 scenarios 6 and 8).
- [ ] T012 [P] [US1] Write `tests/test_api.py` for `units/` and `contract-lines/` with `APITestCase` from `tests/custom.py`: list, get, create, patch, delete, brief mode, validation errors as 400, and the lock as 400 (contracts/rest-api.md).

### Implementation for User Story 1

- [ ] T013 [US1] In `netbox_contract/models.py` add `Unit.clean()` (`months` required and at least 1 when `billing_method` is `recurring`, must be empty otherwise; block changing `billing_method`/`months` while a line of an invoiced contract uses the unit), `ContractLine.clean()` (default the dates and currency from the contract when empty; dates within the contract's dates when the contract has them; `end_date` not before `start_date`; lock when `contract.invoices.exists()`), and `Contract.clean()` (refuse dates that leave existing lines outside them).
- [ ] T014 [US1] Add a `pre_delete` receiver for `ContractLine` in a new `netbox_contract/signals.py`, imported from `ContractsConfig.ready()` in `netbox_contract/__init__.py`, that refuses deletion when the contract has invoices but lets deletions that originate from deleting the contract itself through (use the `origin` argument; verify on NetBox 4.6's Django 6.0).
- [ ] T015 [P] [US1] Add `UnitFilterSet` and `ContractLineFilterSet` (contract, unit, currency, billing method, accounting dimensions, `q`) in `netbox_contract/filtersets.py`.
- [ ] T016 [P] [US1] Add forms in `netbox_contract/forms.py`: `UnitForm`, `UnitFilterForm`, `UnitImportForm`, `UnitBulkEditForm`, and `ContractLineForm` (contract, description, quantity, unit_price, unit, currency defaulted from the contract, dates, accounting dimensions, comments, tags), `ContractLineFilterForm`, `ContractLineImportForm`, `ContractLineBulkEditForm`, following the existing form patterns in that file.
- [ ] T017 [P] [US1] Add `UnitListTable`, `ContractLineListTable` and a `ContractLineContractTable` (columns without the contract) in `netbox_contract/tables.py`.
- [ ] T018 [US1] Add views in `netbox_contract/views.py`: list, detail, edit, delete, bulk import, bulk edit and bulk delete for `Unit` and `ContractLine`, registered with `register_model_view` like the existing models; the contract line add view accepts `?contract=<id>` to pre-select the contract.
- [ ] T019 [US1] Add the URL patterns for both models in `netbox_contract/urls.py` and the menu entries (with add buttons) in `netbox_contract/navigation.py`; add both models to `netbox_contract/search.py`.
- [ ] T020 [P] [US1] Create the templates `netbox_contract/templates/netbox_contract/unit.html` and `contractline.html` (detail pages) in the style of `contracttype.html` and `invoiceline.html`.
- [ ] T021 [US1] Update `netbox_contract/templates/netbox_contract/contract.html` and `ContractView.get_extra_context()` in `netbox_contract/views.py`: add a "Contract lines" table with an add button that carries the contract, hide add/edit/delete buttons and show the "a new contract must be created" notice when the contract has invoices.
- [ ] T022 [P] [US1] Add `UnitSerializer` and `ContractLineSerializer` (fields and validation of contracts/rest-api.md, read-only `total_value` and `yearly_value` from `calculations.py`) in `netbox_contract/api/serializers.py`, viewsets in `netbox_contract/api/views.py`, routes in `netbox_contract/api/urls.py`.
- [ ] T023 [P] [US1] Add sample import files `utils/unit_import.csv` and `utils/contract_line_import.csv`.
- [ ] T024 [US1] Run `ruff check` and the US1 tests until they pass.

**Checkpoint**: contract lines work end to end and are locked once invoiced.

---

## Phase 4: User Story 2 - Keep existing data working after the upgrade (P1)

**Goal**: the upgrade converts costs and templates into contract lines losslessly, can be re-run, and keeps invoices untouched; deprecated fields are hidden by default.

**Independent Test**: run the migration on a dataset with monthly, yearly and one-time costs, templates with dimensions, and empty contracts; compare with the originals.

### Tests for User Story 2

- [ ] T025 [P] [US2] Write `tests/test_conversion.py` calling `conversion.convert_legacy_data()` on data created with the legacy fields: `mrc` gives a "Monthly" (1 month) recurring line, `yrc` a "Yearly" (12 months) line, `nrc` above zero a one-time line with the same prices (scenarios 1-3), contract with no costs gets no line (6), template lines become recurring lines with dimensions copied and no separate `mrc`/`yrc` line (4), template total different from the recurring cost is written to the returned report and not added as a line, both `mrc` and `yrc` set (`yrc` wins), lines take the contract's dates and currency, all contracts billable, invoices and invoice lines unchanged and templates kept (5), running twice creates no duplicate line and no duplicate unit (FR-016), contracts that already have lines are skipped, conversion works for contracts that already have invoices (lock does not apply).
- [ ] T026 [P] [US2] Add to `tests/test_views.py` cases for hidden deprecated fields: `mrc`/`yrc`/`nrc` absent from the contract form and detail page by default and present when `show_deprecated_fields` is true; a `mandatory_contract_fields` or `hidden_contract_fields` entry that names a deprecated field does not crash (logged warning); template invoices show a "deprecated" badge and remain reachable from the contract page.

### Implementation for User Story 2

- [ ] T027 [US2] Write `netbox_contract/conversion.py` with `convert_legacy_data(apps=None)` implementing research D8 (find-or-create units "One-time", "Monthly", "Yearly" by name; skip contracts that already have lines; template lines replace the recurring line; report of differences; usable both with real models and with the historical models of a migration).
- [ ] T028 [US2] Write the data migration `netbox_contract/migrations/0045_convert_legacy_costs.py` (`RunPython` calling `convert_legacy_data`, reverse no-op, depends on 0044) and check it on a copy of a database with legacy data.
- [ ] T029 [P] [US2] Write `netbox_contract/management/commands/convert_contract_lines.py` that runs the conversion again and prints the report.
- [ ] T030 [US2] Implement the deprecated-field behaviour: honour `show_deprecated_fields` in `ContractForm` (`netbox_contract/forms.py`), `ContractListTable` (`netbox_contract/tables.py`) and `contract.html`; mark `mrc`, `yrc`, `nrc`, `calculated_rc` and `Invoice.template` as deprecated in the API serializers (`netbox_contract/api/serializers.py`) and help texts; show the "deprecated" badge on template invoices in `invoice.html` and a read-only "Invoice templates (kept for reference)" panel in `contract.html`; keep the "only one template per contract" checks; offer creating a new template only when `show_deprecated_fields` is true.
- [ ] T031 [US2] Run `ruff check` and the US2 tests until they pass.

**Checkpoint**: an upgraded installation shows its former costs and templates as contract lines and nothing is lost.

---

## Phase 5: User Story 3 - Control billing and see contract values (P2)

**Goal**: contracts have a billable flag and computed total, yearly and yearly billable values.

**Independent Test**: contracts with known lines (recurring, one-time, usage, open-ended, non-billable children) show the hand-computed values.

### Tests for User Story 3

- [ ] T032 [P] [US3] Write `tests/test_values.py`: scenario 1 (total 1,900, yearly 1,200), scenario 2 (billable parent includes non-billable child recurring lines, child's own yearly billable value is zero, billable child is not rolled up), scenario 4 (open-ended: total "not available", yearly shown), zero and negative amounts, multi-level hierarchy, a contract with no lines, and that the contract detail page and the contract list show the values (also updating `tests/query_counts.json` expectations).
- [ ] T033 [P] [US3] Extend `tests/test_api.py` for `contracts/`: `billable` writable, `total_contract_value` (null when not available), `yearly_contract_value`, `yearly_billable_value` read-only, deprecated fields still served, filter `billable`.

### Implementation for User Story 3

- [ ] T034 [US3] Add to `Contract` in `netbox_contract/models.py` the properties `total_contract_value`, `yearly_contract_value` and `yearly_billable_value` (data-model.md: zero for a non-billable contract; own recurring lines plus those of non-billable descendants, stopping at billable descendants) using `netbox_contract/calculations.py`.
- [ ] T035 [US3] Replace the `calculated_rc` annotation in `ContractView`, `ContractListView` (`netbox_contract/views.py`) and `ContractViewSet` (`netbox_contract/api/views.py`) by one annotation of the yearly value over recurring lines (no query per row); keep `calculated_rc` as a deprecated alias in the serializers.
- [ ] T036 [P] [US3] Add the `billable` field and filter to `ContractForm`, `ContractBulkEditForm`, `ContractFilterForm`, `ContractFilterSet`, the import form, `ContractListTable`, and add the values summary panel ("Not available" when open-ended) to `contract.html`; add `billable` and the computed fields to `ContractSerializer` in `netbox_contract/api/serializers.py`.
- [ ] T037 [US3] Regenerate `netbox_contract/tests/query_counts.json` after the list-view changes; run `ruff check` and the US3 tests until they pass.

**Checkpoint**: finance users can see contract values and control billing.

---

## Phase 6: User Story 4 - Prevent inconsistent currencies (P2)

**Goal**: mismatched currencies cannot be newly saved; existing mismatches are reported, never changed.

**Independent Test**: try each mismatch and check the refusal and the message; run the report on data with mismatches.

### Tests for User Story 4

- [ ] T038 [P] [US4] Write `tests/test_currency.py`: scenarios 1-7 of US4 (contract line CHF in EUR contract, invoice versus contract, invoice line versus invoice, contract currency change refused with invoices and accepted with only lines which then follow, non-billable child under a parent of another currency, new invoice with two contracts refused while an existing multi-contract invoice stays editable and cannot get another contract), messages naming both currencies, through the model, the UI forms and the REST API.
- [ ] T039 [P] [US4] Write `tests/test_reports.py` for `find_currency_mismatches()`: lists each kind of mismatched record with a link, alters nothing, returns nothing on clean data (SC-003).

### Implementation for User Story 4

- [ ] T040 [US4] Write `netbox_contract/validators.py` with the shared invoice checks (at most one contract for a new invoice; invoice currency equals contract currency; no increase of the number of contracts on an existing multi-contract invoice) used by `InvoiceForm.clean()` in `netbox_contract/forms.py` and `InvoiceSerializer.validate()` in `netbox_contract/api/serializers.py`.
- [ ] T041 [US4] Add the currency rules to the model `clean()` methods in `netbox_contract/models.py`: `ContractLine.currency` equals the contract's; `InvoiceLine.currency` equals the invoice's; `Contract.currency` cannot change when invoices or invoice lines exist and otherwise the contract's lines follow (updated in `Contract.save()`); a non-billable child has its parent's currency, checked from both sides (`Contract.clean()`).
- [ ] T042 [P] [US4] Write `netbox_contract/reports.py` with `find_currency_mismatches()` returning plain records (kind, object, expected, found, URL) and add the read-only script "Report currency mismatches" to `scripts/netbox-contract.py`; remove the stale scripts `create_invoice_template` and `create_invoice_lines` from that file (contracts/ui-and-settings.md).
- [ ] T043 [US4] Run `ruff check` and the US4 tests until they pass.

**Checkpoint**: new inconsistencies are impossible and old ones are visible.

---

## Phase 7: User Story 5 - Pre-fill an invoice from the contract lines (P2)

**Goal**: the invoice add screen proposes amount and period from contract lines.

**Independent Test**: reference scenarios (full period, partial period, one-time partly and fully invoiced, mixed lines) give the hand-computed proposals.

### Tests for User Story 5

- [ ] T044 [P] [US5] Write `tests/test_prefill.py` (GET of the invoice add view with `?contracts=<id>`): scenarios 1-8 of US5 (300, 30, 60 prorated, one-time 500 with 200 on Posted invoice lines gives 300, draft and canceled ignored, fully invoiced gives nothing, no lines gives nothing, usage line excluded), non-billable contract shows an error message and proposes no amount (FR-008), period derived from `invoice_frequency` and the last invoice, a template invoice is ignored, remaining amount never negative, currency from the contract, all values editable.

### Implementation for User Story 5

- [ ] T045 [US5] Write `netbox_contract/services/invoicing.py` with `propose_invoice(contract, period_start, period_end)` returning per-line proposals and a total from `calculations.py`, including the one-time remaining amount from invoice lines that reference the contract line on Posted invoices (FR-017..FR-019, FR-017a).
- [ ] T046 [US5] Replace the `mrc`/`yrc` amount logic in `InvoiceEditView.get()` (`netbox_contract/views.py`) by `propose_invoice`, add the non-billable error message, and stop using invoice templates for the proposal.
- [ ] T047 [US5] Run `ruff check` and the US5 tests until they pass.

**Checkpoint**: invoices are pre-filled from contract lines.

---

## Phase 8: User Story 6 - Generate invoice lines from the contract lines (P3)

**Goal**: one action generates the invoice lines; the quantity is on the invoice line and the amount is calculated; templates are no longer copied.

**Independent Test**: generate for a hierarchy (billable parent, non-billable child and grandchild, billable child) and check lines, quantities, amounts, dimensions and references.

### Tests for User Story 6

- [ ] T048 [P] [US6] Write `tests/test_generation.py`: scenarios 1-8 of US6 (one line per applicable contract line with reference and dimensions; non-billable descendants included, billable child excluded; non-billable contract fails; usage line generated with no quantity and amount 0, then quantity 10 at 20 gives 200 and 12 gives 240; recurring 100 per month over 3 months gives quantity 1 and amount 300; template lines not copied on invoice save and the template invoice untouched; editing dimensions keeps the reference), one-time quantity reduced by the quantity already on Posted invoices and never below 0, invoice that already has lines (refused unless `replace`), currency of generated lines, contract line from an unrelated contract refused, amount ignored when a contract line is set and required when not, sum of lines above the invoice amount still refused.
- [ ] T049 [P] [US6] Extend `tests/test_api.py` for `invoices/{id}/generate-lines/` (with `quantities` and `replace`) and for `invoice-lines/` (`contract_line`, `quantity`, read-only `unit` and `unit_price`, calculated `amount`).

### Implementation for User Story 6

- [ ] T050 [US6] In `InvoiceLine` (`netbox_contract/models.py`) add the read-only properties `unit` and `unit_price` (from `contract_line`), refuse a `contract_line` that is not of the invoice's contract or of one of its non-billable descendants, and calculate `amount` in `clean()`/`save()` with `calculations.invoice_line_amount` when `contract_line` is set (research D7), keeping the existing "sum of lines not above invoice amount" check.
- [ ] T051 [US6] Add `generate_invoice_lines(invoice, quantities=None, replace=False)` to `netbox_contract/services/invoicing.py`: applicable lines of the invoice's billable contract plus non-billable descendants (stop at billable children), refuse a non-billable contract, set contract line, dimensions, currency, quantity (contract quantity; one-time reduced by what is already invoiced on Posted invoices; usage empty unless given) and calculated amount.
- [ ] T052 [P] [US6] Update `InvoiceLineForm` in `netbox_contract/forms.py` (fields "Contract line" limited to the invoice's contracts and descendants, "Quantity"; amount not required when a contract line is chosen) and `InvoiceLineListTable` in `netbox_contract/tables.py` (quantity, unit, unit price columns); update `invoiceline.html` to show unit and unit price.
- [ ] T053 [US6] Add the "Generate invoice lines" view and URL (`netbox_contract/views.py`, `netbox_contract/urls.py`), a small form with a quantity input for usage-based lines, the button on `netbox_contract/templates/netbox_contract/invoice.html` (permission `add_invoiceline`), and the error messages.
- [ ] T054 [P] [US6] Update `InvoiceLineSerializer` and add the `generate-lines` action to `InvoiceViewSet` in `netbox_contract/api/serializers.py` and `netbox_contract/api/views.py` per contracts/rest-api.md.
- [ ] T055 [US6] Remove the template-line copy from `InvoiceForm.save()` in `netbox_contract/forms.py` and from `InvoiceSerializer.create()` in `netbox_contract/api/serializers.py`; template invoices stay untouched and undeleted.
- [ ] T056 [US6] Run `ruff check` and the US6 tests until they pass.

**Checkpoint**: the full workflow works from contract lines to invoice lines.

---

## Phase 9: Polish and cross-cutting

- [ ] T057 [P] Documentation: `docs/contract.md` (billable, values, deprecated fields, lock), new `docs/contract_lines.md` (units and lines) added to `mkdocs.yml`, `docs/invoice.md` (pre-fill, generation, templates kept), `docs/invoice_line.md` (quantity, calculated amount), `docs/api.md` (new endpoints and action), `README.md` (plugin settings table: `show_deprecated_fields`, NetBox 4.6 minimum).
- [ ] T058 [P] `CHANGELOG.md`: add version 2.5.0 (issue #278) describing the new models, conversion, lock, currency rules, removal of the template-line copy, the report script, the removed stale scripts and the NetBox 4.6 minimum; note the deprecated fields.
- [ ] T059 [P] Update the remaining sample files in `utils/` (`contract_import.csv` with `billable`, `invoice_line_import.csv` with `contract_line` and `quantity`).
- [ ] T060 Regenerate `netbox_contract/tests/query_counts.json` one final time and make sure the whole suite passes on the pinned NetBox 4.6 tag (SC-005, FR-028).
- [ ] T061 Coverage check: walk the traceability table in `specs/001-contract-lines-billing/quickstart.md` and the spec's edge case list and confirm each scenario and edge case has at least one test; add the missing ones (also: recurring line without end date, credit (negative) lines, a unit whose months change after invoices exist, Canceled invoices when computing what remains, running the conversion on contracts that already have lines). Update the test module names in `plan.md` (`test_contract_lines.py`, `test_values.py`, `test_locking.py` are added).
- [ ] T062 Run the manual walkthrough of `specs/001-contract-lines-billing/quickstart.md` on an upgraded copy of real data and fix any gap; run `ruff check`, `makemigrations --check` and the full suite.

---

## Dependencies and execution order

- **Setup** has no dependency. **Foundational** needs Setup and blocks every story.
- **US1** needs Foundational. **US2** needs US1 (models and units). **US3** needs US1 and `calculations.py`. **US4** needs US1 (contract lines) and can run in parallel with US2 and US3. **US5** needs US3 (calculations on contracts) and US1. **US6** needs US5 (`services/invoicing.py`) and US4 (currency rules).
- **Polish** needs all stories.
- Within a story: tests first (they must fail), then models and validation, then filters/forms/tables (parallel), then views/urls/templates, then API.

## Parallel opportunities

- Setup: T002, T003, T004 together.
- Foundational: `calculations.py` and `tests/test_calculations.py` in parallel with the model work once the model task is started.
- US1: the four test tasks together; filtersets, forms, tables, templates, API and sample files are separate files and run in parallel after the model task.
- After US1: US2, US3 and US4 by different people; documentation, changelog and sample files in Polish.

## Implementation strategy

- **MVP**: Setup, Foundational and US1 (contract lines usable and locked), then US2 immediately, since it is the riskiest part and an upgrade without it would break current users.
- **Incremental**: add US3, US4, US5 and US6 in that order, running the full suite after each story. Everything ships together as version 2.5.0; do not publish an intermediate version.
- Commit after each task or logical group; the pre-commit hook runs `ruff` on `netbox_contract/`.
