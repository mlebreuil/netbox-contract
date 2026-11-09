---
name: add-model-field
description: Checklist for adding a field to an existing netbox-contract model (model, migration, validation, serializer, forms, filterset, table, panel, search, GraphQL, locks, tests, docs, specs, changelog). Use when the user asks to add a field or attribute to an existing model.
---

# Add a field to an existing model

A field touches many layers. Work through the list in order. It is a change of behaviour, so tests are written first
and fail before the change (Constitution II), and the field belongs to a specified feature (`specs/NNN-name/`).

## 0. Decide

- **Type and default.** A new required input must not be added to an existing endpoint (Constitution V): make the
  field optional or give it a default that keeps the previous behaviour.
- **Lock.** Is the field frozen once a contract has invoices, or once an invoice is Posted? Locks are in
  `AGENTS.md` ("Locks") and `specs/_global/data-model.md`; if the field is frozen, add it to the lock lists and test
  both the allowed and the refused edit.
- **Hideable or mandatory?** Contract and invoice fields can be listed in `hidden_*_fields` / `mandatory_*_fields`
  (plugin settings). Decide whether the new field takes part; `prune_fieldsets` in `forms.py` applies the settings.
- **Deprecated?** Deprecated fields are hidden unless `show_deprecated_fields` is true (see `remove-model-field`).
- **Choices.** A choice field uses a `ChoiceSet` so `FIELD_CHOICES` can extend it, with `Choice(value, label, color,
  description=_('...'))` entries so the description shows in forms and filters (007).
- **Pointer to any object.** A generic relation uses `GenericObjectChoiceField` + `GenericObjectFormMixin` in the form
  (see `ContractForm.external_party_object`, 004), not two separate fields.
- **FK to a core model.** Use a string reference and a `related_name` unlikely to collide with another plugin's.

## 1. Model and migration (`models.py`, `migrations/`)

Add the field. Rules go in `clean()`; defaults applied in `clean()` are also applied in `save()` (the API validates a
temporary instance). Generate the migration with `makemigrations` (needs `DEVELOPER = True`); never write a schema
migration by hand. If existing rows need a value, add a data migration: lossless, re-runnable, reporting every
judgement call (Constitution IV). Check with `makemigrations netbox_contract --check --dry-run`.

## 2. Validation spanning records

Relations saved after the object (M2M) cannot rely on `clean()`: follow `validators.check_invoice_contracts`, called
from the form, the CSV form, the serializer and `Invoice.clean()` so every entry point enforces it.

## 3. REST API (`api/serializers.py`)

Add the field to `Meta.fields`; to `brief_fields` only if it identifies the object. A brief set may gain a field but
never lose one. Related objects use `Serializer(nested=True)`; a read-only computed field is declared read-only.

## 4. Forms (`forms.py`)

Edit form, filter form, CSV import form, bulk edit form. A field that is in no `fieldsets` section is not rendered:
add it to the right section of each. Add its name to the setting-aware helpers if it can be hidden or mandatory.

## 5. Filterset and table (`filtersets.py`, `tables.py`)

An FK or M2M gets an explicit `<field>_id` filter. Add a table column (not in `default_columns` unless it should be
visible by default). A list that shows a computed value must not query per row (see `with_lock_state()`,
`contract_values()`).

## 6. Detail page, search, GraphQL

- `panels.py`: add the attribute to the model's panel. Settings-aware panels (`SettingsAttributesPanel`) hide the
  field when the settings say so.
- `search.py`: add to the index `fields` if the field should be searchable.
- `graphql/filters.py` and `graphql/types.py`; a choice field also needs its enum in `graphql/enums.py`. Computed
  values are not in GraphQL (stored fields only).

## 7. Tests

- Views: add the field to the `form_data` / `csv_data` / `bulk_edit_data` of the model's case in `tests/test_views.py`.
- API: `create_data` and `bulk_update_data` in `tests/test_api.py`; brief fields if changed.
- Filter, validation, lock and migration behaviour: a test that fails first, citing the requirement
  (`NNN-FR-012`). Migration tests use `MigrationExecutor` in a plain `TestCase`.
- List-view query count changed? Re-record `tests/query_counts.json` serially with `UPDATE_QUERY_COUNTS=1` and state
  the reason (Constitution II). Otherwise leave it alone.

## 8. Documentation, specs, translations, changelog

- `docs/` page of the model; `README.md` if a setting or requirement changed; regenerate affected screenshots with
  `utils/docs_screenshots/make_screenshots.sh`.
- `specs/_global/data-model.md`, `contracts/rest-api.md`, `contracts/graphql.md`, `contracts/ui.md` (and
  `behaviours.md` for rules); then `python3 utils/spec_ids.py check` and, if specs changed,
  `python3 utils/spec_ids.py registry`.
- Run `makemessages -l en -l fr` through NetBox's management command from `netbox_contract/`, then `msgfmt` on the
  plugin's catalogs for new strings.
- `CHANGELOG.md`: Enhancements, plus a bullet under REST API Changes for the model (`netbox_contract.Contract`) listing
  the added field. A change in behaviour for existing users goes under Breaking Changes. Use `draft-changelog`.

## Summary checklist

- [ ] model, migration (`--check` clean) · [ ] serializer · [ ] 4 forms · [ ] filterset · [ ] table · [ ] panel
- [ ] search · [ ] GraphQL · [ ] locks · [ ] tests (fail first) · [ ] query counts · [ ] docs + screenshots
- [ ] `specs/_global/` · [ ] identifier check · [ ] translations · [ ] CHANGELOG · [ ] pre-commit

## Why

The same rule must hold in the UI, bulk edit, CSV import and REST API. Skipping one layer is how a field ends up
editable through the API but not the form, or locked in one and open in another.

## References

`AGENTS.md` ("Where business rules live", "Locks"), constitution II, IV, V, VII, VIII; the
`netbox-plugin-development` skill (`references/model-patterns.md`, `references/forms-tables-filtersets.md`,
`references/views-and-api.md`) for the NetBox API of each layer.
