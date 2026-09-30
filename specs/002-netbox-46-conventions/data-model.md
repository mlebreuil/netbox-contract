# Data model: Align with NetBox 4.6 plugin conventions

No model, field, relation, migration or stored value changes (FR-013). `makemigrations netbox_contract --check`
MUST report nothing pending after the change.

What changes is how the nine existing `NetBoxModel`s are exposed in the UI:

| Model | Detail route today | Journal tab today | After |
|---|---|---|---|
| Contract | `get_model_urls` | yes | unchanged |
| Invoice | `get_model_urls` | yes | unchanged |
| Unit | `get_model_urls` | yes | unchanged |
| ContractLine | `get_model_urls` | yes | unchanged |
| ServiceProvider | `get_model_urls` | yes | unchanged |
| InvoiceLine | hand-written | no | `get_model_urls`, Journal tab |
| AccountingDimension | hand-written | no | `get_model_urls`, Journal tab |
| ContractType | hand-written | no | `get_model_urls`, Journal tab |
| ContractAssignment | hand-written | no | `get_model_urls`, Journal tab |

Journal entries use NetBox's own `extras.JournalEntry` (generic relation to any `JournalingMixin` model); no plugin
table is involved.
