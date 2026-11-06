# Hand-off: AI tooling alignment (branch `ai-gouvernance-adjustment`)

Rewritten 2026-11-03 to start a fresh Claude Code CLI session in the dev container, updated 2026-11-06. It replaces the hand-off of the
implementation of contract lines (feature 001, issue #278), which is finished: shipped in plugin 2.5.0, and NetBox 4.7
support followed in 2.6.0 (feature 008). Update or delete this file when the work below is committed.

## Where things stand

The branch aligns the repository's AI tooling with NetBox's (`netbox-community/netbox`) and NetBox Labs' (`netboxlabs/skills`).
Updated 2026-11-06 in the dev container: the staged files are in place (`.claude/skills/`, `.github/PULL_REQUEST_TEMPLATE.md`)
and the checks pass (1097 tests, `ruff check`, pre-commit, `spec_ids.py check`, no pending migrations, `pip install -e .`
reports 2.6.0). Three commits are made: (a) AI policy, PR template, CONTRIBUTING, README; (b) the project skills and the
regenerated registry; (c) constitution 1.2.0, `AGENTS.md`, `CLAUDE.md`, pre-commit, the `form_with_defaults` docstring
and this file.

**Not committed:** the single-source plugin version (`netbox_contract/version.py`, read by `__init__.py` and
`pyproject.toml`; `test_plugin_version_has_a_single_source` in `tests/test_conventions.py`; `specs/_global/contracts/operations.md`;
the `CHANGELOG.md` Unreleased bullet). It waits for its own issue (see open points).

Notes from the checks:

- The `draft-changelog` skill cites `008-FR-008` as an example, which the registry counts as a citation (the regenerated
  registry is committed). Replace the example if that count should stay at 1.
- The spec-identifier pre-commit hook does not watch `.claude/`, although `spec_ids.py` scans it; CI still checks it.

## Next steps

1. Create the issue (and spec, or a decision that none is needed) for `version.py`, move the uncommitted change to its
   own branch from `develop`, and add the issue link to the changelog bullet.
2. Push this branch and open its pull request when the maintainer asks (it needs an issue too: Constitution, one branch
   per issue).

## Decisions taken with the maintainer (do not reopen without asking)

- `AGENTS.md` is the source of agent instructions; `CLAUDE.md` only imports it.
- The AI policy applies to communications, not to code, specs, changelog or commit messages.
- Not adopted: NetBox's `claude.yml` and issue-triage workflows (cost and secret), the vouching list, the `build-plugin`
  command, and every NetBox Labs skill about operating NetBox rather than building a plugin.
- **No `max_version`.** The maintainer cannot afford to release the plugin at every NetBox minor version. Compatibility
  stays the README table plus the NetBox tag pinned in CI (constitution: newer NetBox is separate work).
- Single-source version: yes (`version.py`). Entry point `netbox.plugins`: no (NetBox imports the module named in `PLUGINS`
  and reads `.config`; it does not use entry points).
- Keep-a-Changelog style from NetBox Labs' packaging reference is not adopted; the changelog follows the rules in
  `AGENTS.md` ("Changelog").

## Open points

- **`version.py` needs an issue and a spec.** The constitution wants one branch per issue and a specified feature. Create
  the issue and `specs/009-*` (or confirm that a packaging fix may go without one), move the change to its own branch, and
  add the issue link to the changelog bullet, which has none. The `operations.md` row still cites the feature 008 requirement on the version.
- **Changelog format conflict.** The written rule (`* [#N](link) - description`) differs from how the 2.6.0 block is
  written (sentences ending with the link). `draft-changelog` follows the rule and flags the difference. Decide which one
  is right and fix the other.
- `release-plugin` assumes a `release-X.Y.Z` branch and a GitHub release targeting `master` (which publishes to PyPI through
  `python-publish.yml`). Check this against how releases are really made, on the next release.
- Possible code follow-ups, not started: `pyproject.toml` lists `Django` in `dependencies` (NetBox provides it; Principle VI);
  some foreign keys to core models use a plain `related_name` such as `'contracts'` (NetBox Labs advises an
  `%(app_label)s_` prefix; renaming changes a reverse accessor that filters and GraphQL may use).
- Refresh the vendored `netbox-plugin-development` skill when NetBox ships a release (procedure in `.claude/skills/README.md`).
- The constitution's "Sync Impact Report (temporary...)" comment is still at the top, as in earlier amendments.

## Environment notes

- Dev container layout: `/workspaces/netbox/netbox` (NetBox, venv in `venv/`) and `/workspaces/netbox/netbox-contract`
  (this repository). The pre-commit hook runs ruff through `/workspaces/netbox/netbox/venv/bin/python`.
- CI pins a NetBox tag (`v4.7.4` at the time of writing) for Python 3.12 to 3.14; `testing/configuration.py` is the NetBox
  configuration CI uses. Run tests with `NETBOX_CONFIGURATION=netbox.configuration_testing`: the default configuration has
  DEBUG on, which the debug toolbar refuses under tests.
- `makemigrations` is refused unless the NetBox configuration sets `DEVELOPER = True`.
- `tests/query_counts.json` is the query-count baseline; re-record it serially and only with a stated reason.
- Test helpers: `netbox_contract/tests/custom.py` and `tests/helpers.py` (factories default to a Posted, hence locked,
  invoice).
- The dev databases from the contract-lines work (`netbox`, `netbox_premigration_testdata`, `netbox_before_0044`) may still
  exist in the container; they are not needed for this work.
- The cloud session that prepared this branch could not write into `.claude/` or `.github/`. That limit came from its
  tools; it should not apply in the dev container, so edit the skills directly there.
