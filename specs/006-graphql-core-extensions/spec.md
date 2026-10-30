# Feature Specification: Contracts reachable from devices, sites and other objects in GraphQL

**Feature Branch**: `318-assess-against-netbox-4-7-4` (specification and implementation both stay on the issue #318 branch)

**Created**: 2026-10-29

**Status**: Draft

**Input**: User description: "Issue #318, opportunity 3 (see `.specify/assessments/netbox-47-opportunities/evaluation.md`): use NetBox 4.7's ability for a plugin to add fields and filters to core GraphQL types, so that a client can read the contracts of a device, site, rack, circuit, virtual circuit, virtual machine or cluster in one query, and list the objects that have or lack a contract."

## Delivery Overview

The plugin's GraphQL API lets a client list contract assignments and read the assigned object. The other direction is missing: starting from a device or a site, a client cannot ask for its contracts, and cannot ask "which devices have no contract". Integrations (inventory exports, coverage reports, dashboards) must fetch all assignments and join them themselves. This feature adds, on the objects that can have contracts, a way to read their contracts and two filters, all inside the standard NetBox GraphQL endpoint.

It needs NetBox 4.7 (see Assumptions). It changes no existing GraphQL, REST or web interface and no stored column. It does change one behaviour: deleting a device, site or other covered object now also deletes its contract assignments (FR-012), and an administrator command removes the orphan assignments that earlier deletions left (User Story 4).

## Clarifications

### Session 2026-10-29

- Q: Which support policy for NetBox versions? → A: Raise the minimum NetBox version to 4.7.0 in the next minor release and use the 4.7 features; NetBox 4.6 users stay on plugin 2.5.x (option A of the #318 compatibility assessment). The plugin does not support 4.6 and 4.7 together.
- Q: Which branch carries the implementation? → A: The same branch as the specification, `318-assess-against-netbox-4-7-4`; no separate implementation branch is created for this feature.
- Q: Does a contract with status active but an end date in the past count as active for the "has an active contract" filter? → A: Yes. Active means the contract's status is active, whatever its dates; start and end dates are not considered.
- Q: Should the filters count contracts the user may not view? → A: No. The filters count only contracts and assignments the user may view, so a user without contract permission sees every object as having no contract and learns nothing about hidden contracts.
- Q: Reaching assignments from a device, site and the other objects needs a link from those objects to their assignments, which also removes an object's assignments when the object is deleted (today they stay as orphan rows; confirmed on NetBox 4.7.4). Accept this? → A: Yes. Deleting an object removes its contract assignments. Orphan rows that already exist are handled by the cleanup command of User Story 4. The changelog lists the deletion behaviour under Breaking Changes.
- Q: Clean up the orphan assignments that deletions left before this release? → A: Yes, in this feature, as an explicit administrator command (not an automatic migration): it reports first and deletes only on request, so no user data is removed silently (constitution principle IV). The earlier decision to leave them untouched is replaced.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Read the contracts of an object in one query (Priority: P1)

An integration developer queries a device (or a site, rack, circuit, virtual circuit, virtual machine or cluster) and asks, in the same request, for its contract assignments and, for each, the contract's name, status, end date and external party. One request returns the object and its contracts.

**Why this priority**: it is the whole point of the feature, and the case integrations hit first.

**Independent Test**: assign two contracts to a device, query the device with its contracts, and compare with the web interface's Contracts tab.

**Acceptance Scenarios**:

1. **Given** a device with two assigned contracts, **When** a client queries the device asking for its contracts, **Then** both are returned with the requested contract fields.
2. **Given** a device with no contract, **When** the same query is made, **Then** the contracts list is empty and there is no error.
3. **Given** a user who may view devices but not contracts, **When** they run the query, **Then** the device is returned with an empty contracts list.
4. **Given** a user whose contract permission is limited by a constraint (for example one tenant's contracts), **When** they run the query, **Then** only the contracts they may view are returned.
5. **Given** the models of the `supported_models` setting, **When** the schema is read, **Then** the contracts field exists on every one of those models that has a GraphQL type, and on no other type.
6. **Given** a query for 200 devices with their contracts, **When** it runs, **Then** the work done does not grow device by device (the number of database queries is the same for 2 devices and for 200).

---

### User Story 2 - Find objects with or without a contract (Priority: P2)

A user preparing a coverage report lists devices (or any supported object) that have at least one contract, that have none, or that have an active contract, by adding a filter to the standard list query. Typical question: "which devices have no active contract?".

**Why this priority**: it turns the read access of story 1 into a direct answer for audit and renewal work, without downloading everything.

**Independent Test**: with three devices (no contract, one cancelled contract, one active contract), run each filter and check the returned devices.

**Acceptance Scenarios**:

1. **Given** the three devices above, **When** the list is filtered with "has contracts" true, **Then** the devices with a cancelled or an active contract are returned.
2. **Given** the same devices, **When** the filter "has contracts" is false, **Then** only the device without contract is returned.
3. **Given** the same devices, **When** the filter "has an active contract" is true, **Then** only the device with an active contract is returned; **When** it is false, **Then** the other two are returned.
4. **Given** a user who may not view contracts, **When** they use the filters, **Then** the filters see no contract (results as if no contract existed), so contract data is not disclosed through filtering.
5. **Given** the filters combined with the standard device filters (site, status, name), **When** the query runs, **Then** all conditions apply together.

---

### User Story 3 - Existing GraphQL clients are unaffected (Priority: P3)

Queries written for the current plugin GraphQL API, and for NetBox core types, keep working with the same results, and the core types keep working when the plugin is not installed or is disabled.

**Why this priority**: GraphQL is a public interface (constitution principle V).

**Independent Test**: run the existing plugin GraphQL tests unchanged.

**Acceptance Scenarios**:

1. **Given** the plugin GraphQL tests written before this change, **When** they run, **Then** they pass unchanged.
2. **Given** another plugin that also extends the device type, **When** NetBox starts with both plugins, **Then** both load, with no clash of field names.

---

### User Story 4 - Clean up orphan assignments left by earlier deletions (Priority: P3)

An administrator runs a command that lists the contract assignments whose device, site or other object has been deleted (they stayed in the database before this release), checks the list, then runs it again asking to delete them.

**Why this priority**: housekeeping; nothing else depends on it, but the new filters and fields should not have to live with stale rows.

**Independent Test**: create assignments, delete the assigned objects the old way (orphans), run the command twice.

**Acceptance Scenarios**:

1. **Given** two orphan assignments and one valid assignment, **When** the command runs without options, **Then** it reports the two orphans (contract, object type, former identifier) and deletes nothing.
2. **Given** the same data, **When** it runs asking to delete, **Then** exactly the two orphans are removed and the valid assignment stays.
3. **Given** the cleanup done, **When** it runs again, **Then** it reports none and changes nothing.
4. **Given** an assignment whose object type is no longer installed, **When** the command runs in either mode, **Then** it is reported separately and kept.

---

### Edge Cases

- A model listed in `supported_models` that has no GraphQL type (for example a custom object type): no field or filter is added for it, and NetBox still starts.
- A model removed from `supported_models` after assignments were made: no field is added; the assignments stay in the database and in the existing assignments API.
- A contract with many assignments or an object with many contracts: results follow the standard pagination limits.
- A deleted contract: its assignments are removed with it, as today. A deleted object (device, site, ...): its assignments are removed with it from this release on; today they stay in the database as orphan rows, which the cleanup command (User Story 4) lists and, on request, removes.
- A client asking only for the object name: no contract work is done.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Each GraphQL type of an object that can have contracts MUST offer a field returning the object's contract assignments, from which the contract and its fields can be read.
- **FR-002**: The types extended MUST be exactly those of the `supported_models` setting that have a GraphQL type.
- **FR-003**: Only contracts and assignments the current user may view MUST be returned, including object permission constraints.
- **FR-004**: The list query of each extended type MUST accept a filter on "has contracts" and a filter on "has an active contract" (a contract whose status is active, whatever its dates), each true or false.
- **FR-005**: The filters MUST respect the user's view permission on contracts and assignments, and MUST combine with the existing filters.
- **FR-006**: The number of database queries to serve a list of objects with their contracts MUST NOT grow with the number of objects.
- **FR-007**: Existing plugin GraphQL queries, REST API and web pages MUST NOT change, with one stated exception (FR-012).
- **FR-008**: The new names MUST NOT collide with names provided by NetBox or other plugins; a collision MUST NOT prevent NetBox from starting.
- **FR-009**: The documentation of the API (`docs/api.md`) MUST describe the new fields, the filters and the permission behaviour, with an example query; the changelog MUST list them under REST API Changes or the release's GraphQL section.
- **FR-010**: The plugin's minimum NetBox version becomes 4.7.0. Provided by specification 008 (minimum NetBox 4.7.0, CI on v4.7.4, README table, changelog warning, version 2.6.0); this specification only relies on it and has no task of its own for it.
- **FR-011**: The behaviour MUST be covered by tests that fail before the change: each scenario above, the permission cases, the query-count check and the unchanged existing queries (constitution principle II).
- **FR-012**: Deleting an object that can have contracts MUST also delete its contract assignments; the upgrade itself MUST NOT delete or change any existing assignment, and the changelog MUST list the deletion behaviour under Breaking Changes.
- **FR-013**: An administrator command MUST find the orphan contract assignments (assignments whose object no longer exists) and report them: how many, per object type, with the contract and the former object identifier of each.
- **FR-014**: The command MUST delete nothing unless explicitly told to; when told to, it MUST delete exactly the orphans it reported, in one transaction, and a second run MUST find none.
- **FR-015**: Assignments whose object type no longer exists in the installation MUST be reported separately and MUST NOT be deleted by the command (the situation cannot be judged safely).
- **FR-016**: The command and its dry-run default MUST be documented (`docs/`, changelog Enhancements), and covered by tests that fail before the change: report, no deletion by default, deletion on request, re-run, assignments with a valid object untouched, unknown object type reported not deleted.

### Key Entities

- **Contract assignment**: the existing link between a contract and an object of a supported type.
- **Contract**: the existing contract, with its status (active or cancelled) used by the "active" filter.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A client obtains a device and its contracts with one request instead of two requests plus a client-side match.
- **SC-002**: "Devices without an active contract" is answered by one filtered request, with no client-side processing.
- **SC-003**: A list of 200 devices with their contracts costs the same number of database queries as a list of 2.
- **SC-004**: A user without permission on contracts never receives a contract name, status or amount through the new fields or filters.
- **SC-005**: 100% of the existing plugin GraphQL tests pass unchanged.
- **SC-006**: After the cleanup command is run on a database with orphans, a second run reports none, and the orphan count shown by the first run equals the number of rows removed.

## Assumptions

- The 4.7 minimum is the shared prerequisite of specifications 004 to 007.
- "Active" means the contract status "active", whatever the start and end dates (the plugin's status choices; installations that replace the status choices through `FIELD_CHOICES` keep the value `active` for this purpose).
- Only the two boolean filters are in scope; filtering by contract type, tenant, dates or external party can follow if users ask.
- The fields are read-only, as the rest of the plugin's GraphQL API.
- Orphan cleanup is an explicit command, run by an administrator after upgrading; it is not run by the upgrade.
- The REST API is not extended here: the REST filters of the assignments list already allow the same questions.
