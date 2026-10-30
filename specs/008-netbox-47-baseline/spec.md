# Feature Specification: NetBox 4.7 as the minimum supported version

**Feature Branch**: `318-assess-against-netbox-4-7-4` (specification and implementation both stay on the issue #318 branch)

**Created**: 2026-10-29

**Status**: Draft

**Input**: User description: "Issue #318: the shared 4.7 baseline change, as its own small first change: pin CI to the NetBox 4.7.4 tag, update the query-count baseline and the REST test data, and raise the minimum NetBox version to 4.7.0, so that specifications 004 to 007 can use 4.7 features."

## Clarifications

### Session 2026-10-29

- Q: Which support policy for NetBox versions? → A: Raise the minimum NetBox version to 4.7.0 in the next minor release; NetBox 4.6 users stay on plugin 2.5.x (option A of `.specify/assessments/netbox-47-compatibility/compatibility.md`). The plugin does not support 4.6 and 4.7 together.
- Q: Which branch carries the implementation? → A: The same branch as the specification, `318-assess-against-netbox-4-7-4`.
- Q: Does this change ship alone? → A: It is the first change implemented, before specifications 004 to 007, but it is not published in pieces: it is released together with them in the next minor release (constitution principle VII, a feature planned as one release is not published in pieces).

## Delivery Overview

The plugin 2.5.0 declares NetBox 4.6.0 as its minimum and is tested against NetBox 4.6.10. The compatibility assessment of NetBox 4.7.4 found that the plugin runs unchanged on 4.7.4 and that all 18 failing tests fail because of the tests themselves: nine list-view query counts are one query lower on 4.7, and nine REST tests give dates and decimals as Python objects where NetBox 4.7's test helper compares text. This change makes the suite green on 4.7.4, pins CI to that release, and declares 4.7.0 as the minimum. It adds no feature and changes no behaviour, API, setting or data.

It carries the shared prerequisite that specifications 004 to 007 each refer to.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The test suite passes on NetBox 4.7.4 in CI (Priority: P1)

A maintainer opens a pull request and CI runs the whole suite against the NetBox 4.7.4 release on Python 3.12, 3.13 and 3.14. It passes, so later features can be merged with confidence.

**Why this priority**: every other 4.7 change depends on a trustworthy test run on 4.7.

**Independent Test**: run the suite against NetBox v4.7.4 and check that no test fails or is newly skipped.

**Acceptance Scenarios**:

1. **Given** NetBox v4.7.4 and the plugin, **When** the full suite runs, **Then** 1020 existing tests plus the metadata test of T006 run, none fail and no test is skipped that ran before (9 tests are skipped today for unrelated reasons).
2. **Given** the CI configuration, **When** it is read, **Then** it checks out the NetBox tag `v4.7.4` and runs on Python 3.12, 3.13 and 3.14.
3. **Given** the REST tests for contracts, contract lines and invoices, **When** they run, **Then** they send dates and amounts the way an API client does (as text) and still check the stored objects.
4. **Given** the list-view tests, **When** the query counts of NetBox 4.7.4 differ by one from the recorded baseline, **Then** the baseline is updated once, with the reason recorded in the commit, and any later change of a count fails the test again.

---

### User Story 2 - Administrators know which NetBox version is needed (Priority: P2)

An administrator reading the README, the changelog or the plugin metadata sees that the next plugin release needs NetBox 4.7.0 or later, that 4.6 installations stay on 2.5.x, and which plugin version goes with which NetBox version.

**Why this priority**: dropping a NetBox version is a breaking decision for users; it must be stated before they upgrade.

**Independent Test**: read the README compatibility table and the top of the changelog; start NetBox 4.6 with the new version and check the plugin refuses to load with a clear message.

**Acceptance Scenarios**:

1. **Given** the README, **When** the compatibility table is read, **Then** it lists NetBox 4.7 with the new plugin version and keeps the rows for earlier NetBox versions with their plugin versions.
2. **Given** the changelog, **When** the new release section is read, **Then** it opens with a warning that NetBox 4.7.0 or later is required and that 4.6 users stay on 2.5.x.
3. **Given** the plugin metadata, **When** NetBox 4.6 loads the new version, **Then** NetBox refuses it because the minimum version is 4.7.0.
4. **Given** the contributor documentation, **When** it names the supported NetBox version or the pinned test version, **Then** it names 4.7 and v4.7.4.

---

### Edge Cases

- A test whose count differs for a reason other than the 4.7 core change: not accepted by re-recording; the cause must be found.
- A future patch release of NetBox 4.7: the pin moves in a later change, not here.
- Documentation screenshots taken on 4.6: they do not affect behaviour or the tests, so this change leaves them; they are regenerated on 4.7.4 with the generator (`utils/docs_screenshots/make_screenshots.sh`) by specifications 004, 005 and 007 for the pages each one changes, and the last of them regenerates the whole set.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The CI MUST run the suite against the NetBox tag `v4.7.4` on Python 3.12, 3.13 and 3.14, and the lint job MUST be unchanged.
- **FR-002**: The REST create, bulk create and update tests for contracts, contract lines and invoices MUST give dates and decimal amounts as text and MUST still verify the stored values.
- **FR-003**: The recorded list-view query counts MUST be updated to the NetBox 4.7.4 values, once, with the reason stated, using the project's re-record procedure (serial run, no parallel).
- **FR-004**: The full suite MUST pass on NetBox v4.7.4: no failure, and no test newly skipped.
- **FR-005**: The plugin's minimum NetBox version MUST be 4.7.0, with no maximum version.
- **FR-006**: The plugin version MUST become 2.6.0 and the README compatibility table MUST list NetBox 4.7 with plugin 2.6, keeping 4.6 with 2.4 and 2.5.
- **FR-007**: The changelog MUST open the 2.6.0 section with the NetBox 4.7.0 requirement warning, and list the CI pin under Other Changes, following the changelog rules of `CLAUDE.md`.
- **FR-008**: `CLAUDE.md`, `CONTRIBUTING.md` and the constitution's compatibility section MUST name NetBox 4.7 as the minimum and `v4.7.4` as the pinned test release, the constitution through `/speckit-constitution`.
- **FR-009**: The change MUST NOT alter plugin behaviour, models, migrations, REST or GraphQL output, settings or templates.

### Key Entities

- **Supported NetBox version**: the minimum NetBox release the plugin accepts at load time, and the pinned release the tests run against.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The suite passes on NetBox 4.7.4 with 0 failures on all three Python versions.
- **SC-002**: An administrator finds the required NetBox version for each plugin version in under one minute from the README.
- **SC-003**: 0 changes to plugin behaviour: the REST, GraphQL and page tests outside the two groups above are untouched.
- **SC-004**: Specifications 004 to 007 can start with a green baseline on the version they target.

## Assumptions

- Plugin 2.5.0 is released (tag v2.5.0), so the next minor version is 2.6.0; specification 003 had named 2.6.0 for a later REST-shrink release, which can ship in the same release or later.
- The plugin is released as one 2.6.0 with specifications 004 to 007 (constitution principle VII); this change alone is not published.
- Python 3.12 to 3.14 stay supported: NetBox 4.7.4 supports the same range.
- Regenerating the documentation screenshots on 4.7 is done by specifications 004, 005 and 007; testing an upgrade of a real installation is a separate follow-up.
