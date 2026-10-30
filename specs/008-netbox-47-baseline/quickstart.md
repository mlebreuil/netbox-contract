# Quickstart: validate the 4.7 baseline

## Prerequisites

A NetBox v4.7.4 checkout with its virtualenv, PostgreSQL 15 or later and Redis, the plugin installed in editable mode (`pip install -e .`), and the test configuration (a copy of `testing/configuration.py`), as described in `CLAUDE.md`.

## Run

```bash
cd ../netbox
NETBOX_CONFIGURATION=netbox.configuration_testing venv/bin/python netbox/manage.py test netbox_contract.tests --keepdb
```

Expected: `Ran 1021 tests` (1020 existing plus the metadata test), `OK (skipped=9)`.

## Check the pieces

1. Query counts: after re-recording, a second run passes without `UPDATE_QUERY_COUNTS`; adding any query to a list view makes its test fail again.
2. REST data: `grep -n "date(" netbox_contract/tests/test_api.py` shows no Python `date` or `Decimal` objects left in `create_data` or `update_data` of the three models.
3. Migrations: `venv/bin/python netbox/manage.py makemigrations netbox_contract --check --dry-run` reports no change (needs `DEVELOPER = True`).
4. Metadata: `grep -n "min_version\|version" netbox_contract/__init__.py pyproject.toml` shows 4.7.0 and 2.6.0.
5. NetBox 4.6 refusal (optional): start a NetBox 4.6 instance with the new version installed; it must stop at start with the plugin's minimum version message.
6. Lint: `ruff check`.
