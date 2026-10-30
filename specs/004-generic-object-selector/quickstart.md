# Quickstart: validate the generic-object selector

## Prerequisites

Specification 008 implemented (NetBox 4.7.4, green baseline). A NetBox 4.7.4 development instance with the plugin installed in editable mode, a superuser, one device, one site, one circuit provider and one service provider.

## Automated

```bash
cd ../netbox
NETBOX_CONFIGURATION=netbox.configuration_testing venv/bin/python netbox/manage.py test \
    netbox_contract.tests.test_assignment_selector netbox_contract.tests.test_views netbox_contract.tests.test_api --keepdb
```

Expected: all pass; before the change the new module and the updated form-data tests fail.

## Manual (about 5 minutes)

1. Open a device, tab **Contracts**, **Add contract**: the device is already chosen; pick a contract and save. You return to the device page (US1-1, US1-4).
2. Open **Contract assignments**, **Add**: choose the type "site", type three letters of a site name, pick it. No number is asked (US1-2).
3. Restrict a test user to one device with an object permission (constraint), then search devices: only that device is offered (US1-4).
4. Save with a type and no object: the message names the type (US1-6).
5. Open the old link `.../assignments/add/?content_type=<ct>&object_id=<id>`: the object is preselected (R3).
6. New contract: the type is "service provider"; switch to "circuit provider", type part of a name, save; edit it: the provider is selected; switch the type: the provider clears (US2).
7. Import a CSV of assignments and bulk edit contracts: same results as before (US3).

## Checks

- `makemigrations netbox_contract --check --dry-run`: no change (the new migration 0053 is part of the repository).
- `ruff check`.
- Search the plugin for the removed code: `grep -n "alter_object" netbox_contract/views.py` shows neither override.

## Duplicate assignments

1. Assign a contract to a device; repeat the same assignment through the form, a CSV import row and `POST /api/plugins/contract/contract-assignments/`: refused each time with the message of `contracts/forms-and-urls.md`.
2. On a copy of a production-like database, insert duplicates with different tags, run `manage.py migrate netbox_contract`: the report lists each group, one row remains with all tags; run `migrate` again: nothing to merge.
3. `psql`: inserting the pair twice by hand fails with the constraint name `netbox_contract_unique_assignment`.
