# Feature Specification: Breadcrumbs declared with the page layouts

**Feature Branch**: `318-assess-against-netbox-4-7-4` (specification and implementation both stay on the issue #318 branch)

**Created**: 2026-10-29

**Status**: Draft

**Input**: User description: "Issue #318, opportunity 2 (see `.specify/assessments/netbox-47-opportunities/evaluation.md`): declare the breadcrumbs of the contract, contract line, invoice and invoice line pages with NetBox 4.7's layout breadcrumbs, and remove the four page templates that exist only to add them."

## Delivery Overview

The contract, contract line, invoice and invoice line pages add one navigation link each above the page title (the "breadcrumb trail"). They do it through four small page templates that otherwise do nothing, while every other part of these pages is already declared in NetBox's standard page layout. NetBox 4.7 lets the layout declare the trail. This feature moves the four trails there and removes the four templates. The visible result is the same trail, with two improvements found while preparing the plan (both confirmed by rendering the pages on NetBox 4.7.4): the contract page's trail entry is empty today, because its template asks for a property the contract does not have, and an invoice linked to several contracts shows its links run together in one entry. After this change the contract entry names the external party, and each contract of an invoice has its own entry.

It needs NetBox 4.7 (see Assumptions). It changes no data, no migration, no permission and no API.

## Clarifications

### Session 2026-10-29

- Q: Which support policy for NetBox versions? → A: Raise the minimum NetBox version to 4.7.0 in the next minor release and use the 4.7 features; NetBox 4.6 users stay on plugin 2.5.x (option A of the #318 compatibility assessment). The plugin does not support 4.6 and 4.7 together.
- Q: Which branch carries the implementation? → A: The same branch as the specification, `318-assess-against-netbox-4-7-4`; no separate implementation branch is created for this feature.
- Q: Should a trail entry be hidden when the user cannot view the related object? → A: No. Keep today's behaviour: the entry is shown with its name and link whatever the user's permission on the related object; the list it opens applies the user's permissions as usual.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The same trail on the four pages (Priority: P1)

A user opening a contract, a contract line, an invoice or an invoice line sees the same navigation as today: the list of that object type, then the related object, each as a link to the corresponding filtered list.

**Why this priority**: navigation links are used all the time, and the change must not lose any of them.

**Independent Test**: open one object of each of the four types and compare the trail, link by link, with the trail shown before the change.

**Acceptance Scenarios**:

1. **Given** a contract, **When** its page is displayed, **Then** the trail shows the contract list, then the name of the contract's external party (an empty link today); the second link opens the contract list filtered to that external party, whether it is a service provider or a circuit provider.
2. **Given** a contract line, **When** its page is displayed, **Then** the trail shows the contract line list, then the line's contract; the second link opens the contract line list filtered to that contract.
3. **Given** an invoice, **When** its page is displayed, **Then** the trail shows the invoice list, then the invoice's contract; the second link opens the invoice list filtered to that contract.
4. **Given** an invoice line, **When** its page is displayed, **Then** the trail shows the invoice line list, then the line's invoice number; the second link opens the invoice line list filtered to that invoice.
5. **Given** any of the other plugin pages (unit, service provider, contract type, accounting dimension, contract assignment), **When** it is displayed, **Then** its trail is unchanged: the list of that object type only.

---

### User Story 2 - One link per contract on invoices (Priority: P2)

An invoice created before the one-contract rule can still be linked to several contracts. Today their links appear side by side inside a single trail entry, without separation. With this change each contract is its own trail entry, so each link is distinct and clickable on its own.

**Why this priority**: it is the only visible difference, and it fixes a readability defect on legacy invoices.

**Independent Test**: open an invoice linked to two contracts and check the trail shows two separate entries, each opening the invoice list filtered to its contract.

**Acceptance Scenarios**:

1. **Given** an invoice linked to two contracts, **When** its page is displayed, **Then** the trail shows the list entry and two contract entries, in the same order as the contracts are listed on the page.
2. **Given** an invoice linked to no contract (a template), **When** its page is displayed, **Then** the trail shows only the list entry and no empty entry.

---

### User Story 3 - Maintainers keep the pages in one place (Priority: P3)

A maintainer who changes the content of these pages finds the whole page, including its trail, in one declaration, as on core NetBox pages, and no longer has to keep four extra page templates in step with each NetBox release.

**Why this priority**: it is the reason for the change, but users do not see it.

**Independent Test**: check that the four templates are gone and that the pages still render in every test that opens them.

**Acceptance Scenarios**:

1. **Given** the plugin's templates, **When** they are listed, **Then** none of the four pages has a page template of its own whose only purpose is the trail.
2. **Given** the existing tests that open these pages, **When** they run, **Then** they pass.

---

### Edge Cases

- A related object the user may not view: the entry is shown with its name and link exactly as today; the list it opens applies the user's permissions.
- An object whose related object is missing (a contract line whose contract is unavailable, an invoice without a contract): no empty entry and no error.
- A related object name containing special characters: it is escaped.
- Plugin content added by other plugins on these pages is unaffected.
- The tabs of a contract (change log, journal, other plugins' tabs) show the same trail as the contract page, as they do today.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The four pages MUST show the trails of User Story 1; the contract line, invoice and invoice line entries MUST link to the same filtered lists as before, and the contract entry MUST name the external party and link to the contracts of that external party.
- **FR-002**: An invoice linked to several contracts MUST show one separate trail entry per contract, and an invoice without a contract MUST show no contract entry.
- **FR-003**: The trails of the other plugin pages MUST NOT change.
- **FR-004**: The four page templates that only add a trail MUST be removed, and the trails MUST be declared with the pages' layouts.
- **FR-005**: The feature MUST NOT change data, permissions, REST, GraphQL or any other page content.
- **FR-006**: The plugin's minimum NetBox version becomes 4.7.0. Provided by specification 008 (minimum NetBox 4.7.0, CI on v4.7.4, README table, changelog warning, version 2.6.0); this specification only relies on it and has no task of its own for it.
- **FR-007**: The behaviour MUST be covered by tests that fail before the change, reading the trail of each of the four pages, the invoice with two contracts and the invoice without contract (constitution principle II).
- **FR-008**: The trail entries MUST NOT depend on the user's permission on the related object, as today.

### Key Entities

- **Breadcrumb trail**: the ordered links above a page title: the object type's list, then the related object.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of the working trail links of the contract line, invoice and invoice line pages are present after the change with the same destination, and the contract page's trail entry shows the external party name instead of an empty link.
- **SC-002**: On an invoice linked to two contracts, a user can open the list of invoices of either contract in one click, and each link is visually separate.
- **SC-003**: The number of page templates kept only for a trail goes from four to zero.
- **SC-004**: The existing tests that display these pages pass without change other than the new trail assertions.

## Assumptions

- The 4.7 minimum is the shared prerequisite of specifications 004 to 007 and is delivered by specification 008, which is implemented first; these specifications rely on it.
- The existing destinations (filtered lists) are kept; adding new entries (for example the contract on an invoice line) is out of scope.
- The deprecated invoice templates (invoices flagged as templates) are shown only when `show_deprecated_fields` is on; their trail follows the same rules.
- The changelog lists the empty contract entry under Bug Fixes and the rest under Other Changes of the release (CLAUDE.md, "Changelog").
