# Views and API Patterns

## Generic View Classes

| View Class | Purpose | Required Attributes |
|-----------|---------|-------------------|
| `ObjectListView` | List/filter objects | `queryset`, `table`, `filterset`, `filterset_form` |
| `ObjectView` | Detail view | `queryset` |
| `ObjectEditView` | Create/edit form | `queryset`, `form` |
| `ObjectDeleteView` | Delete confirmation | `queryset` |
| `BulkImportView` | CSV import | `queryset`, `model_form` |
| `BulkEditView` | Edit multiple | `queryset`, `table`, `filterset`, `form` |
| `BulkDeleteView` | Delete multiple | `queryset`, `table`, `filterset` |
| `ObjectChildrenView` | Related objects tab | `queryset`, `child_model`, `table`, `tab` |

## @register_model_view Decorator

Registers views with NetBox's URL system — eliminates manual URL patterns:

```python
from utilities.views import register_model_view

@register_model_view(AccessList, 'list')      # /plugins/myplugin/access-lists/
@register_model_view(AccessList)               # /plugins/myplugin/access-lists/<pk>/
@register_model_view(AccessList, 'edit')       # /plugins/myplugin/access-lists/<pk>/edit/
@register_model_view(AccessList, 'delete')     # /plugins/myplugin/access-lists/<pk>/delete/
```

Then in `urls.py`:
```python
from netbox.views.generic import get_model_urls
from . import models
urlpatterns = get_model_urls('netbox_myplugin', models)
```

## URL Namespace Conventions

| Context | Pattern | Example |
|---------|---------|---------|
| UI views | `plugins:<plugin>:<view>` | `plugins:netbox_myplugin:accesslist_list` |
| API detail | `plugins-api:<plugin>-api:<basename>-detail` | `plugins-api:netbox_myplugin-api:accesslist-detail` |
| API list | `plugins-api:<plugin>-api:<basename>-list` | `plugins-api:netbox_myplugin-api:accesslist-list` |

## ViewTab — Extending Core Model Views

Add tabs to existing models (core or other plugins):

```python
from utilities.views import register_model_view, ViewTab
from netbox.views.generic import ObjectChildrenView
from dcim.models import Device
from .models import AccessList
from .tables import AccessListTable

@register_model_view(Device, 'access_lists', path='access-lists')
class DeviceAccessListsView(ObjectChildrenView):
    queryset = Device.objects.all()
    child_model = AccessList
    table = AccessListTable
    tab = ViewTab(
        label='Access Lists',
        badge=lambda obj: AccessList.objects.filter(device=obj).count(),
        permission='netbox_myplugin.view_accesslist',
    )

    def get_children(self, request, parent):
        return AccessList.objects.filter(device=parent)
```

## REST API — Serializer Patterns

### Nested/Brief Representation

```python
class AccessListSerializer(NetBoxModelSerializer):
    class Meta:
        model = AccessList
        fields = ('id', 'url', 'display', 'name', 'device', 'type',
                  'tags', 'custom_fields', 'created', 'last_updated')
        brief_fields = ('id', 'url', 'display', 'name')
```

`brief_fields` controls what's shown when this object appears nested inside another
serializer. Always include `id`, `url`, `display` plus the most identifying field.

### Related Object Fields

```python
from netbox.api.fields import ChoiceField, SerializedPKRelatedField

class AccessListSerializer(NetBoxModelSerializer):
    type = ChoiceField(choices=AccessListTypeChoices)
    # For nested representation of related objects, use nested=True:
    device = DeviceSerializer(nested=True, read_only=True)
```

### HyperlinkedIdentityField

If you need to explicitly set the URL field:
```python
from rest_framework.relations import HyperlinkedIdentityField

url = HyperlinkedIdentityField(
    view_name='plugins-api:netbox_myplugin-api:accesslist-detail'
)
```

## REST API — ViewSet & Router

```python
# api/views.py
from netbox.api.viewsets import NetBoxModelViewSet
from ..filtersets import AccessListFilterSet
from .serializers import AccessListSerializer
from ..models import AccessList

class AccessListViewSet(NetBoxModelViewSet):
    queryset = AccessList.objects.all()
    serializer_class = AccessListSerializer
    filterset_class = AccessListFilterSet

# api/urls.py
from netbox.api.routers import NetBoxRouter
from . import views

router = NetBoxRouter()
router.register('access-lists', views.AccessListViewSet)
urlpatterns = router.urls
```

API endpoints appear at `/api/plugins/myplugin/access-lists/`.

**Bulk writes (4.7+):** `NetBoxModelViewSet` inherits NetBox's bulk behavior — `?background=true`
on a bulk write to the list endpoint returns `202` with a job ID/URL (validation happens in the
worker, so check the job's status), and a failed bulk create/update returns
`{"detail": ..., "errors": [{"index": N, "errors": {...}}]}` (still all-or-none). Set
`background_enabled = False` on a viewset to reject background requests. Client-side handling is
covered in [netbox-api-integration](../../netbox-api-integration/SKILL.md).

## GraphQL API (Strawberry)

```python
# graphql/types.py
import strawberry_django
from netbox_myplugin.models import AccessList

@strawberry_django.type(AccessList)
class AccessListType:
    id: int
    name: str
    device: 'DeviceType'  # forward reference

# graphql/schema.py
import strawberry
import strawberry_django
from .types import AccessListType

@strawberry.type(name="Query")
class Query:
    access_list: AccessListType = strawberry_django.field()
    access_list_list: list[AccessListType] = strawberry_django.field()
```

Schema is auto-discovered at `graphql.schema`. No manual registration needed.

> **4.5 breaking change:** GraphQL filter syntax now requires lookup modifiers for
> ID and enum fields (e.g., `device_id: {exact: 1}` not `device_id: 1`).

### Extending Core GraphQL Types (4.7+)

Add fields and filters to NetBox's *existing* types so clients traverse your data from a core
object (`device_list { access_lists { … } }`) instead of a separate top-level query. Auto-discovered
from `graphql_extensions.py` (`type_extensions`, `filter_extensions`; override the paths with
`PluginConfig.graphql_type_extensions` / `graphql_filter_extensions`). Requires `min_version = '4.7.0'`.

```python
# graphql_extensions.py — imported while plugins initialize, BEFORE core GraphQL types are built:
# never import dcim.graphql.types etc. at module level; reference core types via strawberry.lazy().
from typing import Annotated
import strawberry
import strawberry_django
from django.db.models import Q
from utilities.querysets import RestrictedPrefetch
from .models import AccessList

@strawberry_django.type(AccessList, fields='__all__')
class AccessListType:
    device: Annotated['DeviceType', strawberry.lazy('dcim.graphql.types')]

@strawberry.type
class DeviceTypeExtension:
    models = ['dcim.device']    # unannotated class attr (or ClassVar); an annotated `models` is rejected

    @strawberry_django.field(
        prefetch_related=lambda info: RestrictedPrefetch(
            'netbox_myplugin_access_lists', info.context.request.user, 'view',
            queryset=AccessList.objects.all(),
        ),
    )
    def access_lists(self) -> list[Annotated['AccessListType', strawberry.lazy('netbox_myplugin.graphql_extensions')]]:
        return self.netbox_myplugin_access_lists.all()    # related_name='%(app_label)s_access_lists'

@strawberry.type
class DeviceFilterExtension:
    models = ['dcim.device']

    @strawberry_django.filter_field()
    def has_access_lists(self, value: bool, prefix) -> Q:
        return Q(**{f'{prefix}netbox_myplugin_access_lists__isnull': not value})

type_extensions = [DeviceTypeExtension]
filter_extensions = [DeviceFilterExtension]
```

Rules: extensions are strictly additive — every name (fields, resolvers, helpers, attributes) must be
new, or NetBox fails at startup naming the classes; always scope related-object resolvers with
`RestrictedPrefetch(..., user, 'view', ...)` because object permissions apply only to the top-level
queryset; extensions are plain mixins (no GraphQL interfaces, no core GraphQL base classes); a target
model that never assembles a GraphQL type is an error.

## Custom Event Rule Actions (4.7+)

Register new `action_type` choices for event rules alongside webhook/script. Auto-discovered from
`event_rules.event_rule_actions` (override with `PluginConfig.event_rule_actions`). Requires
`min_version = '4.7.0'`.

```python
# event_rules.py
from django.utils.translation import gettext_lazy as _
from netbox.event_rules import EventRuleAction
from .models import Ticket

class OpenTicketAction(EventRuleAction):
    slug = 'netbox_myplugin.open_ticket'   # lowercase; letters/digits/underscores/dots — hyphens are rejected
    label = _('Open ticket')
    description = _('Open a ticket in the external ticketing system')
    object_model = Ticket          # model the rule's action_object must be; None = no object may be set
    object_required = True         # only valid together with object_model

    def validate(self, *, action_object, action_data):
        pass                       # optional: raise ValidationError for bad action_data

    def enqueue(self, *, event_rule, event_context, action_object, action_data):
        ...                        # do or schedule the work; log (don't raise) on rule misconfiguration

event_rule_actions = [OpenTicketAction]
```

- One instance serves every rule, request, and worker thread — keep actions stateless (no per-event state on `self`)
- Override `get_object_queryset()` to restrict selectable objects, `object_label` to relabel the field, and `resolve_import_object(value)` to support CSV import of the target object
- If the plugin is later disabled, rules using its action are skipped (not deleted) and flagged; find them with `?action_is_available=false`

## Declarative Layouts & Breadcrumbs (4.6+ / 4.7+)

`ObjectView` subclasses can declare their page with `netbox.ui.layout` (4.6+) instead of a
template. Breadcrumbs (4.7+) are passed to the layout alongside its panels:

```python
from netbox.ui import layout
from netbox.ui.breadcrumbs import Breadcrumb
from netbox.views import generic

class AccessListView(generic.ObjectView):
    queryset = AccessList.objects.all()
    layout = layout.SimpleLayout(
        breadcrumbs=[Breadcrumb('device.site'), Breadcrumb('device')],   # dotted accessor or callable
        left_panels=[...],
        right_panels=[...],
    )
```

- `Breadcrumb(accessor=None, label=None, url=None)` — link defaults to the resolved object's `get_absolute_url()`; a callable `url` receives the object; an accessor resolving to `None` is omitted; an iterable renders one crumb per item (`Breadcrumb(lambda obj: obj.get_ancestors())`)
- Static crumb: `Breadcrumb(label=_('…'), url=reverse_lazy('…'))`; pass `root_breadcrumb=False` to the layout to replace the default list-view crumb
