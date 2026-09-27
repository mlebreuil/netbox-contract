# Contract: user interface, plugin settings and scripts

## Screens

- New list, detail, add, edit, delete, bulk import, bulk edit, bulk delete and change log screens for **Units** and **Contract lines**, registered like the existing models (`urls.py`, `views.py`, `tables.py`, `filtersets.py`, `forms.py`, `navigation.py`, `search.py`, templates under `templates/netbox_contract/`). Menu: a "Contract lines" and a "Units" entry beside the existing entries.
- **Contract detail**: a "Contract lines" table (with add button prefilled with the contract) replaces the "Invoice template" and "Invoice template lines" panels; a summary panel shows Billable, Total contract value ("Not available" when open-ended), Yearly value and Yearly billable value; deprecated cost fields appear only when `show_deprecated_fields` is true, with a "deprecated" label.
- **Contract form and list**: `billable` field and column; `mrc`, `yrc`, `nrc` hidden unless `show_deprecated_fields`; list column "Yearly value" replaces `calculated_rc`.
- **Invoice add screen**: amount and period are proposed from contract lines; the status defaults to Draft. For a non-billable contract an error message is shown and no amount is proposed. Usage-based lines never contribute to the proposed amount. Users can edit everything before saving. Below the form, **Lines to generate** previews the lines that will be created (contract line, unit, unit price, quantity, accounting dimensions, amount, total), refreshed through HTMX when the contract, period, amount or a value changes; quantities, unit prices and dimensions can be changed and lines without contract line added (**Add a line**) before saving (FR-032).
- **Invoice detail / template invoices**: template invoices show a "deprecated" badge. A Posted invoice hides "Add a line" and shows a notice that its amounts and lines are locked (FR-031); its edit form shows amount, currency, period and contracts disabled.

## Invoice creation, line generation and quantity

- **Invoice creation**: saving a new invoice for a billable contract generates its invoice lines at once (no button, no separate step); usage-based lines appear without quantity and the user enters it on each line. Saving a new invoice for a non-billable contract is refused with an error. Editing an existing invoice never generates lines.
- **Invoice line form**: fields "Contract line", "Unit", "Unit price" and "Quantity"; unit and unit price default to those of the contract line and can be changed while the invoice is not posted; the amount is calculated when the line has a unit price (entered by the user otherwise). On a Posted invoice, only accounting dimensions, comments and tags can change.
- **Contract screens**: when the contract has invoices, the add and delete buttons of its contract lines are hidden and a notice says a new contract must be created; each line keeps an edit button (its accounting dimensions, comments and tags stay editable, its contract terms are shown disabled) and, for recurring and usage-based lines not yet replaced, an **Amend** button.
- **Contract line page and edit page**: an **Amend** button (change of unit price and/or quantity from a date, with a required reason recorded in the change log; FR-030) and "Replaces" / "Replaced by" rows; a locked line explains what can still be edited.
- Invoice templates: never deleted; visible, marked deprecated, from the contract detail page.

## Plugin settings (`PLUGINS_CONFIG['netbox_contract']`)

| Setting | Default | Change |
|---|---|---|
| `show_deprecated_fields` | `False` | new; shows `mrc`, `yrc`, `nrc` in the contract form, detail page and tables, and offers the Template field in the invoice form and bulk edit |
| `hidden_contract_fields`, `mandatory_contract_fields` | unchanged | must keep working when they mention deprecated fields (a mandatory deprecated field is ignored with a logged warning) |
| others | unchanged | |

Metadata: `min_version = '4.6.0'`, no `max_version`, version 2.5.0 (single release).

## Scripts (NetBox custom scripts, `scripts/netbox-contract.py`)

- New, read-only: **Report currency mismatches** lists contract lines, invoices, invoice lines and non-billable child contracts whose currency differs from their parent record, with links, and changes nothing (FR-012).
- Removed: `create_invoice_template` and `create_invoice_lines` (they read fields that no longer exist and are superseded by the conversion).
- Kept: expired-contract status update, replace accounting dimension, contract end check.
- Command line: `python manage.py convert_contract_lines` re-runs the conversion (idempotent) and prints the conversion report.
