---
name: add-model
description: Checklist for adding a new model to the netbox-contract plugin with the full NetBox stack (model, migration, forms, filterset, table, views, API, GraphQL, search, navigation, tests, docs, specs). Use when the user asks to add a new model or object type to the plugin.
---

# Add a model to the plugin

Constitution I: every domain model is a `NetBoxModel` with the whole NetBox stack. Adding one touches about fifteen
places; work through them in order, each builds on the previous. A new model is a feature: it needs a
`specs/NNN-name/` (spec, plan, tasks) before code. If none exists, stop and run the Spec Kit sequence first.

Tests come first (Constitution II): write the view, API and GraphQL tests (step 11), see them fail, then implement.

## 0. Decide

- **Base class.** `NetBoxModel` by default. `OrganizationalModel` for a short list of categories with `name` and
  `slug` (see `ContractType`; its slug is derived from the name when empty, `text.unique_slug`). `PrimaryModel` when it
  needs an owner and description (see `ServiceProvider`). The form, filterset, table, serializer and GraphQL bases
  follow the model base class.
- **Choices.** A status or type field uses a `ChoiceSet` in `models.py` so installations can extend it through
  `FIELD_CHOICES`.
- **Choices.** Use `Choice(value, label, color, description=_('...'))` entries, as the existing choice sets do, so the
  option description shows in forms and filters.
- **Relations to core models.** Name the model as a string (`'dcim.Device'`). A new FK to a core model gets a
  `related_name` that cannot collide with another plugin's (NetBox Labs' advice: prefix it with
  `%(app_label)s_`); the plugin's older relations use plain names, so keep the existing ones as they are (renaming
  one changes a reverse accessor that filters and GraphQL may use). A pointer to "any object" is a
  `GenericForeignKey` with `GenericObjectChoiceField` + `GenericObjectFormMixin` in the form (see
  `ContractAssignmentForm`, 004).
- **Custom manager.** If you override the manager, subclass `RestrictedQuerySet` (see `ContractLineQuerySet`) so object
  permissions keep working.
- **Money.** `DecimalField` plus the existing currency code field; no money library, no conversion.
- **Locks and delete guards.** Does a Posted invoice or an invoiced contract freeze it? Record the answer in the plan;
  guards live in the model's `delete()` and are repeated in `signals.py`.

## 1. Model and migration

1. Add the class to `netbox_contract/models.py`. Single-record rules go in `clean()`; a default applied in `clean()`
   must also be applied in `save()`, because the API validates a temporary instance.
2. Migration. `makemigrations` is refused unless NetBox's configuration sets `DEVELOPER = True`. Never write a schema
   migration by hand. Check afterwards with `makemigrations netbox_contract --check --dry-run`.

## 2. Forms (`forms.py`)

Edit form, filter form, CSV import form and bulk edit form. Each declares `fieldsets`: a field in no fieldset is not
rendered. FK fields use `selector=True` where NetBox offers it.

## 3. Filterset, table (`filtersets.py`, `tables.py`)

- `@register_filterset` on the filterset; an FK needs an explicit `<field>_id = ModelMultipleChoiceFilter(...)`, do not
  rely on `Meta.fields`.
- The table subclasses `NetBoxTable`, with `default_columns`.

## 4. Views and detail page (`views.py`, `panels.py`)

- Register every view with `register_model_view`: detail, `list` (`path=''`, `detail=False`), `add` and `edit`
  (one class), `delete`, `bulk_import` (`path='import'`), `bulk_edit` (`path='edit'`), `bulk_delete`
  (`path='delete'`); the last four with `detail=False`. Copy `AccountingDimension` in `views.py` as the pattern.
- The detail view declares `layout = SimpleLayout(...)` with panels from `panels.py`. Do not add a template unless a
  page needs breadcrumbs; templates live under `templates/netbox_contract/`, never at the root of `templates/`.
- `urls.py` lists the model in its tuple of model names; it includes `get_model_urls` and nothing else per model.
- Route names are pinned by `tests/test_conventions.py`: add the new routes to `ROUTES`.

## 5. Permissions and navigation

- A menu entry and its buttons declare the permission they need (`navigation.py`, `PluginMenuItem`).
- A custom action (like `amend`) is a `Meta.permissions` entry, checked per object.

## 6. REST API (`api/`)

- `NetBoxModelSerializer` with `url`, `display`, `Meta.brief_fields`; related objects use `Serializer(nested=True)`.
  `validate()` returns at once when `self.nested`.
- Viewset in `api/views.py`, route in `api/urls.py` (`router.register`).
- Brief sets may gain fields but never lose one (Constitution V).

## 7. GraphQL (`graphql/`)

Filter in `filters.py`, type in `types.py` (list it in `__all__`), the two query fields in `schema.py`
(`<name>` and `<name>_list`). A choice field needs an enum in `enums.py`.

## 8. Search

A `SearchIndex` subclass in `search.py`, added to the `indexes` list at the bottom of the file.

## 9. Documentation and translations

- `docs/<model>.md` and an entry in `mkdocs.yml`; `docs/permissions.md` if there is a new permission action.
- Screenshots are generated, never taken by hand: add a `SHOTS` entry in `utils/docs_screenshots/capture.py` (and seed
  data if needed), then run `utils/docs_screenshots/make_screenshots.sh <name>` and look at the images.
- New user-facing strings use `gettext`; run `makemessages -l en -l fr` and `msgfmt` (see `AGENTS.md`).

## 10. Specifications and changelog

- Update the `specs/_global/` documents the plan lists, in the same pull request: `data-model.md`,
  `contracts/rest-api.md`, `contracts/graphql.md`, `contracts/ui.md`, `contracts/routes.md`, `behaviours.md`.
- Cite the requirement next to the rule in code and tests with its qualified identifier (`NNN-FR-012`).
- `CHANGELOG.md`: a `##### Title` under New Features, and the new endpoints and model under REST API Changes.
  Use `draft-changelog`.
- Run `python utils/spec_ids.py check`; if the specs changed, `python utils/spec_ids.py registry` and commit the
  result (CI fails on a stale `registry.md`).

## 11. Tests

- `tests/test_views.py`: a `ModelViewTestCase` + `ViewTestCases.PrimaryObjectViewTestCase` class.
- `tests/test_api.py`: `APITestCase` + `APIViewTestCases.APIViewTestCase` (covers REST and GraphQL), with
  `brief_fields`.
- `tests/test_graphql.py` for what the generic cases do not reach.
- A model method or rule gets its own test module; pure calculations go in `calculations.py` and are tested without
  the database.
- List views are covered by the query-count baseline: record the new entry serially with
  `UPDATE_QUERY_COUNTS=1 ...` (see `run-tests`) and state why in the commit.

## Gotchas

- `tests/helpers.py` factories default to Posted invoices, which are locked.
- Do not name a file like a standard module in `utils/docs_screenshots/` (it is put on `PYTHONPATH`).
- A new runtime dependency needs a justification in the plan (Constitution VI).

## Why

The same rules must hold in the UI, bulk edit, CSV import and the REST API, so they live in the model; and a model
missing one layer (no bulk import, no brief fields) is the kind of gap users find first.

## References

- `AGENTS.md`, `.specify/memory/constitution.md` (I, II, IV, V, VII, VIII), `specs/_global/CONVENTIONS.md`.
- The `netbox-plugin-development` skill for the NetBox API details: `references/model-patterns.md` (base classes,
  mixins, choices, migrations), `references/forms-tables-filtersets.md`, `references/views-and-api.md`
  (views, serializers, GraphQL, layouts).
- NetBox's [plugin development](https://netboxlabs.com/docs/netbox/en/stable/plugins/development/) guide.
