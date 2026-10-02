# Contract: detail page layouts (D1-D5, FR-003 to FR-008)

Each page uses `SimpleLayout(left_panels, right_panels, bottom_panels)`. The plugin content areas `left_page`,
`right_page` and `full_width_page` are appended by `SimpleLayout`. "Same as before" means the same label and value
as the deleted template. `tests/test_detail_layouts.py` checks each row of this contract.

## Contract (`contract.html` → breadcrumbs only)

- **Left**
  - `ContractPanel` (settings-aware, `hidden_contract_fields`): name, contract type (link), external party
    (`GenericForeignKeyAttr`, link, with its type), status (badge), external reference, internal party, tenant,
    start date, end date, initial term ("N month"), renewal term, notice period ("N days"), currency, invoice
    frequency, parent (link), documents (link, only when set).
  - `DeprecatedCostsPanel`: `mrc`, `yrc`, calculated value, `nrc`. Only with `show_deprecated_fields`.
  - `CustomFieldsPanel`.
- **Right**
  - `ContractValuesPanel` (template): billable, total ("Not available" when `None`), yearly, yearly billable, from
    `contract_values`.
  - `TagsPanel`.
  - `CommentsPanel`.
  - `ContextTablePanel('invoicelines_table')` with the deprecated template summary. Only with
    `show_deprecated_fields` and a template.
- **Bottom**
  1. `LinesLockedMessagePanel` (template, when the contract has invoices).
  2. Contract lines table, with `AddContractLine` (add permission, contract without invoices,
     `?contract=<pk>&return_url=`).
  3. Assignments table.
  4. Child contracts table (title "Child contracts").
  5. Invoices table (excluding templates), with `AddObject(invoice, ?contracts=<pk>)`.

## Invoice (`generic/object.html`)

- **Left**
  - `InvoicePanel` (settings-aware, `hidden_invoice_fields`): number, date, status (badge), period start, period end,
    currency, amount, invoice lines total, documents.
  - `DeprecatedTemplatePanel`: template flag and message. Only with `show_deprecated_fields`.
  - `CustomFieldsPanel`.
- **Right**: `PostedMessagePanel` (template, when posted), `TagsPanel`, `CommentsPanel`.
- **Bottom**:
  - contracts table (`invoice_id`);
  - invoice lines table (`invoice`), with `AddObject(invoiceline, ?invoice=<pk>)` hidden when the invoice is posted.

## Contract line (`contractline.html` → breadcrumbs only)

- **Actions**: core Clone, Edit, Delete, plus `AmendContractLine`.
- **Left**
  - `LineLockMessagePanel` (template).
  - `ContractLinePanel`: contract (link), description, quantity, unit (link and billing method badge), unit price with
    currency, start date, end date, accounting dimensions (list), total value ("Not available"), yearly value,
    replaces (link with dates), replaced by (links "from <date>"), invoiced at conversion (checkmark).
  - `CustomFieldsPanel`.
- **Right**: `TagsPanel`, `CommentsPanel`.

## Invoice line, unit, accounting dimension, contract type, service provider, contract assignment (`generic/object.html`)

| Page | Left attributes panel | Bottom tables |
|---|---|---|
| Invoice line | invoice (link), contract line (link) and its contract, quantity, unit (link), unit price, amount ("calculated"), currency, accounting dimensions | none |
| Unit | name, description, billing method (badge), months covered by one unit price | contract lines (`unit_id`) |
| Accounting dimension | name, value, status (badge) | none |
| Contract type | `OrganizationalObjectPanel` (name, description) + slug, color, owner | none |
| Service provider | name, slug, description, portal URL (link), owner | contracts (`service_provider_id`) |
| Contract assignment | contract (link), object type, object (`GenericForeignKeyAttr`, link) | none |

Every page has `CustomFieldsPanel` on the left, and `TagsPanel` and `CommentsPanel` on the right where the model has
comments.

## Contract line table actions (all contract line tables)

| Line | Edit | Amend | Delete |
|---|---|---|---|
| Unlocked | yes (change) | no | yes (delete) |
| Locked, amendable, user may amend it | yes (change) | yes | no |
| Locked, not amendable (one-time, replaced) | yes (change) | no | no |
