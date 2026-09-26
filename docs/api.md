# API

The plugin API is under `/api/plugins/contracts/`.

note: When creating invoices and invoice lines through the API, the corresponding contracts respectively accounting dimensions, must be referenced as a list of id.

## Units and contract lines

- `units/`: `name`, `description`, `billing_method` (`one_time`, `recurring`, `usage`), `months` (required for `recurring`, empty otherwise). Deleting a unit used by contract lines returns 409.
- `contract-lines/`: `contract` (id), `description`, `quantity`, `unit_price`, `unit` (id), `currency` (defaults to the contract's), `start_date` and `end_date` (default to the contract's), `accounting_dimensions` (list of ids), and the read-only `total_value`, `yearly_value` and `invoiced_at_conversion`. Filters: `contract_id`, `unit_id`, `unit`, `currency`, `billing_method`, `accounting_dimensions`, `invoice_id`, `q`. Creating or deleting a line of a contract that has invoices, or changing its contract terms, returns 400; its `accounting_dimensions`, `comments` and `tags` can still be changed.

## Contracts

- `billable` (writable, default `true`) and the read-only values `total_contract_value` (null when not available), `yearly_contract_value` and `yearly_billable_value`. Filter: `billable`.
- `mrc`, `yrc` and `nrc` are deprecated and kept for compatibility.

## Invoices

- A new invoice is linked to at most one contract and has its currency.
- `POST invoices/` generates the invoice lines of a new invoice from the contract lines, in the same request. It returns 400 for a non-billable contract, or when `amount` is lower than the total of the lines to generate. Editing an invoice never generates lines.
- `template` is deprecated: invoice templates are no longer copied.

## Invoice lines

- `contract_line` (id, optional), `quantity`, read-only `unit` and `unit_price` (from the contract line).
- When `contract_line` is set, `amount` is calculated and ignored if sent; otherwise it is required.
