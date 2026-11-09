# Quickstart and validation guide

Spec: [spec.md](spec.md) | Plan: [plan.md](plan.md)

## Prerequisites

- A NetBox 4.6 development checkout with its virtualenv, PostgreSQL and Redis running, and this repository installed in editable mode (as done for the current development container: `pip install -e .`).
- `testing/configuration.py` linked as NetBox's configuration file for test runs (same as the CI job).

## Run the checks

```text
ruff check                                  # lint (pre-commit hook and CI use it)
python netbox/manage.py makemigrations netbox_contract --check --dry-run   # no missing migration
python netbox/manage.py test netbox_contract.tests --keepdb
```

Expected: no lint error, no pending migration, every test passes on NetBox 4.6.

## Manual walkthrough

1. Upgrade a copy of a database that contains: a contract with `mrc`, one with `yrc`, one with `nrc`, one with an invoice template that has dimensions, and one with none of these. Run `python manage.py migrate`. Expect the contract lines described in spec user story 2, unchanged invoices, all contracts billable, and a printed conversion report. Run `python manage.py convert_contract_lines` again: expect no new lines.
2. Create a unit "Quarterly" (recurring, 3 months). Create a contract with three lines (one-time 500, monthly 100 x 12 months, usage 10 x 20). Expect total 1,900 and yearly 1,200 (user story 3).
3. Try each mismatch of user story 4 (line, invoice, invoice line, non-billable child, currency change with an invoice). Expect a refusal naming both currencies. Run the report script; expect pre-existing mismatches listed and nothing changed.
4. Add an invoice for a billable contract: expect the amount and period proposed from the lines, usage-based lines ignored; edit them freely. Try a non-billable contract: expect an error and no amount.

5. Create an invoice for a billable parent with a non-billable child and grandchild, and a billable child: expect the lines of the child and grandchild to be generated at once, not those of the billable child; each line references its contract line and carries its dimensions. Enter a quantity on the usage line and check the amount is recalculated. Change a quantity and check the reference is kept. Try to create an invoice for a non-billable contract: expect a refusal.
6. Try to add, edit or delete a contract line of a contract that has an invoice: expect a refusal saying a new contract must be created. Try to change the months of a unit used by such a contract: expect a refusal.
7. Create a new invoice for a contract that has an invoice template: expect no template lines copied, and the template invoice still present and marked deprecated.

## Traceability: scenario to test

| Spec scenarios / requirements | Test module |
|---|---|
| 001-US1 scenarios, 001-FR-001..FR-004, 001-FR-001a, 001-FR-002a, 001-FR-029 | `test_views.py` (Unit, ContractLine cases), `test_contract_lines.py` (dates rules), `test_locking.py`, `test_api.py` |
| 001-US2 scenarios, 001-FR-013..FR-016, 001-SC-002, 001-SC-007, upgrade edge cases | `test_conversion.py`, `test_deprecated.py` |
| 001-US3 scenarios, 001-FR-005..FR-008a | `test_calculations.py`, `test_values.py`, `test_views.py` (contract detail), `test_api.py` |
| 001-US4 scenarios, 001-FR-009..FR-012, 001-SC-003 | `test_currency.py`, `test_reports.py` |
| 001-US5 scenarios, 001-FR-017..FR-020, 001-FR-017a, 001-SC-004 | `test_calculations.py` (amounts), `test_prefill.py` (view) |
| 001-US6 scenarios, 001-FR-021..FR-025, 001-SC-006 | `test_generation.py`, `test_calculations.py` (invoice line amounts), `test_api.py` |
| 001-FR-030 (amendment of a price or quantity) | `test_amendments.py` |
| 001-FR-031 (Draft default, Posted lock) | `test_posted.py`, `test_convergence.py` (bulk edit) |
| 001-FR-032 (preview of the lines of a new invoice) | `test_invoice_preview.py` |
| 001-FR-011, 001-FR-009 through bulk edit; contract values of API lists | `test_convergence.py` |
| 001-FR-026..FR-028, 001-SC-005 | CI workflow pinned to a NetBox 4.6 tag; the full suite |
| Spec edge cases (open-ended, zero/negative, rounding, cancelled invoices, hierarchy changes, repeated upgrade, deprecated fields via import/API, hidden/mandatory settings) | the module named for the behaviour, listed one by one in `tasks.md` |
