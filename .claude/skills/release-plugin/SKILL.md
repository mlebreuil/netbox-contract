---
name: release-plugin
description: Prepare and publish a netbox-contract release - version bump, compatibility table, changelog, checks, release pull request from develop to main, GitHub release that publishes to PyPI. Use when a maintainer asks to prepare, cut, tag or ship a plugin release.
---

# Release the plugin

Releases are built from `develop` and merged into `main`; the tag is created by the GitHub release, and publishing
the release starts `.github/workflows/python-publish.yml`, which uploads to PyPI through trusted publishing (the
`release` environment). **A file uploaded to PyPI can never be replaced.** Prepare the release changes without asking,
but open a pull request only when the maintainer explicitly asks. **Confirm with the maintainer before step 7**, and
never skip a failing check.

Ground rule: a release PR contains release changes only (version, changelog, compatibility table). A fix found on the
way belongs in its own issue and PR, merged before the release. A feature planned as one release is not published in
pieces (Constitution VII).

## 0. Inputs

- The version `X.Y.Z` and its kind: patch (fixes), minor (features, new migrations), major (removals).
- The issues in it. Each should be closed against `develop`.

## 1. Preflight

```bash
git fetch origin
git status --short                       # clean tree
git checkout develop && git merge --ff-only origin/develop
```

Check that CI is green on `develop` (`gh run list --branch develop --limit 5`).

## 2. Run the checks

Use `run-tests`: `ruff check`, `python3 utils/spec_ids.py check` and `registry` (no diff in `registry.md`), the whole
suite against the NetBox tag in `lint-tests.yaml`, `makemigrations --check`.

## 3. Bump the version

The version is written **once**, in `netbox_contract/version.py` (`__version__ = 'X.Y.Z'`). `ContractsConfig.version`
and the package metadata (`dynamic` version in `pyproject.toml`) read it. Change that one line;
`test_plugin_version_has_a_single_source` fails if a second copy appears.

## 4. Compatibility

- `README.md` compatibility table: NetBox versions to plugin versions. If the minimum NetBox version moves,
  `min_version` in `__init__.py`, the `> [!WARNING]` callout of the changelog, `CONTRIBUTING.md`, `AGENTS.md`, the
  constitution's compatibility section and the pinned tag in `lint-tests.yaml` agree.
- Upgrade steps that exist (data conversions, cleanup commands) are in the README section for that version.

## 4b. Build the package

```bash
python -m pip install build twine
python -m build
twine check dist/*
```

The wheel must contain the templates, locale files and migrations (`package-data` in `pyproject.toml`) and must not
contain `tests/`. `dependencies` lists the plugin's own requirements only: never `netbox` (it is on PyPI since 4.7, so
pip would install a second copy into the virtualenv). Remove `dist/` and `build/` afterwards.

## 5. Changelog

Run `draft-changelog` for `X.Y.Z`. Review it with the maintainer. Empty the `## [Unreleased]` heading if its content
moved into the version.

## 6. Open the release PR (only when explicitly requested)

If requested, branch from `develop` named `release-X.Y.Z` (or the issue branch if there is one), commit the release
changes, and open a PR into `main`. Its description is written by the maintainer (AI policy); give a short draft
marked as a draft and say so when handing it over. Wait for CI. Otherwise, hand off the prepared branch and a brief
draft description without opening a PR.

## 7. Publish (confirm first)

After the PR merges and the maintainer says go:

```bash
gh release create vX.Y.Z --target main --title "vX.Y.Z" --notes-file <notes>
```

The notes are the changelog section for the version, reviewed. Then watch the workflow
(`gh run watch`), approve the `release` environment if asked, and verify:

```bash
pip index versions netbox-contract      # X.Y.Z listed
```

Install it in a clean virtualenv and import `netbox_contract` as a smoke test.

## 8. Hand off

Report the release URL, the PyPI version, and any step left to the maintainer (merge `main` back into `develop` if
the branches diverged, close the milestone, announce).

## Why

The README compatibility table and the pinned NetBox tag are what silently drift; PyPI immutability is why the
confirmation sits before the tag, not after.

## References

`CONTRIBUTING.md` ("Deploying"), `.github/workflows/python-publish.yml`, `draft-changelog`, `run-tests`,
constitution VII; the `netbox-plugin-development` skill, `references/packaging.md` (versioning, building, publishing).
