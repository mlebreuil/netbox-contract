# Problem Definition: Contract lines, billing behaviour and currency consistency

- **Slug**: contract-lines-units
- **Created**: 2026-09-26
- **Inputs used**: intake.md, research.md (both as updated on 2026-09-26; scope: NetBox 4.6, plugin minimum version raised to 4.6, NetBox 4.7 out of scope)

## Problem Statement

Users of the netbox-contract plugin can describe what a contract costs only as one monthly or yearly recurring amount plus one non-recurring amount, so contracts made of several billable contract lines, or with one-time and usage-based charges, cannot be represented accurately; invoices for them have to be built and corrected by hand, and nothing keeps the currencies of a contract, its invoices and their lines consistent. This matters now because the invoice-template workaround (one template invoice per contract) is the only structure available and the maintainer wants to move away from it. (Sources: research.md, Prior Art and Users & Demand; intake.md)

## Affected Users & Stakeholders

- **Users**: people who record contracts and post invoices in NetBox through the plugin's UI, imports or API — they cannot express several billable contract lines or non-recurring and usage-based costs per contract, and must adjust invoice amounts and lines manually. (Evidence: plugin documentation and code show one recurring cost and one non-recurring cost per contract, with the non-recurring cost not used when an invoice is pre-filled. Who these users are in practice and how many need the missing capability is not evidenced: [NEEDS CLARIFICATION: identify the actual users and how many rely on multi-line, one-time or usage-based billing today.])
- **Users**: people who consume contract and invoice data through the REST API, imports and the plugin's script — they depend on the current contract cost fields and invoice templates, so any change to how costs are described affects them. (Evidence: the fields and templates appear in the API serializers, views, import tests and `scripts/netbox-contract.py`.)
- **Stakeholders**: the plugin maintainer (author of issue #278) — decides scope and owns compatibility; the target is NetBox 4.6, with NetBox 4.7 compatibility handled separately later.
- **Stakeholders**: administrators who configure the plugin (for example the list of currencies through NetBox `FIELD_CHOICES` and hidden or mandatory contract fields) — their configuration must keep working. (Evidence: README and plugin default settings.)
- **Stakeholders**: finance or accounting users who rely on accounting dimensions on invoice lines. [NEEDS CLARIFICATION: not evidenced beyond the existence of the accounting-dimension model; confirm who they are.]

## Goals

- A contract's billable content can be described line by line, with each contract line's quantity, unit price, applicable period and accounting dimensions, instead of one lump recurring cost and one non-recurring cost. (Source: issue #278 as captured in intake.md.)
- The different natures of cost — one-time, recurring over time, and driven by usage — are distinguishable and each is handled according to its nature when an invoice is prepared. (Source: issue #278 use case.)
- Invoices for a contract can be prepared from that description with each invoice line traceable to the contract line it comes from, while every line stays adjustable. (Source: issue #278.)
- Whether a contract is billable is explicit, and totals that users need (total contract value, yearly value, yearly billable value) are available without manual calculation. (Source: issue #278.)
- Currency is consistent between a contract, its billable contract lines, its invoices and their lines. (Source: issue #278.)
- The plugin's automated tests are updated for the changed behaviour and extended so that every use case described here is covered.
- Existing installations keep their data usable through the change, and the plugin works on NetBox 4.6 (minimum supported version raised to 4.6). (Sources: research.md, Prior Art and Data & Constraints; maintainer decision of 2026-09-26.)

## Non-Goals

- Compatibility work for NetBox 4.7, including replacing the deprecated NetBox custom-script mechanism used by the plugin's script. (Maintainer decision: to be handled separately and later.)
- Support for NetBox versions older than 4.6. (Maintainer decision: minimum version raised to 4.6.)
- Adding a money library: amounts are stored with plain Django decimal and currency fields (maintainer decision, 2026-09-26; django-money is dropped).
- Proposed, to be confirmed: currency conversion or exchange rates between currencies; tax or VAT display on invoices (tracked separately as issue #177); automatic scheduled invoice generation. [NEEDS CLARIFICATION: confirm these are out of scope; none is requested in issue #278.]

## Success Metrics

Baselines are unknown unless stated; no usage data exists in the evidence. All metrics below are qualitative or checkable outcomes proposed from issue #278 and need confirmation.

- A contract with several contract lines of different natures (one-time, recurring, usage-based) can be described without workarounds such as extra contracts. (Baseline: not possible today.) (qualitative)
- Invoice amounts prepared for a contract match the expected amounts for each nature of cost, and every prepared line can still be edited. (Baseline: today only the recurring amount times the invoice frequency is pre-filled; the non-recurring cost is not. Acceptance examples: [NEEDS CLARIFICATION: provide reference scenarios for one-time, recurring and usage-based costs, including partial periods.])
- Contracts, invoices and invoice lines with different currencies can no longer be saved. (Baseline: allowed today.) (checkable)
- Total contract value, yearly value and yearly billable value are shown for a contract. (Baseline: only a monthly-or-yearly equivalent of the recurring cost is shown.) (checkable)
- Existing contracts, invoices and invoice templates remain usable after upgrade. (Baseline: n/a.) [NEEDS CLARIFICATION: define the acceptance criteria and the volume of existing data.]
- The existing tests are updated for the changed behaviour, new tests cover all the use cases described here (including the migrations), and all pass on NetBox 4.6. (Baseline: unknown; the CI does not pin a NetBox release.)

## Cost of Inaction

Users keep describing contracts with one recurring and one non-recurring amount, keep building invoice templates as the only structure, and keep adjusting invoice amounts and lines by hand; one-time and usage-based costs are not distinguished, and inconsistent currencies across a contract and its invoices remain possible. The evidence shows no quantified cost of this and no demand beyond the maintainer's own issue, which has been open since 2025-09-12 with no comments, so the size of the loss is unknown. The main effect on the plugin itself is that the maintainer's stated direction (replacing invoice templates) stays open. (Sources: research.md, Users & Demand and Market & Context.)

## Clarifications (answered by the maintainer, 2026-09-26)

These answers came from the maintainer and bound the problem for the next stages; they are not conclusions of this assessment.

Billing behaviour:

- **Unit "month" attribute**: for a recurring unit it is the number of months one unit price covers (monthly = 1, quarterly = 3, yearly = 12). The unit price is per that period, so an invoice covering N months bills quantity x unit price x N / month.
- **Partial periods**: when an invoice period only partly overlaps a recurring contract line's dates, the amount is prorated by days for the fraction covered; generated invoice lines stay adjustable.
- **One-time ("unique") costs**: the remaining amount is quantity x unit price minus the amounts already invoiced for that contract line on Posted invoices; Draft and Canceled invoices are ignored (the plugin has no Paid status).
- **Child contracts**: an invoice for a billable parent includes the contract lines of all non-billable descendants, stopping at any billable child (which invoices itself).
- **Currency across the hierarchy**: a non-billable child may not have a currency different from its parent; this is validated when the parent link is set.
- **Usage-based contract lines**: a generated invoice line starts with the contract line's quantity and unit price as defaults, and the user edits the quantity to the actual usage on each invoice (amount = quantity x unit price).
- **Accounting dimensions**: a contract line can carry several accounting dimensions, as invoice lines do today; they are copied onto each generated invoice line and stay editable there.
- **Money storage**: plain Django decimal fields next to the existing currency fields and currency choices; no money library (option 1 of the alternatives compared in research.md).
- **Invoices linked to several contracts**: new invoices link at most one contract; existing invoices already linked to several contracts are left as they are (decided during specification, 2026-09-26).
- **Computed contract values**: total = the contract's lines over their periods (recurring lines over their dates, one-time lines once, usage-based lines at their stated quantity); yearly = recurring lines annualised; yearly billable = the yearly value of the lines invoiced under the contract (own lines when billable, plus non-billable descendants' recurring lines) (decided during specification, 2026-09-26).
- **Invoice pre-fill**: it switches to the contract lines in the first release, so it no longer reads the deprecated cost fields; from release 1 it computes the invoice amount and period from the contract lines (recurring, proration by days, one-time), while usage handling, the child roll-up and generation of invoice lines follow in release 2.
- **Tests**: the specification includes modifying the existing tests and adding new tests that cover all the use cases.
- **"Billable" flag**: existing contracts are all billable after the upgrade.
- **Non-recurring cost in the invoice pre-fill**: the question of whether omitting it was deliberate is superseded, since one-time costs are covered by the rules above.

Existing data and upgrade:

- **Invoice templates**: converted by a migration into contract lines, carrying their accounting dimensions; the old template invoices stay in place but are deprecated and no longer used for generation.
- **mrc / yrc / nrc**: converted by a migration into contract lines (monthly recurring, yearly recurring, one-time); the old fields stay but are deprecated and hidden by default.
- **Existing currency mismatches**: currency rules are validated on save only; existing rows are left untouched and a report or warning lists the mismatches.

Compatibility scope:

- The minimum supported NetBox version is raised to 4.6 (`min_version = '4.6.0'`), no `max_version` is set, the CI is pinned to a NetBox 4.6 tag for this work, and new code avoids the NetBox APIs removed in 4.7 so the later 4.7 work stays small.

## Open Questions

- [NEEDS CLARIFICATION: Who beyond the maintainer needs per-line, one-time or usage-based billing today, and how many installations are affected? (research.md)]
- [NEEDS CLARIFICATION: How many existing contracts and invoice templates would the conversion migrations touch, and what reference scenarios (one-time, recurring, usage-based, partial periods) define correct invoice amounts? (research.md)]
- [NEEDS CLARIFICATION: Do the existing tests pass on NetBox 4.6? Not yet run; the CI is to be pinned to a 4.6 tag. (research.md)]
