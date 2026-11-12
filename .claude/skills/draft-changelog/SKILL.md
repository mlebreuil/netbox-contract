---
name: draft-changelog
description: Draft the CHANGELOG.md entries of a netbox-contract release or pull request, organised by kind of change (never by issue), in the format of the latest release. Use when the user asks to write, preview or update the changelog or release notes, or when release-plugin reaches its changelog step.
---

# Draft the changelog

`CHANGELOG.md` is published text that administrators read to decide whether to upgrade (Constitution VII). Present the
draft to the user for review; never commit it unreviewed. `docs/changelog.md` only includes it, so edit
`CHANGELOG.md` alone.

## 1. Gather

- Which version? The one in `pyproject.toml`. If its `### Version X.Y.Z` heading exists under `## Version 2`, add to
  it; otherwise create it above the previous release, keeping the existing heading levels. Ask when unclear.
- The issues: `gh issue view <N> --json title,body,labels,state` for each issue of the release, and the commits since
  the previous tag (`git log vX.Y.Z..HEAD --oneline`) to find changes without an issue entry.
  The `type:` label is a hint, not the rule: `type: bug` usually goes to Bug Fixes, `type: feature` to Enhancements or
  New Features, `type: housekeeping` to Other Changes (or nowhere, when it changes no behaviour). Behaviour that changes
  for existing users goes to Breaking Changes whatever the label.
- The specs of the features (`specs/NNN-*/spec.md`) for what changed in behaviour, and their `tasks.md`, which say
  which section an item goes in.

## 2. Follow the format of the latest release

Open the most recent `### Version` block first and match it. The written rule is in `AGENTS.md` ("Changelog"). Where
the latest block and the written rule differ (for example the shape of the bullets), follow the written rule and tell
the user about the difference instead of choosing silently.

A release is organised **by kind of change, not by issue**. Never add a per-issue entry with nested sub-lists, and
never add a second "Behaviour changes" or "Deprecations" list inside an issue. When several issues ship in one
release, each adds its items to the release's shared sections. Use only the sections that have content, in this
order:

1. `> [!WARNING]` callout for the NetBox minimum version or a mandatory upgrade step.
2. `#### Breaking Changes`: anything that changes behaviour for existing users, administrators or API clients (new
   validation, locks, changed defaults, removed scripts or templates, permission changes, data rewritten by a
   migration, OpenAPI component renames). One bullet per change, saying what to do about it, ending with the issue link.
3. `#### New Features`: one `##### Title ([#N](link))` per major feature, short prose, including how its data is
   upgraded or migrated.
4. `#### Enhancements`, `#### Bug Fixes`, `#### Plugins` (APIs and templates for other plugins),
   `#### Deprecations` (what is deprecated and what replaces it; REST fields to be removed are listed here),
   `#### Other Changes` (CI, dependencies).
5. `#### REST API Changes`: new endpoints with full `/api/plugins/contracts/...` paths, then one bullet per model
   (`netbox_contract.Contract`) with nested bullets for added fields, filters, brief representation changes and
   deprecations.

Issue links are `https://github.com/mlebreuil/netbox-contract/issues/N`.

## 3. Write each entry

- Say what changed for the reader, not what the code did. State the upgrade action in Breaking Changes.
- A spec identifier, when cited, is always qualified (`NNN-FR-008`); the check rejects a bare one.
- Anything that rewrites data names the migration (`0054`) and what is not undone when migrating back.
- No trailing period where the bullet is a short title; match the neighbours.

## 4. Check

- Every closed issue of the milestone or release appears once.
- No issue is described in two sections without a reason.
- `python3 utils/spec_ids.py check` passes (it scans `CHANGELOG.md`).
- Breaking changes imply the right version bump (Constitution VII): patch for fixes, minor for features and new
  migrations, major for removals.

## 5. Flag judgement calls

List for the user what you were unsure about: items you placed in Breaking Changes versus Enhancements, commits with no
issue, wording that promises more than the code does.

## Why

Per-issue entries scatter one kind of change across the page; administrators scan for "Breaking Changes" and
"Deprecations" first, so those must be complete and in one place.

## References

`AGENTS.md` ("Changelog"), `release-plugin`, constitution VII.
