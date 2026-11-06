---
name: remove-model-field
description: Checklist for deprecating and then removing a field of a netbox-contract model without breaking users (deprecation release, then removal across serializer, forms, filterset, table, panel, GraphQL, migration, docs, specs, changelog). Use when the user asks to remove, delete or deprecate a model field.
---

# Deprecate, then remove, a model field

Constitution IV and V: a field is never removed in the release that announces it. It is first **deprecated** and
documented in the changelog for at least one released version, and the removal is itself a specified feature. Existing
user data is never altered, converted or deleted silently.

## Step 0: which step are we in?

Read `CHANGELOG.md` (Deprecations) and `specs/_global/data-model.md`.

| State | Do |
|---|---|
| Field not deprecated yet | Do **Part A** only. Tell the user the removal is a later release. |
| Deprecated in a released version, removal specified (`specs/NNN-*`) | Do **Part B**. |
| Deprecated, but no released version yet, or no spec | Stop. The gate of Constitution IV is not met; say what is missing. |

If the data of the field is worth keeping, the deprecation release should convert it first (as `conversion.py` does
for the legacy cost fields: idempotent, reporting every judgement call) and Part B removes what is left.

## Part A: deprecate

1. Specify it: a `specs/NNN-*` feature whose spec states what replaces the field.
2. Keep the field, its column, REST field and import column working. Hide it from the UI unless the
   `show_deprecated_fields` plugin setting is true: `prune_fieldsets` in `forms.py` and the settings-aware panels in
   `panels.py` already do this for deprecated fields; add the field to their deprecated list.
3. `CHANGELOG.md`: an entry under **Deprecations** saying what is deprecated and what replaces it. A REST field to be
   removed is listed there and in `docs/api.md`.
4. Docs and `specs/_global/` (`data-model.md`, `contracts/rest-api.md`) mark the field deprecated.
5. Tests: the field is hidden by default, shown with `show_deprecated_fields`, and still accepted and returned by
   the API (`tests/test_deprecated.py` is the pattern).

## Part B: remove (outer consumers first)

Remove from the outside in, so imports never break midway.

1. **Tests**: delete tests of the field; keep a test that the migration runs on data that has the field.
2. **Docs**: `docs/`, `README.md`, screenshots (regenerate), `specs/_global/` (a removed requirement is kept as a
   `Retired: NNN-FR-009 (reason, date)` line, never deleted).
3. **GraphQL**: `graphql/types.py`, `graphql/filters.py`, enum if any.
4. **REST**: `api/serializers.py` (`Meta.fields`, and `brief_fields` only after the brief-set deprecation, see
   `docs/api.md`).
5. **Forms**: filter, bulk edit, CSV import (an import column is public: decide whether an old CSV that still has the
   column is rejected or ignored, and record it), edit form `fieldsets`.
6. **Filterset, table, panel, search index.**
7. **Plugin settings**: `mandatory_*_fields` and `hidden_*_fields` may still name the field. Keep accepting the name
   (ignored, as the `external_party_object_type` alias is) so a configuration does not break on upgrade; record it.
8. **Model and migration**: remove the field, run `makemigrations` (needs `DEVELOPER = True`), read the generated
   migration, and check `--check` is clean. If another migration or the conversion code references the field, keep
   the historical model access it needs.
9. `python utils/spec_ids.py check`; `registry` if specs changed; translations; `ruff check`.
10. **Changelog**: Breaking Changes (what users must do), and the removed field under the model's bullet in REST API
    Changes. Version bump is major only for a removal in the public interfaces (Constitution VII).

## Why

Integrations and scripts written by users break first when a field moves (Constitution V); the deprecation release
is the only warning they get.

## References

`AGENTS.md` ("Legacy/deprecated data"), constitution IV, V, VII, VIII; `add-model-field` for the touch points.
