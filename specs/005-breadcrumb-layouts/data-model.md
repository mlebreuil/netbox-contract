# Data Model: breadcrumb layouts

> Delta of feature 005: what this feature adds or changes. The current state is in [specs/_global/data-model.md](../_global/data-model.md), which this feature keeps up to date.

No model, field or migration change. The trail reads existing relations only.

| Page | Relation used |
|------|---------------|
| Contract | `external_party_object` (generic, service provider or circuit provider) |
| Contract line | `contract` |
| Invoice | `contracts` (many-to-many) |
| Invoice line | `invoice` |
