# Research: NetBox 4.7 baseline

All questions were settled by running the suite on NetBox v4.7.4 (Python 3.13, PostgreSQL 16, Redis) and reading the 4.7.4 source. No NEEDS CLARIFICATION remains.

## D1 - Pin the CI to the tag v4.7.4

- **Decision**: `ref: v4.7.4` in the NetBox checkout step.
- **Rationale**: the constitution requires a tag, never a moving branch. v4.7.4 is the latest 4.7 release (2026-10-27) and is the version the assessment ran.
- **Alternatives**: a matrix of 4.7.0 and 4.7.4 (rejected: doubles CI time for no extra evidence, 4.7.x are patch releases); the `main` branch (rejected by the constitution).

## D2 - Fix the REST tests by giving text values

- **Decision**: in `create_data` and `update_data` of the contract, contract line and invoice API tests, give dates as ISO strings (`'2025-01-01'`). Decimal amounts are left as they are: the 4.7 helper compares them with the stored `Decimal`, and a text amount made the invoice tests fail (found during implementation).
- **Rationale**: NetBox 4.7's `assertInstanceEqual(api=True)` turns the stored object into its JSON form (text for dates and decimals) and compares it with the test data as given; an API client sends text anyway, so the test becomes more faithful. 4.6.10 accepted the Python objects; the text form is expected to work there too but is not tested on 4.6.
- **Alternatives**: exclude the fields from the comparison (rejected: loses the assertion on stored values); convert in a custom `assertInstanceEqual` override (rejected: more code than changing the data).

## D3 - Re-record the query-count baseline once

- **Decision**: run the documented procedure `UPDATE_QUERY_COUNTS=1 ... test_views test_api --keepdb`, serially, and commit the changed `query_counts.json` with the reason "NetBox 4.7.4 runs one query fewer on every list page".
- **Rationale**: all nine failures are exactly one lower (15 against 16, 16 against 17, 17 against 18 for four models, 22 against 23), which points to a core change and not to the plugin; the observed query lists show no plugin query. The count is NetBox-version specific, which is why a single baseline cannot serve 4.6 and 4.7 (option B was rejected).
- **Alternatives**: loosen the assertion to a range (rejected: the baseline exists to catch added queries).

## D4 - Version numbers

- **Decision**: plugin `2.6.0`, `min_version = '4.7.0'`, no `max_version`.
- **Rationale**: 2.5.0 is released (tag v2.5.0), a release that drops a NetBox version and adds features is a minor version under the constitution, and specification 003 had already reserved 2.6.0 for the REST representation shrink. 2.6.0 can carry both.
- **Alternatives**: 3.0.0 (rejected: major is for removal of the plugin's own interfaces).

## D5 - Python 3.14 and the CI services

- **Decision**: keep the 3.12 to 3.14 matrix and the unpinned PostgreSQL and Redis service images.
- **Rationale**: NetBox 4.7.4 declares 3.12 to 3.14 in its classifiers. The assessment ran 3.13 only; 3.12 and 3.14 are verified by the first CI run, which is the purpose of the matrix.
- **Risk**: a 3.14-only failure would show in CI; it would be recorded and handled as its own fix.

## D6 - Constitution wording

- **Decision**: change the compatibility section (Python 3.12 or newer; NetBox 4.7 or newer) through `/speckit-constitution` as a PATCH amendment (1.0.1) in the same change.
- **Rationale**: the constitution says "NetBox 4.6 or newer until a specification raises the minimum" and "4.7 compatibility is separate work"; this specification is that raise, so the text must say so, through the amendment procedure it defines.
- **Alternatives**: edit by hand (rejected: governance requires the skill).

## D7 - Owner field migration (found during implementation)

- **Finding**: `makemigrations --check --dry-run` on NetBox v4.7.4 proposes `AlterField` for `contracttype.owner` and `serviceprovider.owner`: 4.7's owner field has `related_name='+'`, the plugin's migrations 0051 and 0052 (written for 4.6) do not. The compatibility assessment had not run this check.
- **Decision**: hand-written `0053_owner_related_name.py` with the two `AlterField` operations, depending on `netbox_contract.0052` and `users.0015_owner` only (the auto-generated dependency on `users.0016_default_ordering_indexes` would make the plugin fail on a 4.7.x that lacks it). A related-name change produces no SQL and no data change.
- **Test**: `MigrationStateTestCase` in `test_conventions.py` asks Django's autodetector for pending changes of `netbox_contract`; it failed before the migration and passes after. It also guards later work (specification 004 adds migration 0054).
- **Alternatives**: setting `related_name` differently on the plugin models (rejected: the field comes from NetBox's mixin).
