# Contract: form sections and filter modifiers

User-visible form layout introduced by FR-004, FR-006 to FR-008. The section-by-section grouping of every model is in
[research.md, D3](../research.md#d3-form-sections-fieldsets-and-fields-hidden-by-settings).

## Invariants (tested)

1. For every model form, bulk-edit form and filter form of the plugin, each visible field (not a hidden input, not
   a custom field, not `comments`, `changelog_message`, `owner` or `owner_group`) appears in exactly one section.
2. No field is added, removed or renamed compared with the form before the change.
3. A field hidden by `hidden_contract_fields` is rendered once, as a hidden input, and in no section.
4. With `show_deprecated_fields` off, `mrc`, `yrc`, `nrc` (contract) and `template` (invoice) are absent and no
   `Deprecated` section is rendered; with it on, they are in a `Deprecated` section.
5. No section without a field is rendered.
6. Filter forms start with the section `q`, `filter_id`, `tag`.
7. `ContractTypeFilterForm`, `ContractTypeCSVForm` and `ContractTypeBulkEditForm` render `description` as a single-line
   text input.

## Filter modifiers

The nine filtersets are registered in `registry['filtersets']` under `netbox_contract.<model_name>`. A filter form
field gets NetBox's modifier selector when its form field type has lookups and the filterset has the matching
filters (for example `external_reference`, `external_reference__ic`, `external_reference__nic`, …). Query strings
accepted before the change are accepted unchanged.

## Edit screens

`invoice_add`/`invoice_edit` and `invoiceline_add`/`invoiceline_edit` answer like core `ObjectEditView`:

| Request | Response |
|---|---|
| `GET` | full page (`invoice_edit.html` with the lines preview for a new invoice; generic page for invoice lines) |
| `GET ?_quickadd=true` | `htmx/quick_add.html`, fields prefixed `quickadd-` |
| `GET` with `HX-Request` (partial) | `htmx/form.html` |

Pre-filled values on a new object, set only for fields the query string leaves empty (a value in the query string wins): invoice from `?contracts=<id>` (date = today, period, currency,
amount from contract lines); invoice line from `?invoice=<id>` (quantity 1, invoice currency, unit price = rest of
the invoice amount). Only objects the user may view are used.
