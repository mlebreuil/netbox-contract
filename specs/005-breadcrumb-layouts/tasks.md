# Tasks: Breadcrumbs declared in page layouts

**Input**: `specs/005-breadcrumb-layouts/` (plan.md, spec.md, research.md R1-R5, data-model.md, contracts/breadcrumbs.md, quickstart.md)

**Tests**: required and written first (constitution II).

**Depends on**: 008 done.

**Test command**: `cd ../netbox && NETBOX_CONFIGURATION=netbox.configuration_testing venv/bin/python netbox/manage.py test netbox_contract.tests.test_breadcrumbs netbox_contract.tests.test_detail_layouts --keepdb`

## Phase 1: Setup

- [X] T001 Read how the four detail views declare their layout today (`netbox_contract/views.py`, `netbox_contract/tests/test_detail_layouts.py`) and the four templates `contract.html`, `contractline.html`, `invoice.html`, `invoiceline.html` in `netbox_contract/templates/netbox_contract/`; list every `template_name` or `{% extends %}` that refers to them (R4). Check that the filter parameters of R2/R3 exist in `netbox_contract/filtersets.py`: `service_provider_id`, `provider_id`, `contract_id`, `contracts`, `invoice`.
- [X] T002 Create `netbox_contract/tests/test_breadcrumbs.py` with fixtures: two contracts (service provider, circuit provider), a contract without external party, a contract line, an invoice with two contracts, an invoice without contract, an invoice line, a view-only user.

## Phase 2: Foundational

- [X] T003 Add a helper in `test_breadcrumbs.py` that renders a page and returns the trail as `[(text, href), ...]`; use it in all tests below.

## Phase 3: User Story 1 - The same trail on the four pages (P1) 🎯 MVP

**Goal**: identical trails, contract entry fixed. **Independent test**: compare each page trail with the table in `contracts/breadcrumbs.md`.

### Tests first (must fail: the contract entry is empty today, tab trails are not asserted)
- [X] T004 [US1] Tests: contract page trail = list, external party name linking to `contract_list?service_provider_id=<pk>` (or `?provider_id=<pk>` for a circuit provider), contract name; contract without external party has no party entry; contract line trail links `contractline_list?contract_id=<pk>`; invoice line trail links `invoiceline_list?invoice=<pk>`; trail of unit, service provider, contract type, accounting dimension and contract assignment pages unchanged.
- [X] T005 [US1] Tests: each link opens a list that contains the object (follow the link, assert the object is in the response); entries show for a view-only user whatever their permission on the related object (FR-008).
- [X] T006 [US1] Tests: tab pages (changelog, journal, others the views define) of the four objects show the same trail.

### Implementation
- [X] T007 [US1] Declare `breadcrumbs=[Breadcrumb(...)]` in the layouts of `ContractView`, `ContractLineView`, `InvoiceView`, `InvoiceLineView` in `netbox_contract/views.py` (or the layouts module the views use): contract via accessor `external_party_object` with a URL callable choosing `service_provider_id` or `provider_id` and no entry without a party; contract line via `contract`; invoice line via `invoice` (R2, R3).
- [X] T008 [US1] Run T004-T006: green for contract, contract line, invoice line; invoice covered by US2.

## Phase 4: User Story 2 - One link per contract on invoices (P2)

**Independent test**: an invoice with two contracts shows two entries.

- [X] T009 [US2] Tests first: invoice with two contracts shows one entry per contract, each linking `invoice_list?contracts=<pk>`; invoice without contract shows none; entry order stable (by contract name).
- [X] T010 [US2] Declare the invoice breadcrumb with the iterable accessor `contracts.all` in the invoice layout (R3); confirm no extra query per contract beyond the existing prefetch; run T009.

## Phase 5: User Story 3 - Pages maintained in one place (P3)

- [X] T011 [US3] Test first: the four template files do not exist (`pathlib` check in `test_breadcrumbs.py`) and no view sets `template_name` to them.
- [X] T012 [US3] Delete `contract.html`, `contractline.html`, `invoice.html`, `invoiceline.html` from `netbox_contract/templates/netbox_contract/` and remove the `template_name` references found in T001; run the full detail-layout tests (`test_detail_layouts`) and T011.

## Phase 6: Polish

- [X] T013 [P] `CHANGELOG.md`: Bug Fixes (contract entry now names and links the external party) and Other Changes (trail declared in layouts, four templates removed).
- [X] T014 [P] (done with the full regeneration at the end of 007, on NetBox 4.7.4) Regenerate the screenshots of the four detail pages with `utils/docs_screenshots/make_screenshots.sh contract contract_line invoice invoice_line`, look at the images, keep meaningful changes.
- [X] T015 (automated checks done; the manual quickstart steps were not run in a browser) `ruff check`, `makemigrations --check --dry-run`, full suite, query counts unchanged (investigate, do not re-record, if one moves), manual steps of `quickstart.md`.
- [X] T016 Stage the files for the owner to commit; do not bypass the pre-commit hook.

## Dependencies and order

008 → T001 → T002 → T003 → US1 (T004-T006 → T007 → T008) → US2 (T009 → T010) → US3 (T011 → T012) → Polish. All three stories edit `views.py`, so they run in sequence.

## Implementation strategy

MVP = US1 plus US2 (the invoice trail is one of the four pages); US3 is the clean-up that proves the layouts are the single source. Ship with the rest of 2.6.0.
