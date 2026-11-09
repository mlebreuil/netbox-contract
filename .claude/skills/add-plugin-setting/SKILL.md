---
name: add-plugin-setting
description: Checklist for adding a plugin setting to netbox-contract (default_settings, reading it at call time, validation, tests, README and docs, specs, changelog). Use when the user asks to add a configuration option, setting or parameter to the plugin.
---

# Add a plugin setting

Plugin settings are a public interface (Constitution V). A new setting **defaults to the previous behaviour** unless
the specification says otherwise, and it is part of a specified feature.

## 1. Declare it

Add it to `default_settings` in `ContractsConfig` (`netbox_contract/__init__.py`) with its default; a comment lists
the allowed values when they are a closed set (see `contract_assignments_display`). Do not add it to
`required_settings` unless the plugin cannot work without it.

## 2. Read it at call time

Read from `settings.PLUGINS_CONFIG['netbox_contract']` when the code runs. The module-level `plugin_settings` is that
same dict; do not copy a value into a module constant at import time, because tests change settings with
`mock.patch.dict` and a copied value would ignore the override. (`constants.ASSIGNEMENT_TYPES` is
read at import; do not copy that pattern.)

If an invalid value is possible, handle it where the setting is consumed and fail with a message naming the setting;
do not let it surface as an unrelated error.

## 3. Use it

Put the behaviour in a function that takes the value as an argument, so the logic is testable without settings
(Constitution VI). Settings that hide or require fields go through `prune_fieldsets` and the settings-aware panels
rather than a new mechanism.

## 4. Tests (first, failing)

```python
with mock.patch.dict(settings.PLUGINS_CONFIG['netbox_contract'], {'my_setting': 'value'}):
    ...
```

Test the default (previous behaviour unchanged) and each non-default value; cite the requirement
(`NNN-FR-012`). If the setting changes a list view, re-record the query counts serially with a stated reason.

## 5. Document

- `README.md`: the setting, its default, allowed values (Constitution VII).
- `docs/`: the page where the behaviour is described.
- `specs/_global/contracts/ui.md` (settings) and, if it changes rules, `behaviours.md`; then
  `python3 utils/spec_ids.py check` (and `python3 utils/spec_ids.py registry` if specs changed).
- `CHANGELOG.md`: Enhancements (or Breaking Changes if the default changes behaviour). Use `draft-changelog`.

## No migration

Settings are not stored in the database. If existing data must change because of the setting, that is a data
migration with its own rules (Constitution IV), not part of this skill.

## Why

A setting is read by administrators who never read the code. A default that changes behaviour, or a value cached at
import, turns an upgrade into an incident.

## References

`AGENTS.md` ("Plugin settings"), `netbox_contract/__init__.py`, constitution V, VI, VII; the
`netbox-plugin-development` skill, section 1 (`PluginConfig`, `default_settings`, `required_settings`).
