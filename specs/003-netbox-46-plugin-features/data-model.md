# Data Model: Adopt NetBox 4.6 plugin features

Phase 1 of [plan.md](plan.md). Only two models change shape (contract type, service provider), and one model gains a
permission (contract line). The other six models are unchanged.

## ContractType → `OrganizationalModel` (D9, D10)

| Field | Before | After | Notes |
|---|---|---|---|
| `name` | `CharField(100, unique)` | unchanged (inherited definition is identical) | |
| `slug` | none | `SlugField(100, unique, blank=True)` (redeclared with `blank=True`) | Derived from `name` in `clean()` and `save()` when empty: `unique_slug(name, taken)` |
| `description` | `TextField(blank)` | `CharField(200, blank)` (inherited) | Over 200 characters: shortened by the migration, full text moved to `comments` |
| `comments` | none | `TextField(blank)` (inherited) | |
| `owner` | none | `ForeignKey(users.Owner, PROTECT, null)` (inherited) | |
| `color` | `ColorField` | unchanged | |

Validation:
- The slug is unique.
- An empty slug is derived from the name and never rejected (FR-018).
- A slug that is given is validated by the slug format and is kept as given.

## ServiceProvider → `PrimaryModel` (D9)

| Field | Before | After |
|---|---|---|
| `name`, `slug`, `portal_url`, `comments`, contacts | unchanged | unchanged (`comments` now inherited, same definition) |
| `description` | none | `CharField(200, blank)` (inherited) |
| `owner` | none | `ForeignKey(users.Owner, PROTECT, null)` (inherited) |

## ContractLine: permission action (D6)

`Meta.permissions = [('amend', 'Amend the price or quantity of an invoiced contract line')]`. There is no column
change.

Permission name: `netbox_contract.amend_contractline`. NetBox lists it as the action `amend` of the object type
`netbox_contract | contract line` in object permissions.

## Migrations

| Migration | Operations | Data |
|---|---|---|
| `0050_contractline_amend_permission` | `AlterModelOptions(contractline, permissions=...)` | none |
| `0051_contracttype_organizational` | add `slug` (null) · add `comments` · add `owner` · `RunPython(fill_slugs_and_shorten_descriptions, restore_descriptions)` · alter `slug` unique not null · alter `description` to `CharField(200)` | Each empty slug is filled. Each description over 200 characters is shortened, with the full text in `comments`. Prints one report line per slug made unique (`-2`, ...) and per description moved |
| `0052_serviceprovider_primary` | add `description` · add `owner` | none |

Re-run safety (Constitution IV):
- The data function only touches rows with an empty slug or a description over 200 characters. A second run finds
  none.
- Reversing `0051` restores `TextField` for `description`. `restore_descriptions` then puts the full text from
  `comments` back into `description` for every moved description (`shorten_description(comments) == description`),
  and only then are the new columns dropped. Moved descriptions are not lost (spec US5-7). Comments typed after the
  upgrade are dropped with their column, as the migration docstring says.
- Both data functions delegate to pure helpers in `netbox_contract/text.py` (`unique_slug`, `shorten_description`,
  `plan_contract_type_changes`).

## Computed state used by the UI (no storage)

| Name | Where | Meaning |
|---|---|---|
| `is_locked_line` | annotation on the contract line list view queryset (`with_lock_state()`) | An invoice line references the line, or its contract has an invoice. This is the `lock_message()` rule. |
| `has_successor` | same | Another line replaces it. `can_be_amended` is false. |
| `invoice_id` | new `ContractFilterSet` filter | Contracts of an invoice (reverse `invoices` relation). Used by the invoice page table. |
