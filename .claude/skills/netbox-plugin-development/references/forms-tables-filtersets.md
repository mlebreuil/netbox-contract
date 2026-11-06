# Forms, Tables & FilterSets

## Form Types

| Class | Purpose | When to Use |
|-------|---------|-------------|
| `NetBoxModelForm` | Create/edit single object | Standard CRUD form |
| `NetBoxModelBulkEditForm` | Edit multiple objects | Bulk edit view |
| `NetBoxModelFilterSetForm` | Filter sidebar in list views | Paired with filterset |
| `NetBoxModelImportForm` | CSV import | Bulk import view |

## NetBoxModelForm — Full Example

```python
from netbox.forms import NetBoxModelForm
from utilities.forms.fields import (
    DynamicModelChoiceField, DynamicModelMultipleChoiceField, CommentField
)
from utilities.forms.rendering import FieldSet
from dcim.models import Device, Region
from .models import AccessList

class AccessListForm(NetBoxModelForm):
    device = DynamicModelChoiceField(
        queryset=Device.objects.all(),
        # query_params filters the API dropdown dynamically
        query_params={'region_id': '$region'},
    )
    region = DynamicModelChoiceField(
        queryset=Region.objects.all(),
        required=False,
        initial_params={'devices': '$device'},  # auto-select based on device
    )
    comments = CommentField()

    fieldsets = (
        FieldSet('name', 'device', 'region', 'type', name='Access List'),
        FieldSet('tags', name='Tags'),
    )

    class Meta:
        model = AccessList
        fields = ('name', 'device', 'type', 'comments', 'tags')
```

**Key fields:**
- `DynamicModelChoiceField` — AJAX-powered dropdown with `query_params` for cascading filters
- `DynamicModelMultipleChoiceField` — same, for M2M relationships
- `CommentField` — markdown-enabled comment textarea
- `$field_name` in `query_params` — references another form field's value dynamically

## Bulk Edit Form

```python
from netbox.forms import NetBoxModelBulkEditForm
from utilities.forms import add_blank_choice

class AccessListBulkEditForm(NetBoxModelBulkEditForm):
    model = AccessList
    type = forms.ChoiceField(
        choices=add_blank_choice(AccessListTypeChoices),
        required=False,
    )
    device = DynamicModelChoiceField(
        queryset=Device.objects.all(),
        required=False,
    )

    nullable_fields = ('description',)  # fields that can be set to null in bulk
```

## Import Form (CSV)

```python
from netbox.forms import NetBoxModelImportForm
from utilities.forms.fields import CSVModelChoiceField, CSVChoiceField

class AccessListImportForm(NetBoxModelImportForm):
    device = CSVModelChoiceField(
        queryset=Device.objects.all(),
        to_field_name='name',  # match by name in CSV, not PK
    )
    type = CSVChoiceField(choices=AccessListTypeChoices)

    class Meta:
        model = AccessList
        fields = ('name', 'device', 'type')
```

## Filter Set Form

```python
from netbox.forms import NetBoxModelFilterSetForm
from utilities.forms.fields import DynamicModelMultipleChoiceField, TagFilterField

class AccessListFilterForm(NetBoxModelFilterSetForm):
    model = AccessList
    device_id = DynamicModelMultipleChoiceField(
        queryset=Device.objects.all(),
        required=False,
        label='Device',
    )
    type = forms.MultipleChoiceField(
        choices=AccessListTypeChoices,
        required=False,
    )
    tag = TagFilterField(AccessList)
```

## Generic Object Fields (4.7+)

`GenericObjectChoiceField` renders a generic foreign key (content type + object) as one
API-backed field; `GenericObjectFormMixin` seeds it from the instance and writes the cleaned
object back to the GFK descriptor in `clean()`. Requires `min_version = '4.7.0'`.

```python
from django.contrib.contenttypes.models import ContentType
from netbox.forms import NetBoxModelForm
from utilities.forms.fields import GenericObjectChoiceField
from utilities.forms.mixins import GenericObjectFormMixin
from utilities.forms.rendering import FieldSet

class AttachmentForm(GenericObjectFormMixin, NetBoxModelForm):
    assigned_object = GenericObjectChoiceField(          # name of the model's GFK descriptor
        content_type_queryset=ContentType.objects.filter(app_label='dcim', model__in=['device', 'rack']),
        label='Assigned object',
        # gfk_name='...' if the form field name differs from the descriptor; selector=True for the modal
    )
    fieldsets = (FieldSet('name', 'assigned_object', 'tags', name='Attachment'),)

    class Meta:
        model = Attachment
        fields = ('name', 'tags')      # the GFK is assigned by the mixin, not by ModelForm
```

## Static Choice Descriptions (4.7+)

`utilities.forms.fields.ChoiceField` / `MultipleChoiceField` render a description under each option
when the `ChoiceSet` uses `Choice(value, label, color=None, description=None)` (see
[model-patterns](model-patterns.md#choices-pattern)); pass `show_descriptions=False` to suppress.

## Tables — NetBoxTable

```python
import django_tables2 as tables
from netbox.tables import NetBoxTable, columns

class AccessListTable(NetBoxTable):
    name = tables.Column(linkify=True)    # clickable link to detail view (no LinkColumn in netbox.tables.columns)
    device = tables.Column(linkify=True)  # clickable FK
    type = columns.ChoiceFieldColumn()    # colored badge for choices
    tags = columns.TagColumn()
    actions = columns.ActionsColumn()     # edit/delete buttons

    class Meta(NetBoxTable.Meta):
        model = AccessList
        fields = ('pk', 'name', 'device', 'type', 'tags', 'actions')
        default_columns = ('name', 'device', 'type')
```

**Available columns** (`netbox.tables.columns`): `ChoiceFieldColumn`, `TagColumn`,
`BooleanColumn`, `ColorColumn`, `TemplateColumn`, `ActionsColumn`, `ArrayColumn` (4.4+),
`MPTTColumn` for hierarchies (on 4.7 an alias of `TreeColumn`; alias removed in 5.0).
Links are `tables.Column(linkify=True)` — there is no `LinkColumn`.

> **NetBox 4.7+** ships django-tables2 v3: in custom table templates `{% querystring %}` (from
> `{% load django_tables2 %}`) is now `{% querystring_replace %}`, and `RelatedLinkColumn` is
> removed (use `tables.Column(linkify=True)`).

## FilterSets — NetBoxModelFilterSet

```python
import django_filters
from netbox.filtersets import NetBoxModelFilterSet
from utilities.filters import register_filterset
from dcim.models import Device
from .models import AccessList

@register_filterset  # Required in 4.5+ for UI lookup modifiers
class AccessListFilterSet(NetBoxModelFilterSet):
    device_id = django_filters.ModelMultipleChoiceFilter(
        queryset=Device.objects.all(),
        label='Device (ID)',
    )
    device = django_filters.ModelMultipleChoiceFilter(
        field_name='device__name',
        queryset=Device.objects.all(),
        to_field_name='name',
        label='Device (name)',
    )

    class Meta:
        model = AccessList
        fields = ('name', 'type')

    def search(self, queryset, name, value):
        """Handles the ?q= parameter. Without this, search won't work."""
        if not value.strip():
            return queryset
        return queryset.filter(
            models.Q(name__icontains=value) |
            models.Q(description__icontains=value)
        )
```

**Tenancy mixin:** If your model has tenant/tenant_group FKs, add `TenancyFilterSet`:
```python
from tenancy.filtersets import TenancyFilterSet

class AccessListFilterSet(TenancyFilterSet, NetBoxModelFilterSet):
    ...
```
