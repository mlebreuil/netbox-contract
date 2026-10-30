# Data Model: NetBox 4.7 baseline

No column, constraint or value changes. One state-only migration, `0053_owner_related_name`, records `related_name='+'` on `ContractType.owner` and `ServiceProvider.owner` (NetBox 4.7 core definition of the owner field); it produces no SQL. `makemigrations --check` reports nothing pending on NetBox 4.7.4. The only stored artefact that changes is the test baseline file `netbox_contract/tests/query_counts.json` (query counts per list view), described in `research.md` D3.
