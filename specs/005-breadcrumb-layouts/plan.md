# Implementation Plan: Breadcrumbs declared in page layouts

**Branch**: `318-assess-against-netbox-4-7-4` | **Date**: 2026-10-29 | **Spec**: [spec.md](spec.md)

**Depends on**: [008-netbox-47-baseline](../008-netbox-47-baseline/spec.md) (minimum NetBox 4.7.0).

## Summary

Declare the breadcrumb trail of contracts, contract lines, invoices and invoice lines as `Breadcrumb` entries in each detail page layout (NetBox 4.7 `breadcrumbs=` on the layout), and delete the four hand-written breadcrumb templates. Tab pages of these objects share the trail automatically. The contract entry, empty today, becomes the external party name linking to the contract list filtered by that party.

## Technical Context

**Language/Version**: Python 3.12 to 3.14, Django 6.1 (NetBox 4.7.4)

**Primary Dependencies**: NetBox 4.7 `netbox.ui.layout` / `netbox.ui` `Breadcrumb`, `filtered_list_url`; no new dependency

**Storage**: none

**Testing**: NetBox view tests, plus a new module asserting the rendered trail per page and tab

**Project Type**: NetBox plugin

**Performance Goals**: no extra query on the detail page beyond the accessors already loaded; list-view query counts unchanged

**Constraints**: entries shown regardless of the viewer's permissions (clarification FR-008); filter parameters must be accepted by the plugin's filtersets

**Scale/Scope**: 4 layouts, 4 templates removed, 1 test module

## Constitution Check

| Principle | Assessment |
|-----------|------------|
| I. NetBox-native | Pass, improved: the platform mechanism replaces template overrides. |
| II. Tested behaviour | Pass. Tests first: trail of each page, each tab, absence of the removed templates, links resolving to filtered lists. |
| III. Lint-clean | Pass. |
| IV. Data safety | Pass, no data change. |
| V. Backward-compatible interfaces | Pass; only the HTML of the trail changes. The contract trail gains a link (bug fix). |
| VI. Simplicity | Pass; four files deleted. |
| VII. Documented change | Pass. `CHANGELOG.md`: Bug Fixes (contract entry) and Other Changes. |

No Complexity Tracking entry.

## Project Structure

```text
specs/005-breadcrumb-layouts/
├── plan.md  research.md  data-model.md  quickstart.md
└── contracts/breadcrumbs.md

netbox_contract/
├── views.py (or layouts module)      # layout=... breadcrumbs=[Breadcrumb(...)]
├── templates/netbox_contract/{contract,contractline,invoice,invoiceline}.html   # deleted
└── tests/test_breadcrumbs.py         # new
CHANGELOG.md
```

**Structure Decision**: breadcrumbs live next to each view's layout; no new module.
