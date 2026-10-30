# Quickstart: validate breadcrumbs

Prerequisite: specification 008 implemented.

```bash
cd ../netbox
NETBOX_CONFIGURATION=netbox.configuration_testing venv/bin/python netbox/manage.py test \
    netbox_contract.tests.test_breadcrumbs --keepdb
```

Manual: open a contract with a service provider, then one with a circuit provider, then one without; click the party entry (list filtered). Open an invoice with two contracts, an invoice line and a contract line; open the changelog tab of each: same trail. Confirm `ls netbox_contract/templates/netbox_contract/` no longer contains the four templates, and `ruff check` is clean.
