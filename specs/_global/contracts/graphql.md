# GraphQL API (current state)

Added to NetBox's `/graphql/` schema; types live in `netbox_contract.graphql.types` (003-FR-013). Deltas:
`specs/003-*/contracts/graphql.md`, `specs/006-*/contracts/graphql-schema.md`.

| Model | Single | List | Type | Base |
|---|---|---|---|---|
| Contract | `contract` | `contract_list` | `ContractType` | `NetBoxObjectType` |
| Contract line | `contract_line` | `contract_line_list` | `ContractLineType` | `NetBoxObjectType` |
| Contract type | `contract_type` | `contract_type_list` | `ContractTypeType` | `OrganizationalObjectType` |
| Contract assignment | `contract_assignment` | `contract_assignment_list` | `ContractAssignmentType` | `NetBoxObjectType` |
| Invoice | `invoice` | `invoice_list` | `InvoiceType` | `NetBoxObjectType` |
| Invoice line | `invoice_line` | `invoice_line_list` | `InvoiceLineType` | `NetBoxObjectType` |
| Unit | `unit` | `unit_list` | `UnitType` | `NetBoxObjectType` |
| Accounting dimension | `accounting_dimension` | `accounting_dimension_list` | `AccountingDimensionType` | `NetBoxObjectType` |
| Service provider | `service_provider` | `service_provider_list` | `ServiceProviderType` | `PrimaryObjectType` |

- Stored fields and relations in both directions; computed values (`total_contract_value`, `yearly_*`,
  `total_value`) are REST-only (003-FR-015a).
- Deprecated fields carry `deprecation_reason`: `Contract.mrc/yrc/nrc`, `Invoice.template` (003-FR-015).
- Generic relations are unions: `Contract.external_party_object` (service provider or circuit provider) and
  `ContractAssignment.content_object` (circuit, virtual circuit, site, device, rack, virtual machine, cluster;
  other `supported_models` resolve to `null`).
- Permissions: results are restricted to `view` with object constraints; unviewable relations are `null`
  (003-FR-014).

## Extensions of core types (006)

Each core GraphQL type of a `supported_models` entry gets `contract_assignments` (assignments the user may view) and
list filters `has_contracts` and `has_active_contract` (status `active`, dates ignored); both respect view permission
on contracts and assignments, and the query count does not grow with the number of objects (006-FR-001 to
006-FR-006). Names that collide with other plugins do not prevent loading (006-FR-008).
