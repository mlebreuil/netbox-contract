# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

`netbox-contract` is a NetBox plugin (Django app `netbox_contract`) managing contracts, contract lines, units,
invoices, invoice lines, accounting dimensions, service providers and contract assignments to NetBox objects.
Minimum NetBox 4.6 (`min_version` in `netbox_contract/__init__.py`), Python 3.12+. Project rules are in
`.specify/memory/constitution.md` (Principles I-VII); it overrides other practice documents when they conflict.

## Environment and commands

The plugin is developed next to a NetBox checkout and installed in NetBox's virtualenv in editable mode
(`pip install -e .`). In the dev container the layout is `/workspaces/netbox/netbox` (NetBox, venv in `venv/`) and
`/workspaces/netbox/netbox-contract` (this repo). Management commands run from the NetBox checkout.

```bash
# Lint (also run by the pre-commit hook on netbox_contract/; never bypass the hook)
ruff check

# Tests: run from the NetBox checkout. The dev configuration has DEBUG on, which the debug toolbar
# refuses under tests, so use the test configuration (a copy of testing/configuration.py for the container).
cd ../netbox
NETBOX_CONFIGURATION=netbox.configuration_testing venv/bin/python netbox/manage.py test netbox_contract.tests --keepdb
# One module / class / test
NETBOX_CONFIGURATION=netbox.configuration_testing venv/bin/python netbox/manage.py test \
    netbox_contract.tests.test_generation.GenerationRulesTestCase.test_credit_line --keepdb

# Query-count baselines (netbox_contract/tests/query_counts.json): list view tests fail when a list view's
# query count changes. Re-record serially (no --parallel) and only with a stated reason (Constitution II).
UPDATE_QUERY_COUNTS=1 NETBOX_CONFIGURATION=netbox.configuration_testing venv/bin/python netbox/manage.py test \
    netbox_contract.tests.test_views netbox_contract.tests.test_api --keepdb

# Migrations: makemigrations is refused unless the NetBox configuration sets DEVELOPER = True.
venv/bin/python netbox/manage.py makemigrations netbox_contract --check --dry-run
venv/bin/python netbox/manage.py migrate netbox_contract

# Re-run the legacy data conversion (idempotent, prints a report)
venv/bin/python netbox/manage.py convert_contract_lines
```

CI (`.github/workflows/lint-tests.yaml`) links `testing/configuration.py` as NetBox's configuration and runs the
suite on a pinned NetBox tag (currently `v4.6.10`) for Python 3.12-3.14.

## Architecture

**Standard NetBox plugin stack per model**: `models.py`, `forms.py` (edit, filter, CSV import, bulk edit),
`filtersets.py`, `tables.py`, `views.py`, `urls.py`, `api/` (serializers, viewsets, router), `search.py`,
`navigation.py`, templates under `templates/netbox_contract/`. Every model is a `NetBoxModel` with the full stack.
Views are mostly wired explicitly in `urls.py`; detail views use `register_model_view` + `get_model_urls` so tabs
and extra actions (e.g. `contractline_amend`) attach to them.

**Where business rules live** (so that the UI, bulk edit, CSV import and REST API enforce them alike):
- Single-record rules are in model `clean()` — NetBox forms, bulk edit, import forms and `ValidatedModelSerializer`
  all call `full_clean()`. For API creates, `clean()` runs on a temporary instance, so defaults applied in
  `clean()` must also be applied in `save()` (see `ContractLine.apply_contract_defaults`,
  `InvoiceLine.apply_line_defaults`).
- The invoice ↔ contract many-to-many rules (one contract for a new invoice, same currency, no added contract,
  locked when Posted) cannot rely on `clean()` alone because the relation is saved after the object:
  `validators.check_invoice_contracts` is called from `InvoiceForm.clean()`, `InvoiceCSVForm.clean()`,
  `InvoiceSerializer.validate()`, and from `Invoice.clean()` through `self._m2m_values`, which NetBox bulk edit and
  the REST API set before `full_clean()`.
- Delete guards (locked contract lines, lines of Posted invoices, contracts whose lines are on Posted invoices) are
  in the models' `delete()` overrides, raising `AbortRequest`; `signals.py` repeats them for queryset deletions.
  They are not in `pre_delete` alone because Django sends it inside `atomic(savepoint=False)`, which breaks the
  caller's transaction (and the tests). Deletions cascading from a parent object are recognised through the
  signal's `origin`.

**Amounts and invoicing**:
- `calculations.py` is database-free (months between dates, proration, totals, rounding once at the end with
  `ROUND_HALF_UP`) and shared by models, services and tests.
- `services/invoicing.py`: `propose_invoice` (pre-fill of the invoice add form), `lines_to_generate` /
  `check_new_invoice` / `generate_invoice_lines` (lines created when a new invoice is saved, from
  `InvoiceForm.save()` and `InvoiceSerializer.create()` only — never on edit or bulk import). A billable contract
  invoices its own lines plus those of non-billable descendants, stopping at billable children
  (`Contract.billing_scope()`). Quantities/unit prices/dimensions typed in the new-invoice preview arrive as
  `line-<id>-*` and `extra-<n>-*` form fields (`parse_line_overrides`, `parse_extra_lines`).
- The new-invoice preview (`invoice_edit.html` + `inc/invoice_lines_preview.html`) is refreshed by an HTMX POST of
  the whole form to `InvoiceLinesPreviewView`; nothing is saved there.
- Every invoice line amount is quantity × unit price (recurring units prorated to the invoice period) and is never
  typed; an amount given alone at creation becomes the unit price (API/import compatibility). Lines of a Posted
  invoice are never recalculated.
- `services/amendments.py`: changing the price/quantity of an invoiced contract line ends it and creates a successor
  (`ContractLine.replaces`); yearly values skip replaced lines.
- Contract values (total, yearly, yearly billable) come from `models.contract_values(contracts)`, which computes a
  whole list in a fixed number of queries; list views/API pass the result in context instead of calling the
  properties per row. The contract list's yearly value is a SQL annotation (`yearly_value_annotation`).

**Locks**: a contract with any invoice freezes the contract terms of its lines (dimensions, comments and tags stay
editable); a Posted invoice (not a template) freezes its amount, currency, period, contracts and the amount fields
of its lines; new invoices are Draft by default.

**Legacy/deprecated data**: `Contract.mrc/yrc/nrc` and invoice templates (`Invoice.template`) are kept but
deprecated and hidden unless the `show_deprecated_fields` plugin setting is true. `conversion.py`
(`convert_legacy_data`) turns them into contract lines; it is used by data migration 0045 with historical models
and by the `convert_contract_lines` command, and must stay idempotent. `reports.py` holds the logic of the
read-only "Report currency mismatches" custom script in `scripts/netbox-contract.py` (custom scripts are deprecated
in NetBox core, so script logic lives in importable modules).

**Plugin settings** are read at call time from `settings.PLUGINS_CONFIG['netbox_contract']` (module-level
`plugin_settings` is that same dict), so tests change them with
`mock.patch.dict(settings.PLUGINS_CONFIG['netbox_contract'], {...})`. Currency choices come from NetBox
`FIELD_CHOICES` (lower-case codes such as `usd`).

## Tests

- `tests/test_views.py` uses NetBox's `ViewTestCases.PrimaryObjectViewTestCase` per model; API tests compose
  `APIViewTestCases` Get/List/Create/Update/Delete mixins (the plugin has no GraphQL, so do not use
  `APIViewTestCase`). `tests/custom.py` overrides the URL helpers for the plugin namespaces.
- `tests/helpers.py` has factories (`make_contract`, `make_line`, `make_invoice`, units `monthly()`, `yearly()`,
  `one_time()`, `usage()`). `make_invoice` defaults to a Posted invoice, which is locked — pass
  `status=InvoiceStatusChoices.STATUS_DRAFT` when a test adds or edits its lines.
- Tests are written first and must fail before the change (Constitution II).

## Workflow

- Branches: `develop` for development, `master` for releases; one branch per GitHub issue, created from `develop`.
- Features follow Spec Kit (`/speckit-*` skills in `.claude/skills/`, artifacts in `specs/<feature>/`: spec, plan,
  research decisions, data model, contracts, tasks). Keep the spec, `research.md` decisions and `tasks.md` in step
  with behaviour changes.
- Every user-visible change updates `docs/` (mkdocs), `CHANGELOG.md` (with a "Behaviour changes" list for changes
  that affect existing users or API clients) and, for settings or requirements, `README.md` (Constitution VII).
- REST fields, endpoints, settings and import columns are public interfaces: deprecate before removing, never add a
  required input to an existing endpoint (Constitution V). Data migrations must be lossless and re-runnable
  (Constitution IV).
