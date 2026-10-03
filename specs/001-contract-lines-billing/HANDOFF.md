# Hand-off: implementing contract lines (issue #278)

Written 2026-09-26 at the end of the specification phase, to start a fresh Claude Code session in the VS Code dev container. Delete or update this file when implementation is under way.

## Where things stand

- Updated 2026-09-27: all tasks of `tasks.md` are done (T001-T073), including the adjustments after the upgrade test (T062-T068: invoice line name, editable dimensions of locked lines, amendment of a price or quantity, invoice line unit and unit price, Posted lock and Draft default, preview of the lines of a new invoice) and the convergence phase (T069-T073). SC-001 was removed from the spec by the maintainer.
- Everything is committed and pushed on branch `278-replace-invoice-templates-with-contract-lines`, apart from the changes of the last `/speckit-implement` run until they are committed.
- Checks: `ruff check` clean, `makemigrations --check` reports nothing (migrations 0044-0048), the full suite passes on the local NetBox 4.6.8 and on a clone of the pinned `v4.6.10` tag.
- Run the tests in the dev container with `NETBOX_CONFIGURATION=netbox.configuration_testing` (the default configuration has DEBUG on, which the debug toolbar refuses in tests).
- Spec Kit artifacts: `spec.md` (FR-001-FR-032), `plan.md`, `research.md` (decisions D1-D12, I1-I13), `data-model.md`, `contracts/`, `quickstart.md`, `tasks.md`, `checklists/requirements.md`. Project rules: `.specify/memory/constitution.md` 1.0.0.
- The dev database `netbox` is migrated to 0048 and contains the `MIG-` test data; `netbox_premigration_testdata` (test data, before the upgrade) and `netbox_before_0044` (original data) are copies to reset from.

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
