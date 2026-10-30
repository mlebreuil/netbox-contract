# Feature Specification: Describe the status and billing choices

**Feature Branch**: `318-assess-against-netbox-4-7-4` (specification and implementation both stay on the issue #318 branch)

**Created**: 2026-10-29

**Status**: Draft

**Input**: User description: "Issue #318, opportunity 4 (see `.specify/assessments/netbox-47-opportunities/evaluation.md`): use NetBox 4.7's choice descriptions so that the invoice status, contract status and unit billing method drop-downs explain what each option means, in English and French."

## Delivery Overview

When a user picks an invoice status or a unit's billing method, the options are a label and a colour. Nothing says that a Posted invoice locks its amounts, or how a usage-based unit differs from a recurring one; users find out from the documentation or by hitting an error. NetBox 4.7 can show a short description under each option of a drop-down. This feature adds those descriptions to the plugin's built-in choices and shows them where users choose.

It needs NetBox 4.7 (see Assumptions). It changes no stored value, no migration, and no REST, GraphQL, import or filter interface.

## Clarifications

### Session 2026-10-29

- Q: Which support policy for NetBox versions? → A: Raise the minimum NetBox version to 4.7.0 in the next minor release and use the 4.7 features; NetBox 4.6 users stay on plugin 2.5.x (option A of the #318 compatibility assessment). The plugin does not support 4.6 and 4.7 together.
- Q: Which branch carries the implementation? → A: The same branch as the specification, `318-assess-against-netbox-4-7-4`; no separate implementation branch is created for this feature.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Know what Draft and Posted mean before choosing (Priority: P1)

A user editing an invoice opens the status drop-down and reads, under Draft, Posted and Canceled, one sentence saying what that status does (for example that Posted freezes the amounts, currency, period and contracts). They choose with the consequence in mind.

**Why this priority**: Posted is the one irreversible-looking choice in the plugin; explaining it at the moment of choice prevents the most expensive mistake.

**Independent Test**: open the invoice add form and read the descriptions under the status options; compare with the lock rules in the user documentation.

**Acceptance Scenarios**:

1. **Given** the invoice form, **When** the user opens the status drop-down, **Then** each of Draft, Posted and Canceled has a one-sentence description, and the Posted description names what becomes locked.
2. **Given** the invoice filter form and bulk edit form, **When** the status drop-down is displayed, **Then** the same descriptions appear wherever NetBox displays descriptions for that kind of drop-down.
3. **Given** a French user, **When** the drop-down is displayed, **Then** the descriptions are in French.
4. **Given** an invoice list or page, **When** a status badge is displayed, **Then** it still shows the same label and colour as before.

---

### User Story 2 - Understand the billing method of a unit (Priority: P2)

A user creating a unit chooses its billing method (One-time, Recurring, Usage-based) and reads under each what it means for invoicing: billed once from quantity and price; billed every period and prorated to the invoice period; billed from a quantity entered on each invoice.

**Why this priority**: the billing method drives how invoices are computed, and the labels alone are ambiguous ("usage-based").

**Independent Test**: open the unit add form and read the three descriptions; check each matches the invoicing documentation.

**Acceptance Scenarios**:

1. **Given** the unit form, **When** the billing method drop-down is opened, **Then** each of the three methods has a description consistent with the user documentation.
2. **Given** an existing unit, **When** it is edited, **Then** its billing method is selected and unchanged.

---

### User Story 3 - Contract status and administrator choices (Priority: P3)

The contract status options (Active, Canceled) are described the same way. Administrators who extend or replace choices through NetBox's `FIELD_CHOICES` configuration keep working as before; they can also give their own choices a description in that configuration, and it is shown like the built-in ones.

**Why this priority**: completes the set and keeps customised installations intact.

**Independent Test**: with an extra contract status added in the configuration, with and without a description, open the contract form.

**Acceptance Scenarios**:

1. **Given** the contract form, **When** the status drop-down is opened, **Then** Active and Canceled each have a description.
2. **Given** an installation that adds a status through the extend option of the configuration, with a description, **When** the drop-down is opened, **Then** the built-in descriptions and the added one are shown.
3. **Given** an installation that adds a status without a description, **When** the drop-down is opened, **Then** that option is shown without description and without error.
4. **Given** an installation that replaces the whole set of statuses, **When** the drop-down is opened, **Then** only its own options are shown, as before.

---

### Edge Cases

- A drop-down that NetBox does not build with description support (for example a filter drop-down of another kind): shows labels as today, no error.
- The internal party and currency choices are defined by each administrator, so the plugin supplies no description for them; their options render as today.
- Colours of badges and tables, and the stored values (`draft`, `posted`, `canceled`, `active`, `one_time`, ...), do not change.
- A very long description supplied by an administrator is shown wrapped, not cut off the page.
- Languages other than English and French fall back to English text.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The built-in invoice status choices MUST each carry a one-sentence description, and the Posted description MUST state what it locks (amount, currency, period, contracts and the amount fields of its lines).
- **FR-002**: The built-in unit billing method choices MUST each carry a one-sentence description consistent with the invoicing rules in `docs/`.
- **FR-003**: The built-in contract status choices MUST each carry a one-sentence description.
- **FR-004**: The descriptions MUST be shown under the options of the status and billing method drop-downs on the plugin's add, edit and filter forms wherever NetBox can display them (the bulk edit forms have no status or billing method field).
- **FR-005**: The descriptions MUST be available in English and French, following the plugin's translation process.
- **FR-006**: Stored values, labels, colours, REST and GraphQL representations, CSV import and export values and filters MUST NOT change, and no migration MUST be needed.
- **FR-007**: Installations that extend or replace the choices through `FIELD_CHOICES` MUST keep working as before; descriptions given in that configuration MUST be displayed.
- **FR-008**: Options without a description MUST render without error.
- **FR-009**: `docs/` and the changelog MUST mention the descriptions and how administrators can supply their own.
- **FR-010**: The plugin's minimum NetBox version becomes 4.7.0. Provided by specification 008 (minimum NetBox 4.7.0, CI on v4.7.4, README table, changelog warning, version 2.6.0); this specification only relies on it and has no task of its own for it.
- **FR-011**: The behaviour MUST be covered by tests that fail before the change: descriptions present for each built-in choice and each language, rendering in the forms, administrator extend and replace cases, and unchanged values and colours (constitution principle II).

### Key Entities

- **Choice**: a selectable value with a label, a colour and, from this feature, a short description.
- **Choice set**: the list of choices of one field (invoice status, contract status, billing method), extendable by administrators.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user can state what a Posted invoice locks from the drop-down alone, without opening the documentation.
- **SC-002**: 100% of the built-in invoice status, contract status and billing method options show a description in English and in French.
- **SC-003**: 100% of the existing tests on forms, imports, REST and GraphQL pass unchanged.
- **SC-004**: An installation using `FIELD_CHOICES` for any of these choice sets upgrades with no configuration change and no visible regression.

## Assumptions

- The 4.7 minimum is the shared prerequisite of specifications 004 to 007.
- The accounting dimension status is left out: its Active and Inactive options are described only once the effect of Inactive is documented in `docs/`. The wording of every description is checked against `docs/` in the plan.
- Descriptions are static texts; they do not depend on the user, the object or the amount.
- Forms that today use a plain drop-down not built by NetBox may need to change to the form of drop-down that shows descriptions; this is a planning question, not a user-visible change besides the descriptions.
- The changelog entry goes under Enhancements of the release (CLAUDE.md, "Changelog").
