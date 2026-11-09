# User interface (current state)

Per-feature deltas: `specs/001-*/contracts/ui-and-settings.md`, `002-*/contracts/forms.md`,
`003-*/contracts/detail-pages.md`, `004-*/contracts/forms-and-urls.md`, `005-*/contracts/breadcrumbs.md`,
`007-*/contracts/choices.md`.

## Registration and pages

- Every model has list, add, import, bulk edit, bulk delete, detail, edit, delete, changelog and journal pages, all
  registered with `register_model_view`; `urls.py` includes `get_model_urls` per model plus non-model pages
  (002-FR-001 to 002-FR-003). Extra tabs and actions from other plugins attach the same way.
- Detail pages are declared with `SimpleLayout` and the plugin's panels; related tables are the list views' tables
  filtered to the object, loaded over HTMX; the left, right and full-width plugin areas exist (003-FR-004,
  003-FR-004a, 003-FR-007).
- Hidden attributes (`hidden_contract_fields`, `hidden_invoice_fields`) and deprecated fields
  (`show_deprecated_fields`) are applied at render time (003-FR-005, 002-FR-012).
- Contract page: contract lines table (add button hidden once the contract has invoices, with a notice), assignments,
  child contracts, invoices; values panel (billable, total or "Not available", yearly, yearly billable) (001-FR-004,
  001-FR-006, 003-FR-006).
- Contract line page: Amend action (`amend` permission, per line), "Replaces" / "Replaced by", lock message
  (003-FR-001 to 003-FR-003). Contract line tables hide Delete on locked lines.
- Invoice page: contracts, lines (add hidden when posted), Posted notice (001-FR-031).

## Forms

- Fieldsets group every visible field of the add/edit, bulk-edit and filter forms in exactly one titled section;
  fields hidden by settings are rendered once as hidden inputs; a `Deprecated` section only with
  `show_deprecated_fields` (002-FR-006, 002-FR-007). Filter forms offer the lookup modifiers (002-FR-004,
  002-FR-005). The contract type description is single-line outside the edit form (002-FR-008).
- Invoice and invoice line edit screens answer quick add and partial refresh like core `ObjectEditView`; values in the
  address win over the pre-fill (002-FR-009, 002-FR-010). New invoice: amount and period proposed from the contract
  lines, status Draft, "Lines to generate" preview refreshed over HTMX, editable quantities, unit prices,
  dimensions, extra lines (001-FR-017 to 001-FR-020, 001-FR-032).
- Selectors: the assignment form chooses an object type then searches an object limited to what the user may view;
  the contract form chooses the external party type then the provider (004-FR-001 to 004-FR-008). Submitted names:
  `content_object_content_type` / `content_object_object_id`, `external_party_object_content_type` /
  `external_party_object_object_id`; the old query names `content_type` / `object_id` still pre-fill (004-FR-004).
- A duplicate assignment is refused with "<contract> is already assigned to <object>." (004-FR-014).
- Choice drop-downs show a description under status and billing method options as `data-description`
  (007-FR-004).

## Breadcrumbs (005-FR-001, 005-FR-002, 005-FR-008)

| Page | Trail |
|---|---|
| Contract | Contracts > external party (omitted without one) > contract |
| Contract line | Contract lines > contract > line |
| Invoice | Invoices > each contract > invoice number |
| Invoice line | Invoice lines > invoice > line |

Tab pages show the same trail; entries do not depend on the viewer's permission on the target.

## Plugin settings (`PLUGINS_CONFIG['netbox_contract']`)

`top_level_menu` (false), `mandatory_contract_fields`, `hidden_contract_fields`, `mandatory_invoice_fields`,
`hidden_invoice_fields`, `mandatory_dimensions`, `supported_models` (object types an assignment may target; 004-FR-002,
006-FR-002), `contract_assignments_display` (`tab`, `inline`, `both`), `show_deprecated_fields` (false, 001-FR-015), and
`FIELD_CHOICES` overrides (007-FR-007). Settings are read at call time. A setting may be added but not removed or
renamed (003-FR-022).
