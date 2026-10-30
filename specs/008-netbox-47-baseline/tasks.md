# Tasks: NetBox 4.7 as the minimum supported version

**Input**: `specs/008-netbox-47-baseline/` (plan.md, spec.md, research.md, contracts/metadata-and-ci.md, quickstart.md)

**Tests**: required (constitution II). This change is mostly test repair: the failing tests are the starting point.

**Branch**: `318-assess-against-netbox-4-7-4`. Implemented first; released together with 004 to 007 as 2.6.0.

**Test command** (`CLAUDE.md`): `cd ../netbox && NETBOX_CONFIGURATION=netbox.configuration_testing venv/bin/python netbox/manage.py test netbox_contract.tests --keepdb`

## Phase 1: Setup

- [X] T001 Check out NetBox `v4.7.4` next to the plugin, install the plugin in editable mode, and run the full suite once to confirm the starting point: 1020 tests, 18 failures (9 query counts, 9 REST), 9 skipped. Record the list of failing test names in the working notes.

## Phase 2: User Story 1 - Suite passes on NetBox 4.7.4 in CI (P1) 🎯 MVP

**Goal**: green suite on v4.7.4, CI pinned. **Independent test**: full run on v4.7.4 gives `OK (skipped=9)`.

- [X] T002 [US1] In `netbox_contract/tests/test_api.py`, give dates as ISO text (not the decimal amounts, which the 4.7 helper compares as `Decimal`) in the `create_data`, bulk create and `update_data` of contracts, contract lines and invoices (about lines 102-111, 345-346, 370-374), keeping the checks of the stored values. Run the three REST test classes: the 9 REST failures are gone.
- [X] T003 [US1] Re-record `netbox_contract/tests/query_counts.json` serially with `UPDATE_QUERY_COUNTS=1 ... manage.py test netbox_contract.tests.test_views --keepdb` (no `--parallel`). Review the diff: exactly the 9 failing list views changed, each by minus one; any other change is investigated, not accepted.
- [X] T004 [P] [US1] In `.github/workflows/lint-tests.yaml` (about line 77) change the NetBox checkout `ref` from `v4.6.10` to `v4.7.4`; leave the Python matrix (3.12, 3.13, 3.14) and the lint job unchanged.
- [X] T005 [US1] Run the full suite: `Ran 1023 tests` (1020 existing plus the 2 metadata tests and the migration-state test), `OK (skipped=9)`; run a second time without `UPDATE_QUERY_COUNTS` to prove the baseline is stable.

- [X] T016 [US1] (added during implementation, research D7) Write `MigrationStateTestCase` in `netbox_contract/tests/test_conventions.py` (autodetector, no pending changes for `netbox_contract`) and watch it fail on 4.7.4: `AlterField` of the two owner fields.
- [X] T017 [US1] Add `netbox_contract/migrations/0053_owner_related_name.py` (`related_name='+'` on `ContractType.owner` and `ServiceProvider.owner`, depends on `0052` and `users.0015_owner`); T016 passes and `makemigrations --check --dry-run` reports no change.

**Checkpoint**: suite green locally on v4.7.4.

## Phase 3: User Story 2 - Administrators know the required NetBox version (P2)

**Goal**: metadata, README and docs state 4.7.0. **Independent test**: the metadata test and a reading of the README and changelog.

- [X] T006 [US2] Write the failing test first in `netbox_contract/tests/test_conventions.py`: the plugin config has `min_version == '4.7.0'`, `max_version is None`, and `version == '2.6.0'`, and `pyproject.toml` carries the same version. Run it and watch it fail.
- [X] T007 [US2] In `netbox_contract/__init__.py` set `version = '2.6.0'` and `min_version = '4.7.0'`; in `pyproject.toml` set `version = "2.6.0"`. T006 passes.
- [X] T008 [P] [US2] README compatibility table: add the row NetBox 4.7 with plugin 2.6, keep the 4.6 row (plugin 2.4 and 2.5) and the earlier ones.
- [X] T009 [P] [US2] `CHANGELOG.md`: open a 2.6.0 section with the warning that NetBox 4.7.0 or later is required and that 4.6 installations stay on 2.5.x; list the CI pin under Other Changes (changelog rules of `CLAUDE.md`: by kind of change, not by issue).
- [X] T010 [P] [US2] Update the NetBox version statements in `CLAUDE.md` (about lines 9, 44, 171) and in `CONTRIBUTING.md` / `docs/contributing.md` where they name the supported or pinned version (4.7, `v4.7.4`).
- [X] T011 [US2] Update the constitution's compatibility section through `/speckit-constitution` (PATCH 1.0.1: minimum NetBox 4.7, pinned test release v4.7.4); check that its sync report lists no template left stale.

## Phase 4: Polish

- [X] T012 `ruff check netbox_contract/` clean (the repository's pre-commit hook runs the linter only); `makemigrations netbox_contract --check --dry-run` reports no change.
- [X] T013 Confirm FR-009: `git diff --stat` for this change touches only the workflow, `__init__.py`, `pyproject.toml`, `test_api.py`, `query_counts.json`, `test_conventions.py`, README, CHANGELOG, `CLAUDE.md`, contributing docs and the constitution; no model, template, serializer or view, and the only migration is `0053_owner_related_name`.
- [X] T014 Walk through `quickstart.md` items 1 to 6 (item 5, the real NetBox 4.6 refusal, was not run).
- [X] T015 Stage the files for the owner to commit (pre-commit hook must not be bypassed); suggested message states the reason for the re-recorded counts (NetBox 4.7 core change).

## Dependencies and order

T001 → T002, T003, T004 (T002 and T004 can run in parallel; T003 after T002 to avoid mixing failures) → T005. T006 → T007 → T008..T010 (parallel) → T011. Phase 4 last. Stories US1 and US2 are independent; US1 first because 004 to 007 need the green baseline.

## Implementation strategy

MVP = Phase 2 (green suite and CI pin). Phase 3 can follow in the same sitting. Nothing here is published alone.
