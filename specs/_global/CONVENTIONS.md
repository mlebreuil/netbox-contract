# Identifier and documentation conventions

Every feature lives in `specs/NNN-name/` (NNN = 001, 002, ...). The numbers inside a feature (`FR-029`, `T017`,
`D6`) restart at 1 in each feature, so on their own they name several different things. **Every identifier is
therefore written with the number of its feature**, in the specification, the plan, the tasks, the code, the tests,
the documentation and the changelog:

```text
NNN-KIND
001-FR-029     functional requirement 29 of feature 001
```

A bare `FR-029`, `US2`, `T017`, `SC-003` or `research D6` is never accepted. `python utils/spec_ids.py check`
rejects it (it runs in CI and in the pre-commit hook).

## Kinds

| Kind | Written | Defined in | Definition line |
|---|---|---|---|
| User story | `NNN-US2` | `spec.md` | heading `### User Story 2 - Title (Priority: P1)` |
| Acceptance scenario | `NNN-US2-4` | `spec.md` | the 4th numbered scenario of user story 2 (only the story is checked) |
| Functional requirement | `NNN-FR-029`, `NNN-FR-029a` | `spec.md` | `- **NNN-FR-029**: The system MUST ...` |
| Success criterion | `NNN-SC-003` | `spec.md` | `- **NNN-SC-003**: ...` |
| Clarification | `NNN-Q3` | `spec.md` | the 3rd `- Q: ... -> A: ...` line of the Clarifications section, counted in file order |
| Task | `NNN-T017` | `tasks.md` | `- [ ] NNN-T017 [P] [NNN-US2] Description` |
| Research decision | `NNN-D6` | `research.md` | heading `## NNN-D6. Title` |
| Implementation decision | `NNN-I14` | `research.md` | `- **NNN-I14. Title**: ...` (decision taken while implementing) |

Rules:

- Numbers are allocated once, in order, and **never reused or renumbered**. A requirement that is removed is kept as
  a line `Retired: NNN-FR-009 (reason, date)` so that old citations still resolve. A requirement that is split gets
  a letter suffix (`NNN-FR-009a`).
- `research.md` decisions are always `D` (older features used `R`; they were renamed to `D`). `C1`/`N1` style
  findings of `/speckit-analyze` are working notes of one review, not identifiers: resolve them, do not cite them.
- A range is written `NNN-T004 to NNN-T006`.
- Citing a requirement in code or tests: put the qualified identifier in the comment or docstring next to the rule
  it explains, e.g. `# a posted invoice is locked (001-FR-031)`. Cite the requirement, not the task.
- Citing across features is the same: `see 003-D6`. Never write "spec 003 FR-018".
- The commit, pull request and issue text should use the qualified form as well.

## Tool

```bash
python utils/spec_ids.py check             # definitions unique, citations resolve, no bare identifier
python utils/spec_ids.py show 001-FR-029   # definition and every place that cites it
python utils/spec_ids.py refs 001-FR-029   # only the places
python utils/spec_ids.py next 004 T        # next free number of a kind in a feature (FR, SC, T, D, I, US)
python utils/spec_ids.py registry          # regenerate specs/_global/registry.md
```

Standard library only. `registry.md` is generated: never edit it by hand.

## Per-feature documents and the global view

A feature directory holds the **change**: `spec.md`, `plan.md`, `research.md`, `tasks.md`, `quickstart.md`,
`checklists/`, and `data-model.md` and `contracts/` as **deltas** (what this feature adds, changes or removes).
`specs/_global/` holds the **current state of the product**, which every feature updates:

| Global document | Holds | Updated when a feature |
|---|---|---|
| `data-model.md` | every model, field, constraint, lock and migration, as it is now | changes anything stored or a rule on stored data |
| `contracts/rest-api.md` | REST endpoints, fields, filters, brief sets, deprecations | changes the REST API |
| `contracts/graphql.md` | GraphQL types, fields, filters, permissions | changes the GraphQL schema |
| `contracts/ui.md` | pages, forms, actions, breadcrumbs, quick add, settings | changes a page, form or setting |
| `contracts/routes.md` | route names and addresses (the list pinned by `tests/test_conventions.py`) | adds or changes a route |
| `contracts/operations.md` | management commands, scripts, metadata, compatibility, CI | changes any of these |
| `behaviours.md` | the business rules by domain, each with the identifiers that introduced or changed it | adds, changes or retires a requirement |

Rules:

- Each statement in a global document carries the identifiers that introduced or last changed it
  (`... (001-FR-031, 004-FR-014)`), so the global view and the feature specifications can be followed in both
  directions.
- `plan.md` has a "Global documents" section listing which of the documents above the feature changes; `tasks.md`
  has a final task `NNN-Txxx Update the global documents` for them. Both are checked at review, like the changelog.
- When the implemented behaviour differs from a global document, the global document is wrong: fix it in the same
  change. When two features disagree, the later feature's identifier wins and the earlier statement is retired
  (`Retired:` line in the earlier spec; the global document shows only the current rule).
- Per-feature `data-model.md` and `contracts/*.md` start with a line pointing to the global document they amend.
