# Quickstart: validate GraphQL extensions

Prerequisite: specification 008 implemented.

```bash
cd ../netbox
NETBOX_CONFIGURATION=netbox.configuration_testing venv/bin/python netbox/manage.py test \
    netbox_contract.tests.test_graphql_extensions netbox_contract.tests.test_graphql --keepdb
```

Manual: open `/graphql/` (GraphiQL), run the example of `contracts/graphql-schema.md`; check a device with and without contracts; log in as a user without contract permission and repeat; delete a test device and confirm its assignments disappear. `makemigrations netbox_contract --check --dry-run` reports no change.

## Orphan cleanup

```bash
python manage.py cleanup_orphan_assignments            # report only
python manage.py cleanup_orphan_assignments --apply    # delete the reported orphans
python manage.py cleanup_orphan_assignments            # reports none
```

Tests: `netbox_contract.tests.test_orphan_cleanup`.
