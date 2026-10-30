# Contract: plugin metadata and CI

Public statements this change makes. Each is checked by a test or a command in `quickstart.md`.

## Plugin metadata (`netbox_contract/__init__.py`, `pyproject.toml`)

| Item | Before | After |
|------|--------|-------|
| `version` (both files) | 2.5.0 | 2.6.0 |
| `min_version` | 4.6.0 | 4.7.0 |
| `max_version` | unset | unset |

NetBox refuses to load the plugin when its own version is below `min_version`, with an `ImproperlyConfigured` message naming the plugin and the version.

## Compatibility table (README)

| NetBox | Plugin |
|--------|--------|
| 4.5 | 2.4 |
| 4.6 | 2.4, 2.5 |
| 4.7 | 2.6 |

A sentence under the table states: version 2.6 requires NetBox 4.7 or later.

## Changelog (`CHANGELOG.md`, 2.6.0 section)

First lines of the section, as the project rules ask for a minimum-version change:

```text
> [!WARNING]
> This version requires NetBox 4.7.0 or later. NetBox 4.6 installations stay on plugin 2.5.x.
```

and under `#### Other Changes`: `* [#318](https://github.com/mlebreuil/netbox-contract/issues/318) - CI runs the tests against the NetBox v4.7.4 tag`.

## CI (`.github/workflows/lint-tests.yaml`)

- NetBox checkout `ref: v4.7.4` (a tag).
- Python matrix 3.12, 3.13, 3.14; lint job unchanged.
- The test command is unchanged (`manage.py test netbox_contract.tests --keepdb`).
