# Research: breadcrumb layouts

Read from NetBox 4.7.4 sources (`netbox/ui/layout.py`, `utilities/views.py`, `render_breadcrumbs`). No NEEDS CLARIFICATION remains.

## R1 - Mechanism
- **Decision**: pass `breadcrumbs=[Breadcrumb(...), ...]` to each detail page layout. The trail is resolved from the detail view's layout, including on tab pages, which reuse it.
- **Rationale**: this is the 4.7 replacement for overriding the `breadcrumbs` template block; it keeps the list link first and the object name last, as before.

## R2 - Contract entry
- **Decision**: accessor `external_party_object`; link built with a small URL callable: `contract_list?service_provider_id=<pk>` for a service provider, `?provider_id=<pk>` for a circuit provider; no entry when there is no external party.
- **Rationale**: today's template tests a missing attribute and renders nothing. Both filter parameters exist in `filtersets.py` (checked); the external party type decides which one applies.
- **Alternatives**: a single generic parameter (rejected: no such filter exists).

## R3 - Other entries
| Page | Entry | Target |
|------|-------|--------|
| Contract line | its contract | `contractline_list?contract_id=<pk>` |
| Invoice | its contracts (iterable accessor `contracts.all`) | `invoice_list?contracts=<pk>` |
| Invoice line | its invoice | `invoiceline_list?invoice=<pk>` |

Each parameter name is verified against the filterset before use; a test fails if a name is not accepted (the list would silently show everything).

## R4 - Removal
- **Decision**: delete the four templates and any `template_name` that points to them; confirm that no other view extends them.
- **Rationale**: dead after R1; keeping them overrides the layout trail.

## R5 - Tests
- **Decision**: new module rendering each detail page and each tab as a superuser and as a user with only view permission on the object, asserting trail text and links (including contracts of two providers, a contract without external party, an invoice with several contracts). Follow each link and assert the filtered list contains the object.
