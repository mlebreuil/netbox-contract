# Contract: REST API changes

This contract covers the nested objects and `brief=true` (D7, FR-009 to FR-012), the amend action (D6) and the new
fields (D9). Tests in `tests/test_nested_api.py` and `tests/test_api.py` assert exactly these sets.

## Brief representations (`Meta.brief_fields`)

| Model | Brief fields after | Change from 2.4 / 2.5.0-dev |
|---|---|---|
| Contract | `id, url, display, name, status` | Removed from `brief=true`: `contract_type`, `external_party_object_type`, `external_party_object_id`, `external_party_object`, `external_reference`, `internal_party`, `tenant`, `start_date`, `end_date`, `initial_term`, `renewal_term`, `currency`, `mrc`, `yrc`, `nrc`, `invoice_frequency`, `billable`, `comments`, `parent` |
| Invoice | `id, url, display, number` | Removed from `brief=true`: `date`, `template`, `contracts`, `period_start`, `period_end`, `currency`, `amount`, `comments` |
| Invoice line | `id, url, display, invoice, amount, currency` | `name` (did not exist) and `accounting_dimensions` removed; `id` and `currency` added |
| Contract line | `id, url, display, contract, description, quantity, unit, unit_price, currency, start_date, end_date` | `start_date`, `end_date` added |
| Accounting dimension | `id, url, display, name, value` | unchanged |
| Unit | `id, url, display, name, description, billing_method, months` | unchanged |
| Contract type | `id, url, display, name, slug, description` | `slug` added |
| Service provider | `id, url, display, name, slug, description` | `description` added |
| Contract assignment | `id, url, display, content_object, contract, tags, custom_fields` | unchanged (its `contract` is now brief) |

## Nested related objects

| Endpoint · field | Before | After | Write |
|---|---|---|---|
| `contractassignment` · `contract` | `NestedContractSerializer` (24 fields) | brief contract (5 fields) | id or attributes dict, unchanged |
| `contract-lines` · `contract` | `NestedContractSerializer` (24 fields) | brief contract | unchanged |
| `contracts` · `parent` | `NestedContractSerializer` (24 fields) | brief contract | unchanged; `null` allowed |
| `invoices` · `contracts` | full `ContractSerializer` (36 fields each) | brief contract | list of ids, unchanged |
| `invoiceline` · `invoice` | `NestedInvoiceSerializer` (`id, url, display, number`) | brief invoice (same fields) | unchanged |
| `contract-lines`, `invoiceline` · `accounting_dimensions` | `NestedAccountingDimensionSerializer` | brief accounting dimension (same fields) | list of ids, unchanged |
| `contract-lines` · `replaces` | `NestedContractLineSerializer` (`id, url, display, description, quantity, unit_price, start_date, end_date`) | brief contract line | read-only |

Fields removed from each nested contract (assignment `contract`, line `contract`, contract `parent`):
`contract_type`, `external_party_object_type`, `external_party_object_id`, `external_party_object`,
`external_reference`, `internal_party`, `tenant`, `start_date`, `end_date`, `initial_term`, `renewal_term`,
`notice_period`, `currency`, `mrc`, `yrc`, `nrc`, `invoice_frequency`, `comments`, `documents`.

Fields removed from each invoice `contracts` item: the list above plus `billable`, `total_contract_value`,
`yearly_contract_value`, `yearly_billable_value`, `parent`, `tags`, `custom_fields`, `created`, `last_updated`.

OpenAPI: nested components are named `BriefContract`, `BriefInvoice`, `BriefContractLine`,
`BriefAccountingDimension`. The `NestedContract*` components disappear. `Contract.external_party_object` and
`ContractAssignment.content_object` stay `object`.

## Amend action

`POST /api/plugins/contracts/contract-lines/{id}/amend/`

| Caller | Result |
|---|---|
| view + amend on the line (constraints included), write-enabled token | 201, the new line |
| amend but the line is outside the view constraints | 404 |
| view but no amend (even with add + change) | 403 |
| read-only token | 403 |

The request and response bodies are unchanged.

## New fields

| Endpoint | Field | Input |
|---|---|---|
| `contracttype/` | `slug` | optional; derived from `name` when omitted or blank |
| `contracttype/` | `comments`, `owner` | optional |
| `contracttype/` | `description` | now max 200 characters (longer input is a 400 error, as on core objects) |
| `serviceproviders/` | `description`, `owner` | optional |

Filters added: `contracttype/?slug=`, `?owner_id=` (core owner filters), `serviceproviders/?description=`,
`?owner_id=`, `contracts/?invoice_id=`.
