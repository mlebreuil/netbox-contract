<!--
Sync Impact Report (temporary, remove before committing)
- Version change: template (unversioned) -> 1.0.0
- Modified principles: none (first ratification; all placeholders replaced)
- Added sections: Core Principles I-VII, Compatibility and Technical Constraints,
  Development Workflow and Quality Gates, Governance
- Removed sections: none
- Deferred TODOs: none. Ratification date set to the date the constitution was adopted
  (2026-09-26); the repository had no earlier constitution.
- Sources: CONTRIBUTING.md, ruff.toml, .pre-commit-config.yaml,
  .github/workflows/lint-tests.yaml, CHANGELOG.md, and the decisions recorded in
  specs/001-contract-lines-billing/ (assessment go decision, plan.md, research.md).
-->
# NetBox Contract Plugin Constitution

## Core Principles

### I. NetBox-Native Plugin

The plugin MUST behave like a first-class part of NetBox. Every domain model MUST be a
`NetBoxModel` with the full NetBox stack (list, detail, edit, delete and bulk views, table,
filterset, forms, REST serializer, search, change log, tags and custom fields), and code MUST
follow the NetBox style guide and Django conventions. The minimum supported NetBox version MUST
be the `min_version` in `netbox_contract/__init__.py`; new code MUST NOT use NetBox or Django
APIs already announced for removal in the next NetBox version, except where a plan records the
exception and its migration path.

Rationale: users adopt the plugin because it feels like NetBox; staying on the platform's
conventions is what keeps upgrades cheap.

### II. Tested Behaviour (NON-NEGOTIABLE)

Every change of behaviour MUST come with automated tests that fail before the change and pass
after it. Each acceptance scenario and edge case of a specification MUST be covered by at least
one test. The suite MUST run in CI against a pinned NetBox release (a tag, never a moving
branch) on every supported Python version, and MUST pass before a merge. The query-count
baseline in `netbox_contract/tests/query_counts.json` MUST be regenerated whenever a list view
changes and MUST NOT be raised without a stated reason.

Rationale: the plugin holds financial records; regressions are expensive and often silent.

### III. Lint-Clean and Consistent Style

`ruff check` (configuration in `ruff.toml`: line length 120, single quotes, isort ordering) MUST
pass with no warnings, both in the pre-commit hook and in CI. A lint rule MUST NOT be disabled
to make a change pass; a rule change is a governance amendment to `ruff.toml` reviewed like any
other change.

Rationale: one style, enforced by machine, keeps review about design rather than formatting.

### IV. Data Safety and Migrations

Schema changes MUST ship as Django migrations and `makemigrations --check` MUST report nothing
pending. Data migrations MUST be lossless, re-runnable without duplicating data, and MUST report
every judgement call instead of hiding it. Existing user data (amounts, currencies, invoices,
templates) MUST NOT be altered, converted or deleted silently. A field, model or setting MUST NOT
be removed until it has been deprecated, documented in the changelog for at least one released
version, and the removal is itself a specified feature.

Rationale: users upgrade in place on live accounting data; there is no second chance.

### V. Backward-Compatible Interfaces

The REST API, the plugin settings and the import formats are public interfaces. A release MUST
NOT remove or rename a REST field, endpoint, plugin setting or import column without the
deprecation path of Principle IV. New required inputs MUST NOT be added to existing endpoints;
new settings MUST default to the previous behaviour unless the specification says otherwise.

Rationale: integrations and scripts written by users break first when an interface moves.

### VI. Simplicity and Minimal Dependencies

The plugin MUST prefer plain Django and NetBox facilities. A new runtime dependency MUST be
justified in a plan (need, maintenance status, compatibility with the supported Django and NetBox
versions) and MUST NOT be added where a few lines of code do the job. Logic that is not about
requests or persistence (calculations, validation rules, conversions) MUST live in small modules
without database or view dependencies so it can be tested directly and reused by screens, API,
migrations and scripts.

Rationale: a small dependency surface is what lets the plugin follow NetBox's Django upgrades.

### VII. Documented Change

Every user-visible change MUST update `docs/`, `CHANGELOG.md` and, when settings or requirements
change, `README.md`, in the same pull request. Plugin versions follow semantic versioning: patch
for fixes, minor for new features and new migrations, major for removals. A feature planned as
one release MUST NOT be published in pieces.

Rationale: administrators decide whether to upgrade from the changelog and the docs.

## Compatibility and Technical Constraints

- Python 3.12 or newer; NetBox 4.6 or newer until a specification raises the minimum. The
  supported Python versions and the pinned NetBox tag are those in
  `.github/workflows/lint-tests.yaml`.
- Currency amounts use `DecimalField` with the existing currency code fields; no currency or
  money library is used, and no currency conversion is performed.
- Permissions use NetBox object permissions; menu entries and buttons MUST declare the
  permission they require.
- NetBox core custom scripts are announced as deprecated; scripts shipped in `scripts/` MUST be
  limited to what cannot reasonably live in the plugin and MUST keep their logic in importable
  plugin modules so they can move to a replacement mechanism.
- NetBox 4.7 compatibility is separate work and is not implied by any feature specification
  that does not say so.

## Development Workflow and Quality Gates

- One branch per GitHub issue, created from `develop`; `master` receives releases only.
  Local `develop` MUST be refreshed with `git fetch` before a branch is created or rebased.
- Features follow the Spec Kit sequence: assessment where the value is unclear, then specify,
  clarify, plan, tasks, analyze, implement. `/speckit-analyze` MUST report no CRITICAL finding
  before implementation starts.
- A plan MUST include a Constitution Check against Principles I-VII; a violation MUST be listed
  in the plan's Complexity Tracking with the simpler alternative that was rejected.
- Merge gates: lint clean, tests pass on the pinned NetBox tag, no pending migration, docs and
  changelog updated, and a review that verifies compliance with this constitution.
- Commits go through the pre-commit hook; the hook MUST NOT be bypassed.

## Governance

This constitution supersedes other practice documents where they conflict. An amendment MUST be
made with `/speckit-constitution`, MUST state its reason, MUST update the version below by
semantic versioning (MAJOR: a principle removed or redefined incompatibly; MINOR: a principle or
section added or materially expanded; PATCH: clarifications), and MUST be reviewed in a pull
request by the maintainer. Compliance is reviewed in every pull request and in every plan's
Constitution Check; unresolved conflicts block the merge. Day-to-day guidance for contributors
is in `CONTRIBUTING.md`.

**Version**: 1.0.0 | **Ratified**: 2026-09-26 | **Last Amended**: 2026-09-26
