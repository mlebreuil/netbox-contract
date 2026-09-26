# Idea Research: Contract lines, units and billing methods

- **Slug**: contract-lines-units
- **Created**: 2026-09-25 (revised 2026-09-26: web research added, scope set to NetBox 4.6 with 4.7 out of scope, `min_version` to be raised to 4.6, django-money replaced by plain fields, notes condensed)
- **Evidence confidence (overall)**: medium — repository evidence is strong; demand evidence is weak; external and NetBox evidence comes from summarised web pages and search results. Readiness for NetBox 4.6 is checked only by code search and by reading the CI workflow, not by running tests (low to medium).

## Users & Demand

- Issue #278 ("Replace invoice templates with contract lines") was opened on 2025-09-12 by the maintainer (mlebreuil); it is open, with no labels, comments or linked issues or PRs. — [source: https://github.com/mlebreuil/netbox-contract/issues/278] (confidence: medium; summarised page)
- No request from other users is visible: the only non-maintainer open issues seen are #291 (currency delimiter display) and #251 (contract assignment dropdown); the related invoice-tax issue #177 is also the maintainer's. The repository has 65 stars, 15 forks and several contributors. — [source: https://github.com/mlebreuil/netbox-contract/issues; https://github.com/mlebreuil/netbox-contract] (confidence: medium; the fetched list may be incomplete)
- The limitation is real: a contract holds one monthly OR yearly recurring cost plus one non-recurring cost, so several billable contract lines or usage-based charges cannot be described. — [source: netbox_contract/models.py (Contract.yrc/mrc/nrc); docs/contract.md] (confidence: high)
- Who beyond the maintainer needs contract lines, usage-based costs or unit-based pricing is unknown. — [ASSUMPTION] (confidence: low)

## Prior Art

Internal:

- **Invoice templates already play part of the proposed contract line role**: an Invoice with `template=True` (one per contract) holds InvoiceLines with accounting dimensions, and new invoices are pre-filled from the contract. The proposal would replace this. — [source: netbox_contract/models.py; docs/invoice.md; netbox_contract/views.py] (confidence: high)
- **Current pre-fill is contract-level and simple**: amount = yrc/12 × invoice_frequency (yrc when frequency is 12), else mrc × invoice_frequency; period_start = last non-template invoice's period_end + 1 day; period_end = start + invoice_frequency months − 1 day. It pre-fills the form only, creates no invoice lines, and does not use `nrc`. — [source: netbox_contract/views.py ~lines 430-470] (confidence: high)
- **Migration precedent**: a NetBox script converts the legacy accounting-dimensions JSON field into invoice templates. — [source: scripts/netbox-contract.py `create_invoice_template`; docs/contract.md] (confidence: high)
- **Hierarchy exists** (`Contract.parent`, related_name `childs`); **Invoice.contracts is many-to-many**, so an invoice can link several contracts. — [source: netbox_contract/models.py] (confidence: high)
- **InvoiceLine is minimal** (invoice, currency, amount, accounting_dimensions, comments); `clean()` blocks lines whose sum exceeds the invoice amount; no reference to a contract line, quantity or unit price. — [source: netbox_contract/models.py] (confidence: high)
- **Currency is a plain CharField per model** (Contract, Invoice, InvoiceLine) with lowercase codes from a ChoiceSet that administrators override through `FIELD_CHOICES`; nothing enforces consistency across the three. Invoice statuses are Draft, Posted, Canceled (no Paid). — [source: netbox_contract/models.py; README.md] (confidence: high)
- No earlier spec, plan or decision on billing exists under `.specify/`; the constitution is still the unfilled template. — [source: .specify/] (confidence: high)

External:

- **Odoo (OCA) `contract` addon**: contract lines carry product, quantity, price, a recurrence rule (days to years), start date, computed and editable next-invoice date and optional end date; a daily cron generates recurring invoices, pre-paid or post-paid. Usage-based billing and a one-time versus recurring distinction are not described. — [source: https://pypi.org/project/odoo14-addon-contract] (confidence: medium; summarised page)
- **CESNET `inventory-monitor-plugin`** (NetBox): contracts and invoices with price, currency and dates, one-level parent-child contracts, and validation that price and currency are set together; no line items, no recurring versus one-time distinction, no conversion. There is no NetBox-ecosystem precedent to copy. — [source: https://github.com/CESNET/inventory-monitor-plugin] (confidence: medium; README summary)
- **NetBox Plugin Ideas PLUGINS-I-31** (support contract plugin) mentions no invoices or billing; a search for NetBox plugins with contract lines or recurring and usage-based billing found only netbox-contract, the CESNET plugin and generic billing software (not exhaustive). — [source: https://plugin-ideas.netbox.dev/ideas/PLUGINS-I-31; web search] (confidence: low to medium)

## Market & Context

- Today users combine one cost per contract (mrc/yrc/nrc), hand-edited invoice amounts and lines, and one invoice template per contract for accounting dimensions. — [source: docs/contract.md, docs/invoice.md] (confidence: medium; from documentation)
- The cost of doing nothing is not quantifiable from the evidence. — [ASSUMPTION] (confidence: low)
- The repository is at v2.4.7 with frequent small releases; `netbox_contract/__init__.py` has `min_version = '4.5.0'` and no `max_version`; the README table maps plugin 2.4 to NetBox 4.3 through 4.6. Issue #278 quotes plugin v2.5.0 and NetBox v4.3.0, which the maintainer attributes to the age of the issue. — [source: pyproject.toml, __init__.py, README.md, CHANGELOG.md] (confidence: high)

## Data & Constraints

- **Breaking-change surface**: mrc/yrc/nrc and invoice templates appear in models, forms, tables, filtersets, API serializers and views, the contract detail template, list annotations, the pre-fill view, import test data and `scripts/netbox-contract.py`; deprecating them touches the public REST API. — [source: grep of netbox_contract/ and scripts/] (confidence: high)
- **Existing data**: the number of contracts with mrc/yrc/nrc values and of existing templates that a migration would touch is unknown. — [NEEDS CLARIFICATION]
- **Amount fields** are `DecimalField(max_digits=10, decimal_places=2)`. — [source: netbox_contract/models.py] (confidence: high)
- **Tests**: NetBox-standard view tests and a `query_counts.json` baseline exist; new models and views would need to extend both. — [source: netbox_contract/tests/] (confidence: medium)
- **Compliance**: not addressed by the issue; the docs say VAT inclusion in line amounts depends on the user's budget, and issue #177 concerns tax display. — [source: docs/invoice_line.md; issues list] (confidence: medium)
- **CI**: `.github/workflows/lint-tests.yaml` checks out `netbox-community/netbox` without a `ref` (Python 3.12 to 3.14), so it does not show that the plugin passes on NetBox 4.6; it also runs `pip install -r requirements.txt -U` after the plugin's own install. — [source: .github/workflows/lint-tests.yaml] (confidence: medium; workflow read, no run inspected)

## NetBox Baseline: 4.6 Target

Maintainer decisions (2026-09-25 and 2026-09-26): the issue targets **NetBox 4.6**; **NetBox 4.7 is out of scope** and will be handled separately later because the deprecation of custom scripts in NetBox core is a large change; `min_version` is raised to 4.6.0 with no `max_version`; the CI is pinned to a 4.6 tag for this work; new code avoids the APIs removed in 4.7; django-money is replaced by plain fields (see the alternatives). The behaviour and upgrade decisions are in problem.md (Clarifications). — [source: user messages] (confidence: high)

NetBox 4.6 facts:

- Released 2026-05-05; pins `Django==6.0.*`, `django-tables2<2.9` and `djangorestframework==3.17.1`; the Python requirement for 4.6 was not found (4.5 required 3.12 to 3.14). — [source: https://netboxlabs.com/docs/netbox/release-notes/version-4.6; https://raw.githubusercontent.com/netbox-community/netbox/v4.6.0/base_requirements.txt] (confidence: medium)
- Deprecations in 4.6 include the custom `querystring` template tag, the `models` key of the application registry, `OptionalLimitOffsetPagination`, `ExpandableIPAddressField`, the `housekeeping` command, legacy view actions, `DEFAULT_ACTION_PERMISSIONS` and v1 API tokens; new: declarative layouts, reusable UI components and plugin-registered model actions. — [source: same release notes] (confidence: medium)
- Plugin scan (code search only): no use found of the deprecated `models` registry key (one comment in `views.py` about issue #303), the `querystring` tag, or the other deprecated APIs; templates only load `render_table` from `django_tables2`. Whether the existing tests pass on 4.6 has not been checked. — [source: grep of netbox_contract/] (confidence: medium)

NetBox 4.7 (out of scope, kept for reference):

- Released 2026-09-02; pins `Django==6.1.*` and `djangorestframework==3.18.0`; upgrades django-tables2 to v3.0 (`querystring` tag renamed, `RelatedLinkColumn` removed); requires PostgreSQL 15+ with `ltree`; removes the `models` registry key and the `querystring` tag; deprecates core custom scripts (removal planned for v5.0); changes the REST and GraphQL format of selection custom fields and bulk-error responses; adds `GenericObjectChoiceField` and `GenericObjectFormMixin`. — [source: https://netboxlabs.com/docs/netbox/release-notes/version-4.7; https://raw.githubusercontent.com/netbox-community/netbox/v4.7.0/base_requirements.txt] (confidence: medium)
- Candidates for the later 4.7 work: `scripts/netbox-contract.py` (a custom script), the hand-built external-party generic relation in `forms.py`, API and test review for the changed formats, and compatibility statements and CI matrix. Another NetBox plugin's 4.7 readiness review found no code changes needed beyond CI and documentation because it used none of the removed APIs. — [source: netbox_contract/forms.py; scripts/; https://github.com/jsenecal/netbox-notices/issues/66] (confidence: low to medium)

## Alternatives to django-money (ranked)

The maintainer decided to replace django-money and asked for alternatives to be ranked; on 2026-09-26 the maintainer **chose option 1 (plain Django fields, no money library)**.

Why django-money was dropped: version 3.6.1 lists Django 4.2 to 5.2 and Python 3.10 to 3.13, with no Django 6.x support or visible work, while NetBox 4.6 runs Django 6.0 (4.7 runs 6.1); it is not a dependency today; the project moved from GitHub (reported archived 2026-06-22) to Codeberg; it adds a second currency column and its own uppercase ISO currency configuration, which clashes with the plugin's lowercase, configurable `FIELD_CHOICES` codes (a data migration would be needed) and changes the API output. — [source: https://pypi.org/project/django-money/; https://codeberg.org/django-money/django-money; https://django-money.readthedocs.io/en/latest/; NetBox 4.6 base_requirements.txt] (confidence: medium; the fetched pages disagree on the year of release 3.6.1)

Criteria: runs on NetBox 4.6 (Django 6.0); fits the plugin's currency handling (lowercase codes, configurable choices); keeps existing data and the flat `amount` and `currency` API shape; low maintenance and dependency weight. — [source: netbox_contract/models.py; api/serializers.py; README.md] (confidence: high)

1. **Plain Django fields (chosen)**: `DecimalField` amounts plus the existing currency `CharField` and `CurrencyChoices`, validated in `clean()`, with `GeneratedField` possible for a single-row total such as quantity times unit price (same-table expressions only, so contract totals across lines are not possible). No dependency or Django-version constraint, no data migration of currency codes, API shape unchanged; the CESNET plugin uses the same pattern and a Django forum thread reported it as sufficient. Cost: no money type, so currency consistency needs explicit validation (which the issue requires anyway). — [source: netbox_contract/models.py; https://github.com/CESNET/inventory-monitor-plugin; https://forum.djangoproject.com/t/solutions-for-amount-fields-with-related-currency/3011; https://docs.djangoproject.com/en/6.0/ref/models/fields/] (confidence: medium)
2. **Plain fields plus `py-moneyed` in Python code only**: `Money` and `Currency` classes, no Django dependency, mature with three maintainers, GitHub repository not archived; adds currency-mismatch protection to computations. Costs: a new dependency, Python 3.12 to 3.14 support unconfirmed (the page read showed Python classifiers up to 3.11), uppercase ISO codes versus the plugin's lowercase configurable ones. — [source: https://pypi.org/project/py-moneyed/; https://github.com/py-moneyed/py-moneyed] (confidence: low to medium)
3. **A small in-plugin two-column money field**: the design of `django-moneyfield` without the dependency; more code (field, migrations, form, filter, serializer) for the same result as option 1. — [source: https://github.com/carlospalol/django-moneyfield; ASSUMPTION for the effort] (confidence: low)
4. **Keep django-money**: viable only after a successful trial on Django 6.0; the only fork found (browniebroke/django-money) shows no Django 6 support. — [source: https://github.com/browniebroke/django-money] (confidence: medium)
5. **`django-prices`** (Saleor, built on `prices`): version 2.4.0 (2025-10-29), Python 3.10 to 3.13, no Django versions stated, oriented to taxed e-commerce prices. — [source: https://pypi.org/project/django-prices/] (confidence: low to medium)
6. **`django-moneyfield`**: documentation refers to Django 1.5 to 1.6, apparently abandoned. — [source: https://github.com/carlospalol/django-moneyfield] (confidence: medium)

Limits: only three of seven packages on the Django Packages "Money" grid could be seen, none of them a money-field library; how `netbox-inventory` stores prices could not be confirmed and no money field was found in NetBox core; no option was installed or run. — [source: https://djangopackages.org/grids/g/money/; https://github.com/ArnesSI/netbox-inventory] (confidence: low)

## Evidence Against the Idea

- **Large scope for a deliberately small data model**: two new models, changes to Contract, Invoice and InvoiceLine, deprecation of three fields and the template mechanism, and new computation rules (proration, remaining amount for one-time costs, usage-based). — [source: intake.md compared with models.py and views.py] (confidence: medium)
- **Breaking-change risk** for the REST API, imports and exports, scripts and existing data. — [source: repository grep] (confidence: high)
- **Overlap with the template mechanism**: a template with lines and accounting dimensions already covers recurring lines per contract; whether extending template lines would meet the need was not examined. — [ASSUMPTION] (confidence: low)
- **No demonstrated demand**: the issue is maintainer-authored, has no comments or linked requests, and no other NetBox plugin found offers this. — [source: issue #278 page; issues list; CESNET plugin README] (confidence: medium)
- **Currency enforcement may reject existing data**, since differing currencies are allowed today. — [source: netbox_contract/models.py] (confidence: medium)
- **Invoices linked to several contracts** conflict with the rule that the invoice currency equals "the" contract currency. — [source: netbox_contract/models.py Invoice.contracts; intake.md] (confidence: high)
- A fetched summary of the issue mentioned an "existing django-money integration"; the pasted issue text and the repository dependencies show none, so it was treated as a summarisation error. — [source: fetch summary versus pyproject.toml] (confidence: medium)

## Gaps & Open Questions

- [NEEDS CLARIFICATION: Beyond the maintainer, who needs contract lines, one-time or usage-based costs today? Are there private requests or discussions not visible in the public issue list?]
- [NEEDS CLARIFICATION: How many existing contracts and invoice templates would the conversion migrations touch?]
- [NEEDS CLARIFICATION: Do the existing tests pass on NetBox 4.6? Not yet run; the CI is to be pinned to a 4.6 tag.]
- [NEEDS CLARIFICATION: Non-NetBox billing products (beyond Odoo) were not surveyed for unit and billing-method models such as usage-based billing.]

## Sources

Page contents were read through a summarising fetch tool, so details may be imprecise. All web hosts were fetched with the user's general authorisation of 2026-09-25 (policy: confirmed-by-user); the URL Trust Policy check could not validate the connected peer, so the first attempt on github.com was refused and the user then authorised fetching.

- github.com: https://github.com/mlebreuil/netbox-contract/issues/278 , https://github.com/mlebreuil/netbox-contract/issues , https://github.com/mlebreuil/netbox-contract , https://github.com/CESNET/inventory-monitor-plugin , https://github.com/jsenecal/netbox-notices/issues/66 , https://github.com/py-moneyed/py-moneyed , https://github.com/carlospalol/django-moneyfield , https://github.com/browniebroke/django-money , https://github.com/ArnesSI/netbox-inventory
- raw.githubusercontent.com: https://raw.githubusercontent.com/netbox-community/netbox/v4.6.0/base_requirements.txt , https://raw.githubusercontent.com/netbox-community/netbox/v4.7.0/base_requirements.txt
- netboxlabs.com: https://netboxlabs.com/docs/netbox/release-notes/version-4.6 , https://netboxlabs.com/docs/netbox/release-notes/version-4.7
- pypi.org: https://pypi.org/project/django-money/ , https://pypi.org/project/py-moneyed/ , https://pypi.org/project/django-prices/ , https://pypi.org/project/odoo14-addon-contract
- other: https://codeberg.org/django-money/django-money , https://django-money.readthedocs.io/en/latest/ , https://plugin-ideas.netbox.dev/ideas/PLUGINS-I-31 , https://forum.djangoproject.com/t/solutions-for-amount-fields-with-related-currency/3011 , https://djangopackages.org/grids/g/money/ , https://docs.djangoproject.com/en/6.0/ref/models/fields/
- Local files (read-only): netbox_contract/models.py, views.py, forms.py, api/serializers.py, templates, tests, scripts/netbox-contract.py, docs/*.md, README.md, CHANGELOG.md, pyproject.toml, .github/workflows/lint-tests.yaml, .specify/memory/constitution.md
