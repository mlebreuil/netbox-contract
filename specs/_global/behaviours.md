# Behaviours by domain (current state)

The business rules of the plugin, grouped by domain. Each rule names the requirements (`NNN-FR-nnn`) that introduced
or last changed it; read them with `python utils/spec_ids.py show <id>`. Update this file when a feature adds,
changes or retires a requirement ([CONVENTIONS.md](CONVENTIONS.md)). Rules that apply to all domains:
backward-compatible interfaces (Constitution V), lossless re-runnable migrations (Constitution IV), tests written
first (Constitution II).

## Units and contract lines

| Rule | IDs |
|---|---|
| Units define the nature of a cost (one-time, recurring, usage-based) and, for recurring, the months one price covers | 001-FR-001 |
| A used unit cannot be deleted; its billing method and months are frozen while an invoiced contract uses it | 001-FR-001a |
| A contract has contract lines (description, quantity, unit, unit price, currency, dates, dimensions) | 001-FR-002, 001-FR-003, 001-FR-004 |
| Line dates stay inside the contract's dates | 001-FR-002a |
| Once a contract has an invoice its lines cannot be added, deleted or have their terms changed; dimensions, comments, tags stay editable | 001-FR-029 |
| Price or quantity of a recurring or usage-based line changes by amendment: the line ends, a successor starts; requires the `amend` permission action | 001-FR-030, 003-FR-001, 003-FR-002, 003-FR-003 |

## Contract values and hierarchy

| Rule | IDs |
|---|---|
| Contracts are billable by default; a non-billable child is invoiced by its nearest billable ancestor | 001-FR-005, 001-FR-022 |
| Total, yearly and yearly billable values are computed on read, in a fixed number of queries | 001-FR-006, 001-FR-007, 003-FR-006 |
| `billable` cannot change once the contract or its family has invoices | 001-FR-008a |

## Currency

| Rule | IDs |
|---|---|
| A line, invoice or invoice line has the currency of its contract / invoice | 001-FR-009 |
| A contract's currency is frozen once it has invoices; lines follow it otherwise | 001-FR-009a |
| A non-billable child has its parent's currency | 001-FR-010 |
| Existing mismatches are never corrected automatically; a report lists them | 001-FR-012, 001-SC-003 |

## Invoicing

| Rule | IDs |
|---|---|
| A new invoice has at most one contract; existing multi-contract invoices stay editable | 001-FR-011 |
| Invoice amount and period are proposed from contract lines (recurring prorated, one-time remaining, usage excluded) and editable | 001-FR-017, 001-FR-017a, 001-FR-018, 001-FR-019, 001-FR-020 |
| Creating an invoice generates its lines (own lines plus non-billable descendants); a non-billable contract is refused; the amount cannot be lower than the lines | 001-FR-021, 001-FR-021a, 001-FR-022, 001-FR-023, 001-FR-025 |
| Invoice line amount is quantity x unit price, never typed | 001-FR-024 |
| The new-invoice screen previews the lines and lets the user edit them | 001-FR-032, 002-FR-009, 002-FR-010 |
| New invoices are Draft; a Posted invoice and its line amounts are locked | 001-FR-031 |

## Legacy data and deprecation

| Rule | IDs |
|---|---|
| Legacy costs and invoice templates are converted into contract lines, idempotently, at upgrade | 001-FR-013, 001-FR-014, 001-FR-016 |
| Deprecated fields stay, hidden unless `show_deprecated_fields` | 001-FR-015, 002-FR-012 |
| REST fields to be removed are announced per field before removal | 003-FR-012a |

## Assignments and external parties

| Rule | IDs |
|---|---|
| Assign a contract to an object by choosing its type then searching the object, limited to what the user may view | 004-FR-001, 004-FR-002, 004-FR-003, 004-FR-004, 004-FR-005, 004-FR-006 |
| Find contracts by the name of their external party: quick search, and a filter in the list, REST and GraphQL; global search unchanged | 009-FR-001 to 009-FR-012 |
| Choose the external party of a contract the same way | 004-FR-007, 004-FR-008 |
| A contract is assigned to an object at most once, enforced in the application and the database; duplicates were merged at upgrade | 004-FR-014, 004-FR-015, 004-FR-016, 004-FR-017 |
| Deleting an object deletes its assignments; orphans are cleaned by an explicit command | 006-FR-012, 006-FR-013, 006-FR-014, 006-FR-015 |

## NetBox integration

| Rule | IDs |
|---|---|
| Every model uses NetBox's model view registration, journal and changelog; routes stay stable | 002-FR-001, 002-FR-002, 002-FR-003 |
| Forms are grouped into sections; filter forms have lookup modifiers | 002-FR-004, 002-FR-005, 002-FR-006, 002-FR-007, 002-FR-008 |
| Detail pages use declarative layouts; breadcrumbs per page | 003-FR-004, 003-FR-004a, 003-FR-005, 003-FR-007, 005-FR-001, 005-FR-002, 005-FR-003, 005-FR-004, 005-FR-008 |
| Contract types and service providers use NetBox's organizational and primary bases | 003-FR-016, 003-FR-017, 003-FR-018, 003-FR-019 |
| REST nested objects use brief serializers; GraphQL exposes all nine models with permissions | 003-FR-009, 003-FR-010, 003-FR-011, 003-FR-012, 003-FR-013, 003-FR-014, 003-FR-015, 003-FR-015a |
| Core GraphQL types expose assignments and `has_contracts` / `has_active_contract` filters | 006-FR-001 to 006-FR-006, 006-FR-008 |
| Choices carry translated descriptions shown in drop-downs | 007-FR-001 to 007-FR-005, 007-FR-007, 007-FR-008 |

## Platform

| Rule | IDs |
|---|---|
| Minimum NetBox 4.7.0, no maximum; CI on the pinned 4.7.4 tag for Python 3.12 to 3.14 | 008-FR-001, 008-FR-005, 008-FR-006, 008-FR-007, 008-FR-008 |
| Query-count baselines change once, with a stated reason | 008-FR-003 |
| No pending migration on NetBox 4.7 | 008-FR-010 |
