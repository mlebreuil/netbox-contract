# NetBox 4.7 Plugin Migration Checklist

Verified against NetBox v4.7.2. Use this when raising `max_version` to `'4.7.99'` or when a
plugin must keep working on 4.5/4.6 *and* 4.7 (each row shows the version-safe form).

## Removed in 4.7 — replace before bumping `max_version`

| Removed | Replacement | Notes |
|---------|-------------|-------|
| NetBox's `{% querystring request page=1 %}` (from `{% load helpers %}`) | Django's built-in `{% querystring page=1 %}` | Django's tag reads `request` from context; passing it raises `TemplateSyntaxError`. It returns `?` (not `''`) when empty. It also works on 4.5/4.6 (Django ≥5.1) **as long as the template does not `{% load helpers %}`**, which shadows it with the old tag |
| `OptionalLimitOffsetPagination` | `netbox.api.pagination.NetBoxPagination` | |
| `ExpandableIPAddressField` | `utilities.forms.fields.ExpandableIPNetworkField` | Rename only; new name exists on 4.5/4.6 too |
| `expand_ipaddress_pattern()` | `utilities.forms.utils.expand_ipnetwork_pattern()` | Same |
| `registry['models']` | `ObjectType.objects.public()` | |
| `registry['denormalized_fields']` | — | Denormalized fields are now maintained by PostgreSQL triggers |
| `DEFAULT_ACTION_PERMISSIONS`, `LEGACY_ACTIONS`, legacy view action mappings | Declare `actions` on the view | |
| `CustomFieldsMixin.populate_custom_field_defaults()` | — | Obsolete; delete the call |
| `OwnerMixin` automatic reverse relation (`owner.accesslist_set`) | Query forward: `AccessList.objects.filter(owner=owner)` | The `owner` FK now uses `related_name='+'` |
| Django `EMAIL_HOST`/`EMAIL_PORT`/`EMAIL_HOST_USER`/`EMAIL_HOST_PASSWORD`/`EMAIL_USE_TLS`/… settings; `EMAIL_BACKEND` | `django.core.mail.send_mail()` or `EmailMessage(...).send()` on the default connection | NetBox populates Django's `MAILERS` instead. `get_connection(backend=...)` with an explicit backend raises `RuntimeError`. Sending requires `EMAIL['SERVER']` in `configuration.py` (else `InvalidMailer`) |
| `DeviceWithConfigContextSerializer`, `VirtualMachineWithConfigContextSerializer` | `DeviceSerializer` / `VirtualMachineSerializer` | `config_context` is now present by default (`?omit=config_context`/`?fields=` skip loading it from 4.7.3); `?exclude=config_context` is ignored |
| Webhook context `request_id`, `username`; `send_webhook(username=...)` | `request.id`, `request.user` | Drain RQ queues before upgrading — queued webhook jobs from 4.6 fail with `TypeError` |
| `JINJA2_FILTERS` (config parameter) | `JINJA_FILTERS` | Old name works until 5.0 |
| `MPTTColumn` (deprecated, removed in 5.0) | `columns.TreeColumn` | `MPTTColumn` still works on 4.5–4.7 as an alias |

## Changed behavior that affects plugin code

- **`obj.custom_fields` and `CustomField.objects.get_for_model()` return a `list`**, not a queryset:
  no `.filter()`/`.exists()`. `get_for_model()` returns only *active* fields (one whose data is
  being provisioned/purged by a background job is omitted unless selected via `statuses=`).
- **django-tables2 v3.0**: in custom table templates, `{% querystring %}` (from `{% load django_tables2 %}`)
  is now `{% querystring_replace %}`; `RelatedLinkColumn` is gone — use `tables.Column(linkify=True)`.
- **Search indexing is deferred**: inside a transaction, cache writes run after commit (in a worker
  if one is listening, inline otherwise). Django `TestCase` never runs on-commit callbacks unless
  you ask — see [testing-guide](testing-guide.md#search-index-assertions-47).
- **Filterset test mixins renamed**: `BaseFilterSetTests` → `BaseFilterSetTestMixin`,
  `ChangeLoggedFilterSetTests` → `ChangeLoggedFilterSetTestMixin` (`utilities.testing`).
- **Hierarchical models on ltree**: `level` is a Python property only; `get_root()`, `get_family()`,
  `is_leaf_node()`, `move_to()`, `insert_at()` are gone — see [model-patterns](model-patterns.md#hierarchical-models-ltree).
- **Bulk REST writes**: `NetBoxModelViewSet` accepts `?background=true` and returns per-object errors —
  see [views-and-api](views-and-api.md).
- **Custom scripts in core are deprecated** (supported through 4.8, removed in 5.0 in favor of a
  dedicated plugin) — a plugin that ships scripts should plan for that move.
- **Custom link `request` is sanitized** to `id`, `path`, `path_info`, `method`, `GET`, `user`.

## New extension points (all require `min_version = '4.7.0'`)

| Feature | Where | Reference |
|---------|-------|-----------|
| Fields/filters on core GraphQL types | `graphql_extensions.py` | [views-and-api](views-and-api.md#extending-core-graphql-types-47) |
| Custom event rule action types | `event_rules.py` — subclass `EventRuleAction` | [views-and-api](views-and-api.md#custom-event-rule-actions-47) |
| Jinja filters + config-template context | `jinja_env.py`, `PluginConfig.get_jinja_context()` | below |
| Breadcrumbs on declarative layouts | `netbox.ui.breadcrumbs.Breadcrumb` | [views-and-api](views-and-api.md#declarative-layouts--breadcrumbs-46--47) |
| Generic FK as one form field | `GenericObjectChoiceField` + `GenericObjectFormMixin` | [forms-tables-filtersets](forms-tables-filtersets.md#generic-object-fields-47) |
| Choice descriptions; dict entries in `FIELD_CHOICES` | `utilities.choices.Choice` | [model-patterns](model-patterns.md#choices-pattern) |
| `update_dependent_objects()` hook (4.7.2) | model method | [model-patterns](model-patterns.md#dependent-objects-472) |

### Jinja filters for config templates

```python
# jinja_env.py — auto-discovered (PluginConfig.jinja_filters defaults to 'jinja_env.filters')
def prefix_list(device):
    return [str(ip.address) for iface in device.interfaces.all() for ip in iface.ip_addresses.all()]

filters = {'prefix_list': prefix_list}    # {% for p in device | prefix_list %}
```

Or register in `ready()`: `from netbox.plugins.registration import register_jinja_filters` then
`register_jinja_filters(filters)` — raises `TypeError` for a non-dict or a non-callable value.

Precedence, lowest → highest: NetBox built-ins → plugin filters → instance `JINJA_FILTERS`
(operators can override any plugin filter in `configuration.py`). Two plugins registering the
same name: the later-loaded plugin wins and NetBox logs a warning.

### Config-template context variables

```python
class MyPluginConfig(PluginConfig):
    def get_jinja_context(self):
        from .utils import LookupNamespace
        return {'netbox_myplugin': LookupNamespace()}   # {% set r = netbox_myplugin.lookup(device.name) %}
```

- Called on **every** config template render, with **no arguments** (no access to the object being
  rendered) — keep it cheap and put lazy lookups on the returned object.
- Prefix keys with your plugin name. Never return an app-label key (`dcim`, `ipam`, …): it silently
  replaces that entire model namespace in the template context.
