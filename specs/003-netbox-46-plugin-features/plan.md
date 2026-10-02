# Implementation Plan: Adopt NetBox 4.6 plugin features

**Branch**: `309-adopt-netbox-4-6-plugin-features` | **Date**: 2026-10-02 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/003-netbox-46-plugin-features/spec.md` (GitHub issue #309)

## Summary

This feature adopts the NetBox 4.6 plugin features in the unreleased 2.5.0, as a #309 entry with three migrations.

- **Amend permission.** Amending moves from add + change to a custom `amend` permission action on contract lines. It
  is checked per line in the UI view, the REST action (which must override the POST → add mapping), an `ObjectAction`
  and a per-line table actions column.
- **Detail pages.** The nine detail pages are rebuilt with `SimpleLayout` and core panels:
  - settings-aware attribute panels;
  - a values panel fed by `contract_values()`;
  - the list views' tables through `ObjectsTablePanel`.

  The page templates go, except two breadcrumb-only stubs.
- **REST.** The four hand-written nested serializers are replaced by `nested=True` with explicit `brief_fields`.
  Every nested contract shrinks to five fields; this was accepted by the maintainer as an exception to Constitution
  IV/V.
- **GraphQL.** A schema covers the nine models: stored fields only, and static unions for the two generic relations.
- **Base classes.** Contract types become `OrganizationalModel` and service providers become `PrimaryModel`. A
  lossless, reported data migration fills the slugs and shortens long descriptions.

Details: [research.md](research.md) (D1-D12), [data-model.md](data-model.md), [contracts/](contracts/),
[quickstart.md](quickstart.md).

## Technical Context

**Language/Version**: Python 3.12 or newer (CI matrix 3.12, 3.13, 3.14)

**Primary Dependencies**:
- NetBox 4.6: `min_version = '4.6.0'`, CI pinned to `v4.6.10`.
- From NetBox: `netbox.ui` (4.5+), `netbox.object_actions` (4.4+), `Meta.permissions` model actions (4.6.0), and
  strawberry / strawberry-django as shipped with NetBox.
- No new dependency.

**Storage**: PostgreSQL through the Django ORM. Migrations 0050 (permission), 0051 (contract type schema + data) and
0052 (service provider schema).

**Testing**:
- The NetBox test runner, with five new modules (D11).
- `test_api.py` moves to `APIViewTestCases.APIViewTestCase` for the nine models (REST + GraphQL).
- Four existing modules are adapted (SC-006).
- ruff.

**Target Platform**: NetBox plugin on Linux servers (self-hosted NetBox 4.6)

**Project Type**: NetBox plugin (Django app, web UI, REST and GraphQL APIs)

**Performance Goals**:
- The contract page computes its values in a fixed number of queries (FR-006).
- The contract line list adds no per-row query for its actions column (annotations, D4).
- GraphQL lists add no per-object query for generic relations (`build_gfk_prefetch`).
- The other list query-count baselines are unchanged, unless the owner join changes them; any change gets a stated
  reason.

**Constraints**:
- Existing route names and page addresses are kept (FR-022), and so are the plugin settings and import columns.
- Contract type creation never requires a slug (FR-018).
- Migrations are lossless and re-runnable (FR-017).
- No API announced for removal in 4.7 is used. The legacy action sets mentioned in `ActionsMixin` are not used.

**Scale/Scope**:
- 9 models.
- Files touched: `models.py`, `views.py`, `tables.py`, `forms.py`, `filtersets.py`, `api/serializers.py`,
  `api/views.py`, `search.py` (contract type description), `templates/netbox_contract/*` (9 page templates
  removed/reduced, 6 panel fragments added), `contractline_edit.html`, `locale/*`, `docs/`, `CHANGELOG.md`,
  `CLAUDE.md`.
- New modules: `panels.py`, `object_actions.py`, `text.py`, `templatetags/contract_tags.py`,
  `graphql/{__init__,filters,types,schema}.py`.
- 3 migrations and 5 test modules.

## Constitution Check

Checked against `.specify/memory/constitution.md` version 1.0.0 (Principles I-VII), before Phase 0 and again after
Phase 1:

| Principle | Status | Evidence |
|---|---|---|
| I. NetBox-native plugin | Met | Core layouts and panels (D1-D4), `ObjectAction` and model actions (D6), `nested=True` serializers (D7), the documented plugin GraphQL path (D8), core base classes (D9). Every API exists in 4.6.0, and none is announced for removal |
| II. Tested behaviour | Met | Five story test modules written first, plus `APIViewTestCase` for nine models. The quickstart scenario map covers every acceptance scenario and edge case. Query-count changes are re-recorded only with a reason |
| III. Lint-clean | Met | `ruff check` after each story; no rule disabled |
| IV. Data safety and migrations | **Exception** (REST field removal, see Complexity Tracking). Met for data | 0051 is lossless (long descriptions moved to comments) and reported, and its data step is idempotent. `makemigrations --check` is clean. No stored value changes except the reported description shortening, which keeps the full text |
| V. Backward-compatible interfaces | **Exception** (nested and brief fields removed without a deprecation release, see Complexity Tracking). Met otherwise | No new required input (the slug is optional, FR-018). Filters, settings, import columns and routes are kept. Writes by id or attributes are unchanged |
| VI. Simplicity | Met | No dependency. Removes about 700 template lines and 4 serializers. The plugin-specific code is small subclasses of core classes plus one pure helper module (`text.py`) |
| VII. Documented change | Met | CHANGELOG 2.5.0 #309 entry with "Behaviour changes" (every removed REST field listed), `docs/` pages for amend, API and models, `CLAUDE.md` updated. README unchanged: requirements are unchanged |

Re-check after design: the only violations are the two recorded below. Both were accepted by the maintainer in
clarification Q2 (2026-10-01) and Q1 (2026-10-02).

## Decisions taken with the maintainer

1. **Amend action only**, with no add + change transition, because Amend was never released (Q1, D6).
2. **Shrink the nested REST objects now**, invoice `contracts` included, with the constitution exception recorded
   (Q2 and 2026-10-02 Q1, D7).
3. **GraphQL and base classes in scope** (Q3, D8, D9).
4. **The list views' configurable tables** on detail pages, with per-line contract line actions (2026-10-02 Q2, D4).
5. **Long contract type descriptions** cut at a word boundary with "…", with the full text moved to comments
   (2026-10-02 Q3, D10).
6. **GraphQL exposes stored fields only** (2026-10-02 Q4, D8).

Points to watch during implementation:
- **REST amend action.** `BaseViewSet.initial()` has already restricted the queryset to `add` and `TokenPermissions`
  requires `add_contractline` before the handler runs. Override `get_permissions()` for the action and rebuild the
  queryset from the model manager (as `ScriptViewSet.run` does). Write the "add + change but not amend → 403" test
  first.
- **`ObjectsTablePanel` loads the list view through HTMX.** Detail page tests must assert the panel's `hx-get` URL
  and its filters, then call that URL to check the rows. Test the excluded columns and the per-line actions on the
  list response.
- **`ContractSerializer.parent` refers to `ContractSerializer`.** Define it after the class body (for example in
  `get_fields()`), or the class is not yet defined.
- **The GraphQL type for the model `Contract` is named `ContractType`.** It clashes with the plugin's `ContractType`
  model inside `types.py`, so import models as a module (`from .. import models`).
- **`fields='__all__'` on GraphQL types must not pick up the deprecated `calculated_rc`.** It is an annotation, not a
  field, so it is not a risk. `mrc`/`yrc`/`nrc` need `deprecation_reason`.
- **Translations.** Strings from the deleted templates move to `panels.py` and the fragments, so refresh the
  catalogs and keep the existing French translations where the msgid is unchanged.
- **Deleting templates.** `test_conventions` and the `generic/object.html` breadcrumb block must still give the
  external party and contract breadcrumbs on the two pages that had them.

## Project Structure

### Documentation (this feature)

```text
specs/003-netbox-46-plugin-features/
├── spec.md
├── plan.md              # this file
├── research.md          # Phase 0: decisions D1-D12
├── data-model.md        # Phase 1: contract type, service provider, amend permission, migrations
├── quickstart.md        # Phase 1: validation commands and scenario map
├── contracts/
│   ├── rest-api.md      # brief sets, nested fields, removed fields, amend action, new fields
│   ├── graphql.md       # queries, types, unions, permissions
│   └── detail-pages.md  # panels per page, table actions matrix
├── checklists/requirements.md
└── tasks.md             # created by /speckit-tasks
```

### Source Code (repository root)

```text
netbox_contract/
├── models.py                   # ContractType(OrganizationalModel), ServiceProvider(PrimaryModel), ContractLine.Meta.permissions (D6, D9)
├── text.py                     # NEW: unique_slug(), shorten_description(), pure (D9, D10)
├── panels.py                   # NEW: SettingsAttributesPanel, per-model attribute panels, deprecated panels, message/values TemplatePanels, AddContractLine (D1-D4)
├── object_actions.py           # NEW: AmendContractLine (D6)
├── templatetags/contract_tags.py   # NEW: can_amend filter for contractline_edit.html (D6)
├── views.py                    # layout on 9 ObjectViews; template_name generic/object.html; amend view permission; contract line list annotations (D1, D4, D6)
├── tables.py                   # ContractLineActionsColumn; locked/contract tables and AMEND_BUTTON removed; owner columns (D4, D9)
├── filtersets.py               # ContractFilterSet.invoice_id; Organizational/PrimaryModelFilterSet bases (D5, D9)
├── forms.py                    # Organizational/PrimaryModel form bases, slug optional, owner fields in fieldsets (D9)
├── api/serializers.py          # nested=True, brief_fields, Nested* removed, Organizational/PrimaryModelSerializer (D7, D9)
├── api/views.py                # amend action permissions; annotations (D4, D6)
├── graphql/                    # NEW: __init__.py, filters.py, types.py, schema.py (D8)
├── migrations/0050_contractline_amend_permission.py
├── migrations/0051_contracttype_organizational.py
├── migrations/0052_serviceprovider_primary.py
├── templates/netbox_contract/
│   ├── contract.html, contractline.html          # reduced to breadcrumbs
│   ├── {invoice,invoiceline,unit,serviceprovider,contracttype,accountingdimension,contractassignment}.html  # deleted
│   ├── contractline_edit.html                    # amend link uses can_amend
│   └── panels/{contract_values,lines_locked,line_lock,invoice_posted,invoice_template,amend_button}.html   # NEW fragments
├── locale/{en,fr}/LC_MESSAGES/django.{po,mo}
└── tests/
    ├── test_amend_permission.py   # NEW (US1)
    ├── test_detail_layouts.py     # NEW (US2)
    ├── test_nested_api.py         # NEW (US3)
    ├── test_graphql.py            # NEW (US4)
    ├── test_base_classes.py       # NEW (US5)
    └── test_api.py, test_issue_307.py, test_amendments.py, test_locking.py, test_deprecated.py   # adapted
CHANGELOG.md, docs/{api,contract_lines,contract,index}.md, CLAUDE.md
```

**Structure Decision**: keep the existing single-plugin layout. The new modules follow core naming: `panels.py`,
`object_actions.py`, a `graphql/` package, and `templatetags/`.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| Constitution IV/V: REST nested and brief fields are removed (nested contract 24 → 5 fields; invoice `contracts` full → brief; contract and invoice `brief=true` sets reduced) without a released deprecation period | The maintainer chose to align with core now (clarification Q2 2026-10-01, Q1 2026-10-02). The nested contract spreads the deprecated `mrc`/`yrc`/`nrc` into every related object, and 2.5.0 already changes the API surface (contract lines, units) | The additive approach (keep today's fields in 2.5.0, announce, and shrink in a later specified release) was offered as the recommended option and declined by the maintainer. Mitigation: every removed field is listed per endpoint in the changelog "Behaviour changes" and in `docs/api.md`, and every removed value is still available from the related object's own endpoint |
