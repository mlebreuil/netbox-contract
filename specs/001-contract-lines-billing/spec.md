# Feature Specification: Contract lines, billing natures and currency consistency

**Feature Branch**: `278-replace-invoice-templates-with-contract-lines` (the spec folder is `specs/001-contract-lines-billing`)

**Created**: 2026-09-26

**Status**: Draft

**Input**: User description: "Let a contract be described line by line (contract lines with a unit that defines the nature of the cost: one-time, recurring or usage-based), replace the contract-level monthly, yearly and non-recurring costs and the invoice templates, add a billable flag and computed contract values, enforce currency consistency between contracts, contract lines, invoices and invoice lines, pre-fill invoices from the contract lines, then generate editable invoice lines from them. Delivered in two releases, targeting NetBox 4.6 as the minimum version. Update the existing tests and add new ones covering every use case." (Source: GitHub issue #278 and the assessment in `.specify/assessments/contract-lines-units/`, verdict go, Option C.)

## Delivery Overview

The feature is delivered in two releases. Each user story below is tagged with its release.

- **Release 1**: contract lines and units, the billable flag and computed contract values, currency consistency, the conversion of existing data, and the invoice pre-fill computed from contract lines.
- **Release 2**: generation of editable invoice lines from contract lines (usage quantity, child contract roll-up, reference back to the contract line) and retirement of invoice templates from generation.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Describe a contract line by line (Priority: P1, Release 1)

A contract manager records what a contract actually bills for as several contract lines instead of one lump recurring cost and one one-time cost. Each contract line has a description, a quantity, a unit price, a unit, its own start and end dates (defaulting to the contract's dates) and accounting dimensions. The unit defines the nature of the cost: one-time, recurring or usage-based, and for a recurring unit the number of months one unit price covers (monthly is 1, quarterly 3, yearly 12).

**Why this priority**: every other part of the feature depends on contract lines existing; on its own it already lets users describe multi-item, mixed-nature contracts, which is the core problem.

**Independent Test**: create a contract with three contract lines (a one-time setup fee, a monthly subscription and a usage-based charge) and check that all three are stored, shown on the contract, and keep their own nature, dates and accounting dimensions.

**Acceptance Scenarios**:

1. **Given** a contract with start and end dates, **When** a contract line is added without dates, **Then** it takes the contract's start and end dates.
2. **Given** a recurring unit that covers 12 months, **When** it is assigned to a contract line, **Then** the line's unit price is understood as a price per 12 months.
3. **Given** a contract line with several accounting dimensions, **When** the contract is viewed, **Then** each contract line shows its dimensions.
4. **Given** a contract in one currency, **When** a contract line is added, **Then** the contract line uses the contract's currency.
5. **Given** a contract line, **When** a user edits or deletes it, **Then** the contract's computed values update accordingly.

---

### User Story 2 - Keep existing data working after the upgrade (Priority: P1, Release 1)

An administrator upgrades an installation that already has contracts with monthly, yearly and one-time costs and invoice templates. After the upgrade those costs and templates are represented as contract lines, nothing is lost, and the old fields and templates remain but are marked as deprecated and hidden by default. Every existing contract is billable.

**Why this priority**: without a safe conversion the feature would break current users; it is the riskiest part and is delivered first on purpose.

**Independent Test**: on a dataset containing contracts with monthly cost, yearly cost, one-time cost, invoice templates with accounting dimensions, and contracts with none of these, run the upgrade and compare the resulting contract lines and totals with the original values.

**Acceptance Scenarios**:

1. **Given** a contract with a monthly recurring cost, **When** the upgrade runs, **Then** it has a recurring contract line covering one month, with the same price.
2. **Given** a contract with a yearly recurring cost, **When** the upgrade runs, **Then** it has a recurring contract line covering twelve months, with the same price.
3. **Given** a contract with a non-zero one-time cost, **When** the upgrade runs, **Then** it has a one-time contract line with that price.
4. **Given** a contract with an invoice template, **When** the upgrade runs, **Then** the template's lines and their accounting dimensions are represented as contract lines, and the template invoice itself is kept, marked as deprecated.
5. **Given** any existing contract, **When** the upgrade completes, **Then** the contract is billable, and existing invoices and their lines are unchanged.
6. **Given** a contract with no costs and no template, **When** the upgrade runs, **Then** it has no contract lines.

---

### User Story 3 - Control billing and see contract values (Priority: P2, Release 1)

A finance user marks whether a contract is billable and sees, for each contract, its total value, its yearly value and its yearly billable value, computed from the contract lines.

**Why this priority**: it turns contract lines into information users need without spreadsheets, and the billable flag drives the invoice behaviour of both releases.

**Independent Test**: create contracts with known contract lines (recurring, one-time, usage-based, with and without end dates, with non-billable children) and check the three values against hand-computed results.

**Acceptance Scenarios**:

1. **Given** a contract whose contract lines are a monthly line (12 months at 100), a one-time line (500) and a usage-based line (quantity 10 at 20), **When** the values are computed, **Then** the total contract value is 1,900 (1,200 + 500 + 200) and the yearly value is 1,200 (recurring lines only).
2. **Given** a billable contract with a non-billable child contract, **When** the values are computed, **Then** the parent's yearly billable value includes the child's recurring contract lines, and the child's own yearly billable value is zero.
3. **Given** a non-billable contract, **When** an invoice is prepared for it, **Then** the user gets a clear error and no invoice amount is proposed.
4. **Given** a contract line without an end date on an open-ended contract, **When** the values are shown, **Then** the yearly values are shown and the total contract value is shown as not available.

---

### User Story 4 - Prevent inconsistent currencies (Priority: P2, Release 1)

A finance user can no longer save a contract line, invoice or invoice line whose currency does not match its contract or invoice. Existing mismatches are not silently changed; they are reported so users can fix them.

**Why this priority**: it removes a class of accounting errors and is required for correct totals, but it does not block the other stories.

**Independent Test**: try to save each kind of mismatched record and check it is refused with a clear message; then check the report lists pre-existing mismatches without altering them.

**Acceptance Scenarios**:

1. **Given** a contract in EUR, **When** a contract line in CHF is saved for it, **Then** the save is refused and the message names both currencies.
2. **Given** an invoice in EUR linked to a contract in CHF, **When** the invoice is saved, **Then** the save is refused.
3. **Given** an invoice in EUR, **When** an invoice line in CHF is saved for it, **Then** the save is refused.
4. **Given** a non-billable child contract in CHF under a parent in EUR, **When** the parent link is set, **Then** it is refused.
5. **Given** a new invoice, **When** a user tries to link it to more than one contract, **Then** it is refused; existing invoices already linked to several contracts stay as they are.
6. **Given** existing records with mismatching currencies before the upgrade, **When** the upgrade completes, **Then** the records are unchanged and a report lists them.

---

### User Story 5 - Pre-fill an invoice from the contract lines (Priority: P2, Release 1)

A user creating an invoice for a billable contract gets the amount and the period proposed from the contract's contract lines instead of from the old monthly, yearly and one-time cost fields. Recurring lines are proposed for the months the invoice covers, prorated by days when the invoice period only partly overlaps the line's dates. One-time lines are proposed for the amount still to invoice. The proposal can be edited before saving.

**Why this priority**: it delivers immediate value from contract lines while invoice line generation follows in release 2.

**Independent Test**: for a set of reference scenarios (full period, partial period at start and end, one-time line partly and fully invoiced, mixed lines), check the proposed amount against hand-computed values.

**Acceptance Scenarios**:

1. **Given** a recurring line of 100 per unit covering 1 month, quantity 1, and an invoice covering 3 full months, **When** the invoice is pre-filled, **Then** the proposed amount for that line is 300.
2. **Given** a recurring line of 120 per unit covering 12 months, quantity 1, and an invoice covering 3 full months, **When** the invoice is pre-filled, **Then** the proposed amount for that line is 30.
3. **Given** a recurring line of 90 per unit covering 1 month, quantity 1, that starts 10 days after the start of a 30-day invoice period covering 1 month, **When** the invoice is pre-filled, **Then** the proposed amount for that line is 60 (20 covered days out of 30).
4. **Given** a one-time line of 500 with 200 already on Posted invoices, **When** an invoice is pre-filled, **Then** 300 is proposed; amounts on Draft and Canceled invoices are ignored.
5. **Given** a one-time line fully invoiced on Posted invoices, **When** an invoice is pre-filled, **Then** nothing is proposed for that line.
6. **Given** a contract with no contract lines, **When** an invoice is pre-filled, **Then** no amount is proposed and the user can enter one manually.

---

### User Story 6 - Generate editable invoice lines from the contract lines (Priority: P3, Release 2)

A user generates the invoice lines of an invoice from the contract lines in one action. Each generated invoice line references the contract line it came from, carries its accounting dimensions, and stays fully editable. A billable parent's invoice includes the contract lines of all non-billable descendants, stopping at any billable child. Usage-based lines start with the contract line's quantity and unit price and the user sets the actual quantity on each invoice.

**Why this priority**: it completes the workflow and retires invoice templates, but it builds on the data conversion and the amount rules delivered first.

**Independent Test**: generate invoice lines for a hierarchy of contracts (billable parent, non-billable child and grandchild, billable child) and check which contract lines produce invoice lines, their amounts, dimensions and references.

**Acceptance Scenarios**:

1. **Given** a billable contract, **When** invoice lines are generated, **Then** one invoice line is created per applicable contract line, each referencing its contract line and carrying its accounting dimensions.
2. **Given** a billable parent with a non-billable child and grandchild, **When** invoice lines are generated for the parent, **Then** the lines of the child and grandchild are included.
3. **Given** a billable parent with a billable child, **When** invoice lines are generated for the parent, **Then** the child's lines are not included.
4. **Given** a non-billable contract, **When** invoice line generation is requested, **Then** it fails with a clear error.
5. **Given** a usage-based contract line with quantity 10 at 20, **When** its invoice line is generated, **Then** it starts at quantity 10 and amount 200, and the user can change the quantity, which recomputes the amount.
6. **Given** any generated invoice line, **When** the user edits its amount or dimensions, **Then** the change is accepted and the reference to the contract line is kept.
7. **Given** invoice lines that are generated, **When** an invoice template exists for the contract, **Then** the template is not used for generation.

---

### Edge Cases

- A contract line whose dates fall partly or wholly outside its contract's dates.
- A contract without start or end dates (open-ended), and recurring lines without end dates.
- Zero or negative quantities, zero prices, and rounding of prorated amounts to two decimals.
- A one-time line invoiced more than its total (the remaining amount is never negative).
- A unit that is in use being edited or deleted, or a unit whose covered months change after invoices were prepared.
- A contract changing currency while it has contract lines, invoices or invoice lines.
- A non-billable child that later becomes billable, or a parent that becomes non-billable, after invoices exist.
- Invoices linked to several contracts that existed before the upgrade (kept unchanged) and their editing.
- Canceled invoices when computing what remains to invoice.
- Running the upgrade conversion more than once, or on contracts that already have contract lines.
- Existing contracts that have both a monthly and a yearly cost value set, or a template whose amount disagrees with the contract's recurring cost.
- Users who rely on the deprecated cost fields or on invoice templates through imports or the programmatic interface.
- Hidden or mandatory field configuration that mentions the deprecated fields.

## Requirements *(mandatory)*

### Functional Requirements

Contract lines and units (Release 1)

- **FR-001**: The system MUST let users define units, each with a name, a description, a billing method (one-time, recurring, usage-based) and, for recurring units, the number of months one unit price covers.
- **FR-002**: The system MUST let users add contract lines to a contract, each with a description, quantity, unit price, unit, start date, end date and accounting dimensions; the dates default to the contract's dates.
- **FR-003**: A contract line MUST support several accounting dimensions.
- **FR-004**: The system MUST show a contract's contract lines on the contract and let users create, edit and delete them, including through bulk import and the programmatic interface used by the plugin today.

Billable flag and computed values (Release 1)

- **FR-005**: Every contract MUST have a billable flag; all contracts existing at upgrade are billable.
- **FR-006**: The system MUST compute and show, for each contract, the total contract value (recurring lines over their dates, one-time lines once, usage-based lines at their stated quantity), the yearly contract value (twelve-month equivalent of the recurring lines only) and the yearly billable value (the yearly value of the lines invoiced under this contract: its own lines when it is billable, plus those of its non-billable descendants; zero for a non-billable contract).
- **FR-007**: When a contract line has no end date and the contract is open-ended, the total contract value MUST be shown as not available while yearly values are still shown.
- **FR-008**: Preparing an invoice for a non-billable contract MUST produce a clear error.

Currency consistency (Release 1)

- **FR-009**: The system MUST refuse to save a contract line whose currency differs from its contract's currency, an invoice whose currency differs from its contract's currency, and an invoice line whose currency differs from its invoice's currency, with a message naming both currencies.
- **FR-010**: The system MUST refuse to set a non-billable child contract's parent when their currencies differ.
- **FR-011**: A new invoice MUST be linked to at most one contract; existing invoices linked to several contracts MUST remain viewable and editable without being altered by the upgrade.
- **FR-012**: The system MUST NOT change the currency of existing records automatically; it MUST provide a report or warning that lists existing records whose currencies do not match.

Conversion of existing data (Release 1)

- **FR-013**: At upgrade, each contract with a monthly recurring cost MUST get a recurring contract line covering one month, each with a yearly recurring cost a recurring line covering twelve months, and each with a non-zero one-time cost a one-time line, all with the existing prices.
- **FR-014**: At upgrade, each existing invoice template MUST be represented as contract lines carrying the template lines' amounts and accounting dimensions; the template invoices MUST be kept, marked as deprecated, and no longer used to prepare or generate invoices.
- **FR-015**: The deprecated cost fields MUST be kept, marked as deprecated, and hidden by default; existing invoices and invoice lines MUST NOT be changed by the upgrade.
- **FR-016**: The upgrade conversion MUST be safe to run again without duplicating contract lines.

Invoice pre-fill (Release 1)

- **FR-017**: When an invoice is created for a billable contract, the system MUST propose the invoice amount and period from the contract lines, not from the deprecated cost fields.
- **FR-018**: For recurring lines the proposed amount MUST be quantity x unit price x (months covered by the invoice) / (months covered by one unit price); when the invoice period only partly overlaps the line's dates the amount MUST be multiplied by (days covered by the line) / (days in the invoice period).
- **FR-019**: For one-time lines the proposed amount MUST be quantity x unit price minus the amounts already invoiced for that line on Posted invoices; Draft and Canceled invoices are ignored and the result is never negative.
- **FR-020**: Users MUST be able to edit any proposed amount and period before saving.

Invoice line generation (Release 2)

- **FR-021**: The system MUST generate, on request, one invoice line per applicable contract line of a billable contract; each generated line MUST reference its contract line, carry its accounting dimensions, and remain editable.
- **FR-022**: A billable parent's generation MUST include the contract lines of all non-billable descendants and stop at any billable child.
- **FR-023**: Generation for a non-billable contract MUST fail with a clear error.
- **FR-024**: A generated line for a usage-based contract line MUST start with the contract line's quantity and unit price, and changing the quantity on the invoice line MUST recompute its amount.
- **FR-025**: Recurring and one-time lines MUST be generated with the same amount rules as the pre-fill (FR-018, FR-019).

Compatibility and quality

- **FR-026**: The plugin's minimum supported NetBox version MUST be 4.6; compatibility with NetBox 4.7 is not part of this feature.
- **FR-027**: The delivery MUST update the existing automated tests affected by the changed data, screens, programmatic interface and pre-fill, and add new automated tests so that every scenario and edge case described in this specification is covered, including the conversion of existing data and the currency rules.
- **FR-028**: The automated tests MUST run against NetBox 4.6 in the project's continuous integration, which MUST be pinned to a NetBox 4.6 release for this work.

### Key Entities

- **Contract line**: a billable or deliverable part of a contract with description, quantity, unit price, unit, its own dates and accounting dimensions; belongs to one contract and takes its currency from that contract.
- **Unit**: defines a billing method (one-time, recurring, usage-based) and, for recurring units, the months covered by one unit price; referenced by contract lines.
- **Contract**: gains a billable flag and three computed values (total, yearly, yearly billable); keeps its parent-child hierarchy and now has contract lines; its deprecated cost fields are kept but hidden.
- **Invoice**: linked to at most one contract for new invoices; its currency equals its contract's currency; deprecated invoice templates are kept but no longer used.
- **Invoice line**: belongs to an invoice, uses the invoice's currency, and (from Release 2) can reference the contract line it was generated from.
- **Accounting dimension**: existing entity; can now be attached to contract lines and copied to generated invoice lines.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user familiar with the plugin can record a contract with at least three contract lines of different natures (one-time, recurring, usage-based) and read its total, yearly and yearly billable values in under 10 minutes, without creating extra contracts or using outside spreadsheets.
- **SC-002**: After the upgrade of a reference dataset, 100% of contracts with a non-zero recurring or one-time cost and 100% of invoice templates are represented as contract lines whose amounts equal the originals, and no existing invoice or invoice line changes.
- **SC-003**: 0 records with mismatching currencies (contract line, invoice, invoice line, non-billable child) can be newly saved, and 100% of pre-existing mismatches appear in the report.
- **SC-004**: For the reference scenarios of this specification (full and partial periods, quantity, unit months, one-time lines partly and fully invoiced), the proposed invoice amounts match the hand-computed values to the cent in 100% of cases.
- **SC-005**: 100% of the acceptance scenarios and edge cases in this specification are covered by at least one automated test, and the whole test suite passes on NetBox 4.6.
- **SC-006** (Release 2): generating the invoice lines of a contract hierarchy takes a single user action, produces exactly the expected contract lines' invoice lines in 100% of reference cases, and each generated line can be traced to its contract line.
- **SC-007**: Users of the deprecated cost fields or invoice templates see no data loss: after the upgrade their previous values are still visible where they were kept, marked as deprecated.

## Assumptions

- Target users are people who record contracts and invoices in NetBox through the plugin; the demand beyond the maintainer is not yet evidenced (see the assessment notes).
- The scope of this feature is bounded by the assessment: NetBox 4.7 compatibility and the replacement of the deprecated custom scripts, versions of NetBox older than 4.6, currency conversion, tax or VAT display on invoices (issue #177), automatic scheduled invoice generation and separate usage records or metering are out of scope.
- Implementation choices (how amounts are stored, how the conversion is built) are decided in planning; the assessment recorded that no additional money library is added (`.specify/assessments/contract-lines-units/decision.md`).
- The total contract value and the yearly value refer to the contract's own contract lines; the yearly billable value adds the recurring lines of non-billable descendants when the contract is billable.
- Prorated amounts are rounded to two decimals, matching the precision of existing amounts.
- Preparing or generating invoices for a non-billable contract is refused with a clear message (Release 1: pre-fill; Release 2: generation).
- The deprecated cost fields and invoice templates are kept for a deprecation period whose length is decided at planning; their removal is not part of this feature.
- The plugin's mismatch report is a user-visible list of records and does not fix them.
- Dependencies: the existing accounting dimensions, contract hierarchy and invoice statuses (Draft, Posted, Canceled) are reused as they are.
