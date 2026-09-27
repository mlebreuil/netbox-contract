# Data Model: Contract lines, billing natures and currency consistency

Spec: [spec.md](spec.md) | Decisions: [research.md](research.md)

Types below are Django fields. All new models are `NetBoxModel`s (tags, custom fields, change log, journaling).

## New: Unit

Defines the nature of a cost and, for recurring units, how many months one unit price covers.

| Field | Type | Rules |
|---|---|---|
| `name` | `CharField(100)`, unique | required |
| `description` | `TextField`, blank | |
| `billing_method` | `CharField`, choices `one_time`, `recurring`, `usage` | required |
| `months` | `PositiveSmallIntegerField`, null | required and at least 1 when `billing_method = recurring`; must be empty otherwise (FR-001) |
| `comments` | `TextField`, blank | |

- Deleting a unit that a contract line uses is refused (`ContractLine.unit` is `on_delete=PROTECT`, FR-001a).
- Editing a used unit is allowed, except that `billing_method` and `months` cannot change while a line of a contract that has invoices uses the unit (FR-001a, FR-029). Computed values are calculated on read.
- Created by the conversion (find-or-create by name): "One-time", "Monthly" (1 month), "Yearly" (12 months).

## New: ContractLine

| Field | Type | Rules |
|---|---|---|
| `contract` | FK `Contract`, cascade, related name `lines` | required |
| `description` | `CharField(200)` | required |
| `quantity` | `DecimalField(12, 4)` | default 1; zero and negative values are accepted (credits) |
| `unit_price` | `DecimalField(12, 2)` | required; zero and negative accepted |
| `unit` | FK `Unit`, `PROTECT` | required |
| `currency` | `CharField(3)`, choices `CurrencyChoices` | defaults to the contract's; must equal it (FR-009); follows the contract when the contract currency changes and it has no invoices (FR-009a) |
| `start_date` | `DateField`, null | defaults to the contract's start date; must not be before the contract start date when the contract has one (FR-002a) |
| `end_date` | `DateField`, null | defaults to the contract's end date; must not be after the contract end date when the contract has one (FR-002a); must not be before `start_date` |
| `accounting_dimensions` | M2M `AccountingDimension`, blank | any number (FR-003) |
| `comments` | `TextField`, blank | |
| `replaces` | FK `ContractLine` (self), null, `SET_NULL`, related name `replaced_by`, read-only in forms and API | set by the amend action (FR-030): the line this line replaces from its start date |
| `invoiced_at_conversion` | `BooleanField`, default `False`, read-only in forms and API | set only by the conversion, for a one-time line of a contract that already had a Posted invoice; the line is then treated as fully invoiced (remaining amount 0) |

Lock: adding, changing or deleting a contract line is refused when its contract has any invoice, and changing or deleting it is also refused when any invoice line references it (FR-029); the lock covers its contract terms (contract, description, quantity, unit price, unit, currency, dates, custom fields), while its accounting dimensions, comments and tags stay editable (decision I9). Its price or quantity changes through the amend action, which ends it the day before the new terms and creates the line that replaces it (FR-030). Ordering: contract, start date, description. Currency-mismatch and date rules are in `clean()`, so the UI, bulk import and REST interface enforce them alike.

Derived (not stored): `total_value`, `yearly_value` per line, computed by `calculations.py`.

## Changed: Contract

| Change | Detail |
|---|---|
| new `billable` | `BooleanField`, default `True`; the migration leaves every existing contract `True` (FR-005) |
| new read-only values | `total_contract_value` (None when not available, FR-007), `yearly_contract_value`, `yearly_billable_value` (FR-006), computed on read by `contract_values()` in a fixed number of queries; the yearly values leave out lines replaced by an amendment |
| deprecated, kept | `mrc`, `yrc`, `nrc` (hidden by default, `show_deprecated_fields` setting); `calculated_rc` alias kept in the API during the deprecation period |
| new `clean()` rules | `billable` cannot change when the contract, any ancestor or any descendant has an invoice, or an invoice line references one of its lines (FR-008a); currency change refused when invoices or invoice lines exist (FR-009a); a non-billable child must have its parent's currency (FR-010); changing dates so that existing lines fall outside is refused (FR-002a) |
| unchanged | hierarchy (`parent`, `childs`), `invoice_frequency`, party, dates, status |

Yearly billable value: 0 when the contract is not billable; otherwise the yearly value of its own recurring lines plus the yearly value of the recurring lines of all non-billable descendants, stopping at any billable descendant (which invoices itself).

## Changed: Invoice

- `template` stays, shown as deprecated; conversion never edits invoices.
- `status` defaults to Draft (migration 0048). A Posted invoice (not a template) is locked: its amount, currency, period and contracts cannot change, lines cannot be added or deleted, and the amount fields of its lines cannot change; its status can (FR-031).
- New invoice rules (form and API, research D4): at most one contract for a new invoice (FR-011); invoice currency equals the contract's currency (FR-009); an existing invoice with several contracts is left as it is and stays editable as long as the number of contracts does not increase.
- Pre-fill for a non-billable contract shows an error and proposes nothing (FR-008).

## Changed: InvoiceLine

| Change | Detail |
|---|---|
| new `contract_line` | FK `ContractLine`, null, `SET_NULL` (FR-021); the contract line's contract must be the invoice's contract or one of its non-billable descendants |
| new `quantity` | `DecimalField(12, 4)`, null; defined at the invoice line (FR-024) |
| new `unit`, `unit_price` | FK `Unit` (null, `PROTECT`) and `DecimalField(12, 2)` (null); default to those of the contract line and can change while the invoice is not posted (FR-024, decisions I11 and I12); migration 0047 copies them from the contract line for existing lines |
| `amount` | calculated from `quantity` and `unit_price` when the line has a unit price (FR-024, research D7) and not entered by the user; otherwise it stays a manually entered amount; never recalculated on a Posted invoice |
| `currency` | must equal the invoice's currency (FR-009) |

The existing rule that the sum of invoice lines cannot exceed the invoice amount is kept.

## Relationships

```text
Contract 1 ── * ContractLine * ── 1 Unit
Contract 1 ── * Contract (parent/childs)
ContractLine * ── * AccountingDimension
Contract * ── * Invoice (existing; new invoices link to one contract)
Invoice 1 ── * InvoiceLine * ── 0..1 ContractLine
```

## State and lifecycle notes

- A contract line has no status of its own; its effect on totals ends with its dates.
- A one-time line's remaining amount = quantity x unit price minus the amounts of invoice lines that reference it on Posted invoices (FR-019); draft and canceled invoices are ignored; never below zero.
- Invoice templates are never deleted (FR-014).

## Migrations

1. `0044_units_contract_lines_billable` (schema): `Unit`, `ContractLine`, `Contract.billable`, `InvoiceLine.contract_line` and `InvoiceLine.quantity`.
2. `0045_convert_legacy_costs` (data): calls `conversion.convert_legacy_data()`; reverse is a no-op.
3. `0046_contractline_replaces` (schema): `ContractLine.replaces`.
4. `0047_invoiceline_unit_unit_price` (schema and data): `InvoiceLine.unit` and `InvoiceLine.unit_price`, copied from the contract line for existing lines; amounts unchanged.
5. `0048_invoice_status_draft_default` (schema): `Invoice.status` defaults to Draft.
