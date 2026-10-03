# Idea Intake: Contract lines, units and billing methods

- **Slug**: contract-lines-units
- **Created**: 2026-09-25
- **Last updated**: 2026-09-26 (scope updates from the maintainer, see Scope Update)
- **Source**: https://github.com/mlebreuil/netbox-contract/issues/278 (content supplied by the user as pasted text)
- **Type**: new-capability

## Idea (as captured)

Source: GitHub issue #278 of mlebreuil/netbox-contract. URL Trust Policy branch taken: `auto-refused: connected peer could not be validated (fetch went through a loopback address)`. The URL was not fetched; the issue body below was pasted by the user.

Issue metadata: netbox-contract plugin version v2.5.0; NetBox version v4.3.0; Feature type: Data model extension.

> **Proposed functionality**
>
> New models:
>
> ContractLine
> New model to replace the invoice templates
> Describes the billable or deliverable items within the contract.
>
> Attributes:
>
> - id
> - contract_id
> - description
> - quantity
> - unit_price (will be MoneyField from the django-money app, https://github.com/django-money/django-money)
> - unit (ref to a unit model instance - see below)
> - start_date, end_date (specific to the line, default to contract start and end)
> - accounting_dimensions
>
> invoice line should be generated from contract lines and editable
> On the invoice line automatically add a reference to the contract line
>
> Unit
> This is a new model
>
> Attributes:
>
> - id
> - name
> - description
> - billing_method (unique, recurring, usage_based)
> - month (only relevant for recurring units. quantity of month)
>
> Invoice line computation:
>
> Unique costs are calculated for each invoice based on the remaining amount to pay compared to the sum of amount paid for this contract line over the entire contract period.
> Recurring costs a billed for each invoice in relation with the period covered by the invoice.
> Usage_based cost are calculated for each invoice based on quantity and unit price only.
> All invoice lines can be adjusted.
>
> Contract model changes:
>
> mrc, yrc and nrc are replaced by the units and associated billing methods and deprecated.
> Add "billable" field to the contract. This will control invoice generation for the contract.
> Add calculated fields for:
> - Total contract value
> - Yearly contract value
> - Yearly contract billable value
>
> Invoice Generation:
>
> - If the contract is not billable generate an error.
> - if the contract is billable create invoice line for each of the contract line and child contact lines if the corresponding contract is not billable.
>
> Currency:
>
> - Enforce invoice line currency to be the invoice currency.
> - Enforce contract line currency to be the contract currency.
> - Enforce Invoice currency to be the contract currency.
>
> **Use case**
>
> Better management of the billing method:
> - non recurring cost vs recurring costs.
> - fixed versus usage based costs
>
> **External dependencies**
>
> none

## Restated

The proposal adds ContractLine and Unit models to the contract plugin so that the billable contract lines of a contract carry a quantity, unit price, unit and billing method (unique, recurring or usage-based). Invoice lines would be generated from contract lines, replacing invoice templates and the contract-level mrc/yrc/nrc fields, with a new "billable" flag on contracts, computed contract values, and enforced currency consistency between contract, contract lines, invoices and invoice lines.

## Origin & Context

- **Raised by**: the plugin maintainer (mlebreuil), who opened issue #278 on 2025-09-12 (the pasted text did not name the author; taken from the issue page, see research.md)
- **Trigger**: [NEEDS CLARIFICATION: the issue gives a use case (better handling of recurring vs non-recurring and fixed vs usage-based costs) but no triggering event]

## Scope Update (maintainer input, 2026-09-25 and 2026-09-26)

- **NetBox baseline**: this issue targets **NetBox 4.6**. The version numbers in the issue (plugin v2.5.0, NetBox v4.3.0) reflect the age of the issue and are not the baseline.
- **NetBox 4.7 is out of scope** for this issue. The maintainer will handle 4.7 compatibility separately and later, because the deprecation of custom scripts in NetBox core is a large change.
- **django-money**: it is missing from the repository's dependencies today (the issue text lists "External dependencies: none"). The maintainer first said it should be added, then decided on 2026-09-26 that it **should be replaced**: `unit_price` and the other amounts will not use django-money's MoneyField. The alternatives are compared in `research.md`; the maintainer chose plain Django decimal and currency fields with no money library (2026-09-26).
- **Minimum NetBox version**: `min_version` is to be **raised to 4.6** (maintainer, 2026-09-26).
- **Behaviour and upgrade clarifications** (unit "month", proration, one-time costs, child contracts, migrations, currency handling, billable default) were answered by the maintainer on 2026-09-26 and are recorded in `problem.md` under Clarifications.

## First-Glance Unknowns

All eight first-glance unknowns were answered by the maintainer on 2026-09-26; the answers are recorded in `problem.md` under Clarifications.

- **Answered** — existing data (invoice templates, mrc/yrc/nrc): migrations convert them into contract lines; the old templates and fields stay, deprecated and hidden.
- **Answered** — meaning of billing_method "unique" and of the Unit "month" attribute: "unique" is a one-time cost; "month" is the number of months one unit price covers (monthly 1, quarterly 3, yearly 12).
- **Answered** — proration when an invoice period partly overlaps a contract line's dates: prorated by days.
- **Answered** — remaining amount for unique costs: quantity x unit price minus the amounts on Posted invoices for that contract line (Draft and Canceled ignored).
- **Answered** — child contract lines: a billable parent's invoice includes the contract lines of all non-billable descendants, stopping at any billable child; a non-billable child must have the same currency as its parent.
- **Answered** — accounting dimensions on a contract line: several per line, copied onto each generated invoice line.
- **Answered** — replacement for django-money's MoneyField: plain Django decimal and currency fields, no money library.
- **Answered** — existing contracts or invoices with mismatching currencies: currency rules are validated on save only; existing rows are untouched and a report or warning lists the mismatches.
