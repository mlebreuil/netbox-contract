# Model Patterns

## Base Class Hierarchy

```
django.db.Model
└── NetBoxModel              # Tags, custom fields, change logging, bookmarks,
    │                        # journaling, export templates, event rules, notifications
    ├── PrimaryModel         # + description, comments fields (4.5+ plugins API)
    │   └── NestedGroupModel # + MPTT tree structure (parent, level, etc.)
    └── OrganizationalModel  # + name (unique), slug (unique), description, comments
```

**Choose your base class:**
- `NetBoxModel` — generic plugin object, you define all fields
- `PrimaryModel` — object with description + comments (e.g., a circuit, a service)
- `OrganizationalModel` — categorization object with unique name/slug (e.g., a role, a type)
- `NestedGroupModel` — hierarchical grouping (e.g., regions, location types); deprecated in 4.7 — use `NestedLtreeGroupModel` if `min_version` >= `'4.7.1'` (see [Hierarchical Models](#hierarchical-models-ltree))

## NetBoxFeatureSet Mixins

`NetBoxModel` includes all of these automatically:

| Mixin | Feature |
|-------|---------|
| `BookmarksMixin` | User bookmarks |
| `ChangeLoggingMixin` | Change log entries |
| `CloningMixin` | Object cloning |
| `CustomFieldsMixin` | Custom fields |
| `CustomLinksMixin` | Custom links |
| `CustomValidationMixin` | Custom validation rules |
| `ExportTemplatesMixin` | Custom export templates |
| `JournalingMixin` | Journal entries |
| `NotificationsMixin` | User notifications |
| `TagsMixin` | Tag assignment |
| `EventRulesMixin` | Event rules (webhooks, scripts) |

## Choices Pattern

```python
from utilities.choices import ChoiceSet

class AccessListTypeChoices(ChoiceSet):
    key = 'AccessList.type'

    CHOICES = [
        ('standard', 'Standard', 'blue'),   # (value, label, color)
        ('extended', 'Extended', 'orange'),
    ]
```

Use in model field:
```python
type = models.CharField(max_length=50, choices=AccessListTypeChoices)
```

> **NetBox 4.7+**: `Choice(value, label, color=None, description=None)` (from `utilities.choices`)
> adds a description that NetBox's `ChoiceField`/`MultipleChoiceField` render under the option, and
> operators may supply `FIELD_CHOICES` entries as dicts instead of tuples. `Choice` does not exist on
> 4.5/4.6 — plugins spanning versions keep the tuple form.
>
> ```python
> from utilities.choices import Choice, ChoiceSet
>
> class AccessListTypeChoices(ChoiceSet):
>     key = 'AccessList.type'
>     CHOICES = [
>         Choice('standard', 'Standard', color='blue', description='Source-address matching only'),
>         Choice('extended', 'Extended', color='orange', description='Source, destination, and ports'),
>     ]
> ```

## RestrictedQuerySet

All plugin models using `NetBoxModel` get object-level permissions via
`RestrictedQuerySet`. The default manager handles this automatically. If you
override the manager, inherit from `RestrictedQuerySet`:

```python
from netbox.models import RestrictedQuerySet

class AccessListQuerySet(RestrictedQuerySet):
    def active(self):
        return self.filter(status='active')

class AccessList(NetBoxModel):
    objects = AccessListQuerySet.as_manager()
```

## ForeignKey Best Practices

```python
# Reference core models as strings
device = models.ForeignKey(
    to='dcim.Device',
    on_delete=models.CASCADE,
    related_name='%(app_label)s_access_lists',  # avoids collisions
)

# Nullable FK (optional relationship)
tenant = models.ForeignKey(
    to='tenancy.Tenant',
    on_delete=models.SET_NULL,
    blank=True, null=True,
    related_name='%(app_label)s_access_lists',
)

# GenericForeignKey for polymorphic relations
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

assigned_object_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
assigned_object_id = models.PositiveBigIntegerField()
assigned_object = GenericForeignKey('assigned_object_type', 'assigned_object_id')
```

## Migration Tips

- Create migrations: `python manage.py makemigrations netbox_myplugin`
- Plugin migrations live in `netbox_myplugin/migrations/`
- When referencing core models in migrations, use `('dcim', 'Device')` tuple
- Test migrations both forward and backward: `python manage.py migrate netbox_myplugin zero`
- Never import model classes directly in migration files — use `apps.get_model()`
- `NestedLtreeGroupModel`: add `InstallLtreeTriggers('netbox_myplugin_<model>', name_column='name')` (from `utilities.ltree`) to the creating migration — makemigrations omits it, and without it `get_ancestors()`/`get_descendants()` silently return nothing
- **Corrective migration:** 4.7.0's trigger definition could not survive `pg_dump`/restore (#23130, fixed 4.7.1). If any install of your plugin may have run the creating migration on 4.7.0, ship a follow-up migration with `ReinstallLtreeTriggers('netbox_myplugin_<model>', name_column='name')` (same arguments): identical forwards, no-op in reverse — reversing `InstallLtreeTriggers` would drop the triggers and functions entirely. Model it on NetBox's `dcim/migrations/0251_fix_ltree_cascade_triggers.py`

## Hierarchical Models (ltree)

```python
from netbox.models import NestedLtreeGroupModel   # 4.7+: name, slug, parent, owner, description, comments

class LocationType(NestedLtreeGroupModel):
    pass
```

- Set `min_version = '4.7.1'` (trigger fix above). `NestedGroupModel` (MPTT) still loads on 4.7 but is deprecated — keep it only while the plugin must also run on 4.5/4.6
- Available: `get_ancestors()`, `get_descendants()`, `get_children()`, queryset `add_related_count()`, and `level` as a Python property — **never** in `filter()`/`order_by()`. Gone vs MPTT: `get_root()`, `get_family()`, `is_leaf_node()`, `move_to()`, `insert_at()`, and the `lft`/`rght`/`tree_id`/`level` columns
- Supporting classes are shared with the MPTT base: `NestedGroupModelForm`/`ImportForm`/`BulkEditForm`/`FilterSetForm` (`netbox.forms`), `NestedGroupModelFilterSet` (`netbox.filtersets`), GraphQL filter `NestedGroupModelFilter`; the GraphQL type base is `netbox.graphql.types.NestedLtreeGroupObjectType`; the table column is `columns.TreeColumn` (`MPTTColumn` alias works on 4.5–4.7)
- Converting an existing MPTT model is a schema + data migration (add the ltree `path` column, install triggers, backfill, drop the MPTT columns) — model it on NetBox's `dcim/migrations/0242_ltree_paths.py`

## Dependent Objects (4.7.2+)

If `save()` derives other objects (as `Cable.save()` traces cable paths), expose that work to
callers that write rows without `save()` — change replay, restores, bulk imports:

```python
class AccessList(NetBoxModel):
    def update_dependent_objects(self):
        ...   # rebuild derived objects purely from database state; idempotent
    update_dependent_objects.alters_data = True
```

Optional: NetBox never calls it during a normal save; callers check for it before calling, and
exceptions propagate unchanged.

## get_absolute_url() Pattern

URL always follows: `plugins:<plugin_name>:<model_name_lower>`

```python
def get_absolute_url(self):
    return reverse('plugins:netbox_myplugin:accesslist', args=[self.pk])
```

Common mistake: forgetting the `plugins:` prefix or using hyphens instead of
underscores in the plugin name portion.
