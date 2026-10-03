# API

The plugin API is under `/api/plugins/contracts/`.

note: When creating invoices and invoice lines through the API, the corresponding contracts respectively accounting dimensions, must be referenced as a list of id.

Every list endpoint accepts the standard NetBox filters (`id`, `q`, `tag`, `created`, `last_updated`, ...) and the filters of its model, for example `serviceproviders/?name=`, `contracttype/?name=`, `accountingdimension/?name=&value=&status=` and `contractassignment/?contract=`.

## Units and contract lines

- `units/`: `name`, `description`, `billing_method` (`one_time`, `recurring`, `usage`), `months` (required for `recurring`, empty otherwise). Deleting a unit used by contract lines returns 409.
- `contract-lines/`: `contract` (id), `description`, `quantity`, `unit_price`, `unit` (id), `currency` (defaults to the contract's), `start_date` and `end_date` (default to the contract's), `accounting_dimensions` (list of ids), and the read-only `total_value`, `yearly_value` and `invoiced_at_conversion`. Filters: `contract_id`, `unit_id`, `unit`, `currency`, `billing_method`, `accounting_dimensions`, `invoice_id`, `q`. Creating or deleting a line of a contract that has invoices, or changing its contract terms, returns 400; its `accounting_dimensions`, `comments` and `tags` can still be changed. The read-only `replaces` field shows the line a line replaces after an amendment.
- `POST contract-lines/{id}/amend/` with `effective_date`, `reason` and a new `unit_price` and/or `quantity`: ends the line the day before `effective_date` and returns the new line (201). Requires the view and **amend** actions on that line (object permissions, constraints included); a write-enabled token is needed. A line outside the view constraints returns 404, a user without the amend action 403. Errors (date before the end of the last invoiced period, one-time line, missing reason) return 400.

## Contracts

- `billable` (writable, default `true`) and the read-only values `total_contract_value` (null when not available), `yearly_contract_value` and `yearly_billable_value`. Filter: `billable`.
- `mrc`, `yrc` and `nrc` are deprecated and kept for compatibility.

## Invoices

- A new invoice is linked to at most one contract and has its currency. Its `status` defaults to `draft`.
- A Posted invoice cannot change its `amount`, `currency`, `period_start`, `period_end` or `contracts` (400); its `status` can change.
- `POST invoices/` generates the invoice lines of a new invoice from the contract lines, in the same request. It returns 400 for a non-billable contract, or when `amount` is lower than the total of the lines to generate. Editing an invoice never generates lines.
- `template` is deprecated: invoice templates are no longer copied.

## Invoice lines

- `contract_line` (id, optional), `unit` (id) and `unit_price` (default to those of the contract line), `quantity`.
- Lines of a Posted invoice cannot be created or deleted, and their unit, unit price, quantity, amount, currency and contract line cannot change (400).
- `amount` is always quantity x unit price and ignored if sent; `unit_price` is required, except that an `amount` given alone when a line is created is taken as its unit price with quantity 1 (compatibility). `quantity` defaults to 1.

## GraphQL

The plugin's objects are in NetBox's GraphQL API (`/graphql/`), with two queries per object type: `contract` / `contract_list`, `contract_line` / `contract_line_list`, `contract_type` / `contract_type_list`, `contract_assignment` / `contract_assignment_list`, `invoice` / `invoice_list`, `invoice_line` / `invoice_line_list`, `unit` / `unit_list`, `accounting_dimension` / `accounting_dimension_list` and `service_provider` / `service_provider_list`. Results follow the user's view permissions, constraints included.

```graphql
{
  contract_list(filters: {status: {exact: STATUS_ACTIVE}, currency: {exact: "usd"}}) {
    name
    contract_type { name }
    external_party_object { __typename ... on ServiceProviderType { name } ... on ProviderType { name } }
    lines { description quantity unit_price unit { name } }
    invoices { number status }
  }
}
```

- Every stored field and relation is available. `mrc`, `yrc`, `nrc` (contracts) and `template` (invoices) are marked deprecated.
- The computed values (`total_contract_value`, `yearly_contract_value` and `yearly_billable_value` of contracts, `total_value` and `yearly_value` of contract lines) are not in GraphQL: read them from the REST API.
- `external_party_object` of a contract is a service provider or a circuit provider. `content_object` of a contract assignment covers the models of the default `supported_models` setting (circuits, virtual circuits, sites, devices, racks, virtual machines, clusters); for an object of another model it is `null`, and `content_type` and `object_id` identify it.

## Nested objects and `brief=true`

Related objects are nested in the responses:

- `invoice` of an invoice line: `id`, `url`, `display`, `number`.
- `accounting_dimensions` of contract lines and invoice lines: `id`, `url`, `display`, `name`, `value`.
- `replaces` of a contract line: the brief contract line (`id`, `url`, `display`, `contract`, `description`, `quantity`, `unit`, `unit_price`, `currency`, `start_date`, `end_date`).
- `contract` of contract assignments and contract lines, and `parent` of contracts: the nested contract, with the fields listed in the next section plus `id`, `url`, `display`, `name` and `status`. `contract_type` is the id of the contract type.
- `contracts` of an invoice: the full contracts.

A related object can be written by id, or by a dictionary of attributes that identifies exactly one object (for example `"contract": {"name": "C-1"}`).

`?brief=true` on a list returns the brief representation of each object, for example `id`, `url`, `display`, `invoice`, `accounting_dimensions`, `amount` and `currency` for invoice lines.

## Deprecated nested fields

A later release will reduce the nested contract and the brief contract to `id`, `url`, `display`, `name` and `status`, the brief invoice to `id`, `url`, `display` and `number`, and the contracts of an invoice to brief contracts. To prepare, read the fields you need from `contracts/{id}/` (or `invoices/{id}/`) instead of the nested objects. The fields that will be removed are:

| Where | Fields that will be removed |
|---|---|
| Nested contract (`contract` of assignments and contract lines, `parent` of contracts) | `contract_type`, `external_party_object_type`, `external_party_object_id`, `external_party_object`, `external_reference`, `internal_party`, `tenant`, `start_date`, `end_date`, `initial_term`, `renewal_term`, `notice_period`, `currency`, `mrc`, `yrc`, `nrc`, `invoice_frequency`, `comments`, `documents` |
| `contracts` of an invoice | the fields above, plus `billable`, `total_contract_value`, `yearly_contract_value`, `yearly_billable_value`, `parent`, `tags`, `custom_fields`, `created`, `last_updated` |
| `contracts/?brief=true` | `contract_type`, `external_party_object_type`, `external_party_object_id`, `external_party_object`, `external_reference`, `internal_party`, `tenant`, `start_date`, `end_date`, `initial_term`, `renewal_term`, `currency`, `mrc`, `yrc`, `nrc`, `invoice_frequency`, `billable`, `comments`, `parent` |
| `invoices/?brief=true` | `date`, `template`, `contracts`, `period_start`, `period_end`, `currency`, `amount`, `comments` |
