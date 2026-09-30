# Feature Specification: Align with NetBox 4.6 plugin conventions

**Feature Branch**: `308-align-with-netbox-4-6-plugin-conventions` (the spec folder is `specs/002-netbox-46-conventions`)

**Created**: 2026-09-30

**Status**: Draft

**Input**: User description: "Work on GitHub issue #308 — Align with NetBox 4.6 plugin conventions: model URLs, register_filterset, fieldsets, edit views." The issue was found while reviewing the plugin against NetBox 4.6.8. It changes no REST field, plugin setting or import column.

## Delivery Overview

This is a conformance change delivered in one patch release (the next 2.5.x version; no migration, setting, field or endpoint is added). Users see four improvements: a Journal tab on every object, lookup modifiers on every filter form, edit, bulk-edit and filter forms grouped into sections, and quick-add and partial page refreshes working on the invoice and invoice line edit screens. Everything else (URLs, REST API, settings, import columns, stored data) stays the same. The user stories are ordered by user value, which is also the suggested build order.

## Clarifications

### Session 2026-09-30

- Q: When deprecated fields are hidden (`show_deprecated_fields` off), should the contract page stop showing the deprecated invoice template section? → A: Yes; with the setting off the section is hidden and the template is not looked up; with it on, the section is shown as before. It is listed as a behaviour change in the changelog.
- Q: Should the list, add, import, bulk edit and delete pages also be registered through NetBox's model view registration, so that the URL configuration is reduced to one include per model? → A: Yes, for all nine object types; every existing route name and address is kept and covered by a test.
- Q: What should happen to `templates/contract_list_bottom.html`, which the plugin's code never uses? → A: Delete it (its last use was removed in commit 9784e95); only `contract_assignments_bottom.html` is moved; the removal is mentioned in the changelog.
- Q: Should this ship as a patch release (2.5.x) or a minor release (2.6.0)? → A: A patch release (next 2.5.x): the changes are conformance fixes with no migration and no new setting, field or endpoint.
- Q: When the add-invoice or add-invoice-line address already carries a value (for example `?date=` or `?period_start=`) and the contract or invoice would propose another, which wins? → A: The address wins, as on NetBox core forms; the contract or invoice only fills the fields the address leaves empty. For invoices this is a behaviour change (today the contract-derived values and today's date replace the address values) and is listed in the changelog.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Journal and extra tabs on every plugin object (Priority: P1)

A contract manager opens an invoice line, an accounting dimension, a contract type or a contract assignment and wants to record a journal entry on it, as they already can on contracts, invoices, units, contract lines and service providers. Today these four object pages show no Journal tab, although NetBox provides journaling for every object.

**Why this priority**: it is the only item of the issue that restores a missing feature; users currently cannot journal four of the nine object types.

**Independent Test**: open the detail page of one object of each of the four types and check that a Journal tab is shown, that a journal entry can be added from it, and that the Changelog tab still works.

**Acceptance Scenarios**:

1. **Given** an invoice line, an accounting dimension, a contract type and a contract assignment, **When** a user with view permission opens each detail page, **Then** each page shows a Journal tab and a Changelog tab.
2. **Given** the Journal tab of one of these objects, **When** a user with the permission to add journal entries adds an entry, **Then** the entry is saved and listed on that tab.
3. **Given** any page, link, bookmark or API client that uses an existing plugin page address (list, add, import, bulk edit, bulk delete, detail, edit, delete, changelog), **When** it is opened after the upgrade, **Then** it reaches the same page as before.
4. **Given** the contract, invoice, unit, contract line and service provider detail pages, **When** they are opened after the upgrade, **Then** they show the same tabs and actions as before (including Amend on contract lines and the Contracts tab on assignable NetBox objects).

---

### User Story 2 - Lookup modifiers on the plugin's filter forms (Priority: P2)

A user filtering the contract, invoice or invoice line list wants the lookup modifiers that NetBox 4.5+ offers on its own filter forms (for example "contains", "starts with", "not equal", "empty"), for example to find every contract whose external reference contains a word.

**Why this priority**: it brings the plugin's lists to the same filtering power as NetBox core lists; it is not a missing feature but a visible gap with core.

**Independent Test**: open the filter tab of the contract list and check that text fields offer a modifier choice, then filter with "contains" and check the result.

**Acceptance Scenarios**:

1. **Given** the filter form of any of the nine plugin object lists, **When** it is displayed, **Then** fields that NetBox supports modifiers for (text, number, date and choice fields) offer the modifier selector as on core lists.
2. **Given** contracts with external references "ALPHA-FIBER-01" and "BETA-POWER-02", **When** the contract list is filtered on external reference "contains FIBER" from the filter form, **Then** only the first contract is listed.
3. **Given** a filtered list address saved before the upgrade, **When** it is opened after the upgrade, **Then** it returns the same results.

---

### User Story 3 - Forms grouped into sections (Priority: P2)

A user creating or editing a contract, an invoice or any other plugin object sees the fields grouped into titled sections (for example for a contract: contract, parties, dates and terms, billing, tenancy, tags), as on NetBox core forms, instead of one long flat list. Filter forms start with the search, saved filter and tag fields, as in core. The contract type's description, a one-line text, is a plain text field instead of a Markdown editor in the filter, bulk-edit and import forms.

**Why this priority**: it improves usability of long forms (contracts and invoices have many fields) but changes no behaviour.

**Independent Test**: open the contract add form and check that fields appear under section titles and that a contract can still be created with the same fields as before.

**Acceptance Scenarios**:

1. **Given** the add, edit, bulk-edit or filter form of any plugin object, **When** it is displayed, **Then** its fields are grouped under titled sections and every field present before the change is still present.
2. **Given** a plugin setting that hides contract fields (`hidden_contract_fields`), **When** the contract form is displayed, **Then** the hidden fields are still not shown and no empty section is shown in their place.
3. **Given** the deprecated fields setting (`show_deprecated_fields`) off, **When** the contract or invoice form is displayed, **Then** the deprecated fields are still hidden; **Given** it on, **Then** they are shown in a section of their own.
4. **Given** the contract type filter, bulk-edit and import forms, **When** they are displayed, **Then** the description is a single-line text field.
5. **Given** a form submitted with the same values as before the change, **When** it is saved, **Then** the stored object is identical.

---

### User Story 4 - Quick add and partial refresh on invoice and invoice line forms (Priority: P3)

A user filling a form that offers a quick-add button for an invoice or an invoice line (NetBox's "+" next to a selection field), or a screen that refreshes an edit form without a full page load, gets the same form as on every other object. Today the invoice and invoice line edit screens ignore these requests and return the full page. The pre-fill of a new invoice from its contract (date, period, currency, proposed amount, preview of lines) and of a new invoice line from its invoice (quantity, unit price, currency) keeps working, still only from a contract or invoice the user is allowed to view.

**Why this priority**: it fixes an inconsistency with NetBox core and removes duplicated code that would drift on each NetBox release, but few users hit it today.

**Independent Test**: open the invoice add form from a contract and check the pre-filled values; then request the invoice add form as a quick-add and as a partial refresh and check that the short form is returned.

**Acceptance Scenarios**:

1. **Given** a contract the user may view, with a previous invoice ending on 31 March and a monthly invoicing frequency, **When** the user opens "add invoice" from the contract, **Then** the form proposes today's date, a period from 1 April to 30 April, the contract currency, the amount from the contract lines and the preview of the lines, as before.
2. **Given** a contract the user may not view, **When** its identifier is passed to the invoice add form, **Then** nothing is pre-filled from it (as fixed in #307).
3. **Given** an invoice the user may view, **When** the user opens "add invoice line" from it, **Then** the form proposes a quantity of 1, the invoice currency and the rest of the invoice amount as unit price, as before; **Given** an invoice the user may not view, **Then** nothing is pre-filled from it.
4. **Given** a quick-add request for an invoice or an invoice line, **When** the add form is requested, **Then** the short quick-add form is returned instead of the full page.
5. **Given** a partial-refresh request for the invoice or invoice line edit form, **When** it is requested, **Then** only the form is returned.
6. **Given** an existing invoice or invoice line, **When** its edit form is opened, **Then** its stored values are shown and nothing is pre-filled over them.

---

### User Story 5 - Deprecated invoice templates hidden on contracts when deprecated fields are off (Priority: P3)

A user viewing a contract with the deprecated fields setting off does not see the deprecated invoice template section, and the page does not look it up. With the setting on, the invoice template section is shown as before.

**Why this priority**: small consistency and performance fix, in line with the rule that deprecated data is hidden unless the setting is on.

**Independent Test**: view a contract that has an invoice template with the setting off and on.

**Acceptance Scenarios**:

1. **Given** a contract with an invoice template and `show_deprecated_fields` off, **When** the contract page is displayed, **Then** no invoice template section is shown and the template is not looked up.
2. **Given** the same contract and `show_deprecated_fields` on, **When** the contract page is displayed, **Then** the invoice template section is shown as before.

---

### Edge Cases

- A page address of a plugin object with a trailing path that only existed through a hand-written route (for example `/<type>/<id>/changelog/`) keeps working and keeps its route name.
- An object type that other plugins or custom code extend with `register_model_view` (extra tab or action) works for the four object types that could not be extended before.
- The contract assignments shown at the bottom of an assignable NetBox object page (inline display) still render after their template moves; a template with the same name in another plugin does not replace them.
- A filter form field that the plugin defines itself (for example a choice of contract or a date) still filters as before when no modifier is chosen.
- The invoice add form opened with an identifier that is not a number, or of a contract that does not exist, opens empty without error, as before.
- The invoice add form opened from a contract with `?date=2026-01-15` in the address keeps 15 January 2026 as the invoice date and fills the other fields from the contract.
- The invoice add form opened with a contract whose lines cannot be proposed (invoicing error) still shows the error message and the rest of the pre-fill.
- Query-count baselines of list views change only if a list view's queries change; any re-recording states the reason.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The detail page of every plugin object type (contract, contract line, contract type, contract assignment, invoice, invoice line, unit, accounting dimension, service provider) MUST show the Journal and Changelog tabs.
- **FR-002**: Every plugin object type MUST accept extra tabs and actions registered for it by NetBox's model view registration, as contracts, invoices, units, contract lines and service providers already do.
- **FR-003**: Every existing plugin page address and route name MUST keep working and reach the same page. All pages of the nine object types (list, add, import, bulk edit, bulk delete, detail, edit, delete, changelog, journal and extra actions) MUST be registered through NetBox's model view registration, with the URL configuration reduced to one include per object type plus the plugin's non-model pages (for example the invoice lines preview); a test MUST resolve every route name that existed before the change.
- **FR-004**: The filter forms of all plugin object lists MUST offer the lookup modifiers NetBox offers on core filter forms for the same kinds of fields.
- **FR-005**: Filter addresses (query strings) valid before the change MUST return the same results after it.
- **FR-006**: The add/edit, bulk-edit and filter forms of every plugin object type MUST group their fields into titled sections; filter forms MUST start with a section holding the search, saved filter and tag fields.
- **FR-007**: No form field MAY be added, removed or renamed by the grouping; fields hidden by `hidden_contract_fields` or `show_deprecated_fields` MUST stay hidden under the same conditions.
- **FR-008**: The contract type description MUST be a single-line text field in the filter, bulk-edit and import forms.
- **FR-009**: The invoice and invoice line add/edit screens MUST answer quick-add and partial-refresh requests like other NetBox edit screens.
- **FR-010**: The pre-fill of a new invoice from a contract and of a new invoice line from an invoice MUST propose the same values as before for the fields the page address leaves empty; a value given in the address MUST be kept. Values are only taken from a contract or invoice the user may view, and an existing invoice or invoice line opened for editing MUST NOT be pre-filled.
- **FR-011**: The contract assignment template used on other NetBox objects' pages MUST live in the plugin's own template folder so that another plugin cannot replace it by accident. The unused `contract_list_bottom.html` template MUST be deleted, with its translation entries, and no plugin template MAY remain at the root of the template folder.
- **FR-012**: The contract page MUST NOT look up or show the deprecated invoice template when `show_deprecated_fields` is off, and MUST show it as before when it is on.
- **FR-013**: No REST field, endpoint, plugin setting, import column or stored data MAY change (Constitution IV and V).
- **FR-014**: Every acceptance scenario above MUST be covered by an automated test that fails before the change where the behaviour changes (Constitution II).
- **FR-015**: `CHANGELOG.md` MUST have a "Changed" entry for these changes, with a "Behaviour changes" note for the invoice template section hidden when deprecated fields are off a mention of the removed unused `contract_list_bottom.html` template, and the invoice pre-fill keeping values given in the page address; `docs/` MUST be updated where form descriptions or screenshots change (Constitution VII).

### Key Entities

No entity is added or changed. The change touches how the nine existing plugin object types (contract, contract line, contract type, contract assignment, invoice, invoice line, unit, accounting dimension, service provider) are presented: page addresses and tabs, filter forms, edit forms.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 9 out of 9 plugin object types show a Journal tab on their detail page (today 5 out of 9).
- **SC-002**: 9 out of 9 plugin filter forms offer lookup modifiers (today 0 out of 9).
- **SC-003**: 100% of the plugin page addresses and route names used before the change still resolve to the same page.
- **SC-004**: 100% of the plugin's add/edit, bulk-edit and filter forms show their fields in titled sections, with the same set of fields as before.
- **SC-005**: The existing automated test suite passes unchanged apart from tests added for this feature; query-count baselines change only with a stated reason.
- **SC-006**: A user can add an invoice or an invoice line through a quick-add button, as for any other NetBox object.

## Assumptions

- The minimum NetBox version stays 4.6; every NetBox facility used (model view registration, filterset registration, form sections, quick add) exists in 4.6.
- Section names and field grouping follow NetBox core forms for similar objects (for example circuits and providers); the exact grouping is a design decision recorded in the plan and not a user requirement.
- Translations (`locale/`) are updated for moved templates and new section titles as part of the normal message extraction.
