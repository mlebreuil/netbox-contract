# Quickstart: validate choice descriptions

Prerequisite: specification 008 implemented.

```bash
cd ../netbox
NETBOX_CONFIGURATION=netbox.configuration_testing venv/bin/python netbox/manage.py test \
    netbox_contract.tests.test_choice_descriptions --keepdb
```

Manual: open an invoice edit form and open the status list: each option shows its sentence; same for contract status, unit billing method and the three filter panels; switch the user language to French and check; set `FIELD_CHOICES` to add a status without description and confirm it renders. `makemigrations --check --dry-run` reports no change; `ruff check` is clean.
