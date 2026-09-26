# Phase 0 Research: Contract lines, billing natures and currency consistency

Feature branch: `278-replace-invoice-templates-with-contract-lines` | Spec: [spec.md](spec.md)

The assessment (`.specify/assessments/contract-lines-units/`) already settled the strategic questions (target NetBox 4.6, phased delivery, no money library). This file records the technical decisions taken for the plan, after reading the current code of the plugin (`netbox_contract/`). No `NEEDS CLARIFICATION` remains; items marked "verify" are checks to perform during implementation, not open decisions.

## What the current code does (facts that drive the design)

- `Contract` holds `mrc`, `yrc`, `nrc`, `invoice_frequency` and `currency` (a plain `CharField` whose choices come from NetBox `FIELD_CHOICES`, lower-case values such as `eur`). It has no accounting dimensions of its own any more.
- `Invoice` has a `template` boolean, a `contracts` many-to-many field, a `currency` and an `amount`. `InvoiceLine` has an `invoice`, `currency`, `amount` and dimensions.
- The invoice add screen pre-fills period and amount in `InvoiceEditView.get()` (`views.py`, around lines 437-471) from `mrc`, `yrc` and `invoice_frequency`.
- `InvoiceForm.save()` (`forms.py`) and `InvoiceSerializer.create()` (`api/serializers.py`) copy the lines of the contract's invoice template onto a new invoice.
- The contract list, contract detail and API view annotate `calculated_rc` with a SQL `Case`/`Round` expression built from `yrc` and `mrc`.
- `scripts/netbox-contract.py` holds NetBox custom scripts; `create_invoice_template` still reads `contract.accounting_dimensions` and `create_invoice_lines` reads `invoice.accounting_dimensions`, fields that no longer exist, so these two scripts are already stale.
- Tests: only `netbox_contract/tests/test_views.py` (generic NetBox view test cases per model) and a `query_counts.json` baseline; there are no API, model or calculation tests.
- CI (`.github/workflows/lint-tests.yaml`) checks out the default branch of `netbox-community/netbox` and runs the tests on Python 3.12, 3.13 and 3.14.
- Plugin metadata: version 2.4.7 (both `__init__.py` and `pyproject.toml`), `min_version = '4.5.0'`.

## Decisions

### D1. Data model: two new models, one new field

- **Decision**: add `Unit` and `ContractLine` as `NetBoxModel`s, add `Contract.billable` (boolean, default true), and add `InvoiceLine.contract_line` (nullable foreign key, set null on delete) and `InvoiceLine.quantity` (nullable decimal). Full detail in [data-model.md](data-model.md).
- **Rationale**: matches the spec's key entities and the plugin's existing conventions (every model is a `NetBoxModel` with views, table, filterset, form, API serializer).
- **Alternatives considered**: putting the billing method on the contract line instead of a unit (rejected: loses the reusable "monthly / quarterly / yearly" definitions the issue asks for); a separate model for usage records (out of scope in the spec).

### D2. Money and rounding: plain decimals, no library

- **Decision**: `DecimalField` everywhere, currency as the existing string code. Unit price `max_digits=12, decimal_places=2`; quantity `max_digits=12, decimal_places=4` (usage quantities such as gigabytes are fractional). All computed amounts are rounded once, at the end of a calculation, to two decimals with `ROUND_HALF_UP`.
- **Rationale**: the assessment decision (django-money does not support Django 6, which NetBox 4.6 requires). The plugin never converts currencies, so a money type adds nothing.
- **Alternatives considered**: `py-moneyed` alone (unneeded weight, still no conversion); rounding each intermediate step (rejected: accumulates error and makes hand-computed test values ambiguous).

### D3. Currency of a contract line: stored, defaulted, validated

- **Decision**: `ContractLine` stores its own `currency` (same field definition as `Invoice.currency`), defaulted from the contract in the form and the API, and validated in the model's `clean()`. When a contract's currency changes and it has no invoices, its contract lines are updated in the same save (spec FR-009a).
- **Rationale**: the spec requires a save to be refused when a contract line's currency differs from its contract (FR-009), which only makes sense if the line has its own currency; it also mirrors `Invoice` and `InvoiceLine`, so the same validation pattern and the same table/filter columns are reused.
- **Alternatives considered**: a derived property with no stored field (rejected: the mismatch could never be expressed, imports could not set it, and the spec's scenario 4.1 would be untestable).

### D4. Where validation lives

- **Decision**: all single-record rules go in each model's `clean()` (currency match, line dates inside contract dates, non-billable child currency versus parent, contract currency change blocked by invoices, unit deletion blocked by contract lines through a `PROTECT` foreign key). NetBox's UI forms, bulk import forms and REST serializers all run model validation, so one implementation covers all three (verify against NetBox 4.6 `ValidatedModelSerializer`). The `Invoice.contracts` many-to-many rules ("new invoice links to at most one contract", "invoice currency equals its contract currency") cannot live in `clean()` because the relation is saved after the invoice, so they are checked in `InvoiceForm.clean()` and `InvoiceSerializer.validate()` through one shared helper in `validators.py`.
- **Lock once invoiced (FR-029)**: a contract line cannot be added, changed or deleted when its contract has any invoice (any status), and cannot be changed or deleted when any invoice line references it (this covers the lines of a non-billable child invoiced through its billable parent). Add and change are checked in `ContractLine.clean()`; deletion is checked in a `pre_delete` signal receiver that ignores deletions started by deleting the contract itself (Django passes the `origin` of a cascade to the receiver; verify on NetBox 4.6's Django 6.0). A `Unit`'s billing method and months cannot change while a line of an invoiced contract uses it (`Unit.clean()`). The conversion migration uses historical models, so neither `clean()` nor the signals run for it; converted lines of contracts that already have invoices are therefore locked from the first day, and the fix is a new contract, as the maintainer decided.
- **Grandfathering**: an existing invoice that already has several contracts stays editable; the rule only refuses an edit that would make the number of contracts larger than it was.
- **Alternatives considered**: database check constraints (cannot span tables); Django signals on `m2m_changed` (fire after the write, so they cannot refuse cleanly).

### D5. Calculation engine: pure functions in one module

- **Decision**: a new module `netbox_contract/calculations.py` with no database access: `months_between(start, end)`, `recurring_amount(...)`, `one_time_remaining(...)`, `line_total_value(...)`, `yearly_value(...)`. Model properties and views call it. Definitions:
  - months in a date range = whole months between start and end (inclusive of the end day) plus the leftover days divided by the number of days of the month in which the range ends;
  - recurring line for an invoice period = quantity x unit price x (months covered by the invoice period) / (unit months) and, when the line only partly overlaps the period, x (days of overlap) / (days of the period), per spec FR-018;
  - total value of a recurring line = quantity x unit price x (months in the line's own dates) / (unit months); one-time = quantity x unit price; usage-based = quantity x unit price;
  - yearly value = recurring lines only, quantity x unit price x 12 / (unit months).
- **Rationale**: pure functions can be tested exhaustively with hand-computed cases (spec SC-004) without a database, and the same functions serve pre-fill, generation and manual edits, which is what FR-025 requires.
- **Alternatives considered**: computing in SQL only (rejected: proration by days is unreadable and untestable in SQL; used only for the list annotation, see D6).

### D6. Computed contract values: computed on read, not stored

- **Decision**: total, yearly and yearly billable values are computed on read (model properties for the detail page and API). The contract list uses one SQL annotation for the yearly value (sum over recurring lines) so that the list does not run a query per row; it replaces the `calculated_rc` annotation, which stays available as a deprecated alias in the API during the deprecation period.
- **Rationale**: stored copies would need updating on every line, unit and hierarchy change and would drift. The dataset (contracts of one organisation) is small.
- **Alternatives considered**: cached columns refreshed by signals (rejected: complexity and staleness for no measured need).

### D7. Invoice pre-fill, invoice line quantity and generation (single release)

- **Decision**: extract the amount logic from `InvoiceEditView.get()` into `services/invoicing.py`: `propose_invoice(contract, period_start, period_end)` gives the header amount proposal (recurring and one-time lines, usage-based lines excluded) and `generate_invoice_lines(invoice, quantities=None)` creates the lines. `InvoiceLine` gets an optional `contract_line` and a `quantity`; when `contract_line` is set, the unit and unit price are read from it (properties, not copied) and the **amount is calculated** in `InvoiceLine.clean()`/`save()` by `calculations.invoice_line_amount(...)`:
  - usage-based: quantity x unit price (a missing quantity gives 0);
  - recurring: quantity x unit price x (months covered by the invoice period) / (unit months), multiplied by (days of overlap) / (days of the period) when the line only partly overlaps the period;
  - one-time: quantity x unit price. At creation the quantity of a one-time line is its contract quantity minus the quantity already invoiced for it on Posted invoices (never below 0), which gives the same amount as the spec rule FR-019 because posted amounts are quantity x unit price.
  A line without a `contract_line` keeps a free, manually entered amount as today.
- **Generation at invoice creation**: one service function `generate_invoice_lines(invoice)` called only when a new invoice is created, from `InvoiceForm.save()` (screen) and `InvoiceSerializer.create()` (REST), not on edit and not on bulk import (maintainer decision, finding C5: there is no separate generation action, so an invoice that already has lines cannot be regenerated). It applies FR-022 (non-billable descendants, stopping at billable children), refuses non-billable contracts, copies the dimensions and sets the reference. Usage-based lines are generated with no quantity (amount 0). The creation is refused when the invoice amount is lower than the total of the lines that would be generated (maintainer decision, finding N1), which keeps the existing rule that lines never exceed the invoice amount; the total is the sum of the amounts of the lines that would be generated (usage-based lines count as 0).
- **Header amount**: the invoice add screen proposes the header amount and period from `propose_invoice` (recurring and one-time lines only, FR-017a); the existing rule that lines cannot exceed the invoice amount stays, so once a usage quantity is entered the user raises the invoice amount.
- **Removed**: the copy of template lines in `InvoiceForm.save()` and `InvoiceSerializer.create()` (invoice templates are kept but no longer used).
- **Rationale**: one place for the amount rules used by pre-fill, generation and manual edits (FR-024, FR-025); the maintainer decided that the quantity lives on the invoice line and the amount is calculated.
- **Consequence**: recurring line amounts depend on the invoice period; they are recalculated when a line is saved, not automatically when the invoice period changes (edge case in the spec).

### D8. Conversion of existing data

- **Decision**: schema migration `0044` creates the tables and the field; data migration `0045` calls `conversion.convert_legacy_data()`, a function that is also exposed as a management command so it can be run again (FR-016). It is idempotent: a contract that already has contract lines is skipped; units are found or created by name ("One-time", "Monthly", "Yearly").
  - `mrc` becomes a recurring line on the "Monthly" unit; `yrc` on the "Yearly" unit (12 months); `nrc` above zero becomes a one-time line. When both `mrc` and `yrc` are set, `yrc` wins, like the current invoice pre-fill does.
  - A contract's invoice template becomes recurring contract lines (one per template line, dimensions copied, price = template line amount, covering `invoice_frequency` months, description "Migrated from invoice template"). When a template with lines exists these lines replace the `mrc`/`yrc` line, since the template already splits the recurring cost by dimension. If the template total differs from the recurring cost for the same period, the difference is written to the conversion report (not silently added), and the deprecated cost fields stay visible for comparison.
  - All contract lines take the contract's own dates and currency; all contracts get `billable = true`; invoices and invoice lines are untouched.
- **One-time lines and past invoices**: old invoices carry no reference to a contract line, so a converted one-time line on a contract that already has a Posted invoice would be proposed again in full. The conversion therefore sets `ContractLine.invoiced_at_conversion = True` on it (maintainer decision, finding C2); pre-fill and generation treat such a line as fully invoiced, and the user can still enter an amount by hand. On a contract with no Posted invoice the line is proposed normally.
- **Rationale**: lossless, re-runnable, and no guess is hidden: every judgement call appears in the report.
- **Alternatives considered**: adding the difference as an extra line (rejected: can double count); deleting the deprecated fields now (rejected by the spec, FR-015).

### D9. Deprecated fields, hiding and the invoice templates

- **Decision**: keep `mrc`, `yrc`, `nrc` and `Invoice.template`. A new plugin setting `show_deprecated_fields` (default `false`) controls whether the cost fields appear in the contract form and detail page; the setting is added to `default_settings`. API serializers keep the fields, documented as deprecated. Template invoices are kept and never deleted (maintainer decision); they are shown with a "deprecated" label, stay out of the default invoice list as they are today in the contract view, and remain reachable from the contract detail page for reference. The option to create new templates is offered only when `show_deprecated_fields` is true.
- **Rationale**: FR-015 and SC-007; the existing `hidden_contract_fields` setting already hides fields, so the new default can be expressed the same way and users who configured it keep control.

### D10. Currency mismatch report

- **Decision**: the detection logic lives in `netbox_contract/reports.py` (`find_currency_mismatches()`, returns plain records so it can be tested), and a read-only custom script `Report currency mismatches` in `scripts/netbox-contract.py` prints it with links. This follows the maintainer's answer in the clarification session. The two stale scripts (`create_invoice_template`, `create_invoice_lines`) are removed from that file because they reference deleted fields and are superseded by the conversion.
- **Consequence to record**: NetBox core custom scripts are announced as deprecated and replaced by an open-source plugin; moving this script is part of the later NetBox 4.7 work and is not designed here.

### D11. NetBox 4.6 baseline and CI

- **Decision**: `min_version = '4.6.0'` in `__init__.py`; `.github/workflows/lint-tests.yaml` checks out `netbox-community/netbox` at a pinned 4.6 tag (`ref: v4.6.x`, the newest 4.6 release tag at implementation time; verify it exists and which Python versions NetBox 4.6 supports before touching the matrix). New code must avoid APIs planned for removal in 4.7; the only known one is the custom script framework used by the report (D10).
- **Rationale**: FR-026 and FR-028; a pinned tag makes CI reproducible and stops a moving `main` from breaking the tests.

### D12. Versioning and documentation

- **Decision**: a single release, plugin version 2.5.0 (new models and a data migration justify a minor version); update `docs/` (contract, a new contract lines page, invoice), `CHANGELOG.md`, `README.md` and the sample import files in `utils/`.

## Decisions taken during implementation (reviewed with the maintainer on 2026-09-26)

- **I1. Currency checks and existing mismatches**: invoices, invoice lines and non-billable children are checked when they are new or when their currency, contract, invoice, parent or billable flag changes. Records mismatched before the upgrade stay editable and are listed by the report script (FR-012).
- **I2. Empty line dates follow the contract**: an empty start or end date of a contract line means the contract's date, for the calculations and for the date checks, so an open-ended contract with invoices can still be given an end date.
- **I3. Pre-fill scope**: the pre-fill covers the same lines as the generation (own lines and those of non-billable descendants), so the proposed amount always passes the FR-021 amount check.
- **I4. No invoice period**: a recurring line counts for one invoice frequency of the invoiced contract (quantity x unit price x frequency / unit months), in the pre-fill, the generation and the invoice line amount. Creation is not refused for a missing period.
- **I5. Applicable lines**: a line of any billing method is proposed or generated only when its dates overlap the invoice period (a missing period date is open-ended).
- **I6. Unit name clash in the conversion**: a unit of the expected name with another definition is not reused; the conversion uses "<name> (converted)" and reports it.
- **I7. Imports**: the invoice import applies the one-contract and currency rules (no line generation); the invoice line import accepts optional `contract_line` and `quantity` columns.
- **I8. `calculated_rc`**: it was never an API field; no API alias is added. It stays on the contract page with a "deprecated" badge when `show_deprecated_fields` is true.
- **I9. Internal fields of a locked contract line**: the lock of FR-029 covers the contract terms (contract, description, quantity, unit price, unit, currency, dates and custom fields). Accounting dimensions, comments and tags stay editable, since they are internal classification; the edit form shows the locked fields disabled. Invoice lines already created keep their dimensions. Adding and deleting lines stays locked.

## Testing approach (feeds tasks)

- Keep the generic NetBox view test cases for every new model (`Unit`, `ContractLine`) in `tests/test_views.py`, and update the existing `Contract`, `Invoice` and `InvoiceLine` cases for the new fields.
- New test modules: `test_calculations.py` (pure functions, every arithmetic example of the spec), `test_currency.py` (each refusal and each accepted case), `test_conversion.py` (each legacy data shape, idempotency, report), `test_prefill.py` (view behaviour including non-billable and usage-based cases), `test_api.py` (create/read/validate through the REST interface, deprecated fields still served), `test_generation.py` (generation, quantity and calculated amounts) and `test_locking.py` (no change of contract lines or of a used unit's billing method once invoiced).
- Regenerate `tests/query_counts.json` after the list-view changes.
- Traceability from every spec scenario and edge case to a test is kept in [quickstart.md](quickstart.md).
