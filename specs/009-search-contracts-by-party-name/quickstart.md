# Quickstart: validate the search by external party name

Prerequisite: the feature implemented on branch `333-search-contracts-by-party-name`.

```bash
./dc test netbox_contract.tests.test_party_name
./dc test            # whole suite, query-count baseline included
./dc ruff check
./dc python utils/spec_ids.py check
./dc manage makemigrations netbox_contract --check --dry-run
```

Manual (`utils/docs_screenshots` data or `manage.py create_demo_data`, which needs `DEVELOPER = True`):

1. Create a service provider "Acme Telecom" and a circuit provider "Globex Carrier" with one Active contract each.
2. Contracts list, search "acme": only the Acme contract; search "carrier": only the Globex contract; search a contract's own name: still found.
3. Set the contract to a status other than Active: the quick search no longer lists it; the filter `?external_party_name=Acme Telecom` still does.
4. Open the filter panel: the "External party name" field is in "Parties"; try the modifier drop-down.
5. REST: `/api/plugins/contract/contracts/?external_party_name__ic=acme`; GraphQL: `{ contract_list(filters: {external_party_name: {i_contains: "acme"}}) { id name } }`: same contract.
6. Rename the provider and repeat: the new name is found at once.

Expected: no migration, no change in the list's query count, `service_provider_id` and `provider_id` unchanged.
