# Contract: GraphQL API (D8, FR-013 to FR-015a)

Queries added to NetBox's `/graphql/` schema (two per model):

| Model | Single | List | Type | Base |
|---|---|---|---|---|
| Contract | `contract(id:)` | `contract_list(filters:, pagination:)` | `ContractType` | `NetBoxObjectType` |
| Contract line | `contract_line` | `contract_line_list` | `ContractLineType` | `NetBoxObjectType` |
| Contract type | `contract_type` | `contract_type_list` | `ContractTypeType` | `OrganizationalObjectType` |
| Contract assignment | `contract_assignment` | `contract_assignment_list` | `ContractAssignmentType` | `NetBoxObjectType` |
| Invoice | `invoice` | `invoice_list` | `InvoiceType` | `NetBoxObjectType` |
| Invoice line | `invoice_line` | `invoice_line_list` | `InvoiceLineType` | `NetBoxObjectType` |
| Unit | `unit` | `unit_list` | `UnitType` | `NetBoxObjectType` |
| Accounting dimension | `accounting_dimension` | `accounting_dimension_list` | `AccountingDimensionType` | `NetBoxObjectType` |
| Service provider | `service_provider` | `service_provider_list` | `ServiceProviderType` | `PrimaryObjectType` |

Types live in `netbox_contract.graphql.types` under these names, so `utilities.api.get_graphql_type_for_model` finds
them (core test case convention).

## Fields

- **Stored fields:** all, through `fields='__all__'`.
- **Relations, both directions:**
  - contract ↔ contract type, parent/`childs`, `lines`, `invoices`, `assignments`, tenant;
  - line ↔ unit, `accounting_dimensions`, `replaces`/`replaced_by`, `invoicelines`;
  - accounting dimension ↔ `contract_lines`, `invoice_lines`;
  - invoice ↔ `contracts`, `invoicelines`.
- **Deprecated, marked with `deprecation_reason`:** `Contract.mrc`, `yrc`, `nrc`; `Invoice.template`.
- **Not exposed:** `total_contract_value`, `yearly_contract_value`, `yearly_billable_value`, `total_value`,
  `yearly_value`. These are REST-only, and the docs say so.
- **Generic relations:**
  - `Contract.external_party_object`: union `ContractExternalPartyType` = `ServiceProviderType | ProviderType`
    (circuits).
  - `ContractAssignment.content_object`: union `ContractAssignmentObjectType` = `CircuitType | VirtualCircuitType |
    SiteType | DeviceType | RackType | VirtualMachineType | ClusterType`. Any other model listed in
    `supported_models` resolves to `null`. `content_type` and `object_id` are always present.

## Filters

`filters:` accepts a `<Model>Filter` per type with core lookups:
- strings: `exact`, `i_contains`, ...;
- numbers and dates: `exact`, `gt`, `lte`, `range`, ...;
- choices: enum lookups;
- relations: `*_id`.

The tags, custom field and change logging filters come from `NetBoxModelFilter`. Owner filters come from the
organizational and primary bases.

## Permissions

Relations to objects the user may not view are `null` (they are nullable in the schema).

Results are restricted to `restrict(user, 'view')`, including object-level constraints (`BaseObjectType`). A user
without view permission gets an empty list, or `null` for a single object, as for core objects.
