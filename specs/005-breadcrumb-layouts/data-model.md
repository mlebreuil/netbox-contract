# Data Model: breadcrumb layouts

No model, field or migration change. The trail reads existing relations only.

| Page | Relation used |
|------|---------------|
| Contract | `external_party_object` (generic, service provider or circuit provider) |
| Contract line | `contract` |
| Invoice | `contracts` (many-to-many) |
| Invoice line | `invoice` |
