# Quickstart: validate the NetBox 4.6 conventions alignment

Validation guide for [spec.md](spec.md). Commands run from the NetBox checkout (`/workspaces/netbox/netbox`) with
the test configuration, as in `CLAUDE.md`.

## Automated checks

```bash
cd /workspaces/netbox/netbox-contract && ruff check
cd /workspaces/netbox/netbox
venv/bin/python netbox/manage.py makemigrations netbox_contract --check --dry-run      # nothing pending
NETBOX_CONFIGURATION=netbox.configuration_testing venv/bin/python netbox/manage.py test \
    netbox_contract.tests.test_conventions --keepdb                                       # this feature
NETBOX_CONFIGURATION=netbox.configuration_testing venv/bin/python netbox/manage.py test \
    netbox_contract.tests --keepdb                                                        # whole suite
```

Expected: lint clean, no migration, all tests pass, `tests/query_counts.json` unchanged (or re-recorded with a
stated reason).

## Scenario map

| Spec scenario | Covered by (`tests/test_conventions.py`) | Manual check |
|---|---|---|
| US1-1, US1-2, SC-001 | Journal and Changelog tabs on each model's detail page; journal entry added | Open an invoice line, a contract type, an accounting dimension and an assignment: Journal tab present, add an entry |
| US1-3, SC-003, FR-003 | every route of [contracts/routes.md](contracts/routes.md) resolves to the same address and view | Bookmarked list, edit and changelog pages still open |
| US1-4 | Amend action and Contracts tab still registered | Contract line page shows Amend; a device page shows the Contracts tab |
| US2-1, SC-002 | nine filtersets registered; modifier widget on a text field of each filter form | Contracts list → Filters: modifier selector next to External reference |
| US2-2 | `external_reference__ic=FIBER` returns only the matching contract | Filter "contains FIBER" |
| US2-3, FR-005 | existing filter query strings (the ones of `test_views`/`test_api`) give the same results | – |
| US3-1, US3-5, SC-004 | each visible field in exactly one section; forms save identical objects | Contract add form shows sections |
| US3-2 | `hidden_contract_fields` patched: field hidden once, no empty section | – |
| US3-3 | `show_deprecated_fields` off/on: Deprecated section absent/present | – |
| US3-4 | contract type description widgets are text inputs | Contract types → Filters |
| US4-1, US4-3, US4-6 | GET pre-fill values of invoice and invoice line; no pre-fill on edit | Add invoice from a contract: date, period, currency, amount and preview filled |
| US4-2 | restricted contract/invoice ignored | – |
| FR-010, edge: address wins | `?contracts=<id>&date=2026-01-15` keeps that date; other fields from the contract | – |
| US4-4, SC-006 | `_quickadd` returns the quick-add template | Open `/plugins/contracts/invoiceline/add/?_quickadd=true`: the short quick-add form is returned, not the full page |
| US4-5 | HTMX partial returns `htmx/form.html` | – |
| US5-1, US5-2 | contract page with setting off (no section, no lookup) and on (section) | – |
| Edge: moved template | assignable object page renders the inline contract assignments | Device page with an assignment, `contract_assignments_display` = `both` |
| Edge: invalid pre-fill id, invoicing error | GET with `contracts=abc` / unknown id; error message kept | – |
