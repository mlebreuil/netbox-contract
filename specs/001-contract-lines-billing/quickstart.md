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

5. On an invoice for a billable parent with a non-billable child and grandchild, and a billable child, press "Generate invoice lines": expect the lines of the child and grandchild, not of the billable child; each line references its contract line and carries its dimensions. Enter a quantity on the usage line and check the amount is recalculated. Change a quantity and check the reference is kept.
6. Try to add, edit or delete a contract line of a contract that has an invoice: expect a refusal saying a new contract must be created. Try to change the months of a unit used by such a contract: expect a refusal.
7. Create a new invoice for a contract that has an invoice template: expect no template lines copied, and the template invoice still present and marked deprecated.

## Traceability: scenario to test

| Spec scenarios / requirements | Test module (to be written) |
|---|---|
| US1 scenarios, FR-001..FR-004, FR-001a, FR-002a, FR-029 | `test_views.py` (Unit, ContractLine cases), `test_currency.py` (dates rules), `test_locking.py`, `test_api.py` |
| US2 scenarios, FR-013..FR-016, SC-002, SC-007, upgrade edge cases | `test_conversion.py` |
| US3 scenarios, FR-005..FR-008, SC-001 arithmetic | `test_calculations.py`, `test_views.py` (contract detail), `test_api.py` |
| US4 scenarios, FR-009..FR-012, SC-003 | `test_currency.py`, `test_reports.py` |
| US5 scenarios, FR-017..FR-020, FR-017a, SC-004 | `test_calculations.py` (amounts), `test_prefill.py` (view) |
| US6 scenarios, FR-021..FR-025, SC-006 | `test_generation.py`, `test_calculations.py` (invoice line amounts), `test_api.py` |
| FR-026..FR-028, SC-005 | CI workflow pinned to a NetBox 4.6 tag; the full suite |
| Spec edge cases (open-ended, zero/negative, rounding, cancelled invoices, hierarchy changes, repeated upgrade, deprecated fields via import/API, hidden/mandatory settings) | the module named for the behaviour, listed one by one in `tasks.md` |
