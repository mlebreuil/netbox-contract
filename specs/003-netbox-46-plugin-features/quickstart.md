# Quickstart: validate the NetBox 4.6 plugin features

These commands run from the NetBox checkout (`/workspaces/netbox/netbox`) with the test configuration, as in
`CLAUDE.md`. Contracts: [rest-api.md](contracts/rest-api.md), [graphql.md](contracts/graphql.md),
[detail-pages.md](contracts/detail-pages.md). Data model: [data-model.md](data-model.md).

```bash
cd /workspaces/netbox/netbox
T="NETBOX_CONFIGURATION=netbox.configuration_testing"

# 1. Lint and migrations
(cd ../netbox-contract && ruff check)
venv/bin/python netbox/manage.py makemigrations netbox_contract --check --dry-run   # nothing pending
venv/bin/python netbox/manage.py migrate netbox_contract                            # 0050-0052 apply, 0051 prints its report

# 2. Story by story (each module can run alone)
env $T venv/bin/python netbox/manage.py test netbox_contract.tests.test_amend_permission --keepdb    # US1
env $T venv/bin/python netbox/manage.py test netbox_contract.tests.test_detail_layouts --keepdb      # US2
env $T venv/bin/python netbox/manage.py test netbox_contract.tests.test_nested_api --keepdb          # US3
env $T venv/bin/python netbox/manage.py test netbox_contract.tests.test_graphql --keepdb             # US4
env $T venv/bin/python netbox/manage.py test netbox_contract.tests.test_base_classes --keepdb        # US5

# 3. Full suite, including APIViewTestCase (REST + GraphQL) for the nine models and query-count baselines
env $T venv/bin/python netbox/manage.py test netbox_contract.tests --keepdb
```

## Scenario map

| Spec scenario | Test |
|---|---|
| US1 1-7, edge cases (amend without view; per-line button) | `test_amend_permission` |
| US2 1-9, edge cases (deleted external party, per-line actions, column choices) | `test_detail_layouts` |
| US3 1-7, edge cases (invoice line brief, unmatched nested dict) | `test_nested_api` (snapshot guard, writes, brief sets, schema, deprecation notice), `test_api` brief sets |
| US4 1-5, edge case (computed value refused) | `test_graphql`, `test_api` GraphQL cases |
| US5 1-7, edge cases (empty slug, long description without spaces, no owner) | `test_base_classes` (pure helpers, migrate forward/back/forward with `MigrationExecutor`) |

## Manual checks (dev server)

1. **Object permissions.** Open Admin → Object permissions → Add and select *Netbox contract | contract line*. The
   actions list **amend**.
2. **Amend as a restricted user.** Log in as a user with view + amend on contract lines and open an invoiced
   recurring line. The **Amend** button appears in the page header and in the contract's line table, and Delete is
   not offered there.
3. **Contract page.** It shows the same attributes as before. The tables load (HTMX) with column configuration, and
   another plugin's `left_page` content appears.
4. **Nested objects.** `GET /api/plugins/contracts/contractassignment/` returns the same 24-key `contract` as before (`contract_type` an id). `GET .../invoiceline/` returns `invoice` with `id, url, display, number`. `docs/api.md` lists the deprecated nested fields.
5. **GraphQL.** In `/graphql/`, `{ contract_list(filters: {status: {exact: "active"}}) { name contract_type { name } lines { description } } }`
   returns data. `yearly_contract_value` is rejected as an unknown field.
6. **Contract types.** After `migrate`, the contract type list shows slugs, and a type created through the API with
   only `name` gets a slug.
