# Implementation Plan: NetBox 4.7 as the minimum supported version

**Branch**: `318-assess-against-netbox-4-7-4` | **Date**: 2026-10-29 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/008-netbox-47-baseline/spec.md`

## Summary

Make the existing suite green on NetBox v4.7.4, pin CI to that tag, and declare 4.7.0 as the minimum version of plugin 2.6.0. No plugin behaviour changes (one state-only migration, see research D7): the compatibility assessment ran the 1020 tests on v4.7.4 and found 18 failures that are all test artefacts (nine query-count baselines one lower, nine REST tests giving Python dates where NetBox 4.7's test helper compares text). The change is therefore test data, a recorded baseline, CI, metadata and documents. It is implemented first, so that plans 004 to 007 start from a green baseline.

## Technical Context

**Language/Version**: Python 3.12, 3.13, 3.14 (same range as NetBox 4.7.4, `requires-python >= 3.12`)

**Primary Dependencies**: NetBox 4.7.4 (Django 6.1.2, django-tables2 3.0.1, django-pgware); the plugin adds no dependency

**Storage**: PostgreSQL 15 or later with the `ltree` extension (NetBox 4.7 requirement); Redis 6 or later. The CI `postgres` service uses the unpinned official image and the `netbox` superuser, which satisfies both. No migration.

**Testing**: NetBox's test runner (`manage.py test netbox_contract.tests`), `--keepdb` allowed; query-count baseline `netbox_contract/tests/query_counts.json`

**Target Platform**: NetBox 4.7.x plugin, any OS NetBox supports

**Project Type**: NetBox plugin (Django app)

**Performance Goals**: none; the suite ran in about 140 seconds once the test database existed

**Constraints**: no behaviour change; the pre-commit hook (ruff on `netbox_contract/`) must pass

**Scale/Scope**: about 6 test locations, 1 workflow file, 2 metadata files, 4 documents

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Assessment |
|-----------|------------|
| I. NetBox-native | Pass. `min_version` stays the single source of the minimum; no removed 4.7 API is used (checked in the compatibility assessment). |
| II. Tested behaviour | Pass. No behaviour changes; the tests are corrected, not weakened: REST tests keep their assertions on stored values, and the baseline is re-recorded once with the reason stated. |
| III. Lint-clean | Pass. Only test data and metadata change; `ruff check` is run before the commit. |
| IV. Data safety | Pass. One state-only migration (`0053_owner_related_name`, no SQL, no data touched), required by NetBox 4.7 so that `makemigrations --check` stays clean; guarded by a test. |
| V. Backward-compatible interfaces | Pass with a stated exception: dropping NetBox 4.6 narrows the supported platform, not a plugin interface; recorded in the changelog warning (option A of the compatibility assessment). |
| VI. Minimal dependencies | Pass. No dependency added. |
| VII. Documented change | Pass. README, changelog, CLAUDE.md and the constitution's compatibility section are in scope (FR-006 to FR-008). |

Post-design re-check: unchanged. No Complexity Tracking entry.

## Project Structure

### Documentation (this feature)

```text
specs/008-netbox-47-baseline/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── metadata-and-ci.md
└── tasks.md             # /speckit-tasks, not created here
```

### Source Code (repository root)

```text
.github/workflows/lint-tests.yaml     # ref: v4.7.4
netbox_contract/__init__.py           # version 2.6.0, min_version 4.7.0
pyproject.toml                        # version 2.6.0
netbox_contract/tests/
├── test_api.py                       # REST create/update data as text
└── query_counts.json                 # re-recorded on 4.7.4
README.md                             # compatibility table
CHANGELOG.md                          # 2.6.0 section, warning, Other Changes
CLAUDE.md                             # minimum version, pinned tag, release-notes link
.specify/memory/constitution.md       # compatibility section (via /speckit-constitution)
```

**Structure Decision**: edit the existing files in place; no new module.

## Complexity Tracking

No constitution violation to justify.
