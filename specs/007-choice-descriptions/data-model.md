# Data Model: choice descriptions

> Delta of feature 007: what this feature adds or changes. The current state is in [specs/_global/data-model.md](../_global/data-model.md), which this feature keeps up to date.

No field, constraint or migration change. Descriptions are presentation metadata of the choice sets.

| ChoiceSet | Values (unchanged) | New metadata |
|-----------|--------------------|--------------|
| StatusChoices (contract) | active, canceled | description per value |
| InvoiceStatusChoices | draft, posted, canceled | description per value |
| BillingMethodChoices | one-time, recurring, usage-based | description per value |
