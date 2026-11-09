---
name: remove-model
description: Checklist for deprecating and then removing a netbox-contract model (tests, docs, navigation, search, GraphQL, REST, views, forms, filterset, table, model, migration, specs, changelog). Use when the user asks to remove, delete or deprecate a model or object type.
---

# Deprecate, then remove, a model

Removing a model deletes users' rows when the migration runs, and a deleted table does not come back. Constitution IV:
the model is first deprecated and documented in the changelog for at least one released version, and the removal is
itself a specified feature. **Confirm with the user before running `makemigrations`** and again before the release.

## Step 0: which step are we in?

| State | Do |
|---|---|
| Not deprecated yet | **Part A** only; the removal is a later release. |
| Deprecated in a released version, removal specified in `specs/NNN-*` | **Part B**. |
| Anything else | Stop and say which condition of Constitution IV is missing. |

Identify before starting: the model's relations (FKs and M2Ms from other models, `ContractAssignment` targets), delete
guards in `models.py` / `signals.py` that mention it, data worth converting, and what replaces it.

## Part A: deprecate

1. A `specs/NNN-*` feature that says what replaces the model and how the data moves.
2. Provide the conversion if the data should survive: idempotent, lossless, reporting every judgement call, in a
   data migration and a management command (see `conversion.py`, `convert_contract_lines`).
3. Hide the UI entry unless `show_deprecated_fields` is true (navigation, panels, forms that reference it); keep REST
   and GraphQL working.
4. `CHANGELOG.md` Deprecations; `docs/`; `specs/_global/` marked deprecated; tests for hidden-by-default and for the
   conversion.

## Part B: remove (consumers before provider)

1. Tests and the query-count entry in `tests/query_counts.json` (re-record serially, with the reason).
2. Docs page, `mkdocs.yml` entry, screenshots, `specs/_global/` (retire requirements with `Retired: ...`, never delete
   an identifier).
3. Navigation (`navigation.py`: menu item and buttons), search index (`search.py`).
4. GraphQL: `schema.py`, `types.py`, `filters.py`, `enums.py`; remove relation fields on other types.
5. REST: serializer, viewset, `api/urls.py` route; relation fields on other serializers (public interface: list
   them in the changelog).
6. Views (`register_model_view` classes), `urls.py` tuple, `tests/test_conventions.py` `ROUTES`, panels, templates.
7. Forms (edit, filter, import, bulk edit) and the fields other forms have for it, filterset, table.
8. Choices used only by this model; delete guards and signals that mention it.
9. The model and the migration: `makemigrations` (needs `DEVELOPER = True`); read it; `--check` clean. Relations from
   other models are removed in the same migration or an earlier one.
10. `python3 utils/spec_ids.py check`, `python3 utils/spec_ids.py registry` if specs changed,
    translations, pre-commit's Ruff hook, full test suite.
11. Changelog: Breaking Changes, REST API Changes (removed endpoints), major version (Constitution VII).

## Why

Order matters: removing the provider first breaks imports in every consumer and leaves a half-working tree. The
deprecation gate exists because the models hold financial records.

## References

`add-model` (reverse of its list), `remove-model-field`, constitution IV, V, VII.
