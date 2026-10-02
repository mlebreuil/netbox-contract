# Feature Specification: Adopt NetBox 4.6 plugin features

**Feature Branch**: `309-adopt-netbox-4-6-plugin-features` (the spec folder is `specs/003-netbox-46-plugin-features`)

**Created**: 2026-10-01

**Status**: Draft

**Input**: User description: "Work on GitHub issue #309 — Adopt NetBox 4.6 plugin features: declarative detail layouts, amend permission action, nested serializers." The issue was found while reviewing the plugin against NetBox 4.6.8. It also lists two optional items: a GraphQL API and the NetBox base classes for contract types and service providers. The maintainer put both in scope (Q3 below). The issue replaces the minimal Amend button fix of #307.

## Delivery Overview

This feature ships in 2.5.0, which is not released yet (the latest release is 2.4.7), as a #309 entry. It adds migrations: one for the amend permission and others for the contract type and service provider base classes. That fits the 2.5.0 minor release. Users see:

- detail pages built from NetBox's standard panels;
- an "amend" permission action;
- a smaller nested representation of related objects in the REST API;
- a GraphQL API;
- a slug, comments and owner on contract types, and a description and owner on service providers.

The user stories are ordered by user value, which is also the suggested build order.

## Clarifications

### Session 2026-10-01

- Q: Amending is new in 2.5.0, which is not released. How should the new "amend" permission action be introduced? → A: Amending requires only the new "amend" action on the contract line, from 2.5.0 on. The issue proposed a one-release period in which add + change would also be accepted, but that period is not needed because no released version had Amend. A migration declares the permission. The changelog and `docs/` describe it.
- Q: The nested contract (the `contract` of assignments and contract lines, and a contract's `parent`) has been a public REST representation since 2.4. How far should the API change go in this release? → A: Shrink it now, in 2.5.0. Nested related objects use each model's brief representation. The removed fields are listed under "Behaviour changes" in the changelog. This removes REST fields without first deprecating them for a release. That conflicts with Constitution IV and V, and the maintainer accepts it. The plan MUST record it in Complexity Tracking.
- Q: Which optional items of the issue are in scope? → A: Both. A GraphQL API for all nine object types (the API tests then use NetBox's complete API test case), and the NetBox base classes for contract types (organizational) and service providers (primary).

### Session 2026-10-02

- Q: Should an invoice's `contracts` in the REST API also shrink to the brief contract form, or keep returning full contracts? → A: Shrink them to the brief contract (id, url, display, name, status), like every other nested contract. The fields removed from invoice contracts are listed under "Behaviour changes", and a full contract is still available from `contracts/{id}/`.
- Q: Should the related-object tables on detail pages become the list page's tables (columns chosen by each user), or keep the fixed tables each page shows today? → A: Use the list page's configurable tables, filtered to the object, everywhere. The contract line actions are decided per line: Amend when that line can be amended and the user may amend it, and no Delete when the line is locked. This replaces the separate table for the lines of invoiced contracts. Only the deprecated invoice template lines keep a fixed table.
- Q: What should the upgrade do with a contract type description longer than 200 characters, NetBox's standard description length? → A: Keep the first 200 characters as the description, cut at a word boundary and ending with "…". Put the full original text at the top of the new comments field, and report each type changed. A description of 200 characters or fewer is unchanged.
- Q: Should the GraphQL API include the computed amounts (a contract's total, yearly and yearly billable values; a line's total and yearly values), or only stored fields? → A: Stored fields and relations only. The computed values stay in the REST API, and the GraphQL documentation says so.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Amend permission action (Priority: P1)

An administrator wants to let a finance user change the price or quantity of invoiced contract lines from a date (Amend) without letting them create or edit contract lines freely. Today Amend needs both the "add" and the "change" contract line permissions, so it cannot be granted on its own and cannot be limited to some lines. With this change, the administrator ticks an **amend** action on a NetBox object permission for contract lines, optionally with constraints (for example only the lines of one tenant's contracts). The **Amend** button appears in the same places as before: on the line page, in the contract line tables and in the locked-line message of the edit page. It is shown only to users allowed to amend that line.

**Why this priority**: it fixes a permission design that grants too much and changes who can amend. Of the issue's items, this one has the most security weight.

**Independent Test**: give a user the view permission plus the amend action on contract lines, without add or change, then amend an invoiced recurring line from the page and through the REST API.

**Acceptance Scenarios**:

1. **Given** the object permission form with the contract line object type selected, **When** it is displayed, **Then** an "amend" action is offered with a description.
2. **Given** a user with view and amend on contract lines (no add, no change) and an invoiced recurring line, **When** they open the line, **Then** the Amend button is shown, the amend screen opens, and saving it ends the line and creates its successor.
3. **Given** the same user, **When** they call the REST amend action on that line, **Then** the amendment is made (201).
4. **Given** a user with add and change on contract lines but without amend, **When** they open an invoiced recurring line, **Then** no Amend button is shown (page, tables, edit page), the amend screen answers "forbidden", and the REST amend action answers 403.
5. **Given** an amend permission constrained to the lines of one contract, **When** the user opens a line of another contract, **Then** no Amend button is shown, and the amend screen and REST action are refused for that line.
6. **Given** a line that cannot be amended (one-time unit, not invoiced, already replaced), **When** a user allowed to amend opens it, **Then** no Amend button is shown, as before.
7. **Given** a superuser, **When** they open an amendable line, **Then** the Amend button is shown.

---

### User Story 2 - Detail pages built from NetBox's standard panels (Priority: P2)

A user opening a contract, invoice, contract line, invoice line, unit, service provider, contract type, accounting dimension or contract assignment sees the same information as today. It is laid out with NetBox's standard panels: attributes, related object tables with their "Add" buttons, comments, tags, custom fields, and content added by other plugins. The pages look and behave like core NetBox pages. Related object tables are the list page's tables, filtered to the object, so each user can choose their columns as on core pages (as asked in #294). Other plugins can add content in all three plugin content areas (left, right, full width), where today only the right one is offered.

**Why this priority**: it removes about 700 lines of hand-written page templates that drift with each NetBox release, and it gives users core behaviour. It changes no data and no permission.

**Independent Test**: open the detail page of one object of each type and check that each attribute, related table, "Add" button and message shown before is still shown under the same conditions.

**Acceptance Scenarios**:

1. **Given** any plugin object, **When** its detail page is displayed, **Then** every attribute shown before is shown with the same value. Linked objects (contract type, external party, parent, unit, contract, invoice, accounting dimensions, assigned object, replaced and replacing lines) are still links.
2. **Given** `hidden_contract_fields` lists `tenant` and `notice_period`, **When** a contract page is displayed, **Then** these two attributes are not shown. **Given** `hidden_invoice_fields` lists a field, **Then** the invoice page does not show it either.
3. **Given** `show_deprecated_fields` off, **When** a contract or invoice page is displayed, **Then** `mrc`, `yrc`, `nrc`, the calculated recurring value and the invoice template section are not shown, and the template is not looked up. **Given** it on, **Then** they are shown with the "deprecated" badge, as before.
4. **Given** a contract, **When** its page is displayed, **Then** it shows the billable flag and the total, yearly and yearly billable values, computed as before in a fixed number of queries. A total that is not available shows "Not available".
5. **Given** a contract with invoices, **When** its page is displayed, **Then** the locked-lines message is shown and the "Add a contract line" button is not. **Given** a contract without invoices and a user allowed to add contract lines, **Then** the button is shown and opens the add form pre-filled with the contract.
6. **Given** a contract, **When** its page is displayed, **Then** its contract lines, assignments, child contracts and invoices (excluding templates) are listed in the list page's tables, filtered to the contract, with the columns the user chose for those lists. The "Add an invoice" button is shown to users allowed to add invoices. A related table whose objects the user may not view is not shown.
7. **Given** an invoice, an accounting dimension's lines, a unit, a service provider and a contract line, **When** their pages are displayed, **Then** they list respectively the invoice's contracts and lines, the unit's contract lines, the provider's contracts, and the contract line's lock message and replacement links, as before.
8. **Given** an invoiced contract with an amendable recurring line and a one-time line, **When** a user allowed to amend and delete contract lines views the contract's line table or the contract line list, **Then** the recurring line offers Edit and Amend, the one-time line offers Edit only, and neither offers Delete. **Given** a contract without invoices, **Then** its lines offer Edit and Delete.
9. **Given** another plugin that adds content to the left, right or full-width area of plugin object pages, **When** a plugin object page is displayed, **Then** the content is shown in that area.

---

### User Story 3 - Smaller nested objects in the REST API (Priority: P2)

An integration reading contract assignments or contract lines gets each related contract as a short reference (id, address, display name, name and status), as NetBox core does for related objects. Today it gets almost the whole contract, including the deprecated `mrc`, `yrc` and `nrc`. Responses are smaller and no longer expose deprecated amounts in every nested contract. Writing a related object (by id or by attributes) works as before.

**Why this priority**: it aligns the API with core and stops spreading deprecated fields. It is a breaking change for clients that read the removed nested fields, which the changelog announces.

**Independent Test**: read a contract assignment, a contract line, a contract with a parent, an invoice and an invoice line through the REST API, and compare their nested objects with the brief representation of the related model.

**Acceptance Scenarios**:

1. **Given** a contract assignment, **When** it is read through the REST API, **Then** its `contract` holds only the brief contract fields (id, url, display, name, status).
2. **Given** a contract line and a contract with a parent, **When** they are read, **Then** `contract` and `parent` hold the brief contract fields. The line's `replaces` holds the brief contract line fields, and the line's `accounting_dimensions` the brief accounting dimension fields.
3. **Given** an invoice and an invoice line, **When** they are read, **Then** the invoice's `contracts` hold brief contracts, and the line's `invoice` holds the brief invoice fields (id, url, display, number).
4. **Given** a request that sets a related object by id or by a dictionary of attributes (for example `"contract": 12` or `"contract": {"name": "C-1"}`), **When** it is sent, **Then** it is accepted as before.
5. **Given** a list request with `brief=true` on any endpoint, **When** it is sent, **Then** each object holds exactly that model's brief fields, and every brief field exists on the model.
6. **Given** the OpenAPI schema, **When** it is generated, **Then** nested objects are documented as the brief representation of their model, and `external_party_object` and `content_object` remain documented as objects.

---

### User Story 4 - GraphQL API (Priority: P3)

An integration or a user of NetBox's GraphQL explorer queries contracts, contract lines, invoices, invoice lines, units, accounting dimensions, service providers, contract types and contract assignments, with filters and their relations, as for core objects. Today the plugin is absent from GraphQL.

**Why this priority**: it completes the standard NetBox feature set (Constitution I), but no current workflow depends on it.

**Independent Test**: query each object type by id and as a filtered list in the GraphQL explorer, as a user with view permission and as one without.

**Acceptance Scenarios**:

1. **Given** a user with view permission on contracts, **When** they query a contract by id or the contract list with a filter (for example status), **Then** the matching contracts are returned with their stored fields and relations (contract type, lines, invoices, assignments, parent and children), without the computed values.
2. **Given** each of the nine object types, **When** it is queried as a single object and as a list, **Then** it is returned with its fields.
3. **Given** a user without view permission on invoices, **When** they query invoices, **Then** no invoice is returned, as for core objects. Object permission constraints restrict results in the same way.
4. **Given** a contract with an external party (service provider or circuit provider) or a contract assignment on a device, **When** it is queried, **Then** the external party or assigned object is returned as a related object.
5. **Given** the deprecated fields (`mrc`, `yrc`, `nrc`, invoice `template`), **When** the schema is read, **Then** they are present and marked deprecated, as in the REST API.

---

### User Story 5 - Contract types and service providers as standard NetBox objects (Priority: P3)

An administrator manages contract types like other NetBox categories (with a slug, comments and an owner) and service providers like other primary objects (with a description and an owner). Contract types can then be filtered and referenced by slug, and both types get the owner field that NetBox 4.5 added to core objects.

**Why this priority**: it is consistency with core plus two small additions (slug and owner). It changes stored data, so it comes after the presentation and API work.

**Independent Test**: upgrade a database with existing contract types and service providers, then check their slugs, descriptions, comments and owner on the pages, in the forms, in the import and through the API.

**Acceptance Scenarios**:

1. **Given** existing contract types "Maintenance" and "Support & Licences", **When** the migration runs, **Then** each gets a unique slug derived from its name (for example `maintenance`, `support-licences`). No other value changes.
2. **Given** two contract types whose names give the same slug, **When** the migration runs, **Then** each still gets a unique slug, and the migration reports the derived slugs it had to make unique.
3. **Given** a contract type whose description is 350 characters long, **When** the migration runs, **Then** its description becomes its first 200 characters or fewer, cut at a word boundary and ending with "…". Its comments start with the full original text, and the migration reports the type. **Given** a description of 200 characters or fewer, **Then** it is unchanged and not reported.
4. **Given** an API client that creates a contract type with only `name` (as before), **When** it is sent, **Then** it is accepted and the slug is derived from the name. A client may also give a slug.
5. **Given** a service provider, **When** it is edited, **Then** a description and an owner can be set. Its existing name, slug, portal URL, comments and contacts are unchanged.
6. **Given** a contract type or a service provider, **When** an owner is set, **Then** it is shown on the page, editable in bulk, importable, filterable and exposed in the REST and GraphQL APIs, as on core objects.
7. **Given** the migration has run, **When** it is run again (or the database is migrated back and forward), **Then** no data is duplicated or lost.

---

### Edge Cases

- A contract whose external party or parent was deleted, or that has no contract type, shows an empty value instead of an error.
- A contract line page opened by a user without permission to view its contract still shows the line. The contract link follows NetBox's usual rule for objects the user cannot view.
- A user with the amend action but no view permission on contract lines cannot open the line page and is refused the amend screen.
- The Amend button in a contract line table is evaluated per line. A table mixing amendable and non-amendable lines shows it only on the amendable ones.
- A related table on a detail page shows the same objects as today: contract invoices exclude invoice templates, a provider's contracts are those whose external party is that provider, and a unit's lines are its contract lines.
- The contract line actions are decided per line, not per page, so a table mixing locked and unlocked lines (for example the contract line list across contracts) offers Delete only on the unlocked ones.
- A user who hid columns on a list page sees the same choice in that list's table on detail pages. Columns that identify the object of the page (for example the contract on a contract's lines) are left out there.
- The plugin's other templates are kept as templates: the invoice edit page with its live preview of generated lines, the amend screen and the contract line edit page.
- `brief=true` on invoice lines returns a valid representation. Today it lists a `name` field, which must exist or be removed.
- A nested write that gives a dictionary which matches no object, or several objects, is refused with a validation error, as before.
- A GraphQL query that asks for a computed value (for example `yearly_contract_value`) is refused as an unknown field, because computed values are not part of the GraphQL types.
- A contract type description longer than 200 characters with no space in its first 200 characters is cut at 199 characters followed by "…". Running the migration again does not move the text into the comments a second time.
- A contract type name that slugifies to an empty string (for example only symbols) still gets a unique slug.
- A NetBox installation without any owner defined shows an empty owner, and the forms do not require one.
- Query-count baselines of list views change only where a list view's queries change, for example from the owner column. Any re-recording states the reason.

## Requirements *(mandatory)*

### Functional Requirements

**Amend permission**

- **FR-001**: Contract lines MUST declare an "amend" permission action with a description. It MUST be selectable in NetBox object permissions and stored by a migration.
- **FR-002**: The amend screen and the REST amend action MUST require the view and amend actions on the contract line being amended, object-level constraints included. They MUST NOT require or accept add + change instead.
- **FR-003**: The Amend button MUST be offered on the contract line page actions, in the contract line tables, and in the locked-line message of the contract line edit page. It MUST be shown only when the line can be amended and the user may amend that line.

**Detail pages**

- **FR-004**: The detail pages of all nine object types MUST be built from NetBox's declarative page layout. They MUST show every attribute, related object table, "Add" button and message they showed before, under the same conditions and permissions.
- **FR-004a**: Related object tables on detail pages MUST be the list page's tables of the related type, filtered to the object, with the user's column choices. Only the deprecated invoice template lines MAY use a fixed table. Contract line table actions MUST be decided per line: Amend as in FR-003, and no Delete on a locked line. The separate table for the lines of invoiced contracts MUST be removed.
- **FR-005**: Attributes hidden by `hidden_contract_fields` or `hidden_invoice_fields` MUST stay hidden. Deprecated fields and the invoice template section MUST be shown only when `show_deprecated_fields` is on, and the template MUST NOT be looked up otherwise.
- **FR-006**: Contract values on the contract page MUST come from the shared contract value computation, in a fixed number of queries.
- **FR-007**: Detail pages MUST offer the left, right and full-width plugin content areas.
- **FR-008**: The invoice edit page (with its line preview), the amend screen and the contract line edit page MUST keep working as they do today. These pages are not detail pages.

**REST API**

- **FR-009**: Every nested related object in the REST API (contract, parent, invoice, invoice contracts, contract line `replaces`, accounting dimensions, unit, contract type) MUST use the brief representation of its model. The plugin's hand-written nested serializers MUST be removed.
- **FR-010**: Every model's brief representation MUST be declared explicitly and contain only existing fields. The brief contract MUST be id, url, display, name and status. The brief invoice MUST be id, url, display and number. The brief accounting dimension MUST be id, url, display, name and value.
- **FR-011**: Writing a related object by id or by a dictionary of attributes MUST keep working on every writable related field.
- **FR-012**: The OpenAPI schema MUST describe nested objects as the brief representation of their model. It MUST keep describing `external_party_object` and `content_object` as objects.

**GraphQL**

- **FR-013**: The plugin MUST expose its nine object types in NetBox's GraphQL API. It MUST provide a single-object query and a list query with filters, and each type's relations to plugin and NetBox objects.
- **FR-014**: GraphQL results MUST respect view permissions and object permission constraints, as for core objects.
- **FR-015**: Deprecated fields MUST be present in GraphQL and marked deprecated.
- **FR-015a**: GraphQL types MUST expose stored fields and relations only. The computed values (contract total, yearly and yearly billable values; contract line total and yearly values) MUST NOT be exposed. `docs/` MUST say that they are available in the REST API.

**Base classes**

- **FR-016**: Contract types MUST become NetBox organizational objects, with a unique name, a unique slug, a description, comments and an owner. Service providers MUST become NetBox primary objects, which gives them a description and an owner. Their existing fields and relations are kept.
- **FR-017**: The migration MUST give every existing contract type a unique slug derived from its name. A description longer than 200 characters MUST be shortened to at most 200 characters, cut at a word boundary and ending with "…", with the full original text placed at the top of the comments, so that no text is lost. It MUST report every slug it had to make unique and every description it had to move. It MUST be re-runnable without duplicating or losing data (Constitution IV).
- **FR-018**: Creating a contract type through the REST API, the import or the form MUST NOT require a slug. When the slug is missing, it MUST be derived from the name (Constitution V: no new required input).
- **FR-019**: The new fields (contract type slug and comments; service provider description; owner on both) MUST be available in the forms, bulk edit, import, filters, tables, REST API and GraphQL, as on core objects.

**Cross-cutting**

- **FR-020**: Every acceptance scenario above MUST be covered by an automated test that fails before the change where the behaviour changes. The REST API tests MUST also cover GraphQL through NetBox's complete API test case (Constitution II).
- **FR-021**: `CHANGELOG.md` MUST have a #309 entry under 2.5.0, with a "Behaviour changes" list covering:
  - the amend permission action (which replaces add + change);
  - the smaller nested objects in the REST API, with every removed field, including the full contracts that invoices returned until now;
  - the contract type slug, comments and owner, and the service provider description and owner;
  - the new GraphQL API.

  `docs/` MUST document the amend action, the nested and brief representations, GraphQL and the new fields. `README.md` MUST be updated if requirements change (Constitution VII).
- **FR-022**: No plugin setting or import column MAY be removed or renamed. Existing page addresses and route names MUST keep working.

### Key Entities

- **Contract type**: a category of contract. It gains a slug (unique, derived from the name when not given), comments and an owner. Its description follows NetBox's standard length.
- **Service provider**: an external party of contracts. It gains a description and an owner.
- **Amend permission action**: a named action on contract lines in NetBox object permissions. It allows ending an invoiced line and creating its successor.
- **Brief representation**: the short form of an object (identity, address, display name and a few identifying fields), used for related objects in the REST API and for `brief=true` lists.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: An administrator can grant amending alone. A user with view + amend and no other contract line permission can amend, and a user with add + change but without amend cannot (0 of the add + change-only users can amend).
- **SC-002**: 9 out of 9 detail pages show the same attributes, tables, buttons and messages as before the change. No detail page template holds attribute or table markup any more: seven are removed and two keep only their breadcrumbs. The edit and amend screens are unchanged.
- **SC-003**: A nested contract in a contract assignment or contract line response holds 5 fields instead of 24.
- **SC-004**: 9 out of 9 object types can be queried through GraphQL (today 0 out of 9), with permissions applied.
- **SC-005**: After the upgrade, 100% of existing contract types have a unique slug, and 0 characters of existing contract type descriptions are lost.
- **SC-006**: The existing test suite passes, apart from tests that check the changed behaviour (amend permission, nested REST output). Those tests are adapted, and each adaptation is listed in the tasks. Query-count baselines change only with a stated reason.

## Assumptions

- The minimum NetBox version stays 4.6.0. The declarative layouts, object actions, custom permission actions, GraphQL support and owner field all exist in NetBox 4.6.0.
- The owner field is NetBox's owner (users and groups), which comes with the base classes. It is not a new plugin concept.
- Units and accounting dimensions keep their current base class. The issue does not ask for a change, and neither has a natural slug.
- The exact panel arrangement of each detail page (which column, panel titles) is decided in the plan. Users must still see the same information.
- Translations are refreshed with `makemessages` and the new French entries are translated, as for #308.
