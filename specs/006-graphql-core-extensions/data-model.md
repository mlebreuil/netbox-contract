# Data Model: GraphQL core extensions

No table, column or migration change.

## Runtime relation added to core models

| Core model | Attribute | Target | Join |
|------------|-----------|--------|------|
| dcim.Device, dcim.Site, dcim.Rack, circuits.Circuit, circuits.VirtualCircuit, virtualization.VirtualMachine, virtualization.Cluster (and any other `supported_models` entry with a GraphQL type) | `contract_assignments` (GenericRelation) | ContractAssignment | `content_type` + `object_id` |

Behaviour: deleting the object deletes its assignments (not the contract). Existing orphan assignments are not modified by the upgrade; the command `cleanup_orphan_assignments` lists them and, on request, deletes them (orphan = no object with that type and identifier).

## GraphQL additions

| Type | Added field | Added filters |
|------|-------------|---------------|
| each covered core type | `contract_assignments: [ContractAssignmentType]` | `has_contracts: Boolean`, `has_active_contract: Boolean` |
