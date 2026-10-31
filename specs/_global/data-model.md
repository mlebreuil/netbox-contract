# Data model (current state)

Conventions: [CONVENTIONS.md](CONVENTIONS.md). Per-feature deltas are in `specs/NNN-*/data-model.md`. Identifiers in
parentheses name the requirement or decision that introduced or last changed the statement. Models inherit the
NetBox bases named below (tags, custom fields, change log and journaling come with `NetBoxModel`, and with
`OrganizationalModel` / `PrimaryModel` which also add description, comments and owner).

## Overview

```text
ContractType 1 ── * Contract * ── 0..1 ServiceProvider / circuits.Provider   (generic external party)
Contract 1 ── * Contract                       (parent / childs; a non-billable child follows its parent)
Contract 1 ── * ContractLine * ── 1 Unit
Contract 1 ── * ContractAssignment * ── 1 any object of supported_models      (generic)
Contract * ── * Invoice 1 ── * InvoiceLine * ── 0..1 ContractLine
ContractLine * ── * AccountingDimension * ── * InvoiceLine
ContractLine 0..1 ── replaces ── 0..1 ContractLine                               (amendment chain)
```

## ContractType (`OrganizationalModel`, 003-FR-016)

| Field | Type | Rules |
|---|---|---|
| `name` | `CharField(100)`, unique | required |
| `slug` | `SlugField(100)`, unique, blank | derived from `name` in `clean()` and `save()` when empty, made unique (003-FR-018) |
| `description` | `CharField(200)`, blank | longer legacy texts were shortened by migration 0051, full text kept in `comments` (003-FR-017) |
| `comments`, `owner` | inherited | owner `PROTECT`, null (003-FR-019) |
| `color` | `ColorField` | default grey |

## ServiceProvider (`PrimaryModel` + `ContactsMixin`, 003-FR-016)

`name`, `slug` (unique), `portal_url`, contacts, `comments`, plus inherited `description` and `owner` (003-FR-019).

## Contract (`NetBoxModel` + `ContactsMixin`)

| Field | Type | Rules |
|---|---|---|
| `name` | `CharField(100)` | required |
| `contract_type` | FK `ContractType`, `PROTECT`, null | related name `contracts` |
| `external_party_object_type` / `_id` / `external_party_object` | generic FK, null | service provider or circuit provider (004-FR-007); the form writes both parts or neither (004-FR-006) |
| `external_reference`, `internal_party`, `tenant`, `documents`, `comments` | | `internal_party` choices `InternalEntityChoices` |
| `status` | choices `StatusChoices` (`active`, `canceled`) | default `active`; each value has a description (007-FR-003) |
| `start_date`, `end_date` | `DateField`, null | changing them so that existing lines fall outside is refused (001-FR-002a) |
| `initial_term` (12), `renewal_term` (12), `notice_period` (90), `invoice_frequency` | integers | months / days |
| `currency` | choices `CurrencyChoices` | cannot change once the contract has invoices or invoice lines (001-FR-009a); lines and non-billable descendants follow a change otherwise (001-FR-009a, 001-FR-010) |
| `parent` | FK `Contract`, null | related name `childs`; a non-billable child has its parent's currency (001-FR-010) |
| `billable` | `BooleanField`, default `True` | all contracts existing at the upgrade are billable (001-FR-005); cannot change when the contract, an ancestor or a descendant has an invoice, or an invoice line references one of its lines (001-FR-008a) |
| `mrc`, `yrc`, `nrc` | `DecimalField` | **deprecated**, hidden unless `show_deprecated_fields` (001-FR-015) |

Computed on read, never stored, not in GraphQL (003-FR-015a): `total_contract_value` (none when a line is open-ended
on an open-ended contract, 001-FR-007), `yearly_contract_value`, `yearly_billable_value` (0 when not billable;
otherwise its own recurring lines plus those of non-billable descendants, stopping at billable children, replaced lines
left out; 001-FR-006, 001-FR-022). They come from `models.contract_values()`, in a fixed number of queries
(003-FR-006).

## Unit (`NetBoxModel`)

| Field | Type | Rules |
|---|---|---|
| `name` | `CharField(100)`, unique | |
| `description`, `comments` | `TextField`, blank | |
| `billing_method` | choices `BillingMethodChoices` (`one-time`, `recurring`, `usage-based`) | each value has a description (007-FR-002) |
| `months` | `PositiveSmallIntegerField`, null | required and at least 1 for `recurring`, empty otherwise (001-FR-001) |

Deleting a unit used by a contract line is refused (`PROTECT`); `billing_method` and `months` cannot change while a
line of an invoiced contract uses the unit (001-FR-001a, 001-FR-029). Created by the conversion: "One-time",
"Monthly" (1), "Yearly" (12) (001-FR-013).

## ContractLine (`NetBoxModel`; permission action `amend`, 003-FR-001)

| Field | Type | Rules |
|---|---|---|
| `contract` | FK `Contract`, cascade, related name `lines` | required |
| `description` | `CharField(200)` | required |
| `quantity` | `DecimalField(12, 4)` | default 1; zero and negative accepted (credits) |
| `unit_price` | `DecimalField(12, 2)` | required; zero and negative accepted |
| `unit` | FK `Unit`, `PROTECT` | required |
| `currency` | choices `CurrencyChoices` | defaults to the contract's and must equal it (001-FR-009) |
| `start_date`, `end_date` | `DateField`, null | default to the contract's; must lie within the contract's and not be reversed (001-FR-002, 001-FR-002a) |
| `accounting_dimensions` | M2M `AccountingDimension`, blank | any number (001-FR-003) |
| `comments` | `TextField`, blank | |
| `replaces` | FK self, null, `SET_NULL`, related name `replaced_by`, read-only | set by the amend action (001-FR-030) |
| `invoiced_at_conversion` | `BooleanField`, read-only | set only by the conversion for a one-time line already invoiced (001-FR-014) |

Ordering: contract, start date, description. Lock: once the contract has any invoice, lines cannot be added or
deleted and their contract terms (contract, description, quantity, unit price, unit, currency, dates, custom fields)
cannot change; accounting dimensions, comments and tags stay editable (001-FR-029, 001-I9). A line referenced by an
invoice line cannot be deleted. The price or quantity of a recurring or usage-based line changes through the amend
action: the line ends the day before the effective date and a successor line is created (001-FR-030, 001-I10). Not
stored: `total_value`, `yearly_value` (`calculations.py`).

## Invoice (`NetBoxModel`)

| Field | Type | Rules |
|---|---|---|
| `number`, `date`, `documents`, `comments` | | |
| `status` | choices `InvoiceStatusChoices` (`draft`, `posted`, `canceled`) | default `draft` (001-FR-031); each value has a description (007-FR-001) |
| `contracts` | M2M `Contract`, related name `invoices`, blank | a new invoice has at most one contract (001-FR-011); an existing invoice with several keeps working while the number does not increase |
| `period_start`, `period_end`, `currency`, `amount` | | currency equals the contract's (001-FR-009) |
| `template` | `BooleanField` | **deprecated** (001-FR-014, 001-FR-015); never deleted |

Ordering `-period_start`. A Posted invoice (not a template) is locked: amount, currency, period and contracts cannot
change, lines cannot be added or deleted, and the amounts of its lines cannot change; its status can
(001-FR-031, 001-I12). Creating an invoice for a billable contract generates its lines (001-FR-021, 001-FR-022);
creating one for a non-billable contract is refused (001-FR-023). The sum of the lines never exceeds the invoice
amount.

## InvoiceLine (`NetBoxModel`)

| Field | Type | Rules |
|---|---|---|
| `invoice` | FK `Invoice` | required |
| `contract_line` | FK `ContractLine`, null, `SET_NULL` | belongs to the invoice's contract or a non-billable descendant (001-FR-021a) |
| `unit` | FK `Unit`, null, `PROTECT` | default from the contract line (001-FR-024, 001-I11) |
| `unit_price`, `quantity` | `DecimalField(12, 2)`, `(12, 4)`, null | default 1; editable while the invoice is not posted |
| `amount` | `DecimalField` | always quantity x unit price, never typed; an amount given alone at creation becomes the unit price (001-FR-024, 001-I14); not recalculated on a Posted invoice |
| `currency` | choices | equals the invoice's (001-FR-009) |
| `accounting_dimensions`, `comments` | | stay editable on a Posted invoice |

## AccountingDimension (`NetBoxModel`)

`name` (20), `value` (20), `status` (`active`, `inactive`), `comments`; unique together (`name`, `value`); ordering
`name`, `value`.

## ContractAssignment (`NetBoxModel`)

| Field | Type | Rules |
|---|---|---|
| `content_type`, `object_id`, `content_object` | generic FK | types limited to `supported_models` that exist and are exposed in the REST API (004-FR-002) |
| `contract` | FK `Contract`, cascade, related name `assignments` | |

`UniqueConstraint(contract, content_type, object_id)` named `netbox_contract_unique_assignment` and an application
check "<contract> is already assigned to <object>." (004-FR-014, 004-FR-015). Deleting an assigned core object deletes
its assignments through a `GenericRelation` on the supported core models (006-FR-012); orphans left from before are
listed and removed by `cleanup_orphan_assignments` (006-FR-013).

## Choice sets

`StatusChoices` (contract), `InvoiceStatusChoices`, `BillingMethodChoices`, `CurrencyChoices`,
`InternalEntityChoices`, `AccountingDimensionStatusChoices`. Installations extend them through `FIELD_CHOICES`
(`netbox_contract.<ChoiceSetName>`); a choice may carry a `description` (007-FR-007, 007-D2). Stored values, labels
and colours are public interfaces (Constitution V).

## Migrations

| Migration | Content | Feature |
|---|---|---|
| 0044 | `Unit`, `ContractLine`, `Contract.billable`, `InvoiceLine.contract_line`, `InvoiceLine.quantity` | 001 |
| 0045 | data: convert legacy costs and invoice templates into contract lines (idempotent, 001-FR-016) | 001 |
| 0046 | `ContractLine.replaces` | 001 |
| 0047 | `InvoiceLine.unit`, `unit_price` copied from the contract line | 001 |
| 0048 | `Invoice.status` default Draft | 001 |
| 0049 | data: derive unit price of existing invoice lines, amounts unchanged | 001 |
| 0050 | `amend` permission on `ContractLine` | 003 |
| 0051 | `ContractType`: slug, comments, owner, description shortened (reversible) | 003 |
| 0052 | `ServiceProvider`: description, owner | 003 |
| 0053 | state only: `related_name='+'` on both `owner` fields (NetBox 4.7) | 008 |
| 0054, 0055 | merge duplicate assignments, then the unique constraint | 004 |

Data migrations are lossless and re-runnable (Constitution IV).
