# Research: generic-object selector

Prototype run on NetBox v4.7.4 (Python 3.13, PostgreSQL 16) with a probe form `class AssignForm(GenericObjectFormMixin, NetBoxModelForm)` on `ContractAssignment`. No NEEDS CLARIFICATION remains.

## R1 - Use the NetBox selector for both forms

- **Decision**: declare `content_object = GenericObjectChoiceField(...)` on `ContractAssignmentForm` and `external_party_object = GenericObjectChoiceField(...)` on `ContractForm`, each form deriving from `GenericObjectFormMixin` listed before `NetBoxModelForm`.
- **Rationale**: NetBox's circuits, ipam and dcim forms use exactly this pattern (`CircuitTerminationForm`, `CircuitGroupAssignmentForm`). The probe showed: valid data saves a device assignment with the right type and ID; a type without an object gives "Please select a device."; the object field renders the selected device.
- **Alternatives**: keep the two fields and add search to the object field (rejected: re-implements the platform control and keeps the custom code); a `DynamicModelChoiceField` per type (rejected: the number of types is configurable).

## R2 - Field name equals the generic foreign key name

- **Decision**: the form fields are named `content_object` and `external_party_object`, the names of the model's `GenericForeignKey`s, and the mixin assigns the chosen object through them (setting both stored columns). The submitted names become `content_object_content_type` / `content_object_object_id` and `external_party_object_content_type` / `external_party_object_object_id`.
- **Rationale**: the mixin assigns to `gfk_name or field_name`; NetBox's own cloning of a generic foreign key (`clone_fields`) emits `<gfk>_content_type` / `<gfk>_object_id`, so the Clone button works with no extra code.
- **Consequence**: `Meta.fields` lists only the model's real form fields (`contract`, `tags`, ...), and the stored columns are not form fields; model validation skips them, the mixin sets them in `clean()` before saving.

## R3 - Pre-fill parameters

- **Decision**: new links use the new names. The assignment form also accepts the old `content_type` and `object_id` parameters by copying them to the new initial keys in `__init__` when the new ones are absent, and the Add-another redirect keeps the object through the clone fields (the view override `get_extra_addanother_params` was removed: with `clone_fields` it appended the same parameters a second time).
- **Rationale**: three places build the old link (the Add button class in `views.py`, the inline table template `inc/contract_assignments_bottom.html`, and the add-another params), and users may have bookmarks. The probe could not prove that the old keys alone select the object, so the mapping is explicit and tested.
- **Alternatives**: break the old links (rejected: public-facing URLs, constitution V in spirit).

## R4 - Remove the view workarounds

- **Decision**: delete `ContractEditView.alter_object` (it copied the posted type and ID onto the object because the old form could not) and the unreachable `ContractAssignmentEditView.alter_object` (it assigns `instance.object`, an attribute that does not exist, and runs only when the object has no pk but URL arguments exist, which never happens).
- **Rationale**: the mixin does the assignment; keeping the code would be dead or contradictory. Verified by reading `views.py` lines 190-207 and 410-440.

## R5 - Default external party type

- **Decision**: a new contract opens with the type "service provider" selected, as today, by seeding the field's initial content-type key in `ContractForm.__init__` when the form is unbound, has no instance primary key and no value in the address.
- **Alternatives**: no default (rejected: changes the first-screen behaviour of every new contract).

## R6 - Which types are offered

- **Decision**: `content_type_queryset=ContentType.objects.filter(ASSIGNEMENT_MODELS)` for assignments and `...filter(SERVICE_PROVIDER_MODELS)` for the external party (the existing `Q` objects in `constants.py`).
- **Rationale**: `supported_models` entries that do not resolve to an installed model have no content type row, so they disappear without error (spec edge case). The selector reads objects through each model's REST list endpoint, so a supported model needs one; NetBox core models have it. A model without an endpoint would give a dead selector, so the form drops content types for which `get_action_url(model, 'list', rest_api=True)` raises `NoReverseMatch`.

## R7 - Documentation of the constraint

- **Decision**: add one sentence to `docs/contract.md` (and the `supported_models` description in the README if it has one): a supported model must be exposed in NetBox's REST API.
- **Rationale**: an administrator who adds a model by hand needs to know why it may not be offered.

## R8 - Tests

- **Decision (selector)**: update the form-data of the two NetBox view test cases to the new names (they must fail first), and add `test_assignment_selector.py` for: pre-filled Add link (new and old names), return to the object's page, `supported_models` limit, constrained view permission (the object is not selectable), missing object error, edit shows current values and a type change clears the object, assignment clone parameters, unchanged CSV import / bulk edit / REST.
- **Rationale**: the NetBox test cases post `form_data` and do not know about the selector's names; the other behaviours are plugin-specific.

## R9 - Query counts

- **Decision**: no baseline change expected; the baseline covers list views only. If the contract list or assignment list count moves, the cause is investigated, not re-recorded (constitution II).

## R10 - No duplicate assignments

- **Decision**: three layers. (1) `ContractAssignment.clean()` raises a `ValidationError` when another assignment has the same contract, content type and object id (excluding itself), message naming the contract and the object. NetBox runs `full_clean()` for forms, REST (`ValidatedModelSerializer`) and CSV import, so all three refuse with the same message. (2) `Meta.constraints = [UniqueConstraint(fields=['contract', 'content_type', 'object_id'], name='netbox_contract_unique_assignment')]` as the database backstop. (3) Migrations `0054_merge_duplicate_assignments` and `0055_contractassignment_unique`: a `RunPython` step first merges duplicates, then `AddConstraint`.
- **Why `clean()` and not only the constraint**: Django skips constraint validation when one of the constraint fields is not a form field, and with the selector `content_type`/`object_id` are no longer form fields (R2). Without `clean()` the form would end in a database error page. Verified by reading `BaseModelForm._get_validation_exclusions` and the selector mixin.
- **Merge rules** (lossless, constitution IV): group by (contract, content type, object id); keep the lowest primary key. For each removed row: re-point to the kept row its tags (`extras.TaggedItem`, skipping tags the kept row has), journal entries (`JournalEntry.assigned_object_type/id`), bookmarks and subscriptions (skipping a user who already has one on the kept row, whose unique rule would otherwise fail) and image attachments (`ImageAttachment`); fill each custom field that is empty on the kept row from the removed row; list every custom field where both rows have different non-empty values, with the kept and the removed value in the report (nothing is silently dropped); then delete the removed rows. Their change-log entries (`ObjectChange`) stay. The step is skipped when no group has more than one row. Reverse: the constraint is dropped; deleted rows are not restored (stated in the changelog).
- **Report channel**: written to the migration's stdout (visible in `manage.py migrate` output) and to the `netbox_contract` logger.
- **Alternatives**: constraint only (rejected: the form error above); failing the migration when duplicates exist (rejected: forces manual cleanup of production data); keeping duplicates (the first 2026-10-29 answer, replaced by the owner on 2026-10-30).
- **Tests**: duplicate refused in form (message names contract and object), CSV import and REST; edit without change saves; moving onto an existing pair refused; different pairs accepted; merge test with three duplicates, differing tags, a journal entry, a bookmark of the same user on two rows, empty and conflicting custom fields (everything moved or reported, oldest kept, report text, second run no-op); database rejects a raw insert of the pair.

## Implementation notes (2026-10-30)

- **R6 deviation**: content types without a REST list endpoint are not filtered out of the type list; the form offers every installed type of `supported_models`. Filtering would need a database query while the form class is built; the constraint is documented instead (README `supported_models`, `docs/contract.md`).
- **R10 detail**: `ContractAssignment.validate_constraints()` is overridden to do nothing: `clean()` reports the pair with the contract and object names, and Django's generic constraint message would be added a second time on REST and import. The database constraint remains the backstop.
- **R10 detail**: the merge function is `merge_duplicates(apps)` in `0054_merge_duplicate_assignments.py`; its tests drop the unique rule inside the test transaction to create old-style duplicates, then call it directly (rolled back with the test).
- **Settings**: `mandatory_contract_fields` / `hidden_contract_fields` entries `external_party_object_type` are kept as an alias of `external_party_object` (`apply_field_settings(..., aliases=...)`), without a warning; the field is always required, so mandatory is a no-op and hidden is ignored.
