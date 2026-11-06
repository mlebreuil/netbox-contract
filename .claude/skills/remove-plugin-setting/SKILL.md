---
name: remove-plugin-setting
description: Checklist for deprecating and then removing a netbox-contract plugin setting without breaking existing configurations. Use when the user asks to remove, rename or deprecate a configuration option, setting or parameter of the plugin.
---

# Deprecate, then remove, a plugin setting

Settings are a public interface (Constitution V). An administrator's `PLUGINS_CONFIG` must keep working on upgrade, so
a setting is **never removed in the release that deprecates it**, and the removal is a specified feature
(Constitution IV).

## Step 0: which step?

| State | Do |
|---|---|
| Not deprecated yet | **Part A** only |
| Deprecated in a released version, removal specified in `specs/NNN-*` | **Part B** |
| Anything else | Stop; say which condition is missing |

A **rename** is a deprecation of the old name plus a new setting (`add-plugin-setting`): accept both, the old one as an
alias, as `external_party_object_type` is for `external_party_object`.

## Part A: deprecate

1. Keep the setting in `default_settings` and keep honouring it.
2. Document it as deprecated in `README.md` and `docs/`, naming the replacement.
3. `CHANGELOG.md` under Deprecations (what, and what replaces it).
4. `specs/_global/contracts/ui.md` marks it deprecated.
5. Test that it is still honoured.

## Part B: remove

1. Find every use: `grep -rn "<name>" netbox_contract/ docs/ README.md specs/_global/`; uses are read from
   `PLUGINS_CONFIG['netbox_contract']`.
2. Remove the tests of the old behaviour; keep one test that a configuration still containing the setting loads
   without error (NetBox ignores unknown plugin settings; confirm it).
3. Remove the code branches, then the entry in `default_settings`.
4. Remove it from `README.md`, `docs/`, `specs/_global/` (retire its requirement with `Retired: ...`).
5. If removing it changes behaviour (the former default now always applies), that is a Breaking Change: say what
   administrators must do.
6. `python utils/spec_ids.py check`, `ruff check`, test suite; `CHANGELOG.md` Breaking Changes. Major version only
   if the removal changes behaviour for existing configurations (Constitution VII).

## Why

Configurations live outside the repository and are edited by other people. They find out about a removal only from
the changelog.

## References

`add-plugin-setting`, `AGENTS.md` ("Plugin settings"), constitution IV, V, VII.
