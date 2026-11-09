# REST API (current state)

Base path `/api/plugins/contracts/`. NetBox plugin API conventions: token authentication, object permissions,
`brief`, filtering, pagination, bulk operations. Fields, endpoints and filters are public interfaces: deprecate
before removing, never add a required input to an existing endpoint (Constitution V). Per-feature deltas:
`specs/001-*/contracts/rest-api.md`, `specs/003-*/contracts/rest-api.md`.

## Endpoints

| Endpoint | Model | Notes |
|---|---|---|
| `contracts/` | Contract | writable `billable`; read-only `total_contract_value`, `yearly_contract_value`, `yearly_billable_value`, computed for a page at once (001-FR-006); `mrc`, `yrc`, `nrc` deprecated; filters `billable`, `invoice_id` |
| `contract-lines/` | ContractLine | read-only `total_value`, `yearly_value`, `replaces`, `invoiced_at_conversion`; `currency` defaults to the contract's; filters `contract_id`, `unit_id`, `unit`, `currency`, `billing_method`, `accounting_dimensions`, `invoice_id` |
| `contract-lines/{id}/amend/` | action | POST `effective_date`, `reason`, `unit_price` and/or `quantity` (001-FR-030); 201 with the new line |
| `units/` | Unit | `months` required for `recurring`, forbidden otherwise; DELETE refused (409) while used |
| `invoices/` | Invoice | `status` defaults to `draft` (001-FR-031); creating generates the lines (001-FR-021) |
| `invoice-lines/` | InvoiceLine | `contract_line`, `unit`, `unit_price`, `quantity`; `amount` derived (001-FR-024) |
| `contracttype/` | ContractType | `slug` optional (derived, 003-FR-018), `comments`, `owner`, `description` max 200 (003-FR-019); filters `slug`, `owner_id` |
| `serviceproviders/` | ServiceProvider | `description`, `owner` (003-FR-019); filters `description`, `owner_id` |
| `contractassignment/` | ContractAssignment | duplicate (contract, object) is a 400 (004-FR-014) |
| `accountingdimension/` | AccountingDimension | |

## Validation behaviour (400 unless stated)

- Currency: a contract line, invoice or invoice line whose currency differs from its contract's / invoice's; a
  contract currency change once invoices or invoice lines exist; a non-billable child with another currency than its
  parent (001-FR-009, 001-FR-009a, 001-FR-010).
- Lines outside the contract's dates (001-FR-002a). A unit's `billing_method` or `months` changed while used by an
  invoiced contract (001-FR-001a).
- Locks: creating or deleting a line of an invoiced contract, or changing its contract terms (001-FR-029); a Posted
  invoice's amount, currency, period, contracts, lines (001-FR-031).
- A new invoice lists more than one contract, or has a lower amount than the lines to generate, or is for a
  non-billable contract (001-FR-011, 001-FR-021, 001-FR-023). Editing an invoice or bulk import never generates
  lines.
- `amend`: 403 without the `amend` permission action (view + amend; add + change is not enough), 404 outside the
  view constraints, 400 for a one-time or replaced line, a date inside invoiced periods, a missing reason or no
  change (003-FR-002, 001-FR-030).
- Related objects can still be written by id or by an attributes dictionary (003-FR-011).

## Brief representations (`Meta.brief_fields`; may gain fields, never lose one without a deprecation path)

| Model | Brief fields |
|---|---|
| Contract | `id, url, display, name, contract_type, external_party_object_type, external_party_object_id, external_party_object, external_reference, internal_party, tenant, status, start_date, end_date, initial_term, renewal_term, currency, mrc, yrc, nrc, invoice_frequency, billable, comments, parent` |
| Invoice | `id, url, display, number, date, template, contracts, period_start, period_end, currency, amount, comments` |
| Invoice line | `id, url, display, invoice, accounting_dimensions, amount, currency` |
| Contract line | `id, url, display, contract, description, quantity, unit, unit_price, currency, start_date, end_date` |
| Accounting dimension | `id, url, display, name, value` |
| Unit | `id, url, display, name, description, billing_method, months` |
| Contract type | `id, url, display, name, slug, description` |
| Service provider | `id, url, display, name, slug, description` |
| Contract assignment | `id, url, display, content_object, contract, tags, custom_fields` |

Nested related objects use `Serializer(nested=True)`; a serializer's `validate()` returns at once when
`self.nested` (003-FR-009, 003-D7). OpenAPI components `NestedInvoice`, `NestedAccountingDimension`,
`NestedContractLine` are now `Brief*` (003-FR-012).

## Deprecations announced (removal in a later specified release, 003-FR-012a)

`NestedContractSerializer` stays, deprecated. After the later shrink the nested contract becomes
`id, url, display, name, status`, the contract brief set `id, url, display, name, status`, and the invoice brief set
`id, url, display, number`. The fields to be removed are listed per field in `docs/api.md` and the changelog; see
`specs/003-*/contracts/rest-api.md` for the full table. Also deprecated: `Contract.mrc/yrc/nrc`, `Invoice.template`.
