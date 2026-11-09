# Packaging & Distribution

## pyproject.toml (Recommended)

```toml
[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "netbox-myplugin"
dynamic = ["version"]
description = "A NetBox plugin for managing access lists"
readme = "README.md"
license = {text = "Apache-2.0"}
requires-python = ">=3.12"
authors = [{name = "Your Name", email = "you@example.com"}]
dependencies = []    # your plugin's own deps only — never "netbox" (see below)

[project.urls]
Homepage = "https://github.com/yourname/netbox-myplugin"
Repository = "https://github.com/yourname/netbox-myplugin"
Issues = "https://github.com/yourname/netbox-myplugin/issues"

[project.entry-points."netbox.plugins"]
netbox_myplugin = "netbox_myplugin:config"

[tool.setuptools.dynamic]
version = {attr = "netbox_myplugin.version.__version__"}

[tool.setuptools.packages.find]
include = ["netbox_myplugin*"]
```

NetBox has been published to PyPI since 4.7, so a `netbox` entry in `dependencies` makes
`pip install netbox-myplugin` pull a second NetBox into the venv next to the real installation.
Declare NetBox compatibility with `min_version`/`max_version` on `PluginConfig` instead, and add
a `COMPATIBILITY.md` table (plugin release → min/max NetBox) for users planning upgrades.

## Version Management

Keep version in a dedicated file to avoid import side effects:

```python
# netbox_myplugin/version.py
__version__ = '1.0.0'
```

Import in `__init__.py`:
```python
from .version import __version__
```

## Entry Point

The entry point key must match `PluginConfig.name` and point to the `config` variable:

```
netbox_myplugin = "netbox_myplugin:config"
```

This is how NetBox discovers and loads your plugin.

## Version Compatibility Strategy

In `PluginConfig`:
```python
min_version = '4.5.0'     # oldest NetBox version supported
max_version = '4.7.99'    # span 4.5–4.7; use .99 to allow all patch releases
```

**Versioning guidelines:**
- Use `.99` for max_version — `'4.5.0'` would block `4.5.1`!
- Test against min and max versions in CI
- Bump `min_version` when you use features from a newer release — e.g. `'4.6.0'` for declarative UI layouts or `Meta.permissions` custom actions; `'4.7.0'` for GraphQL core-type extensions, `EventRuleAction`, Jinja filters/context, breadcrumbs, or `GenericObjectChoiceField`; `'4.7.1'` for `NestedLtreeGroupModel`
- NetBox refuses to load plugins outside the declared version range
- Remember the Django split when spanning 4.5–4.7: 4.5 is Django 5.2, 4.6 is Django 6.0, 4.7 is Django 6.1 — third-party deps must support all three
- Spanning 4.6 and 4.7? Work through [netbox-4.7-migration](netbox-4.7-migration.md) first: several 4.6 deprecations were removed in 4.7

## Building & Publishing

```bash
# Install build tools
pip install build twine

# Build distribution
python -m build

# Check the package
twine check dist/*

# Upload to PyPI
twine upload dist/*

# Upload to TestPyPI first
twine upload --repository testpypi dist/*
```

## Installation

Users install your plugin with:

```bash
pip install netbox-myplugin
```

Then add to NetBox's `configuration.py`:
```python
PLUGINS = ['netbox_myplugin']
PLUGINS_CONFIG = {
    'netbox_myplugin': {
        'feature_x': True,  # matches default_settings keys
    }
}
```

Then run migrations:
```bash
cd /opt/netbox/netbox
python manage.py migrate
python manage.py collectstatic --no-input
systemctl restart netbox netbox-rq
```

## Development Installation

For development, install in editable mode:

```bash
cd /opt/netbox
source venv/bin/activate
pip install -e /path/to/netbox-myplugin

# Create initial migrations
cd /opt/netbox/netbox
python manage.py makemigrations netbox_myplugin
python manage.py migrate
```

## CI Testing Matrix

Test against multiple NetBox versions in CI:

```yaml
# .github/workflows/test.yml
strategy:
  matrix:
    netbox-version: ['4.5.0', '4.5.8', '4.6.2', '4.7.2']
    python-version: ['3.12', '3.13', '3.14']
```

Clone NetBox at the target version, install your plugin, run tests (the 4.7.x job needs a
PostgreSQL 15+ service; 4.5/4.6 accept 14):

```bash
git clone --depth 1 --branch v$NETBOX_VERSION https://github.com/netbox-community/netbox.git
cd netbox
pip install -r requirements.txt
pip install -e /path/to/plugin
python netbox/manage.py test netbox_myplugin.tests
```

## Changelog

Maintain a `CHANGELOG.md` following [Keep a Changelog](https://keepachangelog.com/):

```markdown
# Changelog

## [1.1.0] - 2026-04-15
### Added
- Support for extended access lists
### Fixed
- Filter form missing device field
```
