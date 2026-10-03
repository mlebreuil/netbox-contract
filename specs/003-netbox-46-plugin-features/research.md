# Research: Adopt NetBox 4.6 plugin features

Phase 0 of [plan.md](plan.md). Every decision below was checked against the NetBox source in the dev container
(`/workspaces/netbox/netbox`, 4.6.x) and the CI pin (`v4.6.10`). No `NEEDS CLARIFICATION` remains: the maintainer
answered the scope, amend, nested-API, table, description and GraphQL questions (spec Clarifications).

## D1. Detail pages: `layout = SimpleLayout(...)` on the nine `ObjectView`s

**Decision**: every detail view declares `layout = layout.SimpleLayout(left_panels=..., right_panels=...,
bottom_panels=...)`, built from `netbox.ui.panels`, `netbox.ui.attrs` and `netbox.ui.actions`. Panel classes specific
to the plugin live in a new module `netbox_contract/panels.py`. The nine page templates are deleted, with four
exceptions. `contract.html`, `contractline.html`, `invoice.html` and `invoiceline.html` are reduced to their
`breadcrumbs` block (external party, contract, contracts of the invoice, invoice). The other five views set
`template_name = 'generic/object.html'`.

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
runs one (`replaced_by.exists()`). The contract line list view therefore annotates its queryset once (`ContractLine.objects.with_lock_state()`) with:
- `is_locked_line = Exists(invoice line referencing it) | Exists(invoice of its contract)`;
- `has_successor = Exists(line replacing it)`.

The column reads these annotations when present and falls back to the model methods otherwise. The query-count
baseline of the contract line list must stay the same or change only by the constant cost of the annotations, with
that reason stated. The REST viewset is not annotated, because no REST output reads the lock state (implementation
note, T005). The baseline did not change.

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
  `ContractLineView.actions` after the core actions. It declares `permissions_required = {'amend'}`, so
  `get_permitted_actions()` drops it for users without any amend permission (Constitution: buttons declare their
  permission). Its `render()` also returns `''` unless `obj.can_be_amended` and
  `user.has_perm('netbox_contract.amend_contractline', obj)` (object-level). `contractline_edit.html` uses the same check, through a
  `can_amend` template filter in `templatetags/contract_tags.py`.

**Rationale**:
- This is how core's `DataSource` declares `sync` (`core.sync_datasource`).
- On the REST side, `BaseViewSet.initial()` restricts POST to `add` and `TokenPermissions` maps POST to
  `add_<model>`. A custom action must override both, as the script `run` action does (`extras/api/views.py`).
- `ActionsMixin.get_permitted_actions()` checks permissions per model without the object, so the per-line rule belongs
  in `render()`.

**Alternatives considered**:
- The transition period accepting add + change: rejected in Q1, because no release had Amend.
- `permissions_required = {'amend'}` alone: this is model-level, and would show the button on non-amendable lines and
  on lines outside the constraints. It is used together with the `render()` check.

## D7. REST nested objects: the brief mechanism where output is identical; the nested contract kept and deprecated (analysis remediation 2026-10-02)

**Decision**: 2.5.0 removes no REST field. The clarification answers Q2 (2026-10-01) and Q1 (2026-10-02) are
superseded: removing fields conflicted with Constitution IV/V and VII.

- **Switched now, with identical output:**
  - `NestedInvoiceSerializer` → `InvoiceSerializer(nested=True, fields=('id', 'url', 'display', 'number'))`. An explicit
    `fields=` keeps today's four fields without shrinking the invoice `brief=true` set.
  - `NestedAccountingDimensionSerializer` → `SerializedPKRelatedField(serializer=AccountingDimensionSerializer,
    nested=True, ...)`. The brief set is the same five fields.
  - `NestedContractLineSerializer` → `ContractLineSerializer(nested=True, read_only=True)`. `replaces` is new in 2.5.0,
    so it is free to change.
- **Kept**: `NestedContractSerializer`, for assignment `contract`, line `contract` and contract `parent`.
  `ContractSerializer(nested=True, fields=<the same 24 names>)` would not be identical, because `ContractSerializer`
  declares `contract_type` as a nested object while the nested serializer returns its id. The class gets a docstring
  "Deprecated: replaced by the brief contract (`ContractSerializer(nested=True)`) in the release that removes the
  fields listed in docs/api.md", and its deprecated fields get help texts.
- **Kept**: invoice `contracts` stays `SerializedPKRelatedField(serializer=ContractSerializer)` (full contracts).
- **`brief_fields`, declared on all nine serializers** (see [contracts/rest-api.md](contracts/rest-api.md)):
  - existing sets are kept;
  - the invoice line drops its invalid `name` (ignored today) and gains `id` and `currency`;
  - the contract line gains `start_date` and `end_date`;
  - the contract type gains `slug`, and the service provider gains `description` (US5).
- **Deprecations** (FR-012a): the per-field list of contracts/rest-api.md goes under "Deprecations" in the changelog
  entry and into `docs/api.md`. The shrink is a later specified feature, which the maintainer named 2.6.0. Constitution
  VII requires a major version for removals, so that feature must ship as 3.0.0 or amend VII first. This is recorded
  in the spec assumptions.

**Rationale**:
- `BaseModelSerializer(nested=True)` accepts a PK or an attributes dict on write, restricted to what the user may view,
  as `WritableNestedSerializer` does (FR-011).
- `fields=` overrides `brief_fields` for one usage, so exact output is kept where the brief set differs.
- The OpenAPI generator names nested components `Brief<Name>`, so the three components keep the properties of the
  ones they replace. On the pinned NetBox 4.6.10 this includes `BriefAccountingDimension` (netbox#22989). Earlier 4.6
  releases document the accounting dimension lists with the `AccountingDimension` component (implementation note, T044,
  corrected after the CI run).

**Alternatives considered**:
- Shrinking in 2.5.0: blocked by `/speckit-analyze` (C1, C2).
- `ContractSerializer(nested=True, fields=...)` for contracts: changes the type of `contract_type`.
- A `NestedContractCompatSerializer` subclass that overrides `contract_type`: it is the same hand-written serializer
  under another name, so it gains nothing.

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

    Running it again changes nothing: slugs exist, and no description is over 200 characters.

    The reverse is lossless for the moved descriptions (spec US5-7). Django reverses the operations in reverse order,
    so `description` is back to `TextField` before the reverse `RunPython`
    (`restore_descriptions(apps, schema_editor)`) runs. For each type whose `comments` is longer than 200 characters
    and gives back its `description` through `shorten_description(comments)`, the reverse sets
    `description = comments`. Only then are `comments`, `owner` and `slug` dropped. Comments typed by users after the
    upgrade are lost on reverse, like any column a reverse migration drops; the migration docstring says so.
    Migrating forward again shortens and moves the text again.

    The data functions are thin wrappers around pure helpers in `text.py` (`plan_contract_type_changes(rows, taken)`
    returns the slug and description changes plus the report lines). The helpers are tested directly, and the
    migration is tested end to end with `MigrationExecutor` (migrate to 0050, create rows with the historical model,
    migrate to 0051, back to 0050, then forward again).
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
- `test_issue_307` (Amend button rule; the `NestedContract` schema name is kept, so only the button rule changes);
- `test_amendments` (REST permission);
- `test_locking` (locked table class);
- `test_deprecated` (badges become panels).

**Rationale**: the tests mirror the user stories, so each story can be verified alone.

## D12. Release and documentation

**Decision**: a #309 entry in the unreleased 2.5.0 section of `CHANGELOG.md`, with "Behaviour changes":
- the amend action replaces add + change;
- the nested invoice, accounting dimension and contract line serializers move to NetBox's brief mechanism with
  identical output, and their OpenAPI components are renamed `Brief*`;
- `brief=true` additions and the removal of the invalid invoice line `name` declaration;
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

A "Deprecations" list in the same entry gives the per-field list of contracts/rest-api.md (nested contract,
invoice `contracts`, contract and invoice `brief=true`) to be removed by a later specified release.

**Rationale**: Constitution VII. 2.5.0 removes no field, so a minor version fits. Its migrations ship in the same
unreleased minor version.
