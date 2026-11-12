# Data model: Search contracts by external party name

> Delta of feature 009: what this feature adds or changes. The current state is in [specs/_global/data-model.md](../_global/data-model.md); this feature does not change it.

No model, field, constraint, index or migration is added or changed (009-FR-010). The feature reads `Contract.external_party_object_type` and `external_party_object_id` (a service provider or a circuit provider) and the `name` of those providers.

The existing index on `external_party_object_type, external_party_object_id` serves the contract side; provider names are looked up in the providers' own tables, which are small. No index is added (to be re-examined if the list slows, with a stated reason).
