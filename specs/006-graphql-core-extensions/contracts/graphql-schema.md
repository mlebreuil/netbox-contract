# Contract: GraphQL schema additions

```graphql
query {
  device_list(filters: {has_active_contract: false, site: "paris"}) {
    name
    contract_assignments {
      contract { name status end_date external_party_object { __typename } }
    }
  }
}
```

- `contract_assignments`: list, empty when none or when the user may not view contracts; ordered as the assignments list.
- `has_contracts`: true = at least one viewable assignment; false = none.
- `has_active_contract`: true = at least one viewable assignment to a viewable contract with status `active` (dates ignored); false = none.
- Absent on types that are not in `supported_models` or have no GraphQL type. Existing plugin queries unchanged.

# Contract: cleanup command

`python manage.py cleanup_orphan_assignments [--apply]`

- Without `--apply`: prints totals per object type, one line per orphan (assignment id, contract, object type, former object id) and a separate list of assignments whose object type is not installed; exit code 0; nothing changed.
- With `--apply`: deletes exactly the orphans listed (not the "cannot judge" ones) in one transaction and prints the count; running again prints none.
