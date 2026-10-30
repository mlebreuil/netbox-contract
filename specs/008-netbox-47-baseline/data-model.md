# Data Model: NetBox 4.7 baseline

No change. No model, field, constraint or migration is added or altered; `makemigrations --check` must still report nothing pending on NetBox 4.7.4. The only stored artefact that changes is the test baseline file `netbox_contract/tests/query_counts.json` (query counts per list view), described in `research.md` D3.
