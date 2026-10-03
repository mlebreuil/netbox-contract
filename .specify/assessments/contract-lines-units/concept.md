# Concept: Contract lines with billing natures and currency consistency

- **Slug**: contract-lines-units
- **Created**: 2026-09-26
- **Recommended option**: Option C — Phased delivery: contract lines and upgrade first, invoice generation second
- **Maintainer choice**: Option C confirmed on 2026-09-26, with plain decimal and currency fields for amounts and the invoice pre-fill switched to the contract lines in release 1, and the release 1 / release 2 split confirmed

Inputs: problem.md (with the maintainer's 2026-09-26 clarifications), research.md and intake.md. Appetites below are rough budgets, not estimates: the evidence contains no velocity data for this plugin, only its release history of frequent small releases, so every appetite is low-confidence.

## Options

### Option A — Enrich the existing invoice template
- **Sketch**: keep the current mechanism of one template invoice per contract and extend what a template line can express: a quantity, a unit price, a nature (one-time, recurring, usage-based) and its own dates. New invoices are pre-filled from the template lines with the rules the maintainer decided (months covered per unit, proration by days, remaining amount for one-time costs on Posted invoices, quantity edited per invoice for usage). Currency consistency between contract, invoices and lines is added as validation on save. The contract's recurring and one-time cost fields stay as they are.
- **Appetite**: small to medium (low confidence).
- **Trade-offs**: wins — least change to the data users already have, little or no upgrade migration, small API change, quickest to ship. Sacrifices — it keeps the template workaround the maintainer wants to replace, leaves the contract-level cost fields and the "billable" flag and computed contract values unresolved unless added on top, has no reusable unit concept, and does not fit the child-contract roll-up cleanly (the template is an invoice, not a contract-level line). It meets only part of issue #278's goals.
- **Rabbit holes**: a template is an invoice (with a required amount and possibly several linked contracts), so bending it to describe contract lines may need more special cases than a new concept would; the "one template per contract" rule would have to be relaxed or explained.

### Option B — Full contract lines in one release
- **Sketch**: deliver everything in issue #278 together. Contracts get contract lines with units that define the nature of the cost; invoices are generated from those contract lines with a reference from each line back to its contract line; contracts get the billable flag and the three computed values; currency rules are enforced; templates and the old recurring and one-time cost fields are converted by migrations and deprecated; the minimum NetBox version is raised to 4.6. Amounts use plain Django decimal and currency fields (research.md ranks this first among the alternatives to django-money).
- **Appetite**: large (low confidence).
- **Trade-offs**: wins — the complete result the maintainer asked for, one upgrade event for users. Sacrifices — the largest change surface at once (models, forms, tables, filters, API, imports, migrations, documentation, tests), the most risk of a delayed or unstable release, and generation rules that cannot be validated until contract line data exists in the field.
- **Rabbit holes**: the conversion migrations (templates whose amounts do not match the contract's recurring cost, contracts with no template, several linked contracts); proration by days over uneven months; the "remaining amount" of one-time costs when invoice lines have been adjusted; the child roll-up rules; an invoice that can be linked to several contracts while the invoice currency must equal "the" contract currency; interaction with the hidden and mandatory field settings and with the API consumers of the old fields.

### Option C — Phased: contract lines and upgrade first, invoice generation second
- **Sketch**: split B in two releases that each leave the plugin coherent. Release 1: contract lines and units (nature of cost, months per unit, dates, dimensions), the billable flag, the three computed contract values, currency validation on save with the mismatch report, the parent-child currency rule, and the conversion of templates and of the recurring and one-time cost fields into contract lines, with the old fields deprecated and hidden; the minimum NetBox version goes to 4.6 and the CI is pinned to a 4.6 tag. Amounts use plain Django decimal and currency fields; no money library is added. The invoice pre-fill switches to the contract lines in this release: it no longer reads the deprecated cost fields, and computes the invoice amount and period from the contract lines with the recurring, proration-by-days and one-time rules (split confirmed by the maintainer, 2026-09-26). Release 2: generation of invoice lines from contract lines, adding the usage quantity edited per invoice and the child roll-up to the release 1 rules, the reference from each invoice line to its contract line, and retirement of the template mechanism from generation. Both releases update the existing tests and add new tests covering every use case.
- **Appetite**: two medium steps, large in total; release 1 is on the larger side of medium because the pre-fill uses the computation rules, and both releases include the test updates and new tests (low confidence).
- **Trade-offs**: wins — the risky data conversion ships and settles on real installations before the harder generation logic depends on it, each release is testable on its own, and the maintainer's small-release habit is kept. Sacrifices — the full result arrives later, users face two upgrade steps, and release 1 alone carries two overlapping mechanisms (contract lines and deprecated templates) for a while.
- **Rabbit holes**: the release 1 pre-fill amount needs the recurring, proration and one-time rules, so that computation work sits in release 1 (child roll-up and usage handling stay in release 2); deciding what release 1 shows for the deprecated fields; the same migration risks as Option B, taken first.

Not sketched: "do nothing" is covered by the cost of inaction in problem.md, and "buy instead" does not apply because the plugin lives inside NetBox; an external billing system (for example the Odoo contract module seen in research.md) would be an integration outside the scope of the issue.

## Recommendation

Option C. The problem's goals are all reachable by B or C, but the riskiest part for existing users is converting existing templates and cost fields, and the evidence shows no reference scenarios or data volumes yet (problem.md open questions); shipping the conversion and the data-side rules first lets that risk be found before the invoice generation logic depends on it. Option A is the cheapest but leaves the maintainer's stated direction (replacing invoice templates) unaddressed and covers only part of the goals and success metrics, so it is a fallback if the appetite turns out much smaller than assumed. If the maintainer prefers a single upgrade, Option B is the same scope as C in one release, at higher risk.

## Out of Scope (for the recommended option)

- NetBox 4.7 compatibility, including replacing the NetBox custom-script mechanism used by the plugin's script (separate, later work), and support for NetBox versions older than 4.6.
- Currency conversion or exchange rates, tax or VAT display on invoices (issue #177), and automatic scheduled invoice generation (proposed non-goals in problem.md, to be confirmed).
- Separate usage records or metering per contract line: usage quantity is edited on each generated invoice line.
- Any money library: amounts use plain Django decimal and currency fields (maintainer decision, 2026-09-26).

## Assumptions to Validate

- Plain decimal and currency fields (chosen) are enough for amounts, and currency consistency can be enforced by validation alone (research.md, alternatives ranking).
- Computing the release 1 pre-fill amount from contract lines does not need the full invoice line generation logic (confirmed by the maintainer).
- Existing templates and the recurring and one-time cost fields convert cleanly into contract lines; templates are roughly one per contract and their amounts agree with the contract's recurring cost. The number of affected rows is unknown.
- Users accept proration by days and the decided one-time cost rule on Posted invoices, and reference scenarios can be written for them.
- Invoices linked to several contracts are rare enough, or a currency rule can be defined for them; this needs checking against real data.
- The existing tests pass on NetBox 4.6 once the CI is pinned to a 4.6 tag (not yet run).
- Demand exists beyond the maintainer's own issue (no evidence yet).
- Two upgrade steps are acceptable to users (specific to Option C).
