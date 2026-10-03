# Contract: REST API changes

This contract covers the nested objects and `brief=true` (D7, FR-009 to FR-012a), the amend action (D6) and the new
fields (D9). 2.5.0 removes no field from any REST response (Constitution IV/V). Tests in `tests/test_nested_api.py`
and `tests/test_api.py` assert exactly these sets.

## Brief representations (`Meta.brief_fields`), 2.5.0

| Model | Brief fields in 2.5.0 | Change |
|---|---|---|
| Contract | unchanged: `id, url, display, name, contract_type, external_party_object_type, external_party_object_id, external_party_object, external_reference, internal_party, tenant, status, start_date, end_date, initial_term, renewal_term, currency, mrc, yrc, nrc, invoice_frequency, billable, comments, parent` | none (shrink deprecated, see below) |
| Invoice | unchanged: `id, url, display, number, date, template, contracts, period_start, period_end, currency, amount, comments` | none (shrink deprecated) |
| Invoice line | `id, url, display, invoice, accounting_dimensions, amount, currency` | the invalid `name` declaration is removed (it was ignored); `id` and `currency` are added |
| Contract line | `id, url, display, contract, description, quantity, unit, unit_price, currency, start_date, end_date` | `start_date` and `end_date` are added (the model is new in 2.5.0) |
| Accounting dimension | `id, url, display, name, value` | none |
| Unit | `id, url, display, name, description, billing_method, months` | none |
| Contract type | `id, url, display, name, slug, description` | `slug` is added (US5) |
| Service provider | `id, url, display, name, slug, description` | `description` is added (US5) |
| Contract assignment | `id, url, display, content_object, contract, tags, custom_fields` | none |

## Nested related objects, 2.5.0

| Endpoint · field | Before | 2.5.0 | Output |
|---|---|---|---|
| `invoiceline` · `invoice` | `NestedInvoiceSerializer` | `InvoiceSerializer(nested=True, fields=('id', 'url', 'display', 'number'))` | identical |
| `contract-lines`, `invoiceline` · `accounting_dimensions` | `NestedAccountingDimensionSerializer` | `SerializedPKRelatedField(serializer=AccountingDimensionSerializer, nested=True, ...)` | identical (the brief set is the same) |
| `contract-lines` · `replaces` | `NestedContractLineSerializer` (new in 2.5.0) | `ContractLineSerializer(nested=True, read_only=True)` | the brief contract line |
| `contractassignment` · `contract`, `contract-lines` · `contract`, `contracts` · `parent` | `NestedContractSerializer` | **unchanged**, kept and marked deprecated in its docstring and in the field help texts | identical (24 fields, `contract_type` as an id) |
| `invoices` · `contracts` | full `ContractSerializer` | **unchanged** | identical |

Writes by id or by attributes dict are unchanged on every writable field.

OpenAPI: `NestedInvoice`, `NestedAccountingDimension` and `NestedContractLine` become `BriefInvoice`,
`BriefAccountingDimension` and `BriefContractLine`, with the same properties, on the pinned NetBox 4.6.10. Earlier 4.6
releases document the accounting dimension lists with the `AccountingDimension` component, because their schema extension
for `SerializedPKRelatedField` resolves the serializer class (fixed by netbox#22989). The response keeps the five brief
fields either way (implementation note, T044, corrected after CI on v4.6.10).

## Deprecations announced in 2.5.0 (removed by the later specified release)

These are listed per field in the #309 changelog entry under "Deprecations" and in `docs/api.md`, with "read
`contracts/{id}/` instead" (FR-012a). After the shrink:
- the nested contract becomes the brief contract `id, url, display, name, status`;
- the contract brief set becomes `id, url, display, name, status`;
- the invoice brief set becomes `id, url, display, number`.

| Where | Fields that will be removed |
|---|---|
| Nested contract (assignment `contract`, line `contract`, contract `parent`) | `contract_type`, `external_party_object_type`, `external_party_object_id`, `external_party_object`, `external_reference`, `internal_party`, `tenant`, `start_date`, `end_date`, `initial_term`, `renewal_term`, `notice_period`, `currency`, `mrc`, `yrc`, `nrc`, `invoice_frequency`, `comments`, `documents` |
| Invoice `contracts` items | the fields above plus `billable`, `total_contract_value`, `yearly_contract_value`, `yearly_billable_value`, `parent`, `tags`, `custom_fields`, `created`, `last_updated` |
| `contracts/?brief=true` | `contract_type`, `external_party_object_type`, `external_party_object_id`, `external_party_object`, `external_reference`, `internal_party`, `tenant`, `start_date`, `end_date`, `initial_term`, `renewal_term`, `currency`, `mrc`, `yrc`, `nrc`, `invoice_frequency`, `billable`, `comments`, `parent` |
| `invoices/?brief=true` | `date`, `template`, `contracts`, `period_start`, `period_end`, `currency`, `amount`, `comments` |

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
