# Tasks: Search contracts by external party name

**Input**: `specs/009-search-contracts-by-party-name/` (plan.md, spec.md, research.md 009-D1 to 009-D7, data-model.md, contracts/filters.md, quickstart.md)

**Tests**: required and written first; each must fail before the change (Constitution II).

**Test command**: `./dc test netbox_contract.tests.test_party_name` (whole suite: `./dc test`). Never run Python on the Mac.

**Checks before every commit** (skill `run-tests`): tests, `./dc ruff check` through the pre-commit hook, `python utils/spec_ids.py check`, `makemigrations --check --dry-run` (nothing pending). Commit through `./dc git commit`; never bypass the hook.

## Phase 1: Setup

- [ ] 009-T001 Read `netbox_contract/filtersets.py` (`ContractFilterSet`, its `search` and the two provider filters), `netbox_contract/forms.py` (`ContractFilterForm`, "Parties" fieldset), `netbox_contract/graphql/filters.py` (`ContractFilter`), `netbox_contract/graphql_extensions.py` (filter methods, 006-D5 pattern), `netbox_contract/tests/helpers.py` and `tests/test_graphql.py`, plus NetBox 4.7.4 `netbox/netbox/filtersets.py` (`get_additional_lookups`) and `utilities/forms/mixins.py` (`FilterModifierMixin`), to confirm 009-D2 and 009-D4 before writing code.
- [ ] 009-T002 Create `netbox_contract/tests/test_party_name.py` with a shared fixture: service provider "Acme Telecom", circuit provider "Globex Carrier", a service provider and a circuit provider with the same primary key (create rows so the IDs collide), Active contracts for each, an Active contract without a party, an Active contract whose own name contains "acme", a non-Active contract for Acme; use `tests.helpers.make_contract` and `mock.patch.dict(settings.PLUGINS_CONFIG['netbox_contract'], ...)` where a setting is needed.

## Phase 2: Foundational (blocks both user stories)

- [ ] 009-T003 Write the failing unit tests of the shared condition: `party_name_condition('icontains', ['acme'])` selects the Acme contract only, `'exact'` is case-sensitive, `'iexact'` is not, several names match any of them, a service provider and a circuit provider with the same ID are never confused (009-FR-005), a contract without a party and a contract whose provider was deleted never match, each contract appears once (009-FR-003). In `netbox_contract/tests/test_party_name.py`.
- [ ] 009-T004 Create `netbox_contract/external_party.py` with `party_name_condition(lookup, values)` returning the `Q` of 009-D1: for each of `ServiceProvider` and circuits `Provider`, `external_party_object_type` equals the model's content type AND `external_party_object_id` is in the subquery of providers whose `name` satisfies `name__<lookup>` for any of the values; the two OR-ed. Cite `009-FR-001`, `009-FR-002`, `009-FR-005` in comments. Run 009-T003.

## Phase 3: User Story 1 - Find a contract by typing its supplier's name (P1) 🎯 MVP

**Independent test**: with the 009-T002 data, search "acme" then "carrier" in the contract list.

### Tests first
- [ ] 009-T005 [009-US1] Failing tests in `netbox_contract/tests/test_party_name.py` for the quick search (`ContractFilterSet(data={'q': ...})` and the list view `?q=`): "acme" lists the Acme contract (009-US1-1), "carrier" the Globex contract (009-US1-2), a text matching both a contract's own name and another's party lists both once (009-US1-3), the non-Active Acme contract is not listed (009-US1-4), a contract without party only through its own fields (009-US1-5), upper-case text matches, an empty text leaves the list unchanged, a provider renamed is found by its new name at once, an existing quick search by name, external reference and comments returns what it returned before (009-SC-004).

### Implementation
- [ ] 009-T006 [009-US1] `netbox_contract/filtersets.py`: in `ContractFilterSet.search` OR `party_name_condition('icontains', [value])` with the three existing conditions, keeping `Q(status__iexact='Active')` ANDed (009-FR-001 to 009-FR-004, 009-D3). Run 009-T005.
- [ ] 009-T007 [009-US1] Add a test that the contract list view makes the same number of queries with 3 and with 30 contracts when a quick search is applied (009-SC-003); run the whole `netbox_contract.tests.test_views` and the query-count baseline; `tests/query_counts.json` is changed only if a count changed, and then only with the reason written in the commit (Constitution II).

**Checkpoint**: the quick search finds contracts by party name. Story 1 can ship alone.

## Phase 4: User Story 2 - Filter by party name in the list, REST API and GraphQL (P2)

**Independent test**: request the contracts filtered by "Acme Telecom" in the list view, REST and GraphQL: each returns the Acme contract only.

### Tests first
- [ ] 009-T008 [P] [009-US2] Failing filterset and view tests in `netbox_contract/tests/test_party_name.py`: `external_party_name`, `__ic`, `__ie`, `__n` on `ContractFilterSet` (009-D2); both party types (009-US2-1); same name on a service provider and a circuit provider returns both (009-US2-3); a non-Active contract is returned (009-US2-4); combination with `status`, `service_provider_id` and `contract_type` (009-FR-009); `service_provider_id` and `provider_id` give the same results as before (009-US2-5); the contract list address `?external_party_name__ic=acme` works.
- [ ] 009-T009 [P] [009-US2] Failing REST tests in `netbox_contract/tests/test_api.py` or `test_party_name.py`: `/api/plugins/contract/contracts/?external_party_name=Acme Telecom` and `?external_party_name__ic=acme` return the same contracts as the list view, a user limited by an object permission only gets the contracts the permission allows (009-FR-011), the response fields are unchanged (009-FR-010, 009-US2-2).
- [ ] 009-T010 [P] [009-US2] Failing GraphQL tests in `netbox_contract/tests/test_graphql.py` or `test_party_name.py`: `contract_list(filters: {external_party_name: {i_contains: "acme"}})` returns the REST result; `exact`, `i_exact`, `starts_with`, `in_list` where supported (009-D4); the filter also works when `ContractFilter` is nested (for example from a contract line) (009-FR-008, 009-SC-002).
- [ ] 009-T011 [P] [009-US2] Failing form test in `netbox_contract/tests/test_party_name.py`: `ContractFilterForm` has `external_party_name` in the "Parties" fieldset (so it is rendered), keeps its value when the filter is applied, and the modifier drop-down shows for it when NetBox offers one (009-D2 open point: record what is observed in `research.md` as the next free implementation decision (`python utils/spec_ids.py next 009 I`)).

### Implementation
- [ ] 009-T012 [009-US2] `netbox_contract/filtersets.py`: declare `external_party_name`, `external_party_name__ic`, `external_party_name__ie`, `external_party_name__n` as `MultiValueCharFilter`s with a method that calls `party_name_condition` (`exclude` for `__n`), labelled "External party name", next to `service_provider_id` and `provider_id` (009-FR-006, 009-FR-009, 009-D2). Run 009-T008 and 009-T009.
- [ ] 009-T013 [009-US2] `netbox_contract/forms.py`: add `external_party_name = forms.CharField(required=False, label=_('External party name'))` to `ContractFilterForm` and to its "Parties" `FieldSet` (a field left out of every section is not rendered). Run 009-T011.
- [ ] 009-T014 [009-US2] `netbox_contract/graphql/filters.py` (and `graphql_extensions.py` only if a shared helper is needed): `ContractFilter.external_party_name` as a `@strawberry_django.filter_field()` method with the lookup subset of 009-D4 applying `party_name_condition` with the `prefix`; if the lookup type cannot be used, use the fallback of 009-D4 and record it in `research.md` as the next free implementation decision. Run 009-T010.
- [ ] 009-T015 [009-US2] Run the whole suite (`./dc test`) and `./dc manage makemigrations netbox_contract --check --dry-run` (nothing pending).

**Checkpoint**: both stories work and share one condition.

## Phase 5: Polish and cross-cutting

- [ ] 009-T016 [P] Documentation: `docs/contract.md` (search and filter contracts by external party name: quick search keeps Active-only, filter modifiers) and `docs/api.md` (REST parameters, GraphQL filter with one example query). Rerun `utils/docs_screenshots/make_screenshots.sh` only if a page shown in the docs changed (the filter form is not shown there today: check `SHOTS` in `capture.py`).
- [ ] 009-T017 [P] `CHANGELOG.md`: one bullet in the Enhancements section of the Unreleased release, `* [#333](https://github.com/mlebreuil/netbox-contract/issues/333) - ...`, in the format of the latest release and the order of the `draft-changelog` skill; no per-issue sublist.
- [ ] 009-T018 [P] French translation: `makemessages -l en -l fr` from `netbox_contract/` with NetBox's `manage.py` and the test configuration, translate the new label ("External party name"), then `msgfmt` on the plugin's `.po` files (not `compilemessages`, which rebuilds NetBox's own catalogs).
- [ ] 009-T019 Update the global documents listed in the plan: `specs/_global/contracts/rest-api.md` (filters on `contracts/`), `specs/_global/contracts/graphql.md` (`ContractFilter.external_party_name`), `specs/_global/contracts/ui.md` (filter form field and quick search), `specs/_global/behaviours.md` (rule with 009-FR-001 to 009-FR-009); each statement cites its identifiers. Then `python utils/spec_ids.py registry` and check `git diff specs/_global/registry.md` shows only the 009 entries.
- [ ] 009-T020 Final checks: `./dc test` (whole suite, serially), pre-commit through the commit, `python utils/spec_ids.py check`, `makemigrations --check`, `tests/query_counts.json` unchanged or changed with a stated reason; walk through `quickstart.md`; set the spec `Status` to Implemented. Do not push or open a pull request unless the maintainer asks (AI policy); the pull request will be `Closes: #333`, based on `develop`, after `gh issue view 333 --json state,assignees`.

## Dependencies and order

- Phase 1 → Phase 2 → Phase 3 (MVP) → Phase 4 → Phase 5.
- Phase 4 depends on Phase 2 (the shared condition), not on Phase 3's code: 009-T008 to 009-T011 can be written in parallel with each other; 009-T012, 009-T013 and 009-T014 touch three different files and can be done in parallel once their tests exist, but 009-T012 should come first because the REST and view tests use it.
- 009-T016, 009-T017, 009-T018 are parallel; 009-T019 needs the final behaviour; 009-T020 is last.

## Implementation strategy

MVP is Phase 3: the quick search alone answers the use case of the issue and ships on its own. Phase 4 adds the filter to the list, REST and GraphQL on the same condition. Proposal 3 of issue #333 (global search) is not part of this feature.
