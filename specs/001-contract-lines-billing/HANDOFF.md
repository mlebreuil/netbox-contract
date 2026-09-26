# Hand-off: implementing contract lines (issue #278)

Written 2026-09-26 at the end of the specification phase, to start a fresh Claude Code session in the VS Code dev container. Delete or update this file when implementation is under way.

## Where things stand

- Branch: `278-replace-invoice-templates-with-contract-lines` (based on GitHub `develop`, plugin version 2.4.7 at the time). Refresh with `git fetch origin` before starting.
- Spec Kit artifacts are complete and analysed with no CRITICAL or HIGH finding: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/rest-api.md`, `contracts/ui-and-settings.md`, `quickstart.md`, `tasks.md` (61 tasks, Phases 1-9) and `checklists/requirements.md`.
- Project rules: `.specify/memory/constitution.md` version 1.0.0 (Principles I-VII). The plan's Constitution Check is done.
- Assessment notes: `.specify/assessments/contract-lines-units/` (verdict go).
- Nothing of the feature is implemented yet: no model, migration or test has been written.

## Start here

1. `git fetch origin` and check the branch is up to date with `origin/develop`.
2. Make sure the dev container has NetBox 4.6 or newer (the plugin's new minimum) on Python 3.12 or newer, with PostgreSQL and Redis running, and this repository installed in editable mode. `testing/configuration.py` is the NetBox configuration used by CI.
3. Run the existing suite once as the baseline: `python netbox/manage.py test netbox_contract.tests --keepdb`, and `ruff check`.
4. Run `/speckit-implement` and follow `tasks.md` in order: Setup, Foundational, then US1 (MVP), US2 immediately after (the riskiest part), then US3, US4, US5, US6, Polish. Tests come first in each story and must fail before the code that fixes them. Run `ruff check` and the story's tests at the end of each story. Do not commit without asking; the pre-commit hook must not be bypassed.

## Decisions taken with the maintainer (do not reopen without asking)

- Target NetBox 4.6 (`min_version = '4.6.0'`, no `max_version`); NetBox 4.7 is separate later work. CI is pinned to a NetBox 4.6 tag (latest seen: `v4.6.9`). No money library: plain Django decimals and the existing currency fields.
- One single release, plugin version 2.5.0. No intermediate publication.
- New models `Unit` and `ContractLine`; `Contract.billable` (existing contracts billable); `InvoiceLine.contract_line` and `quantity`. Invoice templates are kept and never deleted, deprecated, no longer used to pre-fill or generate.
- Conversion at upgrade is idempotent; template lines replace the `mrc`/`yrc` line (differences reported); a one-time line on a contract that already has a Posted invoice gets `invoiced_at_conversion = True` and is never proposed again.
- Invoice lines are generated when a new invoice is created (screen and REST create), never on edit or bulk import; there is no generation button or endpoint. Creation is refused for a non-billable contract, or when the invoice amount is lower than the total of the lines to generate. A new invoice has at most one contract.
- Quantity lives on the invoice line; unit and unit price come from the contract line; the amount is calculated when a contract line is referenced. Usage-based lines are generated with no quantity (amount 0). The pre-fill never proposes usage-based lines.
- Lock: contract lines cannot be added, changed or deleted once the contract has any invoice (any status), and cannot be changed or deleted once any invoice line references them. A unit's billing method and months cannot change while a line of an invoiced contract uses it. The billable flag and a contract's currency cannot change once invoices exist (currency: lines follow only when no invoice exists).
- Line dates must lie inside the contract's dates. Months are counted as whole calendar months plus leftover days over the days of the month where the range ends (1 January to 20 March = 2 + 20/31).
- The currency mismatch report is a read-only NetBox custom script (its logic lives in `reports.py`); custom scripts are expected to be deprecated in NetBox core, so moving it is part of the later 4.7 work.
- The two stale scripts `create_invoice_template` and `create_invoice_lines` are removed and announced in the changelog with a "Behaviour changes" list.

## Environment notes

- The pre-commit hook runs ruff on `netbox_contract/` through `/workspaces/netbox/netbox/venv/bin/python` (the dev container).
- Test helpers: `netbox_contract/tests/custom.py` (`ModelViewTestCase`, `APITestCase`); existing tests are in `tests/test_views.py`; `tests/query_counts.json` is the query-count baseline to regenerate when list views change.
- The plugin is at `netbox_contract/`; important existing places to change: `models.py`, `views.py` (`InvoiceEditView.get()` holds the current pre-fill), `forms.py` (`InvoiceForm.save()` copies template lines today), `api/serializers.py` (`InvoiceSerializer.create()` does the same), `scripts/netbox-contract.py`.
