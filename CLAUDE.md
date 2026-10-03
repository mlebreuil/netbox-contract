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
`filtersets.py`, `tables.py`, `views.py`, `urls.py`, `api/` (serializers, viewsets, router), `graphql/` (filters,
types, schema; registered by `PluginConfig.graphql_schema`), `search.py`, `navigation.py`, templates under
`templates/netbox_contract/` (never at the root of `templates/`). Every model is a `NetBoxModel` with the full
stack; `ContractType` is an `OrganizationalModel` (its slug is derived from the name when empty, `text.unique_slug`)
and `ServiceProvider` a `PrimaryModel`, with the matching core form, filterset, table, serializer and GraphQL bases.
Every view is registered with `register_model_view` (list, add, import, bulk edit/delete with `detail=False`);
`urls.py` only includes `get_model_urls` per model plus the non-model `invoice_lines_preview`, so NetBox adds
changelog and journal and other code can attach tabs and actions (e.g. `contractline_amend`). Route names are pinned
by `tests/test_conventions.py`. Filtersets are registered with `@register_filterset` (lookup modifiers on filter
forms). Model, bulk-edit and filter forms declare `fieldsets`: a field left out of every section is not rendered,
and `prune_fieldsets` removes fields deleted (deprecated) or hidden by the settings.
- New-object pre-fill (invoice, invoice line) uses `form_with_defaults` in `views.py` and then core
  `ObjectEditView.get()`, so quick add and HTMX partials work; values in the page address win over the pre-fill.
- Detail pages are declared with `layout = SimpleLayout(...)` on the `ObjectView`s; the plugin's panels are in
  `panels.py` (`SettingsAttributesPanel` applies `hidden_contract_fields` / `hidden_invoice_fields` at render time,
  deprecated panels follow `show_deprecated_fields`, messages are `TemplatePanel` fragments under
  `templates/netbox_contract/panels/`). Related tables are `ObjectsTablePanel`s that load the list views over HTMX
  (tests read them with `tests.helpers.contract_page_with_lines` or the panel's `hx-get` URL). Only the contract,
  contract line, invoice and invoice line pages keep a template, for their breadcrumbs.
- Amending a contract line needs the `amend` permission action (`ContractLine.Meta.permissions`,
  `netbox_contract.amend_contractline`), checked per line: `object_actions.AmendContractLine` (page),
  `tables.ContractLineActionsColumn` (tables; also hides Delete on locked lines), `can_amend` template filter (edit
  page), `ContractLineAmendView` and the REST `amend` action, which overrides NetBox's POST → "add" mapping
  (`get_permissions()`). The contract line list reads lock and successor state from
  `ContractLine.objects.with_lock_state()` instead of querying per row.

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
  properties per row. The contract list's yearly value is a SQL annotation (`yearly_value_annotation`). They are
  not in GraphQL (stored fields only).

**REST representations**: related objects use `Serializer(nested=True)` and each serializer declares
`Meta.brief_fields`. A serializer's `validate()` must return at once when `self.nested` (it then receives the related
object, not data). `NestedContractSerializer` is kept, deprecated, until a later release shrinks the nested contract to
its brief form; the fields to be removed are listed in `docs/api.md` and the changelog (#309, research D7). Brief sets
may gain fields but never lose one without that deprecation path.

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

- `tests/test_views.py` uses NetBox's `ViewTestCases.PrimaryObjectViewTestCase` per model; `tests/test_api.py` uses
  `APIViewTestCases.APIViewTestCase` (REST and GraphQL) per model. `tests/custom.py` overrides the URL helpers for the
  plugin namespaces.
- Migration tests run in a plain `TestCase` with `MigrationExecutor` (PostgreSQL rolls the schema back with the test
  transaction); a `TransactionTestCase` cannot flush NetBox's database. Create rows with the historical model through
  `bulk_create()` (no `post_save`, which NetBox's search cache handles with the current fields).
- `tests/helpers.py` has factories (`make_contract`, `make_line`, `make_invoice`, units `monthly()`, `yearly()`,
  `one_time()`, `usage()`). `make_invoice` defaults to a Posted invoice, which is locked — pass
  `status=InvoiceStatusChoices.STATUS_DRAFT` when a test adds or edits its lines.
- Tests are written first and must fail before the change (Constitution II).
- With `--parallel`, a failing test can surface only as `TypeError: cannot pickle 'traceback' object`; rerun
  serially to see the real failure.
- Translations: `makemessages -l en -l fr` from `netbox_contract/` (NetBox's `manage.py`, test configuration), then
  `msgfmt` on the plugin's `.po` files (`compilemessages` also rebuilds NetBox's own catalogs). For a msgid NetBox
  core also translates, NetBox's catalog wins.

## Workflow

- Branches: `develop` for development, `master` for releases; one branch per GitHub issue, created from `develop`.
- Features follow Spec Kit (`/speckit-*` skills in `.claude/skills/`, artifacts in `specs/<feature>/`: spec, plan,
  research decisions, data model, contracts, tasks). Keep the spec, `research.md` decisions and `tasks.md` in step
  with behaviour changes.
- Every user-visible change updates `docs/` (mkdocs), `CHANGELOG.md` (see "Changelog" below) and, for settings or
  requirements, `README.md` (Constitution VII).
- REST fields, endpoints, settings and import columns are public interfaces: deprecate before removing, never add a
  required input to an existing endpoint (Constitution V). Data migrations must be lossless and re-runnable
  (Constitution IV).

## Changelog

`CHANGELOG.md` follows the NetBox release notes (e.g. `../netbox/docs/release-notes/version-4.6.md`, or
https://netboxlabs.com/docs/netbox/release-notes/version-4.7). `docs/changelog.md` only includes it, so edit
`CHANGELOG.md` alone. A release is organised **by kind of change, not by issue**: never add a per-issue entry with
nested sub-lists, and never add a second "Behaviour changes" or "Deprecations" list inside an issue. When several
issues ship in one release, each one adds its items to the release's shared sections. (Before this rule, 2.5.0 had
a nested "Behaviour changes" list under #309 in addition to the release-wide one, which confused readers.)

Under `### Version X.Y.Z` (keep the existing heading levels; older releases keep their old flat format), use only
the sections that have content, in this order:

1. `> [!WARNING]` callout for the NetBox minimum version or a mandatory upgrade step.
2. `#### Breaking Changes`: anything that changes behaviour for existing users, administrators or API clients
   (new validation, locks, changed defaults, removed scripts/templates, permission changes, data rewritten by a
   migration, OpenAPI component renames). One sentence-style bullet per change ending with `([#N](link))`, saying
   what to do about it.
3. `#### New Features`: one `##### Title ([#N](link))` per major feature, with a short prose description
   (including the upgrade/migration of its data).
4. `#### Enhancements`, `#### Bug Fixes`, `#### Plugins` (APIs and templates for other plugins),
   `#### Deprecations` (what is deprecated and what replaces it; REST fields to be removed are listed here),
   `#### Other Changes` (CI, dependencies): bullets `* [#N](link) - Short description`, sorted by issue number,
   no trailing period.
5. `#### REST API Changes`: new endpoints (full `/api/plugins/contracts/...` paths), then one bullet per model
   (`netbox_contract.Contract`) with nested bullets for added fields, filters, brief representation changes and
   deprecations.

Specs and `tasks.md` should say which section an item goes in (e.g. "add to 2.5.0 Breaking Changes"), not ask for
a per-issue entry. The specs of 001-003 predate this rule and still mention per-issue "Behaviour changes" lists.
