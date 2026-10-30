# Assessment: plugin 2.5.0 (`develop`) against NetBox 4.7.4 (issue #318)

- **Assessed**: 2026-10-29
- **Method**: the full plugin test suite (1020 tests, Python 3.13, PostgreSQL 16, Redis) run against the NetBox v4.7.4 tag with the plugin's `testing/configuration.py`; a search of the plugin code for the APIs that 4.7.0 removed or changed; a reading of the 4.7.0 to 4.7.4 release notes and the 4.7 plugin development documentation.

## Result

The plugin runs on NetBox 4.7.4 without a code change. **1002 tests pass, 18 fail, 9 are skipped.** All 18 failures come from the tests, not from plugin behaviour, and fall into two groups.

| Group | Tests | Cause | Fix |
|-------|-------|-------|-----|
| List view query counts | 9 (`test_list_objects_with_permission` of each model) | NetBox 4.7.4 runs one query fewer on every list page: 15 against 16 (accounting dimension, contract type, ...), 16 against 17, 17 against 18 (four models), 22 against 23. The baseline file `tests/query_counts.json` was recorded on 4.6.10. | Re-record the baseline on 4.7 with `UPDATE_QUERY_COUNTS=1`, stating the reason (core change, constitution principle II). |
| REST create and update | 9 (`test_create_object`, `test_bulk_create_objects`, `test_update_object` for contract, contract line and invoice) | The test data holds Python `date`, `Decimal` and number values; NetBox 4.7's test helper compares the stored object with its JSON form (strings), so the two no longer match. The API itself answers correctly. | Write dates as ISO strings and decimals as strings in `create_data` and `update_data`. |

The failing groups hide nothing else: the remaining 1002 tests, including migration, amendment, lock, GraphQL, conventions and permission tests, pass, and the run printed no deprecation warning from the plugin.

## Required adjustments

1. **Tests**: re-record the query-count baseline and fix the REST test data, as above. The baseline is version specific, so a plugin release cannot keep one baseline for both 4.6 and 4.7 (see decision 1).
2. **CI** (`.github/workflows/lint-tests.yaml`): pin NetBox to the 4.7.4 tag (currently `v4.6.10`); keep Python 3.12, 3.13 and 3.14.
3. **Supported versions**: update `min_version` (if 4.6 is dropped), the README compatibility table (it ends at 4.6 with plugin 2.5), the changelog warning, and `docs/`.
4. **Documentation screenshots**: regenerate them with `utils/docs_screenshots/make_screenshots.sh` on 4.7 and review them, because the page chrome changed.

## Checked and found unaffected

The 4.7 breaking changes below do not touch the plugin; the search covered `netbox_contract/`, `scripts/`, `utils/` and `testing/`.

- django-tables2 3.0: no use of the removed `RelatedLinkColumn` or the `querystring` template tag; tables use standard columns.
- MPTT replaced by `ltree`: no model uses a nested group base class or tree fields.
- Search index updated in the background: search indexes are declared in the standard way; no test failed because of the delay.
- Webhook, `send_webhook`, event data keys, custom field helper changes, `registry` keys, legacy view actions, `DEFAULT_ACTION_PERMISSIONS`: not used.
- Custom field value format in REST and GraphQL: the plugin declares no selection custom field.
- Service `protocol` and `ports`, config contexts, cooling, module bays: unrelated to the plugin.
- GraphQL circuit status enum rename (4.7.4): the plugin does not use that enum.

## Not verified

- A real upgrade of an existing 4.6 installation with data, and the `convert_contract_lines` command on 4.7.
- The custom scripts in `scripts/` run from the web interface on 4.7 (core scripts are deprecated but still supported until 5.0).
- Third-party plugins used together with this one (for example the custom objects plugin that `supported_models` can reference).

## Decisions for the maintainer

**Decided 2026-10-29:** decision 1 is option A (minimum NetBox 4.7.0, 4.6 users stay on 2.5.x), and the implementation stays on the #318 branch. Decisions 2 and 3 are open.

1. **Support policy.** Option A: raise the minimum to 4.7.0 in the next minor release and use the 4.7 features of specifications 004 to 007; 4.6 users stay on 2.5.x. Option B: keep 4.6 and 4.7 together, which excludes 4.7-only features, needs a baseline per NetBox version, and doubles the CI matrix. This assessment recommends A: the four opportunities (see `../netbox-47-opportunities/evaluation.md`) all need 4.7.
2. **Release number.** A release that drops NetBox 4.6 is at least a minor version; the constitution allows a minor release for new features and reserves major for removals of the plugin's own interfaces.
3. **Where the shared 4.7 change lands.** In the first of specifications 004 to 007 to be implemented, or as its own small change first (recommended: it unblocks the tests and the CI).
