# Research: Adopt NetBox 4.6 plugin features

Phase 0 of [plan.md](plan.md). Every decision below was checked against the NetBox source in the dev container
(`/workspaces/netbox/netbox`, 4.6.x) and the CI pin (`v4.6.10`). No `NEEDS CLARIFICATION` remains: the maintainer
answered the scope, amend, nested-API, table, description and GraphQL questions (spec Clarifications).

## D1. Detail pages: `layout = SimpleLayout(...)` on the nine `ObjectView`s

**Decision**: every detail view declares `layout = layout.SimpleLayout(left_panels=..., right_panels=...,
bottom_panels=...)`, built from `netbox.ui.panels`, `netbox.ui.attrs` and `netbox.ui.actions`. Panel classes specific
to the plugin live in a new module `netbox_contract/panels.py`. The nine page templates are deleted, with two
exceptions. `contract.html` and `contractline.html` are reduced to their `breadcrumbs` block, which links to the
external party and the contract. The other seven views set `template_name = 'generic/object.html'`.

**Rationale**:
- `generic/object.html` renders `{% for row in layout %}` when the view passes `layout` (`ObjectView.get()`).
- Core views keep a thin template only for extra blocks (for example `circuits/provider.html`).
- `SimpleLayout` appends `PluginContentPanel('left_page' | 'right_page' | 'full_width_page')` to its three columns,
  which gives FR-007 with no code.
- `ui.panels` was added in NetBox 4.5.0, so it is available from the minimum 4.6.0.

**Alternatives considered**:
- Keeping hand-written templates: this is the drift the issue removes.
- A custom `Layout` per page: `SimpleLayout` fits every page, since all of them already have two columns and a full-width
  bottom.

## D2. Attributes hidden by settings and deprecated attributes

**Decision**: `panels.SettingsAttributesPanel(ObjectAttributesPanel)` has a class attribute `hidden_setting` (the
name of the plugin setting: `hidden_contract_fields` or `hidden_invoice_fields`). Its `get_context()` removes the
listed attribute names from the rendered attributes at render time, before calling the parent. Deprecated values
move to their own panels, which render only when `show_deprecated_fields` is on (`should_render`):
- `DeprecatedCostsPanel` on contracts: `mrc`, `yrc`, the calculated recurring value, `nrc`.
- `DeprecatedTemplatePanel` on invoices: the template flag.

The deprecation shows in the panel title ("Deprecated costs"), and the invoice template message moves into the
invoice deprecated panel.

**Rationale**:
- `ObjectAttributesPanel.get_context()` already filters with `only`/`exclude`. Doing it per render keeps the rule that
  plugin settings are read at call time (tests patch `PLUGINS_CONFIG`).
- `ObjectAttribute.render()` gets only `name`, `perms` and `preferences`, so a per-attribute `should_render` would need
  a core change. Filtering in the panel does not.
- Panel and attribute labels are escaped, so the current inline "deprecated" badge cannot be kept on each row. A
  separate panel is clearer than a badge per row.

**Alternatives considered**:
- `ObjectAttribute` subclasses returning `''`: the row label would still show.
- One panel class per setting combination: combinatorial.

## D3. Contract values, lock messages and other computed content

**Decision**:
- **Contract values.** `ContractView.get_extra_context()` keeps returning
  `contract_values([instance])[instance.pk]`. A `TemplatePanel('netbox_contract/panels/contract_values.html')` renders
  the billable flag and the three values from the context. "Not available" is shown for a `None` total.
- **Messages.** These are `TemplatePanel`s with small fragments under `templates/netbox_contract/panels/`. Each
  fragment renders nothing when its condition is false:
  - the locked-lines message (contract);
  - the line lock message (contract line);
  - the posted-invoice message (invoice).
- **Contract line replacement links.** `replaces` uses a `RelatedObjectAttr`. `replaced_by` uses a
  `RelatedObjectListAttr` plus a `TemplatedAttr` for the "from <date>" text.

**Rationale**: `TemplatePanel` passes the full view context (`context.flatten()`), so the fixed-query values computed
once in the view reach the panel (FR-006). The fragments are a few lines each and hold no page structure.

**Alternatives considered**:
- Attaching the values to the instance: hidden coupling.
- A property per value: an N+1 query on lists, which is the reason `contract_values()` exists.

## D4. Related tables: `ObjectsTablePanel` on the list views; per-line contract line actions

**Decision** (clarification 2026-10-02 Q2): every related table becomes
`ObjectsTablePanel(model=..., filters=..., exclude_columns=[<the page's own object column>], actions=[AddObject(...)])`.
These panels load the list view's table over HTMX, with the user's saved columns.

| Page | Table | Filters | Excluded column | Add action |
|---|---|---|---|---|
| Contract | contract lines | `contract_id` | `contract` | `AddContractLine` (hidden when the contract has invoices) |
| Contract | assignments | `contract` | `contract` | none (assignments are added from the object) |
| Contract | child contracts | `parent` | `parent` | none |
| Contract | invoices | `contracts`, `template=False` | `contracts` | `AddObject('netbox_contract.invoice', url_params={'contracts': pk})` |
| Invoice | contracts | `invoice_id` (new filter, D5) | none | none |
| Invoice | invoice lines | `invoice` | `invoice` | `AddObject('netbox_contract.invoiceline', ...)` when not posted |
| Unit | contract lines | `unit_id` | `unit` | none |
| Service provider | contracts | `service_provider_id` | none | none |

The deprecated invoice template lines on the contract page stay a `ContextTablePanel('invoicelines_table')`. That
table is built only when `show_deprecated_fields` is on.

Contract line tables get `ContractLineActionsColumn(ActionsColumn)`. Its `render()`:
- drops `delete` when `record.is_locked()` (the existing lock rule);
- prepends an Amend button when `record.can_be_amended` and the user may amend that line
  (`user.has_perm('netbox_contract.amend_contractline', record)`).

`ContractLineLockedContractTable`, `ContractLineContractTable` and the `AMEND_BUTTON` template string are removed.
`ContractLineListTable` is the only contract line table.

The column must not cost queries per row. `ContractLine.lock_message()` runs up to three queries and `can_be_amended`
runs one (`replaced_by.exists()`). The contract line list view (and its REST viewset) therefore annotates its
queryset once with:
- `is_locked_line = Exists(invoice line referencing it) | Exists(invoice of its contract)`;
- `has_successor = Exists(line replacing it)`.

The column reads these annotations when present and falls back to the model methods otherwise. The query-count
baseline of the contract line list must stay the same or change only by the constant cost of the annotations, with
that reason stated.

**Rationale**:
- `ObjectsTablePanel.should_render()` hides the panel without view permission, which matches today's
  `perms.*.view_*` checks.
- Core `ActionsColumn` checks permissions per model, not per record. Removing an action for one record needs the
  subclass.
- Deleting a locked line is already refused in `ContractLine.delete()`. The column just stops offering it.

**Alternatives considered**: today's fixed tables (clarification answer B); keeping the locked table (answer C).

## D5. New filter `invoice_id` on contracts

**Decision**: add `invoice_id = django_filters.ModelMultipleChoiceFilter(field_name='invoices', queryset=Invoice...)`
to `ContractFilterSet`. It is additive: no existing filter changes.

**Rationale**: the invoice page lists its contracts through the contract list view. No filter on the reverse relation
exists today.

## D6. Amend permission action (clarification Q1)

**Decision**:
- **Model.** `ContractLine.Meta.permissions = [('amend', 'Amend the price or quantity of an invoiced contract line')]`.
  Migration `0050_contractline_amend_permission` (`AlterModelOptions`) records it. `NetBoxFeatureSet.register_models()`
  then registers `ModelAction('amend')` for the ObjectPermission form, and the permission name is
  `netbox_contract.amend_contractline`.
- **UI view.** `ContractLineAmendView.get_required_permission()` returns `'netbox_contract.amend_contractline'`. The
  queryset is restricted with `restrict(user, 'amend')` (object-level constraints). `has_permission()` also requires
  `view_contractline`. The add + change check is removed.
- **REST.** `ContractLineViewSet.get_permissions()` returns `[AmendPermission()]` for the `amend` action. That
  permission is: authenticated, and the token, if any, must be write-enabled. The handler resolves the line from
  `ContractLine.objects.restrict(user, 'view').restrict(user, 'amend')` (404 when not visible) and raises 403 when the
  user has no amend permission at all.
- **Buttons.** `AmendContractLine(ObjectAction)` (`netbox_contract/object_actions.py`) is added to
  `ContractLineView.actions` after the core actions. Its `render()` returns `''` unless `obj.can_be_amended` and
  `user.has_perm('netbox_contract.amend_contractline', obj)`. `contractline_edit.html` uses the same check, through a
  `can_amend` template filter in `templatetags/contract_tags.py`.

**Rationale**:
- This is how core's `DataSource` declares `sync` (`core.sync_datasource`).
- On the REST side, `BaseViewSet.initial()` restricts POST to `add` and `TokenPermissions` maps POST to
  `add_<model>`. A custom action must override both, as the script `run` action does (`extras/api/views.py`).
- `ActionsMixin.get_permitted_actions()` checks permissions per model without the object, so the per-line rule belongs
  in `render()`.

**Alternatives considered**:
- The transition period accepting add + change: rejected in Q1, because no release had Amend.
- `permissions_required = {'amend'}` alone: this is model-level, and would show the button on non-amendable lines.

## D7. REST nested objects: `Serializer(nested=True)` and explicit `brief_fields` (clarification Q2, 2026-10-02 Q1)

**Decision**:
- **Removed classes.** `NestedContractSerializer`, `NestedInvoiceSerializer`, `NestedAccountingDimensionSerializer` and
  `NestedContractLineSerializer` are removed.
- **Replacements.**

  | Field | Becomes |
  |---|---|
  | `contract` (assignments, contract lines) | `ContractSerializer(nested=True)` |
  | `parent` (contracts) | `ContractSerializer(nested=True, required=False, allow_null=True)` |
  | `invoice` (invoice lines) | `InvoiceSerializer(nested=True)` |
  | `accounting_dimensions` | `SerializedPKRelatedField(serializer=AccountingDimensionSerializer, nested=True, ...)` |
  | invoice `contracts` | `SerializedPKRelatedField(serializer=ContractSerializer, nested=True, ...)` |
  | `replaces` | `ContractLineSerializer(nested=True, read_only=True)` |

  The serializers are reordered so that each one is defined before it is used. `ContractSerializer.parent` refers to
  its own class, which needs a small `get_fields()` hook or a lazy field. The plan accepts either.
- **`brief_fields`, declared on every serializer** (see [contracts/rest-api.md](contracts/rest-api.md)):
  - contract: `id, url, display, name, status`;
  - invoice: `id, url, display, number`;
  - accounting dimension: `id, url, display, name, value`;
  - invoice line: `id, url, display, invoice, amount, currency`. Today's set lists `name`, which does not exist on
    invoice lines.
  - The other brief sets are kept.

**Rationale**:
- `BaseModelSerializer.__init__(nested=True)` uses `Meta.brief_fields` and accepts a PK or a dict of attributes on
  write (`get_related_object_by_attrs`, restricted to what the user may view). This is the same behaviour as
  `WritableNestedSerializer` (FR-011).
- The OpenAPI generator (`core/api/schema.py`) names nested components `Brief<Name>`.
- The constitution exception is recorded in the plan's Complexity Tracking.

**Alternatives considered**: additive brief sets with a later shrink (rejected in Q2); shrinking only the 2.5.0-new
serializers.

## D8. GraphQL API

**Decision**: new package `netbox_contract/graphql/` with:
- **`filters.py`**: a `strawberry_django.filter_type` per model. Each one is based on `NetBoxModelFilter`, or on
  `OrganizationalModelFilter` (contract type) or `PrimaryModelFilter` (service provider) after D9. Each filter covers
  the stored fields with core lookups (`StrFilterLookup`, `ComparisonFilterLookup` for amounts and dates, enum lookups
  for choices).
- **`types.py`**: `<Model>Type` per model, matching the naming that `get_graphql_type_for_model` expects
  (`netbox_contract.graphql.types.ContractType`, ...). They are `NetBoxObjectType`, or `OrganizationalObjectType` and
  `PrimaryObjectType` after D9, with `fields='__all__'` and `pagination=True`.
  - Computed values are excluded: they are properties, not model fields, so `fields='__all__'` leaves them out
    (FR-015a).
  - Deprecated fields carry `deprecation_reason` (FR-015). That covers `mrc`, `yrc`, `nrc` and invoice `template`.
  - The type named `ContractType` (for the model `Contract`) collides with the model name `ContractType`. The module
    imports the models as `models`, and the GraphQL type of the contract type model is `ContractTypeType`.
  - The two generic relations become unions resolved with `build_gfk_prefetch`, as `CircuitGroupAssignmentType.member`
    does:
    - `Contract.external_party_object` → `ContractExternalPartyType` = `ServiceProviderType | circuits ProviderType`.
    - `ContractAssignment.content_object` → `ContractAssignmentObjectType` = a union of the seven default
      `supported_models` types (Circuit, VirtualCircuit, Site, Device, Rack, VirtualMachine, Cluster).
    - An object of another model added to `supported_models` resolves to `null`, while `content_type` and `object_id`
      still identify it. This is documented.
- **`schema.py`**: `@strawberry.type class NetBoxContractQuery` with `<name>: <Type> = strawberry_django.field()` and
  `<name>_list: list[<Type>] = strawberry_django.field()` per model. Names follow the default of the core GraphQL tests
  (`contract`, `contract_line`, `invoice`, `invoice_line`, `unit`, `accounting_dimension`, `service_provider`,
  `contract_type`, `contract_assignment`). It also has `schema = [NetBoxContractQuery]`.

NetBox imports `graphql.schema` from the plugin automatically. Permissions come from `BaseObjectType.get_queryset()`
(`restrict(user, 'view')`).

**Rationale**: this is the documented plugin path (`docs/plugins/development/graphql-api.md`). Strawberry needs unions
at schema build time, so the union is static. The settings-driven alternative would change the schema with
configuration.

**Alternatives considered**:
- Building the assignment union from `supported_models` at import: NetBox would need a GraphQL type for any model a
  user lists. A missing type would fail startup.
- Exposing only `content_type`/`object_id`: this fails acceptance scenario 4.4.

## D9. Base classes: `ContractType(OrganizationalModel)`, `ServiceProvider(PrimaryModel)`

**Decision**:
- **`ContractType`** keeps `name` and `color`.
  - It inherits `slug` (unique), `description` (`CharField(200)`), `comments` and `owner`.
  - `slug` is redeclared with `blank=True` so that forms, import and API can omit it (FR-018).
  - `ContractType.clean()` and `save()` set a missing slug to `unique_slug(name, taken)`, where `taken` is the set of slugs
    already used: `slugify(name)`, `contract-type` when that is empty, and `-2`, `-3`, ... until it is not in `taken`. The helper is a small pure function in a new module
    `netbox_contract/text.py`, with no database access (Constitution VI).
- **`ServiceProvider`** keeps `name`, `slug`, `portal_url`, `comments` and its contacts, and inherits `description`
  and `owner`.
- **Forms, filtersets, tables, serializers and GraphQL** switch to the matching `OrganizationalModel*` /
  `PrimaryModel*` base classes. `ContractTypeForm.slug` is `SlugField(required=False)`, prepopulated from `name` by
  core JavaScript.
- **Migrations** (Constitution IV):
  - `0051_contracttype_organizational`:
    1. add `slug` (null), `comments`, `owner`;
    2. `RunPython` with the historical model: fill each empty slug with `unique_slug`, shorten descriptions over 200
       characters (D10), and print a report of slugs made unique and descriptions moved;
    3. alter `slug` to unique and not null, and `description` to `CharField(200)`.

    The reverse migration is a no-op `RunPython` plus the schema reversal. Running it again changes nothing: slugs
    exist, and no description is over 200 characters.
  - `0052_serviceprovider_primary`: add `description` and `owner`.
- **Query counts**: the owner columns are not default columns. The new `owner` select may add a join to the contract
  type and service provider lists. Baselines are re-recorded only if they change, with that reason (Constitution II).

**Rationale**: core base classes bring the owner field and core UI conventions (FR-016, FR-019).

**Alternatives considered**: `ContractType(OrganizationalModel)` with `slug` required everywhere, rejected because
Constitution V forbids a new required input.

## D10. Long contract type descriptions (clarification 2026-10-02 Q3)

**Decision**: `shorten_description(text, limit=200)` (pure, in `netbox_contract/text.py` next to `unique_slug`) returns
`text` when `len(text) <= 200`. Otherwise it cuts at the last space in the first 199 characters (or at 199 when there
is none), right-strips, and appends `…`. The migration:
- sets `description` to the shortened text;
- sets `comments` to the full original text, followed by a blank line and the existing comments when there are any
  (there are none: the field is new in the same migration);
- prints `contract type <name>: description shortened, full text moved to comments`.

**Rationale**: lossless and reported (FR-017), and idempotent, since a second run finds no description over 200.

## D11. Tests

**Decision**: new modules, written first (Constitution II):
- `tests/test_amend_permission.py` (US1);
- `tests/test_detail_layouts.py` (US2; one test per acceptance scenario, using `self.client.get(obj.get_absolute_url())`
  and checking the rendered attributes, panels and HTMX table URLs);
- `tests/test_nested_api.py` (US3);
- `tests/test_graphql.py` (US4, with object-permission cases);
- `tests/test_base_classes.py` (US5, including the migration's helper functions and a migrate-back-and-forward check on
  the data functions).

`tests/test_api.py` moves all nine models to `APIViewTestCases.APIViewTestCase` (GraphQL included). Its `brief_fields`
lists follow [contracts/rest-api.md](contracts/rest-api.md).

Adapted existing tests (SC-006):
- `test_issue_307` (Amend button rule and `NestedContract` schema name);
- `test_amendments` (REST permission);
- `test_locking` (locked table class);
- `test_deprecated` (badges become panels).

**Rationale**: the tests mirror the user stories, so each story can be verified alone.

## D12. Release and documentation

**Decision**: a #309 entry in the unreleased 2.5.0 section of `CHANGELOG.md`, with "Behaviour changes":
- the amend action replaces add + change;
- the nested REST objects are reduced, with every removed field listed per field, invoice `contracts` included;
- `brief=true` sets;
- contract type slug, comments and owner;
- service provider description and owner;
- the GraphQL API and its computed-value and `supported_models` limits.

`docs/` changes:
- `contract_lines.md`: the amend permission;
- `api.md`: brief and nested objects, GraphQL;
- `contract.md` / `index.md`: the contract type and service provider fields.

`README.md` changes only if requirements change. They don't: NetBox 4.6.0 is already the minimum. `CLAUDE.md`
architecture notes are updated for layouts, `panels.py`, the GraphQL package and the amend permission. The translations
are refreshed and translated into French.

**Rationale**: Constitution VII. Two migrations in the same unreleased minor version.
