# Feature Specification: Contract lines, billing natures and currency consistency

**Feature Branch**: `278-replace-invoice-templates-with-contract-lines` (the spec folder is `specs/001-contract-lines-billing`)

**Created**: 2026-09-26

**Status**: Draft

**Input**: User description: "Let a contract be described line by line (contract lines with a unit that defines the nature of the cost: one-time, recurring or usage-based), replace the contract-level monthly, yearly and non-recurring costs and the invoice templates, add a billable flag and computed contract values, enforce currency consistency between contracts, contract lines, invoices and invoice lines, pre-fill invoices from the contract lines, then generate editable invoice lines from them. Delivered as a single release, targeting NetBox 4.6 as the minimum version. Update the existing tests and add new ones covering every use case." (Source: GitHub issue #278 and the assessment in `.specify/assessments/contract-lines-units/`, verdict go, Option C.)

## Delivery Overview

The feature is delivered as a single release (plugin version 2.5.0). The user stories are ordered by priority, which is also the suggested build order: contract lines and the conversion of existing data first, then billable flag and computed values, currency rules, invoice pre-fill and finally invoice line generation. Existing invoice templates are kept for future reference and are never deleted.

## Clarifications

### Session 2026-09-26

- Q: When an invoice is pre-filled, what is proposed for usage-based contract lines? → A: Nothing; the amount pre-fill covers recurring and one-time lines only. Usage-based lines are handled through the quantity entered on the invoice line.
- Q: What happens when a contract's currency is changed while it has contract lines, invoices or invoice lines? → A: Refused only if invoices or invoice lines exist; if only contract lines exist, they follow the contract's new currency.
- Q: What happens when a contract line's dates fall outside its contract's dates? → A: The save is refused when the contract has that date; an open-ended contract imposes no limit on that side.
- Q: What happens when a unit that contract lines use is edited or deleted? → A: Deleting a used unit is blocked; editing is allowed and only affects future computations, saved invoices keep their amounts.
- Q: Who can see the currency mismatch report and where does it appear? → A: It is delivered as a NetBox custom script (run by users allowed to run scripts), not a plugin page; NetBox core custom scripts will be deprecated and replaced by an open-source plugin, so moving the report is part of the later NetBox 4.7 work.
- Q: How are months counted for a recurring line whose dates cover a partial month? → A: Whole calendar months from the start date, plus the leftover days divided by the number of days of the month in which the range ends (1 January to 20 March is 2 + 20/31 months), rounded once at the end.
- Q: What happens when the billable flag is changed after invoices exist? → A: The change is refused when the contract, any of its descendants or any of its ancestors has an invoice, or when an invoice line references one of its contract lines; a new contract is needed instead.
- Q: What happens when invoice lines are generated for an invoice that already has lines? → A: This cannot happen: invoice lines are generated from the contract lines at invoice creation time, for a new invoice only; there is no separate generation action.
- Q: What if the amount typed on a new invoice is lower than the total of the lines to generate? → A: The save is refused with a message showing both amounts, consistent with the existing rule that invoice lines never total more than the invoice amount; a higher or equal amount is accepted.
- Q: Should the work ship as two releases? → A: No, a single release; release 1 and release 2 are merged.
- Q: How is a one-time line converted from the old one-time cost treated by the pre-fill on a contract that already has invoices? → A: It is considered already fully invoiced; the pre-fill and the generation propose nothing for it, and the user can still enter an amount by hand.
- Q: What happens to invoice templates? → A: They are kept for future reference and never deleted; they are no longer used to pre-fill or to generate invoices, and the copy of template lines on invoice save is removed.
- Q: Where is the quantity defined for an invoice? → A: On the invoice line, which references its contract line; unit and unit price come from the contract line and the invoice line amount is calculated.
- Q: Can a contract line be changed once invoices exist? → A: No. As soon as a contract has an invoice, its contract lines can no longer be added, changed or deleted; a new contract must be created. A line is also locked once an invoice line references it, even when its own contract (a non-billable child) has no invoice.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Describe a contract line by line (Priority: P1)

A contract manager records what a contract actually bills for as several contract lines instead of one lump recurring cost and one one-time cost. Each contract line has a description, a quantity, a unit price, a unit, its own start and end dates (defaulting to the contract's dates) and accounting dimensions. The unit defines the nature of the cost: one-time, recurring or usage-based, and for a recurring unit the number of months one unit price covers (monthly is 1, quarterly 3, yearly 12).

**Why this priority**: every other part of the feature depends on contract lines existing; on its own it already lets users describe multi-item, mixed-nature contracts, which is the core problem.

**Independent Test**: create a contract with three contract lines (a one-time setup fee, a monthly subscription and a usage-based charge) and check that all three are stored, shown on the contract, and keep their own nature, dates and accounting dimensions.

**Acceptance Scenarios**:

1. **Given** a contract with start and end dates, **When** a contract line is added without dates, **Then** it takes the contract's start and end dates.
2. **Given** a recurring unit that covers 12 months, **When** it is assigned to a contract line, **Then** the line's unit price is understood as a price per 12 months.
3. **Given** a contract line with several accounting dimensions, **When** the contract is viewed, **Then** each contract line shows its dimensions.
4. **Given** a contract in one currency, **When** a contract line is added, **Then** the contract line uses the contract's currency.
5. **Given** a contract from 1 January to 31 December, **When** a contract line ending on the following 31 March is saved, **Then** the save is refused with a message naming the contract's dates.
6. **Given** a unit used by a contract line, **When** a user tries to delete it, **Then** the deletion is refused; **When** the user edits the unit's covered months while only contracts without invoices use it, **Then** the edit is accepted; if a contract with invoices uses it, the change to billing method or covered months is refused.
7. **Given** a contract line, **When** a user edits or deletes it, **Then** the contract's computed values update accordingly.
8. **Given** a contract that already has an invoice, **When** a user tries to add, change or delete one of its contract lines, **Then** it is refused with a message saying that a new contract must be created.
9. **Given** a non-billable child contract whose contract line was used by an invoice line of its billable parent's invoice, **When** a user tries to change or delete that contract line, **Then** it is refused; **When** the child has another line that no invoice line references, **Then** that line can still be changed.

---

### User Story 2 - Keep existing data working after the upgrade (Priority: P1)

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

### User Story 3 - Control billing and see contract values (Priority: P2)

A finance user marks whether a contract is billable and sees, for each contract, its total value, its yearly value and its yearly billable value, computed from the contract lines.

**Why this priority**: it turns contract lines into information users need without spreadsheets, and the billable flag drives the invoice behaviour.

**Independent Test**: create contracts with known contract lines (recurring, one-time, usage-based, with and without end dates, with non-billable children) and check the three values against hand-computed results.

**Acceptance Scenarios**:

1. **Given** a contract whose contract lines are a monthly line (12 months at 100), a one-time line (500) and a usage-based line (quantity 10 at 20), **When** the values are computed, **Then** the total contract value is 1,900 (1,200 + 500 + 200) and the yearly value is 1,200 (recurring lines only).
2. **Given** a billable contract with a non-billable child contract, **When** the values are computed, **Then** the parent's yearly billable value includes the child's recurring contract lines, and the child's own yearly billable value is zero.
3. **Given** a non-billable contract, **When** an invoice is prepared for it, **Then** the user gets a clear error and no invoice amount is proposed.
4. **Given** a contract line without an end date on an open-ended contract, **When** the values are shown, **Then** the yearly values are shown and the total contract value is shown as not available.
5. **Given** a contract, or one of its ancestors or descendants, that already has an invoice, **When** a user changes its billable flag, **Then** the change is refused with a message; **When** no invoice or referencing invoice line exists in the family, **Then** the change is accepted.

---

### User Story 4 - Prevent inconsistent currencies (Priority: P2)

A finance user can no longer save a contract line, invoice or invoice line whose currency does not match its contract or invoice. Existing mismatches are not silently changed; they are reported so users can fix them.

**Why this priority**: it removes a class of accounting errors and is required for correct totals, but it does not block the other stories.

**Independent Test**: try to save each kind of mismatched record and check it is refused with a clear message; then check the report lists pre-existing mismatches without altering them.

**Acceptance Scenarios**:

1. **Given** a contract in EUR, **When** a contract line in CHF is saved for it, **Then** the save is refused and the message names both currencies.
2. **Given** an invoice in EUR linked to a contract in CHF, **When** the invoice is saved, **Then** the save is refused.
3. **Given** an invoice in EUR, **When** an invoice line in CHF is saved for it, **Then** the save is refused.
4. **Given** a contract in EUR that has an invoice, **When** its currency is changed to CHF, **Then** the change is refused; with only contract lines and no invoice, the change is accepted and its contract lines become CHF.
5. **Given** a non-billable child contract in CHF under a parent in EUR, **When** the parent link is set, **Then** it is refused.
6. **Given** a new invoice, **When** a user tries to link it to more than one contract, **Then** it is refused; existing invoices already linked to several contracts stay as they are.
7. **Given** existing records with mismatching currencies before the upgrade, **When** the upgrade completes, **Then** the records are unchanged and a report lists them.

---

### User Story 5 - Pre-fill an invoice from the contract lines (Priority: P2)

A user creating an invoice for a billable contract gets the amount and the period proposed from the contract's contract lines instead of from the old monthly, yearly and one-time cost fields. Recurring lines are proposed for the months the invoice covers, prorated by days when the invoice period only partly overlaps the line's dates. One-time lines are proposed for the amount still to invoice. Usage-based lines are not proposed; their amount comes from the quantity entered on the invoice line. The proposal can be edited before saving.

**Why this priority**: it is the first place where contract lines produce invoice values, before invoice lines are generated.

**Independent Test**: for a set of reference scenarios (full period, partial period at start and end, one-time line partly and fully invoiced, mixed lines), check the proposed amount against hand-computed values.

**Acceptance Scenarios**:

1. **Given** a recurring line of 100 per unit covering 1 month, quantity 1, and an invoice covering 3 full months, **When** the invoice is pre-filled, **Then** the proposed amount for that line is 300.
2. **Given** a recurring line of 120 per unit covering 12 months, quantity 1, and an invoice covering 3 full months, **When** the invoice is pre-filled, **Then** the proposed amount for that line is 30.
3. **Given** a recurring line of 90 per unit covering 1 month, quantity 1, that starts 10 days after the start of a 30-day invoice period covering 1 month, **When** the invoice is pre-filled, **Then** the proposed amount for that line is 60 (20 covered days out of 30).
4. **Given** a one-time line of 500 with 200 already on Posted invoices, **When** an invoice is pre-filled, **Then** 300 is proposed; amounts on Draft and Canceled invoices are ignored.
5. **Given** a one-time line fully invoiced on Posted invoices, **When** an invoice is pre-filled, **Then** nothing is proposed for that line.
6. **Given** a contract with no contract lines, **When** an invoice is pre-filled, **Then** no amount is proposed and the user can enter one manually.
7. **Given** a contract with a usage-based line and a recurring line, **When** an invoice is pre-filled, **Then** only the recurring line contributes to the proposed amount.

---

### User Story 6 - Invoice lines are generated from the contract lines at invoice creation (Priority: P3)

When a user creates a new invoice for a billable contract, its invoice lines are generated from the contract lines at that moment, with no extra action, and can then be edited. Each generated invoice line references the contract line it came from and carries its accounting dimensions. The quantity is defined on the invoice line; the unit and the unit price come from the contract line and the amount is calculated. A billable parent's invoice includes the contract lines of all non-billable descendants, stopping at any billable child. Usage-based lines are generated without a quantity and the user enters the actual quantity on each invoice.

**Why this priority**: it completes the workflow and replaces the invoice templates as the way to prepare invoice lines, but it builds on the data conversion and the amount rules.

**Independent Test**: create an invoice for a hierarchy of contracts (billable parent, non-billable child and grandchild, billable child) and check which contract lines produce invoice lines, their amounts, dimensions and references.

**Acceptance Scenarios**:

1. **Given** a billable contract, **When** a new invoice is created for it, **Then** one invoice line is created per applicable contract line, each referencing its contract line and carrying its accounting dimensions.
2. **Given** a billable parent with a non-billable child and grandchild, **When** a new invoice is created for the parent, **Then** the lines of the child and grandchild are included.
3. **Given** a billable parent with a billable child, **When** a new invoice is created for the parent, **Then** the child's lines are not included.
4. **Given** a non-billable contract, **When** a new invoice is created for it, **Then** the creation is refused with a clear error and no invoice line is generated.
5. **Given** a usage-based contract line with unit price 20, **When** its invoice line is generated, **Then** it has no quantity and amount 0; **When** the user enters quantity 10, **Then** the amount becomes 200, and changing the quantity to 12 makes it 240.
6. **Given** any generated invoice line, **When** the user edits its dimensions or quantity, **Then** the change is accepted, the amount is recalculated from the quantity, and the reference to the contract line is kept.
7. **Given** a recurring contract line of 100 per month generated for an invoice covering 3 months, **When** the invoice line is created, **Then** its quantity is the contract line's quantity (1) and its amount is 300.
8. **Given** a contract that has an invoice template, **When** a new invoice is saved, **Then** the template's lines are not copied and the template invoice itself stays untouched.
9. **Given** a contract whose lines would generate a total of 300, **When** a new invoice is saved with an amount of 250, **Then** the save is refused with both amounts in the message; **When** the amount is 300 or more, **Then** it is accepted and the lines are generated.

---

### Edge Cases

- A contract line whose dates fall partly or wholly outside its contract's dates: refused (FR-002a); the conversion of existing data gives lines the contract's own dates so it is never affected.
- A contract without start or end dates (open-ended), and recurring lines without end dates.
- Zero or negative quantities, zero prices, and rounding of prorated amounts to two decimals.
- A one-time line invoiced more than its total (the remaining amount is never negative).
- A unit that is in use being deleted (blocked, FR-001a) or edited; changing its billing method or covered months is refused when a contract with invoices uses it.
- A contract with invoices that needs a different price or a new line: a new contract must be created (FR-029); this includes contracts converted at upgrade that already had invoices, whose converted lines are therefore locked.
- A Draft or Canceled invoice also locks the contract's lines.
- An invoice amount typed lower than the total of the lines to generate: the creation is refused (FR-021); equal or higher is accepted.
- An invoice whose period is changed after its lines were generated: the amounts of its lines are recalculated when each line is saved again, not automatically.
- The sum of the invoice lines exceeding the invoice amount (an existing rule), for instance once a usage quantity is entered: the user raises the invoice amount.
- A contract changing currency: refused when invoices exist, contract lines follow otherwise (FR-009a).
- A non-billable child that later becomes billable, or a parent that becomes non-billable, after invoices exist: refused (FR-008a).
- Invoices linked to several contracts that existed before the upgrade (kept unchanged) and their editing.
- Canceled invoices when computing what remains to invoice.
- Running the upgrade conversion more than once, or on contracts that already have contract lines.
- A one-time line converted on a contract that already has Posted invoices is flagged as already invoiced and never proposed again; on a contract with no Posted invoice it is proposed normally.
- Existing contracts that have both a monthly and a yearly cost value set, or a template whose amount disagrees with the contract's recurring cost.
- Users who rely on the deprecated cost fields or on invoice templates through imports or the programmatic interface.
- Hidden or mandatory field configuration that mentions the deprecated fields.

## Requirements *(mandatory)*

### Functional Requirements

Contract lines and units

- **FR-001**: The system MUST let users define units, each with a name, a description, a billing method (one-time, recurring, usage-based) and, for recurring units, the number of months one unit price covers.
- **FR-001a**: The system MUST refuse to delete a unit used by contract lines. Editing a used unit is allowed, except that its billing method and covered months MUST NOT be changed while a contract line of a contract that has invoices uses it (FR-029).
- **FR-002**: The system MUST let users add contract lines to a contract, each with a description, quantity, unit price, unit, start date, end date and accounting dimensions; the dates default to the contract's dates.
- **FR-002a**: The system MUST refuse to save a contract line whose start or end date falls outside its contract's dates, when the contract has that date; a contract without a start or end date imposes no limit on that side. Changing a contract's dates so that existing contract lines fall outside them MUST also be refused.
- **FR-003**: A contract line MUST support several accounting dimensions.
- **FR-004**: The system MUST show a contract's contract lines on the contract and let users create, edit and delete them, including through bulk import and the programmatic interface used by the plugin today.

Billable flag and computed values

- **FR-005**: Every contract MUST have a billable flag; all contracts existing at upgrade are billable.
- **FR-006**: The system MUST compute and show, for each contract, the total contract value (recurring lines over their dates, one-time lines once, usage-based lines at their stated quantity), the yearly contract value (twelve-month equivalent of the recurring lines only) and the yearly billable value (the yearly value of the lines invoiced under this contract: its own lines when it is billable, plus those of its non-billable descendants; zero for a non-billable contract).
- **FR-007**: When a contract line has no end date and the contract is open-ended, the total contract value MUST be shown as not available while yearly values are still shown.
- **FR-008**: Preparing an invoice for a non-billable contract MUST produce a clear error.
- **FR-008a**: Changing a contract's billable flag MUST be refused, with a clear message, when the contract, any of its descendants or any of its ancestors has an invoice, or when an invoice line references one of its contract lines.

Currency consistency

- **FR-009**: The system MUST refuse to save a contract line whose currency differs from its contract's currency, an invoice whose currency differs from its contract's currency, and an invoice line whose currency differs from its invoice's currency, with a message naming both currencies.
- **FR-009a**: Changing a contract's currency MUST be refused, with a message naming the blocking records, when invoices or invoice lines exist for it; when only contract lines exist, they MUST follow the contract's new currency.
- **FR-010**: The system MUST refuse to set a non-billable child contract's parent when their currencies differ.
- **FR-011**: A new invoice MUST be linked to at most one contract; existing invoices linked to several contracts MUST remain viewable and editable without being altered by the upgrade.
- **FR-012**: The system MUST NOT change the currency of existing records automatically; it MUST provide a report, delivered as a NetBox custom script, that lists existing records whose currencies do not match, with a link to each record. The report only reads data and MUST NOT alter it. It is a known temporary choice: custom scripts are to be deprecated in NetBox core, so its replacement is planned with the NetBox 4.7 work.

Conversion of existing data

- **FR-013**: At upgrade, each contract with a monthly recurring cost MUST get a recurring contract line covering one month, each with a yearly recurring cost a recurring line covering twelve months, and each with a non-zero one-time cost a one-time line, all with the existing prices. A one-time line created for a contract that already has at least one Posted invoice MUST be flagged as already invoiced at conversion (it has no invoice line reference to prove it), and MUST be treated as fully invoiced by FR-019 and FR-021; the flag is read-only and visible.
- **FR-014**: At upgrade, each existing invoice template MUST be represented as contract lines carrying the template lines' amounts and accounting dimensions. The template invoices MUST be kept for future reference and MUST NOT be deleted; they are marked as deprecated, are no longer used to pre-fill invoices or to generate invoice lines, and the copy of a template's lines onto a new invoice on save is removed.
- **FR-015**: The deprecated cost fields MUST be kept, marked as deprecated, and hidden by default; existing invoices and invoice lines MUST NOT be changed by the upgrade.
- **FR-016**: The upgrade conversion MUST be safe to run again without duplicating contract lines.

Invoice pre-fill

- **FR-017**: When an invoice is created for a billable contract, the system MUST propose the invoice amount and period from the contract lines, not from the deprecated cost fields.
- **FR-018**: For recurring lines the proposed amount MUST be quantity x unit price x (months covered by the invoice) / (months covered by one unit price); when the invoice period only partly overlaps the line's dates the amount MUST be multiplied by (days covered by the line) / (days in the invoice period).
- **FR-019**: For one-time lines the proposed amount MUST be quantity x unit price minus the amounts of the invoice lines that reference that contract line on Posted invoices; Draft and Canceled invoices are ignored and the result is never negative.
- **FR-017a**: The pre-fill MUST NOT propose an amount for usage-based contract lines; their amount comes from the quantity entered on the invoice line (FR-024).
- **FR-020**: Users MUST be able to edit any proposed amount and period before saving.

Invoice line generation

- **FR-021**: When a new invoice is created for a billable contract (through the screen or the programmatic interface, not through bulk import), the system MUST generate at that moment one invoice line per applicable contract line; each generated line MUST reference its contract line and carry its accounting dimensions. There is no separate generation action, and generation never runs on an existing invoice. The creation MUST be refused, with a message showing both amounts, when the invoice amount is lower than the total of the lines that would be generated (the existing rule that invoice lines never total more than the invoice amount).
- **FR-021a**: An invoice line MUST only reference a contract line of the invoice's contract or of one of its non-billable descendants.
- **FR-022**: A billable parent's generation MUST include the contract lines of all non-billable descendants and stop at any billable child.
- **FR-023**: Creating a new invoice for a non-billable contract MUST be refused with a clear error; existing invoices are left as they are.
- **FR-024**: An invoice line MUST have a quantity entered on the invoice line itself. It carries its own unit and unit price: they default to those of the referenced contract line and can be changed on any line of an invoice that is not posted (for example a discount on one invoice), without changing the contract line. When the line has a unit price, its amount MUST be calculated from the quantity and the unit price (amended 2026-09-26, decisions I11 and I12): quantity x unit price for usage-based lines, with the amount rules of FR-018 and FR-019 for recurring and one-time lines. Changing the quantity MUST recompute the amount. A usage-based invoice line is generated with no quantity and an amount of zero until the user enters the quantity.
- **FR-025**: Recurring and one-time lines MUST be generated with the same amount rules as the pre-fill (FR-018, FR-019), starting from the contract line's quantity.
- **FR-029**: As soon as a contract has an invoice (of any status), the system MUST refuse to add, change or delete its contract lines, with a message that a new contract must be created. The accounting dimensions, comments and tags of a line are internal classification, not contract terms: they remain editable on a locked line, and invoice lines already created keep their own dimensions (clarified 2026-09-26, decision I9). A contract line MUST also be locked, whatever its contract, as soon as any invoice line references it, so that the lines of a non-billable child invoiced through its billable parent cannot change afterwards. The conversion of existing data at upgrade is not affected by this rule.
- **FR-030**: The system MUST let users amend the unit price and/or quantity of a recurring or usage-based contract line from a date, also once the line is locked (FR-029): the line ends the day before that date and a new line with the new terms, the same unit, currency, dimensions and end date, replaces it from that date and references it. The date MUST be after the start of the line, not after its end, and after the end of the last period invoiced for the line (Draft and Posted invoices of its contract or referencing it; Canceled invoices ignored). A reason is required and is recorded as the change-log message of both lines and as a comment on the new line. One-time lines cannot be amended. Yearly values count only lines that are not replaced; the total contract value counts each line over its own dates (added 2026-09-26, decision I10).
- **FR-031**: New invoices MUST be Draft by default. A Posted invoice (other than a deprecated invoice template) MUST be locked: its amount, currency, period and contracts cannot change, lines cannot be added to or deleted from it, and the unit, unit price, quantity, amount, currency and contract line of its lines cannot change; their accounting dimensions, comments and tags remain editable, and the amounts of its lines are never recalculated. Its status can still change (for example back to Draft to correct it). Deleting the invoice itself still deletes its lines (added 2026-09-26, decision I12).
- **FR-032**: The screen for a new invoice MUST show the invoice lines that will be generated (contract line, unit, unit price, quantity, calculated amount, total), refreshed when the contract, period, amount or a typed value changes, and MUST let the user change the quantity, the unit price and the accounting dimensions of each line, and add lines without contract line (description, optional unit, unit price, quantity, accounting dimensions), before saving; the dimensions follow the rules of the invoice line form (no two of the same name, mandatory dimensions present); the invoice and its lines are then created in one step with these values, which also count for the check of FR-021. Values changed there apply to that invoice only (added 2026-09-27, decision I13).

Compatibility and quality

- **FR-026**: The plugin's minimum supported NetBox version MUST be 4.6; compatibility with NetBox 4.7 is not part of this feature.
- **FR-027**: The delivery MUST update the existing automated tests affected by the changed data, screens, programmatic interface and pre-fill, and add new automated tests so that every scenario and edge case described in this specification is covered, including the conversion of existing data and the currency rules.
- **FR-028**: The automated tests MUST run against NetBox 4.6 in the project's continuous integration, which MUST be pinned to a NetBox 4.6 release for this work.

### Key Entities

- **Contract line**: a billable or deliverable part of a contract with description, quantity, unit price, unit, its own dates and accounting dimensions; belongs to one contract and takes its currency from that contract.
- **Unit**: defines a billing method (one-time, recurring, usage-based) and, for recurring units, the months covered by one unit price; referenced by contract lines.
- **Contract**: gains a billable flag and three computed values (total, yearly, yearly billable); keeps its parent-child hierarchy and now has contract lines; its deprecated cost fields are kept but hidden.
- **Invoice**: linked to at most one contract for new invoices; its currency equals its contract's currency; deprecated invoice templates are kept but no longer used.
- **Invoice line**: belongs to an invoice, uses the invoice's currency, has a quantity, and can reference the contract line it comes from, from which it takes its unit and unit price; its amount is calculated when it references a contract line.
- **Accounting dimension**: existing entity; can now be attached to contract lines and copied to generated invoice lines.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user familiar with the plugin can record a contract with at least three contract lines of different natures (one-time, recurring, usage-based) and read its total, yearly and yearly billable values in under 10 minutes, without creating extra contracts or using outside spreadsheets.
- **SC-002**: After the upgrade of a reference dataset, 100% of contracts with a non-zero recurring or one-time cost and 100% of invoice templates are represented as contract lines whose amounts equal the originals, and no existing invoice or invoice line changes.
- **SC-003**: 0 records with mismatching currencies (contract line, invoice, invoice line, non-billable child) can be newly saved, and 100% of pre-existing mismatches appear in the report.
- **SC-004**: For the reference scenarios of this specification (full and partial periods, quantity, unit months, one-time lines partly and fully invoiced), the proposed invoice amounts match the hand-computed values to the cent in 100% of cases.
- **SC-005**: 100% of the acceptance scenarios and edge cases in this specification are covered by at least one automated test, and the whole test suite passes on NetBox 4.6.
- **SC-006**: creating an invoice for a contract hierarchy generates its invoice lines with no user action beyond creating the invoice, and produces exactly the expected contract lines' invoice lines in 100% of reference cases, and each generated line can be traced to its contract line.
- **SC-007**: Users of the deprecated cost fields or invoice templates see no data loss: after the upgrade their previous values are still visible where they were kept, marked as deprecated.

## Assumptions

- Target users are people who record contracts and invoices in NetBox through the plugin; the demand beyond the maintainer is not yet evidenced (see the assessment notes).
- The scope of this feature is bounded by the assessment: NetBox 4.7 compatibility and the replacement of the deprecated custom scripts, versions of NetBox older than 4.6, currency conversion, tax or VAT display on invoices (issue #177), automatic scheduled invoice generation and separate usage records or metering are out of scope.
- Implementation choices (how amounts are stored, how the conversion is built) are decided in planning; the assessment recorded that no additional money library is added (`.specify/assessments/contract-lines-units/decision.md`).
- The total contract value and the yearly value refer to the contract's own contract lines; the yearly billable value adds the recurring lines of non-billable descendants when the contract is billable.
- Prorated amounts are rounded to two decimals, matching the precision of existing amounts.
- The months covered by a date range are counted as whole calendar months from the start date plus the leftover days divided by the number of days of the month in which the range ends; the total contract value of a recurring line is quantity x unit price x (months in the line's dates) / (months covered by the unit).
- Preparing or creating an invoice for a non-billable contract is refused with a clear message (pre-fill and creation).
- The deprecated cost fields are kept for a deprecation period whose length is decided at planning; invoice templates are kept for future reference and are not deleted; the removal of the deprecated cost fields is not part of this feature.
- The plugin's mismatch report is a read-only custom script listing records and does not fix them; it is expected to move to the replacement of core custom scripts later (outside this feature).
- Dependencies: the existing accounting dimensions, contract hierarchy and invoice statuses (Draft, Posted, Canceled) are reused as they are.
