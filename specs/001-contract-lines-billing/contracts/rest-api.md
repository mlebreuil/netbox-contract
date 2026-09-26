# Contract: REST API changes

Base path: `/api/plugins/contract/` (existing). All endpoints follow the NetBox plugin API conventions already used by the plugin (token authentication, object permissions, `brief` mode, filtering, pagination, bulk operations). Single release, plugin 2.5.0.

## New endpoints

| Endpoint | Methods | Notes |
|---|---|---|
| `units/` | GET, POST, PATCH, PUT, DELETE | fields: `id`, `url`, `display`, `name`, `description`, `billing_method` (`one_time` / `recurring` / `usage`), `months`, `comments`, `tags`, `custom_fields`, `created`, `last_updated`. DELETE is refused while contract lines use the unit. `months` required for `recurring`, forbidden otherwise. Changing `billing_method` or `months` is a 400 while a line of an invoiced contract uses the unit. |
| `contract-lines/` | GET, POST, PATCH, PUT, DELETE | fields: `contract` (id), `description`, `quantity`, `unit_price`, `unit` (id), `currency`, `start_date`, `end_date`, `accounting_dimensions` (ids), `comments`, `tags`, `custom_fields`, read-only `total_value`, `yearly_value`, `invoiced_at_conversion`. `currency` defaults to the contract's; another value is a 400 naming both currencies. Dates outside the contract's dates are a 400. Any write or delete on a contract that already has an invoice is a 400 ("a new contract must be created"). Filters: `contract_id`, `unit_id`, `currency`, `billing_method`, `accounting_dimensions`, `q`. |

## Changed endpoints

| Endpoint | Change |
|---|---|
| `contracts/` | new writable `billable` (default true); new read-only `total_contract_value` (null when not available), `yearly_contract_value`, `yearly_billable_value`; `mrc`, `yrc`, `nrc`, `calculated_rc` stay, documented as deprecated. Setting `currency` on a contract that has invoices or invoice lines is a 400. Setting `parent` to a contract of another currency, for a non-billable child, is a 400. Changing `billable` is a 400 when the contract or its family has invoices (FR-008a). Filter `billable`. |
| `invoices/` | 400 when a new invoice lists more than one contract, or when its `currency` differs from its contract's; an existing invoice with several contracts can still be updated without adding contracts. Creating an invoice no longer copies template lines. New action below. |
| `invoice-lines/` | new optional `contract_line` (id) and `quantity`; read-only `unit` and `unit_price` (from the contract line). When `contract_line` is set, `amount` is calculated and ignored if sent; when it is not set, `amount` is required as today. 400 when `currency` differs from the invoice's or when the contract line does not belong to the invoice's contract or one of its non-billable descendants. |

## Invoice creation generates the lines

There is no separate generation endpoint. `POST invoices/` for a new invoice linked to one billable contract creates, in the same request, one invoice line per applicable contract line (its own lines plus those of non-billable descendants, stopping at billable children), each with `contract_line`, dimensions, currency, quantity and calculated amount set; usage-based lines get no quantity and amount 0 until the client sets it with `PATCH invoice-lines/{id}/`. It is a 400 to create an invoice for a non-billable contract, or one whose `amount` is lower than the total of the lines that would be generated (both amounts are in the message). Editing an invoice (`PATCH`/`PUT`) never generates lines, and neither does bulk import through the UI.

## Compatibility

No field is removed or renamed; added fields are optional on write, except that invoice lines that reference a contract line get their amount calculated. Error messages are plain strings under the field name or `non_field_errors`, as elsewhere in the plugin.
