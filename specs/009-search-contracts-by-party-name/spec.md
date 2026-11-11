# Feature Specification: Search contracts by external party name

**Feature Branch**: `333-search-contracts-by-party-name` (specification and implementation both stay on the issue #333 branch)

**Created**: 2026-11-11

**Status**: Draft

**Input**: User description: "Issue #333, proposals 1 and 2 only (see `.specify/assessments/search-by-external-party-name/intake.md`): the contract list quick search also matches the name of the contract's external party (service provider or circuit provider), and a party-name filter is added to the contract list, REST API and GraphQL next to the existing ID filters. Global search indexing (proposal 3) is out of scope."

## Delivery Overview

A contract's external party is the supplier or customer on the other side of the contract: a service provider or a circuit provider. Users remember that party by its name. Today, typing the name in the contract list search box finds nothing, and the only way to list a party's contracts is to filter by the party's database ID, which users must first look up. This feature lets users find contracts by the party's name in the list quick search, and filter by it in the contract list, REST API and GraphQL.

It stores nothing new: no model field, no migration. It adds one filter to three interfaces and widens what the quick search matches. Global (NetBox-wide) search is not changed.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Find a contract by typing its supplier's name (Priority: P1)

A user opens the contract list and types part of a supplier's name (a service provider or a circuit provider) in the search box. The list shows the active contracts whose external party's name contains that text, together with those that already matched on their own name, reference or comments.

**Why this priority**: This is the use case of the issue: users remember the name, not the ID. The quick search is the entry point nearly everybody uses.

**Independent Test**: Create a service provider "Acme Telecom" and a circuit provider "Globex Carrier", one Active contract for each, and an unrelated contract. Searching "acme" lists the first contract only; searching "carrier" lists the second only.

**Acceptance Scenarios**:

1. **Given** an Active contract whose external party is the service provider "Acme Telecom", **When** the user searches "acme" in the contract list, **Then** the contract is listed.
2. **Given** an Active contract whose external party is the circuit provider "Globex Carrier", **When** the user searches "carrier", **Then** the contract is listed.
3. **Given** an Active contract whose own name contains the search text and another whose party name contains it, **When** the user searches that text, **Then** both are listed once each.
4. **Given** a contract whose party name matches but whose status is not Active, **When** the user searches that name, **Then** the contract is not listed, as for any other quick-search match today.
5. **Given** a contract without an external party, **When** the user searches any text, **Then** it is listed only if its own name, reference or comments match.

---

### User Story 2 - Filter contracts by party name in the list, REST API and GraphQL (Priority: P2)

A user, a script or an integration lists the contracts of a party knowing only its name: through a filter on the contract list (the filter form and the address), a filter on the contracts REST endpoint, and a filter on the contract list query in GraphQL. The filter sits next to the existing service provider and circuit provider ID filters, which keep working unchanged.

**Why this priority**: It serves automation and bookmarkable views, but the quick search already covers the interactive need.

**Independent Test**: With the contracts of Story 1, request the contract list filtered by party name "Acme Telecom" in the list view, the REST endpoint and a GraphQL query; each returns the Acme contract only.

**Acceptance Scenarios**:

1. **Given** contracts of several parties, **When** the contract list is filtered by a party name, **Then** only the contracts whose external party, service provider or circuit provider, has that name are listed.
2. **Given** the same data, **When** the REST contracts endpoint and the GraphQL contract list query are filtered by the same name, **Then** they return the same contracts as the list view.
3. **Given** a service provider and a circuit provider with the same name, **When** the filter is applied with that name, **Then** the contracts of both are returned.
4. **Given** a contract with a status other than Active whose party name matches, **When** the filter is applied, **Then** the contract is returned (unlike the quick search, the filter does not restrict the status; it combines with the status filter).
5. **Given** the existing `service_provider_id` and `provider_id` filters, **When** they are used as before, **Then** they return the same contracts as before this feature.

---

### Edge Cases

- The search text matches several parties (for example "tele"): all their contracts are listed.
- A provider is renamed: the next search and the next filter use the new name immediately; nothing is indexed, so nothing can be stale.
- A party is deleted, or its type is no longer present: its contracts are not matched by name and the list still renders.
- The search text is empty: the list is unchanged.
- Letter case differs ("ACME" against "Acme Telecom"): the quick search matches; the filter follows the same rule as the plugin's other name filters.
- A service provider and a circuit provider share the same numeric ID: only the contracts of the party with the matching name are listed, never those of the other party type.
- Many contracts and parties: the list stays within its recorded query count (see 009-SC-003).

## Requirements *(mandatory)*

### Functional Requirements

- **009-FR-001**: The contract list quick search MUST also list contracts whose external party is a service provider whose name contains the search text.
- **009-FR-002**: The contract list quick search MUST also list contracts whose external party is a circuit provider whose name contains the search text.
- **009-FR-003**: The quick search MUST match the party name regardless of letter case, and MUST list a contract once even when several of its fields match.
- **009-FR-004**: The quick search MUST keep its current behaviour for the other fields and for the status: only Active contracts are listed, and a contract is still found by its name, external reference or comments.
- **009-FR-005**: A party-name match MUST consider the party's type: a contract is matched through the provider of its own party type, never through a provider of the other type that has the same ID.
- **009-FR-006**: The contract list MUST offer a filter on the external party name, in its filter form and its address, matching contracts whose service provider or circuit provider name satisfies the filter.
- **009-FR-007**: The contracts REST endpoint MUST accept the same filter, with the same result as the list view.
- **009-FR-008**: The GraphQL contract list query MUST accept the same filter, with the same result as the list view.
- **009-FR-009**: The party-name filter MUST combine with the other contract filters, and MUST NOT restrict the status by itself.
- **009-FR-010**: The `service_provider_id` and `provider_id` filters, the contract fields and the REST and GraphQL outputs MUST stay unchanged; the new filter is additive (Constitution V).
- **009-FR-011**: The new filter and the quick search MUST NOT reveal anything the user may not already see: they return contracts the user may view, as the list does today, and a provider's name is only used for matching, never added to the output.
- **009-FR-012**: The feature MUST NOT change what NetBox's global search indexes (issue #333, proposal 3 is out of scope).
- **009-FR-013**: The documentation, the changelog, the French translation of any new label and the global specifications (REST, GraphQL, UI, behaviours) MUST describe the new search and filter (Constitution VII, VIII).

### Key Entities

- **Contract**: has at most one external party, either a service provider or a circuit provider; the party is identified by its type and ID.
- **Service provider** (plugin) and **circuit provider** (NetBox core): the two kinds of external party; only their name is used here.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **009-SC-001**: A user finds the contracts of a supplier by typing any part of its name in the contract list search, for both party types, with no lookup of an ID first.
- **009-SC-002**: The list view, the REST endpoint and the GraphQL query return the same contracts for the same party-name filter in every test case.
- **009-SC-003**: The contract list needs no more database queries than today beyond the added match (a fixed number, independent of the number of contracts or parties); the recorded list-view query counts change only by that fixed amount, with a stated reason.
- **009-SC-004**: Every request that worked before this feature, including the ID filters and the quick search by name, reference and comments, returns the same result as before.

## Assumptions

- One filter serves both party types, matching on the name with the usual lookup modifiers that NetBox filters offer (contains, exact, negation and the like); the quick search uses "contains". The filter's exact name and modifiers are a planning decision.
- The quick search keeps its Active-only restriction as is (009-FR-004); changing it is a separate request.
- Only the name of the party is searched, not its slug, description or other fields.
- A party type other than service provider and circuit provider cannot be a party today; a future type would need its own match.
- Global search is unchanged (proposal 3 of the issue); it may be handled in a separate issue because NetBox re-indexes an object only when it is saved.
- The issue #333 is not yet triaged; the maintainer asked for this work explicitly.
