---
name: run-tests
description: Run the netbox-contract checks locally - ruff, the Django test suite (whole, one module or one test), the migration check, the query-count baseline and the identifier check. Use when the user asks to run tests or to verify a change before a pull request.
---

# Run the checks

The plugin is tested inside a NetBox checkout. The suite uses NetBox's `django.test.TestCase` classes, not pytest.
CI (`.github/workflows/lint-tests.yaml`) runs the suite on pinned NetBox `v4.7.4` for Python 3.12 to 3.14, and
`.github/workflows/spec-ids.yaml` runs the identifier check.

## Prerequisites

1. A NetBox checkout of the pinned release (the tag named in `lint-tests.yaml`), its virtualenv active, the plugin
   installed with `pip install -e .`, and PostgreSQL and Redis running.
2. Set `NETBOX_CONFIGURATION=netbox.configuration_testing`; do not use the development configuration because the
   debug toolbar refuses to run under tests.
3. If something is missing, tell the user; do not skip a check silently.

## The checks, in the order to run them

From the plugin repository:

```bash
ruff check                                   # also run by the pre-commit hook; never bypass the hook
python3 utils/spec_ids.py check
```

From the NetBox checkout:

```bash
cd ../netbox
export NETBOX_CONFIGURATION=netbox.configuration_testing
venv/bin/python netbox/manage.py test netbox_contract.tests --keepdb
venv/bin/python netbox/manage.py test netbox_contract.tests.test_generation --keepdb
venv/bin/python netbox/manage.py test \
    netbox_contract.tests.test_generation.GenerationRulesTestCase.test_credit_line --keepdb
venv/bin/python netbox/manage.py makemigrations netbox_contract --check --dry-run
```

`makemigrations` is refused unless the NetBox configuration sets `DEVELOPER = True`.

## Query-count baseline

`netbox_contract/tests/query_counts.json` records the query count of each list view. A list view test fails when the
count changes. Re-record **serially** (no `--parallel`) and only with a stated reason (Constitution II):

```bash
UPDATE_QUERY_COUNTS=1 venv/bin/python netbox/manage.py test \
    netbox_contract.tests.test_views netbox_contract.tests.test_api --keepdb
```

Review the diff of the JSON: an increase you cannot explain is a bug (a per-row query), not a baseline to update.

## Failures

- With `--parallel`, a failing test can show only as `TypeError: cannot pickle 'traceback' object`. Rerun serially to
  see the real failure.
- Migration tests run in a plain `TestCase` with `MigrationExecutor`; a `TransactionTestCase` cannot flush NetBox's
  database.
- `tests/helpers.py` factories (`make_contract`, `make_line`, `make_invoice`) create a **Posted** invoice by default,
  which is locked; pass `status=InvoiceStatusChoices.STATUS_DRAFT` when a test edits it.
- After changing a model, check for a pending migration before blaming the test.
- NetBox 4.7 needs PostgreSQL 15 or newer: its system check fails under `manage.py test` on 14.
- Global search is indexed after the transaction commits, and Django's `TestCase` never runs on-commit callbacks. A
  test that saves an object and then searches for it wraps the save in
  `with self.captureOnCommitCallbacks(execute=True):`.
- NetBox 4.7 renamed the filterset test mixins to `BaseFilterSetTestMixin` and `ChangeLoggedFilterSetTestMixin`
  (`utilities.testing`); use the new names.
- A test that needs core objects (device, site) builds them in `setUpTestData`; share them across the class rather than
  recreating them in `setUp`.

## Before a pull request

pre-commit, `spec_ids.py check` (and `spec_ids.py registry` if specs changed, then commit `registry.md`), the whole
suite, `makemigrations --check`, and no unexplained change in `query_counts.json`.

## Why

- Run through `manage.py test`: the base classes come from NetBox's own test utilities.
- The test configuration: it sets the databases and plugins the CI uses.
- Serial re-record: parallel runs interleave and can record wrong counts.

## References

`AGENTS.md` ("Environment and commands", "Tests"), `.github/workflows/lint-tests.yaml`, constitution II, III; the
`netbox-plugin-development` skill, `references/testing-guide.md` (model, API, view and filterset tests, search index
assertions).
