# Feature Specification: Choose related objects with a search selector

**Feature Branch**: `318-assess-against-netbox-4-7-4` (specification and implementation both stay on the issue #318 branch)

**Created**: 2026-10-29

**Status**: Draft

**Input**: User description: "Issue #318, opportunity 1 (see `.specify/assessments/netbox-47-opportunities/evaluation.md`): pick the assigned object of a contract assignment, and the external party of a contract, with NetBox 4.7's standard generic-object selector instead of a typed numeric ID and an unsearchable full list."

## Delivery Overview

Two forms let the user point a contract at an object of a type chosen at the same time: the contract assignment form (any supported object: device, site, rack, circuit, virtual machine, cluster, ...) and the contract form's external party (a service provider or a circuit provider). Today the assignment form asks for the object's database number, and the external party form lists every provider in one drop-down. This feature replaces both with the choose-a-type, then search-and-pick control that core NetBox pages use.

It needs NetBox 4.7, which raises the plugin's minimum NetBox version from 4.6.0 to 4.7.0. That change (minimum version, CI, README, changelog warning) is shared by the specifications 004 to 007 and is delivered by specification 008, implemented first. The two selectors change no stored data and no REST, GraphQL, import or bulk-edit interface. The same release also forbids duplicate assignments (User Story 4), which needs one migration: it merges existing duplicates, with a report, and then adds a uniqueness rule.

## Clarifications

### Session 2026-10-29

- Q: Which support policy for NetBox versions? → A: Raise the minimum NetBox version to 4.7.0 in the next minor release and use the 4.7 features; NetBox 4.6 users stay on plugin 2.5.x (option A of the #318 compatibility assessment). The plugin does not support 4.6 and 4.7 together.
- Q: Which branch carries the implementation? → A: The same branch as the specification, `318-assess-against-netbox-4-7-4`; no separate implementation branch is created for this feature.
- Q: What should happen when the contract is already assigned to the chosen object? → A: Forbid duplicate assignments (same contract, same object) in this feature, everywhere an assignment is created or changed (form, CSV import, REST API), and remove the duplicates that already exist when upgrading. This replaces the first answer of this session (keep accepting them, follow-up issue); no separate issue is needed.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Assign a contract to an object by choosing it (Priority: P1)

A user wants to record that a contract covers a device, a rack, a circuit or another supported object. From the object's **Contracts** tab, **Add contract** opens the assignment form with the object already chosen, and the user picks the contract. From the contract assignment list, **Add** opens the same form empty: the user chooses the type of object, then searches the objects of that type by typing part of a name, and picks one. Nobody has to know or type a database number.

**Why this priority**: this is the form people use daily, and the typed number is the main source of mistakes (assigning a contract to the wrong object, silently).

**Independent Test**: open the Contracts tab of a device, add an assignment, and check the device is preselected; then open the add form from the assignment list, choose a type, search for an object by name and save.

**Acceptance Scenarios**:

1. **Given** the Contracts tab of a device, **When** the user chooses **Add contract**, **Then** the form shows the device as the chosen object and asks only for the contract, and saving returns to the device page.
2. **Given** the assignment form opened from the list, **When** the user chooses the object type "site", **Then** the object field offers sites only and narrows its matches as the user types part of a name.
3. **Given** the `supported_models` setting lists only sites and devices, **When** the form is displayed, **Then** the object types offered are exactly sites and devices.
4. **Given** a user who may view only some devices (object permission with a constraint), **When** they search devices in the form, **Then** only the devices they may view are offered.
5. **Given** an existing assignment, **When** the user edits it, **Then** the current type and object are shown as selected, and changing the type clears the object.
6. **Given** a type chosen and no object, or an object and no type, **When** the user saves, **Then** a clear error says both are needed, and nothing is saved.
7. **Given** a contract assignment saved from the new form, **When** the REST API, the CSV export or the contract page lists it, **Then** it is the same assignment as one created before this change (same type, same object, same contract).

---

### User Story 2 - Choose the external party of a contract by searching (Priority: P2)

A user creating or editing a contract chooses whether the external party is a service provider or a circuit provider, then searches the providers of that kind by name instead of scrolling a list of all of them. The edit page of an existing contract shows the current external party.

**Why this priority**: the same improvement as story 1, on a form used less often and where the list is usually short. It also removes the hand-written code that fills the field.

**Independent Test**: create a contract choosing a circuit provider by typing part of its name; edit it and switch to a service provider.

**Acceptance Scenarios**:

1. **Given** the new contract form, **When** it is displayed, **Then** the external party type is "service provider" as today, and the external party must be chosen to save.
2. **Given** the type "circuit provider", **When** the user types part of a provider's name, **Then** matching circuit providers are offered.
3. **Given** an existing contract with a circuit provider, **When** the user edits it, **Then** the type and provider are shown as selected; **When** they switch the type to service provider, **Then** the previous provider is cleared and they must choose again.
4. **Given** a contract that has invoices or lines, **When** the external party is changed, **Then** the existing rules about changing a contract apply exactly as today.

---

### User Story 3 - Nothing else changes (Priority: P3)

Administrators and integrations see no difference elsewhere. CSV import of assignments and contracts, bulk edit, the REST API, GraphQL, filters and the saved data behave as before, and existing contracts and assignments need no upgrade step.

**Why this priority**: it protects public interfaces (constitution principle V) while the forms change.

**Independent Test**: run the existing import, bulk edit, REST and GraphQL tests unchanged.

**Acceptance Scenarios**:

1. **Given** a CSV of assignments using object type and object ID columns, **When** it is imported, **Then** the result is the same as before.
2. **Given** a bulk edit of assignments or contracts, **When** it is applied, **Then** the fields offered and their effects are the same as before.
3. **Given** a request to the REST API or GraphQL for assignments and contracts, **When** the response is read, **Then** it is identical to the one before this change.
4. **Given** the import, REST and bulk operations, **When** they create or change an assignment that is not a duplicate, **Then** they behave as before; the only new refusal is the duplicate (User Story 4).

---

### User Story 4 - A contract is assigned to an object only once (Priority: P2)

A user, an import or an integration tries to assign a contract to an object that already has this contract. It is refused with a message saying so, instead of silently creating a second identical assignment that doubles the object's contract lists, counts and exports. When upgrading, the duplicates that already exist are merged into one, with a report of what was merged.

**Why this priority**: duplicates are the data-quality problem the selector makes easier to create (one more click on the same pair), and later features (GraphQL counts, reports) assume one assignment per pair.

**Independent Test**: assign a contract to a device, repeat the same assignment through the form, the CSV import and the REST API, then run the upgrade on a database holding duplicates.

**Acceptance Scenarios**:

1. **Given** a contract already assigned to a device, **When** the user assigns the same contract to the same device in the form, **Then** the form shows an error naming the contract and the device and nothing is saved.
2. **Given** the same case, **When** a CSV import row or a REST create repeats the pair, **Then** it is refused with the same message (the row or request fails, other rows are unaffected as for any other import error).
3. **Given** an existing assignment, **When** it is edited (tags, comments) without changing contract or object, **Then** it saves; **When** it is edited to a pair that exists on another assignment, **Then** it is refused.
4. **Given** a database with three assignments of the same contract to the same device, with different tags, a journal entry on a removed one and a different custom field value, **When** the plugin is upgraded, **Then** one assignment remains (the oldest), carrying the union of the tags and the journal entry, its empty custom fields filled, the report lists every merged group with the removed identifiers, what was moved and the conflicting custom field values, and running the upgrade step again changes nothing.
5. **Given** two different contracts assigned to the same device, or the same contract assigned to two devices, **When** they are saved, **Then** they are accepted (only the exact pair is refused).
6. **Given** a database that bypassed the application (two inserts of the same pair), **When** the second insert is made, **Then** the database itself rejects it.

---

### Edge Cases

- Assigning a contract that is already assigned to the same object: refused with a clear message, in the form, the CSV import and the REST API (User Story 4); editing an assignment without changing its contract or object is not a duplicate of itself.
- A model listed in `supported_models` is not installed or comes from another plugin that has not finished loading: it is left out of the type list, as today, without breaking the form.
- An assigned object that has been deleted: its assignments are removed with it as today; editing a stale assignment shows no selected object and asks the user to choose.
- The page address already carries a type and an object (the **Add contract** link) and also a return address: both must be honoured; values typed by the user win over the address.
- The type is changed after an object was chosen: the object is cleared, other fields already typed (contract, tags) keep their values.
- A supported model with no searchable list (for example an object type whose list the user may not view): it is not offered, rather than showing an empty selector.
- Quick add and partial page refreshes of the form keep working.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The contract assignment form MUST let the user choose an object type and then search and pick an object of that type by name, without showing or requiring a numeric identifier.
- **FR-002**: The object types offered MUST be exactly the types allowed by the `supported_models` setting that exist on the installation.
- **FR-003**: The objects offered MUST be limited to those the current user may view.
- **FR-004**: The **Add contract** link on an object's Contracts tab MUST open the form with that object chosen, and saving MUST return the user to that object's page.
- **FR-005**: Editing an assignment MUST show its current type and object; changing the type MUST clear the object.
- **FR-006**: Saving with only one of type and object MUST be refused with a message naming both.
- **FR-007**: The contract form MUST let the user choose the external party type (service provider or circuit provider) and then search and pick one provider of that type; an external party remains required.
- **FR-008**: Editing a contract MUST show the current external party type and provider.
- **FR-009**: Except for the duplicate rule of FR-014 to FR-018, the saved data, CSV import and export, bulk edit, REST API, GraphQL and filters of assignments and contracts MUST NOT change.
- **FR-010**: The two selectors MUST NOT change any stored value; the only migration of the feature is the one of FR-016 and FR-017.
- **FR-011**: The plugin's minimum NetBox version becomes 4.7.0. Provided by specification 008 (minimum NetBox 4.7.0, CI on v4.7.4, README table, changelog warning, version 2.6.0); this specification only relies on it and has no task of its own for it.
- **FR-012**: The behaviour MUST be covered by tests that fail before the change, including the pre-filled link, the permission limit, the `supported_models` limit, edit, clone of an assignment and the unchanged interfaces (constitution principle II).
- **FR-013**: Both forms MUST remain usable through NetBox quick add and partial refreshes.
- **FR-014**: A contract MUST NOT be assigned twice to the same object: saving an assignment whose contract and object (type and identifier) are those of another assignment MUST be refused with a message naming the contract and the object, in the web form, the CSV import and the REST API; editing an assignment without changing that pair MUST remain possible.
- **FR-015**: The rule MUST also be enforced by the database, so that an insert that bypasses the application is rejected.
- **FR-016**: Upgrading MUST merge the existing duplicates before the rule is applied, without losing information: keep the oldest assignment of each group; move to it the tags, journal entries, bookmarks, subscriptions and image attachments of the others (a bookmark or subscription the same user already has on the kept one is dropped as redundant); fill the custom fields that are empty on the kept one from the others; then delete the others. Nothing else is changed.
- **FR-017**: The merge MUST print a report of every group merged (contract, object, kept and removed identifiers, what was moved) and, for every custom field with different non-empty values, the value kept and the value of the removed assignment, so that no value is lost silently; it MUST be safe to run again (second run: nothing to merge) and MUST do nothing when there are no duplicates beyond adding the rule.
- **FR-018**: The behaviour MUST be covered by tests that fail before the change: refusal in the form, import and REST, edit without change, different pairs accepted, the migration merge (tags, report, re-run) and the database rule.

### Key Entities

- **Contract assignment**: links one contract to one object of a supported type; the object is identified by its type and its identifier, shown to users as a name.
- **External party of a contract**: the service provider or circuit provider a contract is made with, identified the same way.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user can assign a contract to a device they have never opened by typing part of its name, without looking up or typing any number, in under 30 seconds.
- **SC-002**: With 5,000 providers, a user finds one by typing three letters, and the contract form opens as fast as with 10 providers.
- **SC-003**: 100% of the existing import, bulk edit, REST and GraphQL tests for assignments and contracts pass unchanged.
- **SC-004**: A user restricted to a subset of devices can never select, or see the name of, a device outside it in either form.
- **SC-005**: Upgrading leaves every external party and every non-duplicate assignment unchanged; a duplicate group is reduced to its oldest assignment, which keeps all tags, journal entries, bookmarks, subscriptions and image attachments of the group, with a report of each merge and of every conflicting custom field value.
- **SC-006**: After the upgrade, no pair (contract, object) appears twice, and an attempt to create a second one through any interface fails with a clear message.

## Assumptions

- Users are NetBox users with the usual view and add permissions on assignments and contracts.
- The 4.7 minimum is the shared prerequisite of specifications 004 to 007 and is delivered by specification 008, which is implemented first; these specifications rely on it.
- The external party stays limited to service providers and circuit providers (the existing setting of allowed types is not made configurable here).
- Duplicate assignments are forbidden here (previously planned as a follow-up issue); the cleanup command of specification 006 handles orphan assignments only and does not need to know about duplicates.
- Merging keeps the oldest assignment's values where both have one (conflicts are reported, with the removed value); a removed duplicate's changelog entries stay in NetBox's change log.
- Import and bulk-edit forms are out of scope: they keep separate type and identifier columns.
- The changelog entry goes under the release's New Features or Enhancements, not under a per-issue list (CLAUDE.md, "Changelog").
