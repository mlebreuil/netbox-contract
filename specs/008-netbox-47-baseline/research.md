# Research: NetBox 4.7 baseline

All questions were settled by running the suite on NetBox v4.7.4 (Python 3.13, PostgreSQL 16, Redis) and reading the 4.7.4 source. No NEEDS CLARIFICATION remains.

## D1 - Pin the CI to the tag v4.7.4

- **Decision**: `ref: v4.7.4` in the NetBox checkout step.
- **Rationale**: the constitution requires a tag, never a moving branch. v4.7.4 is the latest 4.7 release (2026-10-27) and is the version the assessment ran.
- **Alternatives**: a matrix of 4.7.0 and 4.7.4 (rejected: doubles CI time for no extra evidence, 4.7.x are patch releases); the `main` branch (rejected by the constitution).

## D2 - Fix the REST tests by giving text values

- **Decision**: in `create_data` and `update_data` of the contract, contract line and invoice API tests, give dates as ISO strings (`'2025-01-01'`) and decimals as strings (`'50.00'`).
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
