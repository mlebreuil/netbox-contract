# AGENTS.md

This file provides guidance to AI coding agents (Claude Code, Codex, Cursor, Copilot and others) working in this
repository. `CLAUDE.md` imports it, so Claude Code reads the same text.

## What this is

`netbox-contract` is a NetBox plugin (Django app `netbox_contract`) managing contracts, contract lines, units,
invoices, invoice lines, accounting dimensions, service providers and contract assignments to NetBox objects.
Minimum NetBox 4.7 (`min_version` in `netbox_contract/__init__.py`), Python 3.12+. Project rules are in
`.specify/memory/constitution.md` (Principles I-IX); it overrides other practice documents when they conflict.

## Environment and commands

The plugin is developed next to a NetBox checkout and installed in NetBox's virtualenv in editable mode
(`pip install -e .`). Management commands and tests run from the NetBox checkout. Use the test configuration, not
the development one (the debug toolbar refuses to run under tests).

```bash
# Lint (also run by the pre-commit hook on netbox_contract/; never bypass the hook)
ruff check
python3 utils/spec_ids.py check

# Tests: run from the NetBox checkout with its test configuration
cd ../netbox
NETBOX_CONFIGURATION=netbox.configuration_testing venv/bin/python netbox/manage.py test netbox_contract.tests --keepdb
# One module / class / test
NETBOX_CONFIGURATION=netbox.configuration_testing venv/bin/python netbox/manage.py test \
    netbox_contract.tests.test_generation.GenerationRulesTestCase.test_credit_line --keepdb

# Migrations (makemigrations requires DEVELOPER = True)
venv/bin/python netbox/manage.py makemigrations netbox_contract --check --dry-run
venv/bin/python netbox/manage.py migrate netbox_contract

# Re-run the legacy data conversion (idempotent, prints a report)
venv/bin/python netbox/manage.py convert_contract_lines
```

List-view query counts are recorded in `netbox_contract/tests/query_counts.json`. Re-record them serially, never with
`--parallel`, and only with a stated reason (Constitution II); see the `run-tests` skill for the command.

CI (`.github/workflows/lint-tests.yaml`) runs the suite on pinned NetBox `v4.7.4` for Python 3.12-3.14.

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
  (tests read them with `tests.helpers.contract_page_with_lines` or the panel's `hx-get` URL). The contract,
  contract line, invoice and invoice line pages declare their breadcrumbs in the layout (`Breadcrumb` from
  `netbox.ui.breadcrumbs`, NetBox 4.7+), so no page template is needed.
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
its brief form; the fields to be removed are listed in `docs/api.md` and the changelog (#309, research 003-D7). Brief sets
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
- Translations: run `makemessages -l en -l fr` from `netbox_contract/` with NetBox's `manage.py` and test
  configuration, then `msgfmt` on the plugin's `.po` files (`compilemessages` also rebuilds NetBox's own catalogs).
  For a msgid NetBox core also translates, NetBox's catalog wins.

## Workflow

- Branches: `develop` for development, `master` for releases; one branch per GitHub issue, created from `develop`.
- Features follow Spec Kit (`/speckit-*` skills in `.claude/skills/`, artifacts in `specs/<feature>/`: spec, plan,
  research decisions, data model, contracts, tasks). Keep the spec, `research.md` decisions and `tasks.md` in step
  with behaviour changes.
- **Identifiers are always qualified with the feature number**: `001-FR-029`, `003-US2`, `002-SC-005`, `004-T017`,
  `003-D6` (research decision), `001-I14` (implementation decision), `002-Q1` (clarification). Never write a kind and
  number without the feature number — in specs, code, tests, docs, commits or the changelog; numbers are never reused
  or renumbered. In code, cite the requirement next to the rule it explains, e.g. `# a posted invoice is locked
  (001-FR-031)`. `python3 utils/spec_ids.py check` enforces it (CI and pre-commit); `show <id>` prints a definition and
  its citations, `next <NNN> <KIND>` gives the next free number. Details: `specs/_global/CONVENTIONS.md`.
- **`specs/_global/` is the current state of the product** (data model, REST, GraphQL, UI, routes, operations, business
  rules by domain, generated `registry.md`). Read it first to learn what exists; every feature updates it in the same
  pull request, its own `data-model.md` and `contracts/` being deltas (Constitution VIII).
- Every user-visible change updates `docs/` (mkdocs), `CHANGELOG.md` (see "Changelog" below) and, for settings or
  requirements, `README.md` (Constitution VII).
- Screenshots in `docs/img/` are generated, never taken by hand: `utils/docs_screenshots/make_screenshots.sh
  [name ...]` recreates a separate `netbox_docs` database, seeds it (`seed.py`), runs NetBox on port 8001 and captures
  the regions listed in `SHOTS` of `capture.py` (see its README). When a change alters a page shown in the docs, rerun
  it and look at the images before committing; a new screenshot is a `SHOTS` entry plus, if needed, seed data.
  Don't name a file in that directory like a standard module (it is put on `PYTHONPATH`).
- REST fields, endpoints, settings and import columns are public interfaces: deprecate before removing, never add a
  required input to an existing endpoint (Constitution V). Data migrations must be lossless and re-runnable
  (Constitution IV).

## AI policy

All contributions follow the project's [AI policy](AI_POLICY.md) (Constitution IX). In short:

- AI tools may be used to explore the codebase and to generate code, tests, documentation, specifications and
  changelog drafts.
- The contributor must understand, and be able to explain, every change submitted.
- Issues, pull request descriptions and comments are written in the contributor's own voice. Anything you draft for
  them is a starting point for the contributor to review and rewrite: keep it brief and plain, and say that it is a
  draft when you hand it over.
- Do not open an issue, a pull request or a comment unless the maintainer asks you to.

## Pull requests

- One branch per GitHub issue, created from `develop` after a `git fetch`, named `<issue-number>-short-description`
  (e.g. `318-assess-against-netbox-4-7-4`). `master` receives releases only.
- Every pull request closes an issue: its description has a `Closes: #<number>` line, and it is based on `develop`
  (release pull requests excepted).
- Before drafting a pull request, check that the issue is open and, for an outside contributor, assigned to them:

  ```bash
  gh issue view <number> --json state,assignees
  ```

  If the issue is closed or assigned to someone else, report it instead of opening the pull request.
- A pull request includes tests that failed before the change, and the documentation, `CHANGELOG.md` and
  `specs/_global/` updates the constitution requires. The merge gates are in the constitution's Development
  Workflow; `.github/PULL_REQUEST_TEMPLATE.md` carries the checklist.

## Gotchas

- Schema migrations are generated by `makemigrations` (it needs `DEVELOPER = True`), never written by hand. Data
  migrations are written by hand under Constitution IV.
- Do not run `ruff format` on existing files: it introduces unrelated style changes. Use the pre-commit Ruff hook.
- A foreign-key filter declares an explicit `<field>_id = ModelMultipleChoiceFilter(...)`; do not rely on
  `Meta.fields`.
- Only documented NetBox plugin APIs are stable; NetBox internals can change between releases, which is why CI pins a
  NetBox tag.

## Skills

Project skills and their selection guide live in `.claude/skills/README.md`. The `speckit-*` skills run the Spec
Kit sequence; other skills provide NetBox API reference or recurring-change checklists. Specify and plan a feature
before using an implementation checklist; consult the NetBox reference for API details rather than duplicating it.

## Changelog

`CHANGELOG.md` is grouped by kind of change, not by issue; never add per-issue sublists. Preserve the format and
heading levels of the latest release, use only sections with content, and follow the category order in the
`draft-changelog` skill. `docs/changelog.md` includes this file, so edit `CHANGELOG.md` only. Specs and tasks identify
the release section for each entry.
