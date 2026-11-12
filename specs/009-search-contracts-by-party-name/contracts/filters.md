# Contract filters: external party name

> Delta of feature 009. Current state: [REST](../../_global/contracts/rest-api.md), [GraphQL](../../_global/contracts/graphql.md), [UI](../../_global/contracts/ui.md), which this feature keeps up to date.

## Quick search (contract list)

`q=<text>` also lists the contracts whose external party, a service provider or a circuit provider, has a name containing `<text>`, case-insensitive. Still limited to Active contracts; still matches name, external reference and comments (009-FR-001 to 009-FR-004).

## REST and list view

| Parameter | Meaning |
|---|---|
| `external_party_name=<name>` | the party's name is exactly `<name>`; repeatable (any of) |
| `external_party_name__ic=<text>` | the party's name contains `<text>`, case-insensitive |
| `external_party_name__ie=<name>` | exactly, case-insensitive |
| `external_party_name__n=<name>` | the party's name is not `<name>` (contracts without a party included) |

Both party types are searched. The filters combine with every other contract filter and do not restrict the status. `service_provider_id` and `provider_id` are unchanged. The same parameters work in the contract list address and in `/api/plugins/contract/contracts/` (009-FR-006, 009-FR-007, 009-FR-009).

## GraphQL

`contract_list(filters: {external_party_name: {i_contains: "acme"}})`. The supported lookups are those of 009-D4; for the same text and an equivalent lookup (`i_contains` for `__ic`, `exact` for the exact filter, `i_exact` for `__ie`) the result equals the REST result (009-FR-008, 009-SC-002). GraphQL has no negated variant.

## Filter form

Contract filter form, "Parties" section: a text field "External party name" with the lookup-modifier drop-down when NetBox offers it for the field (009-D2). The French label is translated.
