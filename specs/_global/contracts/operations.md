# Commands, scripts, metadata and CI (current state)

Deltas: `specs/001-*/contracts/ui-and-settings.md`, `specs/006-*/contracts/graphql-schema.md`,
`specs/008-*/contracts/metadata-and-ci.md`.

## Management commands

| Command | Purpose |
|---|---|
| `convert_contract_lines` | Re-runs the conversion of legacy costs and invoice templates into contract lines; idempotent; prints a report (001-FR-013, 001-FR-014, 001-FR-016) |
| `cleanup_orphan_assignments [--apply]` | Lists contract assignments whose object no longer exists; deletes exactly those only with `--apply`; assignments of uninstalled object types are listed apart and kept (006-FR-013 to 006-FR-015) |

## NetBox custom scripts (`scripts/netbox-contract.py`)

Report currency mismatches (read-only, logic in `reports.py`, 001-FR-012); expired-contract status update; replace
accounting dimension; contract end check. `create_invoice_template` and `create_invoice_lines` were removed.

## Metadata

| Item | Value | Feature |
|---|---|---|
| Plugin version | 2.6.0 (`__init__.py`, `pyproject.toml`) | 008-FR-006 |
| `min_version` | 4.7.0, no `max_version` | 008-FR-005 |
| README compatibility | NetBox 4.5: 2.4; 4.6: 2.4, 2.5; 4.7: 2.6 | 008-FR-006 |
| Changelog | by kind of change; minimum-version warning first | 008-FR-007 |

## CI

`.github/workflows/lint-tests.yaml`: NetBox tag `v4.7.4`, Python 3.12, 3.13, 3.14, lint job (008-FR-001). The suite
must pass with no test skipped (008-FR-004). Query-count baselines (`tests/query_counts.json`) change only with a
stated reason (008-FR-003, Constitution II). `makemigrations --check` reports nothing pending (008-FR-010).
The identifier check (`python utils/spec_ids.py check`) runs in CI.
