# Research: Align with NetBox 4.6 plugin conventions

Phase 0 of [plan.md](plan.md). Every decision below was checked against the NetBox source in the dev container
(`/workspaces/netbox/netbox`, 4.6.x) and the CI pin (`v4.6.10`). No `NEEDS CLARIFICATION` remains.

## D1. URL registration: every view through `register_model_view`

**Decision**: decorate every list, add, import, bulk edit, bulk delete, detail, edit and delete view of the nine
models with `@register_model_view`, using the names and paths core uses:

| View | Decorator |
|---|---|
| list | `@register_model_view(Model, 'list', path='', detail=False)` |
| add | `@register_model_view(Model, 'add', detail=False)` |
| import | `@register_model_view(Model, 'bulk_import', path='import', detail=False)` |
| bulk edit | `@register_model_view(Model, 'bulk_edit', path='edit', detail=False)` |
| bulk delete | `@register_model_view(Model, 'bulk_delete', path='delete', detail=False)` |
| detail | `@register_model_view(Model)` |
| edit | `@register_model_view(Model, 'edit')` (stacked with `add` on the same class, as core does) |
| delete | `@register_model_view(Model, 'delete')` |

`urls.py` becomes, per model, `path('<prefix>/', include(get_model_urls('netbox_contract', '<model>', detail=False)))`
and `path('<prefix>/<int:pk>/', include(get_model_urls('netbox_contract', '<model>')))`, keeping today's prefixes
(`serviceproviders/`, `contracts/`, `units/`, `contract-lines/`, `invoices/`, `assignments/`, `invoiceline/`,
`accountingdimension/`, `contracttype/`). The non-model page `invoices/lines-preview/` (`invoice_lines_preview`) stays a
hand-written path, placed before the invoice include.

**Rationale**: `get_model_urls` builds the name `f'{model_name}_{name}'` (or `model_name` for the detail view) and the
path from `path`, so these decorators reproduce exactly the 82 route names and addresses of today (see
[contracts/routes.md](contracts/routes.md)). `register_models()` (`netbox/models/features.py`) already registers
`journal` and `changelog` for every `NetBoxModel`; they only appear once the detail include exists. The hand-written
`*_changelog` paths become duplicates and are removed. This is the core pattern (for example `circuits/urls.py`).

**Alternatives considered**: registering only the four detail views (clarification Q2, rejected by the maintainer);
keeping hand-written list paths next to includes (two sources of truth for the same names).

## D2. Filterset registration

**Decision**: decorate each of the nine `*FilterSet` classes with `@register_filterset`
(`from utilities.filtersets import register_filterset`).

**Rationale**: `FilterModifierMixin._enhance_fields_with_modifiers` (`utilities/forms/mixins.py`) looks the filterset
up in `registry['filtersets']['netbox_contract.<model>']`; without it no field gets the `FilterModifierWidget`. With
it, each filter form field whose form-field class has lookups and whose filterset has the matching `__<lookup>`
filters gets the modifier selector. Filter query strings are unchanged (FR-005): the filtersets themselves are not
modified.

**Alternatives considered**: none; this is the only mechanism.

## D3. Form sections (`fieldsets`) and fields hidden by settings

**Decision**:
- Add `fieldsets = (FieldSet(...), ...)` to the nine model forms, the nine bulk-edit forms and the nine filter forms.
  Import (CSV) forms get none: core import forms do not render sections.
- `comments` is left out of the sections of model and bulk-edit forms: `htmx/form.html` and `generic/bulk_edit.html`
  render `form.comments` on their own after the sections; listing it would render it twice.
- Filter forms start with `FieldSet('q', 'filter_id', 'tag')`; the tenancy and contact mixins' fields get their core
  sections (`FieldSet('tenant_group_id', 'tenant_id', name=_('Tenant'))`,
  `FieldSet('contact', 'contact_role', 'contact_group', name=_('Contacts'))`).
- Deprecated fields (`mrc`, `yrc`, `nrc` on the contract form, `template` on the invoice model and bulk-edit forms)
  get a `Deprecated` section of their own (the contract bulk-edit form has no deprecated field; the invoice filter
  form's `template` filter is shown whatever the setting, as today); `render_fieldset`
  skips names not in `form.fields`, so the section content disappears when the fields are deleted, and the section
  itself is dropped (next point).
- `apply_field_settings` (hidden contract fields) and the deprecated-field deletion rebuild `form.fieldsets` on the
  instance: hidden (`HiddenInput`) and deleted names are removed from each `FieldSet`, and a `FieldSet` left empty is
  dropped. A hidden field is then rendered once by the `form.hidden_fields` loop, as today.

**Rationale**: once a form has `fieldsets`, `htmx/form.html`, `generic/bulk_edit.html` and `inc/filter_list.html`
render only the names listed in them (plus hidden fields, custom fields, owner, comments, changelog message). A field
left out of every section silently disappears, and a hidden field left in a section renders a label with no visible
input. Removing hidden and deleted names keeps FR-007 (same fields, same hiding) and scenario US3-2 (no empty
section). A generic test checks, for every plugin form, that each visible field is in exactly one section.

**Grouping** (section names are translatable). The Tenant and Contacts filter sections hold the fields inherited from
NetBox's `TenancyFilterForm` (`tenant_group_id`, `tenant_id`) and `ContactModelFilterForm` (`contact`, `contact_role`,
`contact_group`); these filters exist today and would disappear if left out of the sections:

| Model | Model and bulk-edit form sections | Filter form sections (after `q, filter_id, tag`) |
|---|---|---|
| Contract | Contract (name, contract type, status, external reference, parent, documents, tags); Parties (external party type/object, internal party); Dates and terms (start, end, initial term, renewal term, notice period); Billing (currency, invoice frequency, billable); Tenancy (tenant); Deprecated (mrc, yrc, nrc) | Attributes (contract type, status, external reference, internal party, parent, billable); Parties (service provider, provider); Billing (currency); Tenant (tenant group, tenant); Contacts (contact, contact role, contact group) |
| Invoice | Invoice (number, date, contracts, status, documents, tags); Period and amount (period start, period end, currency, amount); Deprecated (template) | Attributes (number, status, contracts); Billing (currency, accounting dimensions); Deprecated (template, always shown: the filter form never removed it) |
| Invoice line | Invoice line (invoice, contract line, accounting dimensions, tags); Amount (unit, unit price, quantity, currency, amount) | Attributes (invoice); Billing (currency, accounting dimensions) |
| Contract line | Contract line (contract, description, accounting dimensions, tags); Price (quantity, unit price, unit, currency); Dates (start, end) | Attributes (contract); Billing (currency, unit, billing method, accounting dimensions) |
| Unit | Unit (name, description, billing method, months, tags) | Attributes (name, billing method) |
| Service provider | Service provider (name, slug, portal URL, tags) | Attributes (name); Contacts (contact, contact role, contact group) |
| Contract type | Contract type (name, description, color, tags) | Attributes (name, description) |
| Contract assignment | Assignment (object type, object, contract, tags) | Attributes (contract) |
| Accounting dimension | Accounting dimension (name, value, status, tags) | Attributes (name, value, status) |

Bulk-edit forms use the same sections restricted to the fields they have.

**Alternatives considered**: deleting hidden fields instead of hiding them (rejected: a new contract could no longer
receive a hidden field's value from the query string, and the setting's behaviour would change); leaving hidden
fields in sections (renders empty labelled rows).

## D4. Contract type description is a `CharField`

**Decision**: `ContractTypeFilterForm`, `ContractTypeCSVForm` and `ContractTypeBulkEditForm` declare
`description = forms.CharField(required=False, ...)`, optional as today (`CommentField` defaults to `required=False` and the model field is `blank=True`). The unused
`nullable_fields = ('comments',)` of `ContractTypeBulkEditForm` (the model form has no comments field) becomes
`('description',)` so the description can be cleared in bulk, matching `UnitBulkEditForm` (accepted by the maintainer).

**Rationale**: `CommentField` is a Markdown `Textarea` meant for `comments`; the model field is a short text.

**Alternatives considered**: keeping `CommentField` with a `TextInput` widget (still labelled as Markdown).

## D5. Invoice and invoice line pre-fill without copying `ObjectEditView.get`

**Decision**: `InvoiceEditView.get` and `InvoiceLineEditView.get` compute the pre-filled values as today (restricted
lookups with `restrict(request.user, 'view')`, #307), then set `self.form` to a per-request subclass of the form whose
`__init__` merges them under the `initial` core passes (`initial={**defaults, **(initial or {})}`), and return
`super().get(request, *args, **kwargs)`. A small helper in `views.py` builds that subclass. Because core's `initial`
comes from the query string, a value in the address wins for both screens (clarification Q5, as core does); for
invoices this changes today's behaviour, where the contract-derived values and today's date replaced query-string
values, and it is listed as a behaviour change. The values keep their Python types (`date`, `Decimal`), so the
existing pre-fill tests (`test_prefill.py`, `test_issue_307.py`) pass unchanged. The new-invoice preview moves to
`InvoiceEditView.get_extra_context`, which already returns it on POST: on GET for a new invoice it returns
`build_lines_preview({**defaults, **normalize_querydict(request.GET)}, request.user)`, the same merged data as the
form. Nothing is pre-filled for an existing object (`kwargs` holds `pk`). The view instance is created per request by
`as_view()`, so setting `self.form` does not leak between requests.

**Rationale**: core `get()` builds `initial` from `normalize_querydict(request.GET)`, applies the `quickadd` prefix,
returns `htmx/quick_add.html` for `_quickadd` and `htmx/form.html` for HTMX partial requests (FR-009). Wrapping the
form class reuses all of that with no copy. The form's `__init__` cannot do it: it has no access to
the user, so it could not apply the #307 restriction. `alter_object()` is rejected because it also runs on POST.

**Alternatives considered**: writing the values into a copy of `request.GET` (suggested in the issue; rejected because
the values become strings, which changes the form's `initial` types and breaks the existing pre-fill tests);
pre-fill in `InvoiceForm.__init__` (no user); `alter_object` setting instance attributes (runs on POST and cannot set
the `contracts` many-to-many on an unsaved instance).

## D6. Templates under `templates/netbox_contract/`

**Decision**: move `templates/contract_assignments_bottom.html` to
`templates/netbox_contract/inc/contract_assignments_bottom.html` and update `template_content.py`; delete
`templates/contract_list_bottom.html` (clarification Q3). New section titles are translated in `locale/fr` (for
example Parties → Parties, Dates and terms → Dates et conditions, Billing → Facturation). Refresh the `.po` references with `makemessages` and
recompile the `.mo` files; the only message of the deleted template (`Contracts`) is used elsewhere, so no
translation is lost.

**Rationale**: Django resolves `contract_assignments_bottom.html` across all apps' template folders, so a same-named
template of another app could shadow it. `inc/` is where the plugin keeps its partials.

## D7. Invoice template only with deprecated fields shown

**Decision**: in `ContractView.get_extra_context`, look up the invoice template and build its lines table only when
`show_deprecated_fields` is true; otherwise `invoice_template` and `invoicelines_table` are `None`, so the section of
`contract.html` (`{% if invoice_template %}`) is not rendered (clarification Q1).

**Rationale**: consistent with the rest of the deprecated data; saves one query (two with a template) per contract
page when the setting is off, which is the default.

## D8. Tests and baselines

**Decision**: one new module `netbox_contract/tests/test_conventions.py`, written first, with:
- the 82 route names of [contracts/routes.md](contracts/routes.md) reversed and resolved to the expected view class;
- the Journal and Changelog tabs present on a detail page of each of the nine models, and a journal entry added
  through the journal view of one of the four models;
- `registry['filtersets']` holding the nine filtersets, the modifier widget on
  `ContractFilterForm().fields['external_reference']`, and the `external_reference__ic` filter result;
- each form's visible fields in exactly one section, hidden/deprecated handling (settings patched with
  `mock.patch.dict`), no empty section;
- contract type description widgets;
- invoice and invoice line pre-fill on GET (same values as the tests of `test_prefill.py`/`test_issue_307.py`),
  `_quickadd` returning the quick-add template, an HTMX partial returning `htmx/form.html`, restricted objects not
  used;
- the moved template rendered on an assignable object page, and no plugin template at the root of `templates/`;
- the contract page with and without `show_deprecated_fields`.

List view query counts should not change (no queryset or table changes); `tests/query_counts.json` is re-recorded
only if a list view test reports a change, with the reason stated in the commit.

## D9. Release

**Decision**: no version bump. 2.5.0 is not released yet (latest tag `v2.4.7`; the #307 fixes are already listed in
the 2.5.0 section of `CHANGELOG.md`), so these changes ship in 2.5.0 with a `#308` entry in that section, after #307,
and the two visible changes are added to its "Behaviour changes" list (invoice template section hidden when
deprecated fields are off; unused root template removed; invoice pre-fill keeps values given in the address). This keeps clarification Q4 (a 2.5.x release, no new
feature version) without numbering a patch of an unreleased version. If 2.5.0 is tagged before this branch is
merged, the entry moves to a new 2.5.1 section and `version` is bumped in `netbox_contract/__init__.py` and
`pyproject.toml`. `docs/contract.md` and `docs/invoice.md` are checked where they describe the forms and updated if a
description no longer matches (`docs/index.md` only includes the README). No README change (no setting or
requirement change).
