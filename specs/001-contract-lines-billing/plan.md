# Implementation Plan: Contract lines, billing natures and currency consistency

**Branch**: `278-replace-invoice-templates-with-contract-lines` | **Date**: 2026-09-26 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-contract-lines-billing/spec.md`

## Summary

Add contract lines and units to the netbox-contract plugin, a billable flag with computed contract values, currency consistency rules, a re-runnable conversion of existing costs and invoice templates, and an invoice pre-fill computed from contract lines and generation of invoice lines from contract lines, all in a single release (plugin 2.5.0). The approach is: two new `NetBoxModel`s (`Unit`, `ContractLine`), one new field on `Contract`, two on `InvoiceLine` (contract line reference and quantity, amount calculated), a lock on contract lines once the contract has an invoice, a database-free `calculations.py` used by both releases, validation in model `clean()` plus one shared helper for the invoice-contract relation, and a data migration calling a re-runnable conversion function. No money library is added. Details: [research.md](research.md), [data-model.md](data-model.md), [contracts/](contracts/), [quickstart.md](quickstart.md).

## Technical Context

**Language/Version**: Python 3.12 or newer (project `requires-python >=3.12`; CI matrix 3.12, 3.13, 3.14, to be checked against NetBox 4.6's supported versions)

**Primary Dependencies**: NetBox 4.6 (minimum, `min_version = '4.6.0'`), which brings Django 6.0, Django REST framework and django-tables2; no new third-party dependency

**Storage**: PostgreSQL through the Django ORM; new tables via migrations 0044 (schema) and 0045 (data conversion)

**Testing**: NetBox test runner (`manage.py test netbox_contract.tests`) with NetBox's `ModelViewTestCase` and `APITestCase` helpers; ruff for lint; CI pinned to a NetBox 4.6 tag

**Target Platform**: NetBox plugin on Linux servers (self-hosted NetBox 4.6)

**Project Type**: NetBox plugin (Django app, web UI plus REST API)

**Performance Goals**: contract list and detail stay within the existing query-count baseline plus a documented, bounded increase (regenerate `tests/query_counts.json`); no per-row query on lists

**Constraints**: NetBox 4.7 compatibility is out of scope; new code avoids APIs known to be removed in 4.7 (the custom-script report is the accepted exception); no silent change to existing currencies or invoices; conversion must be idempotent

**Scale/Scope**: contract data of one organisation (hundreds to low thousands of contracts, a few lines each); about 2 new models, 14 files changed, 8 new test modules

## Constitution Check

Checked against `.specify/memory/constitution.md` version 1.0.0 (Principles I-VII), before Phase 0 and again after the design of Phase 1:

| Principle | Status | Evidence |
|---|---|---|
| I. NetBox-native plugin | Met | `Unit` and `ContractLine` are `NetBoxModel`s with the full stack (tasks T015-T022, including the change log route); `min_version` 4.6.0; the one known deprecation-bound API (custom scripts) is recorded as an accepted exception in research D10 with its migration path (logic kept in `reports.py`) |
| II. Tested behaviour | Met | tests first in every story; every scenario and edge case mapped in quickstart.md; CI pinned to a NetBox 4.6 tag (T002); query-count baseline regenerated with a stated reason (list views change) |
| III. Lint-clean | Met | every story ends with `ruff check` |
| IV. Data safety and migrations | Met | migration 0044 schema, 0045 idempotent lossless conversion with a report; `invoiced_at_conversion` flag; nothing altered silently; deprecated fields and templates kept and never deleted |
| V. Backward-compatible interfaces | Met with recorded behaviour changes | no REST field, endpoint, setting or import column removed or renamed; new validation rules and invoice-creation behaviour are listed as behaviour changes in the changelog task (T057) |
| VI. Simplicity and minimal dependencies | Met | no new dependency (money library rejected); logic in `calculations.py`, `validators.py`, `conversion.py`, `reports.py`, `services/invoicing.py` |
| VII. Documented change | Met | documentation, changelog and README tasks (T056-T058); single release 2.5.0 published only when all milestones are done |

Re-check after design: no violation, so no entry in Complexity Tracking.

## Decisions taken with the maintainer

1. **Single release** (2.5.0). Release 1 and release 2 are merged; the build order in the spec's story priorities is kept as internal milestones.
2. **Quantity at the invoice line**: unit and unit price come from the contract line, the amount is calculated (research D7). Usage-based lines are generated without quantity.
3. **Lock once invoiced**: a contract that has an invoice cannot get new, changed or deleted contract lines; a new contract must be created. Consequence: converted lines of contracts that already had invoices at upgrade are locked; a used unit's billing method and months are locked with them.
4. **Invoice templates are kept**, never deleted, deprecated; the template-line copy on save is removed in this release.
5. **Invoice lines are generated at invoice creation** (screen and REST create), never on an existing invoice and never through bulk import; there is no generation button or endpoint.
6. **Conversion**: template lines replace the `mrc`/`yrc` line; differences are reported, not added.

Points to watch during implementation: amounts of recurring invoice lines are recalculated on save, not when the invoice period changes; the existing rule that lines cannot exceed the invoice amount means the user raises the invoice amount once usage quantities are entered.

## Project Structure

### Documentation (this feature)

```text
specs/001-contract-lines-billing/
├── spec.md
├── plan.md              # this file
├── research.md          # Phase 0
├── data-model.md        # Phase 1
├── quickstart.md        # Phase 1
├── contracts/           # Phase 1: rest-api.md, ui-and-settings.md
├── checklists/requirements.md
└── tasks.md             # created later by /speckit-tasks
```

### Source Code (repository root)

```text
netbox_contract/
├── __init__.py                 # min_version 4.6.0, version, new setting
├── models.py                   # + Unit, ContractLine, Contract.billable, InvoiceLine.contract_line/quantity/calculated amount, clean() rules, lock signal
├── calculations.py             # NEW pure functions (months, proration, totals, yearly)
├── validators.py               # NEW shared invoice/contract currency and cardinality checks
├── conversion.py               # NEW idempotent conversion of legacy costs and templates
├── reports.py                  # NEW currency mismatch detection
├── services/invoicing.py       # NEW propose_invoice, generate_invoice_lines
├── management/commands/convert_contract_lines.py   # NEW
├── forms.py, views.py, tables.py, filtersets.py, urls.py, navigation.py, search.py   # new screens, pre-fill, hidden deprecated fields
├── api/serializers.py, api/views.py, api/urls.py   # new endpoints, new fields, validation
├── templates/netbox_contract/  # unit.html, contractline.html, contract.html, invoice.html changes
├── migrations/                 # 0044 schema, 0045 data conversion
└── tests/
    ├── test_views.py           # updated + Unit/ContractLine cases
    ├── test_calculations.py, test_currency.py, test_conversion.py,
    ├── test_contract_lines.py, test_values.py, test_prefill.py, test_api.py,
    ├── test_reports.py, test_generation.py, test_locking.py,
    ├── test_deprecated.py      # NEW (deprecated fields and invoice templates, US2)
    ├── helpers.py              # NEW shared test factories (not a test module)
    └── query_counts.json       # regenerated
scripts/netbox-contract.py      # + currency report script, - two stale scripts
.github/workflows/lint-tests.yaml   # pinned NetBox 4.6 tag
docs/, CHANGELOG.md, README.md, utils/   # documentation and sample imports
```

**Structure Decision**: single Django app (the existing `netbox_contract` package). New logic is put in small modules with no dependency on views (`calculations`, `validators`, `conversion`, `reports`, `services`) so it can be unit-tested and reused by the UI, the API, the migration and the script.

## Delivery order (one release, 2.5.0)

Milestones, each leaving lint and tests green: (1) schema, units and contract lines screens and API, with the lock; (2) billable flag and computed values; (3) currency rules and report script; (4) conversion migration and command; (5) pre-fill; (6) invoice line quantity, calculated amounts and generation, removal of the template-line copy; (7) documentation, CI pin to NetBox 4.6, changelog and version bump. The release is published only when all milestones are done.

## Complexity Tracking

No constitution violations to justify.
