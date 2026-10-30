# Data Model: generic-object selector

No new column. One constraint and one data migration are added to `ContractAssignment` (see Validation); the form-level mapping below is otherwise the only structure involved.

## Stored data (unchanged)

| Model | Stored columns | Generic foreign key |
|-------|----------------|---------------------|
| ContractAssignment | `content_type` (FK ContentType), `object_id` (big integer), `contract` | `content_object` |
| Contract | `external_party_object_type` (FK ContentType), `external_party_object_id` (big integer) | `external_party_object` |

## Form field to stored columns

| Form | Form field | Writes | Allowed types |
|------|------------|--------|---------------|
| ContractAssignmentForm | `content_object` | `content_type`, `object_id` | content types of `supported_models` (those installed and exposed in the REST API) |
| ContractForm | `external_party_object` | `external_party_object_type`, `external_party_object_id` | `circuits.provider`, `netbox_contract.serviceprovider` |

## Validation (existing, unchanged)

- Both parts present or both absent (selector rule, "Please select a <type>."); for these two forms the field is required.
- The chosen type is within the allowed types; the object exists and is visible to the user.

## Added in this feature

| Rule | Where | Detail |
|------|-------|--------|
| Unique pair | `ContractAssignment.Meta.constraints` | `UniqueConstraint(fields=['contract', 'content_type', 'object_id'], name='netbox_contract_unique_assignment')` |
| Application check | `ContractAssignment.clean()` | error "<contract> is already assigned to <object>." when another row has the same triple; ignores the row itself |
| Migration `0054_contractassignment_unique` | before the constraint | merge duplicate groups: keep lowest id; move tags, journal entries, bookmarks, subscriptions, image attachments; fill empty custom fields; report groups and conflicting custom field values; delete the rest; no-op when no duplicate |
