# Evaluation: NetBox 4.7 opportunities for the contract plugin (issue #318)

- **Slug**: netbox-47-opportunities
- **Evaluated**: 2026-10-29
- **Compared against**: NetBox v4.7.4 source (plugin development docs and code), the plugin on `develop` (2.5.0, `min_version` 4.6.0)
- **Scope**: the first four opportunities found while assessing issue #318. Compatibility fixes are tracked in the #318 assessment, not here.
- **Verdicts**: all four are **go**, in the order of the table below. Each becomes one specification.

## Cross-cutting finding: all four need NetBox 4.7 as the minimum

Every API below exists only in NetBox 4.7 (`Breadcrumb`, `GenericObjectChoiceField` and `GenericObjectFormMixin`, GraphQL type and filter extensions, `Choice` with descriptions). Using any of them raises the plugin's minimum from 4.6.0 to 4.7.0. The constitution says the minimum changes only through a specification, and that 4.7 compatibility is separate work. Each of the four specifications therefore states the dependency. The first one implemented carries the shared change (`min_version`, CI pinned to a 4.7 tag, README compatibility table, changelog warning). A plugin release containing them is a new minor version that drops NetBox 4.6.

## Scorecard

| # | Opportunity | Value | Effort | Risk | Verdict | Spec |
|---|-------------|-------|--------|------|---------|------|
| 1 | Pick the assigned object and the external party with the standard generic-object selector | High: replaces typing a numeric object ID and an unsearchable full list | Medium | Medium: pre-fill links, bulk edit and import must keep working | Go, first | 004 |
| 2 | Declare detail-page breadcrumbs in the layouts and drop four templates | Medium: less code, consistent trail, fixes a multi-link crumb | Small | Low | Go | 005 |
| 3 | Add contracts to the core GraphQL types and filters (device, site, rack, ...) | Medium: one query from an object to its contracts | Medium | Medium: permissions, query counts, configurable model list | Go | 006 |
| 4 | Describe the status and billing choices | Low to medium: explains what Posted and Draft mean where users choose | Small | Low | Go, last | 007 |

## 1. Generic-object selector (spec 004)

**Today.** The contract assignment form shows an object type drop-down and a raw numeric `object_id` field; the Add button on an object's Contracts tab pre-fills both from the address. The contract form builds the external party by hand: an HTMX-driven type drop-down plus a plain choice field filled with every provider or service provider, with custom code in the form's `__init__` and in the edit view that copies the chosen ID and type back.

**NetBox 4.7.** `GenericObjectChoiceField` renders one field made of an object type selector and a search-as-you-type object selector, and `GenericObjectFormMixin` fills it from the instance and assigns the result back to the generic relation. NetBox's own ipam, circuits and dcim forms already use it.

**Benefit.** Users stop typing database IDs; large provider lists become searchable; the hand-written form and view code for the generic relation goes away.

**Risks to resolve in the plan.** The pre-fill from the Add button and from `return_url`; the type list must still follow the `supported_models` setting and models from other plugins; import and bulk edit keep their own fields and must be untouched; REST and GraphQL are unchanged.

## 2. Breadcrumbs in layouts (spec 005)

**Today.** The contract, contract line, invoice and invoice line pages each keep a 7-line template whose only purpose is to add a breadcrumb through `{% block breadcrumbs %}`. The invoice template puts every contract link inside one list item.

**NetBox 4.7.** Layouts accept `Breadcrumb` objects (a related object, a custom label, a filtered list link through `filtered_list_url`) and render one crumb per object when the accessor returns several. The old block still exists in the 4.7 page template and renders the new trail by default, so the current templates keep working, which makes this a cleanup, not a fix.

**Benefit.** Four templates deleted; invoices linked to several contracts show one crumb per contract; the pages follow the same mechanism as the rest of the layout.

**Risks.** Keeping the same destinations (the filtered lists) and the root crumb; the tests that read these pages.

## 3. GraphQL extensions on core types (spec 006)

**Today.** Contract assignments and their `content_object` are queryable, but from a device or a site there is no way to reach its contracts in the same query, and no filter such as "devices with an active contract".

**NetBox 4.7.** A plugin can add fields and filters to core GraphQL types. NetBox's documentation requires the related objects to be fetched through a permission-restricted prefetch, because permissions are applied only to the top-level list.

**Benefit.** Integrations get an object and its contracts in one request, and can list objects that have (or lack) a contract.

**Risks.** The core models have no reverse relation to assignments, so the resolver must go through the content type; the extended models must follow `supported_models` and only models that have a GraphQL type; field names must not collide with other plugins; list queries must keep a fixed query count.

## 4. Choice descriptions (spec 007)

**Today.** Status, invoice status, internal party, currency and billing-method choices carry a label and a colour only. Nothing tells a user that a Posted invoice locks its amounts, or what a usage-based unit means.

**NetBox 4.7.** A `Choice` carries a label, colour and description, is still a two-item tuple, and also feeds the colour map; administrators can give descriptions in `FIELD_CHOICES` through dictionaries. Descriptions appear under the options of NetBox's static choice fields.

**Benefit.** Self-explaining drop-downs without extra documentation.

**Risks.** Descriptions show only where a form uses NetBox's choice field, so some forms must change field class; translations (English and French) must cover the new texts; an administrator who replaces a choice set through `FIELD_CHOICES` replaces our descriptions too, which is expected.

## Out of this evaluation

- Core custom scripts are deprecated (removal in 5.0): the plugin's `scripts/` and the constitution already require logic to live in importable modules. Worth a later evaluation of an event-rule action or a management command.
- Compatibility fixes and the 4.7.4 test run: see the #318 assessment.
