# Contract: forms and URLs

Web-interface contract of this feature. REST, GraphQL, CSV import columns and filters are unchanged and are not repeated here.

## Contract assignment form

Route `plugins:netbox_contract:contractassignment_add` (`assignments/add/`) and the edit route.

| Submitted field | Meaning |
|-----------------|---------|
| `content_object_content_type` | primary key of the object's content type |
| `content_object_object_id` | primary key of the object |
| `contract` | primary key of the contract |
| `tags` | tag keys |

Pre-fill by the address, new form: `?content_object_content_type=<ct>&content_object_object_id=<id>&return_url=<url>`.
Pre-fill, accepted for compatibility: `?content_type=<ct>&object_id=<id>&return_url=<url>`; both forms behave identically and the new names win when both are present.

Clone of an assignment returns `content_object_content_type`, `content_object_object_id` and `contract` (plus tags).

Errors: only a type, or only an object: "Please select a <object type>." / "Both an object type and an object must be specified."

## Contract form

Route `contract_add` / `contract_edit`.

| Submitted field | Meaning |
|-----------------|---------|
| `external_party_object_content_type` | content type of the external party (service provider or circuit provider) |
| `external_party_object_object_id` | primary key of the external party |

A new contract opens with the type "service provider" selected. The old fields `external_party_object_type` and `external_party_object` are no longer submitted by the form; the model and the REST/CSV names are unchanged.

## Links built by the plugin

| Where | Before | After |
|-------|--------|-------|
| Add button on an object's Contracts tab (`AddContractAssignment`) | `?content_type=&object_id=&return_url=` | `?content_object_content_type=&content_object_object_id=&return_url=` |
| Inline table on the object page (`inc/contract_assignments_bottom.html`) | old names | new names |
| Add-another after saving | old names (override of `get_extra_addanother_params`) | new names, carried by the clone fields; the override is removed |

## Duplicate assignments

Saving a contract assignment whose contract and object equal those of another assignment fails with: `<contract> is already assigned to <object>.` (field error on the object in the form; non-field error in REST and CSV import, attached to the row). Editing an assignment without changing contract or object is accepted. REST status 400 on create/update.
