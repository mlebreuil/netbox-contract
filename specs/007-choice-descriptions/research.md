# Research: choice descriptions

Source: NetBox 4.7.4 `utilities/choices.py`, `utilities/forms/fields/fields.py`, widgets. No NEEDS CLARIFICATION remains.

## R1 - Choice definition
- **Decision**: replace the plain `(value, label, color)` tuples by `Choice(value, label, color=..., description=_('...'))`. Colours and values stay identical.
- **Rationale**: `ChoiceSet` accepts `Choice` and still builds `colors` and `CHOICES` as before; plain tuples remain supported, so options a deployment adds through `FIELD_CHOICES` need no change.

## R2 - Rendering
- **Decision**: declare the status and billing-method fields explicitly with `utilities.forms.fields.ChoiceField` (and `MultipleChoiceField` for multi-selects), `choices=<ChoiceSet>.CHOICES`. This applies to: ContractForm.status, InvoiceForm.status, UnitForm.billing_method (add/edit); ContractFilterForm.status, InvoiceFilterForm.status, UnitFilterForm and ContractLineFilterForm billing method (filters).
- **Rationale**: the auto-generated form fields of a model use Django's `ChoiceField` and do not emit `data-description`; filter forms use plain Django fields today. Bulk edit forms have no such field, so nothing to change there.
- **Alternatives**: patch widgets (rejected: more code than using the platform field).

## R3 - Wording (reviewed with the invoicing rules in docs)
| Choice | Description |
|--------|-------------|
| Invoice Draft | Being prepared: amounts and lines can still change |
| Invoice Posted | Final: amount, currency, period, contracts and the amounts of its lines are locked |
| Invoice Canceled | No longer valid; kept for the record |
| Contract Active | In force |
| Contract Canceled | Ended or withdrawn; kept for the record |
| One-time | Billed once, from quantity and unit price |
| Recurring | Billed every period, prorated to the invoice period |
| Usage-based | Billed from a quantity entered on each invoice |

Wording checked against the posted-invoice rules and the billing documentation before being fixed in the tests; final text is the translation source string.

## R4 - Translations
- **Decision**: wrap descriptions in `gettext_lazy`; run `makemessages -l fr`, translate the eight new strings, compile with `compilemessages`; a test asserts every built-in description has a French translation different from the English source.

## R5 - FIELD_CHOICES
- **Decision**: no code change; documentation shows a dict entry with `description` (4.7 accepts it). Tests: extend (existing options keep descriptions, the added option without description renders) and replace (only the configured options, with their descriptions when given).

## R6 - Excluded
- Accounting dimension choices: out of scope (no fixed meaning in the plugin).
