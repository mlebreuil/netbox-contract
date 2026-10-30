# Implementation Plan: Descriptions under status and billing method options

**Branch**: `318-assess-against-netbox-4-7-4` | **Date**: 2026-10-29 | **Spec**: [spec.md](spec.md)

**Depends on**: [008-netbox-47-baseline](../008-netbox-47-baseline/spec.md) (minimum NetBox 4.7.0).

## Summary

Give the three built-in choice sets (invoice status, contract status, unit billing method) a one-sentence description per option using NetBox 4.7's `Choice(value, label, color, description)`, and make the forms render them by using NetBox's own `ChoiceField` / `MultipleChoiceField` classes where the plugin declares fields by hand (the filter forms). Model-generated form fields (add/edit) pick up the description-aware field only if they are declared with the NetBox field, so those are declared explicitly. French translations are added. Stored values, labels, colours and all interfaces stay unchanged.

## Technical Context

**Language/Version**: Python 3.12 to 3.14, Django 6.1 (NetBox 4.7.4)

**Primary Dependencies**: NetBox 4.7 `utilities.choices.Choice`, `utilities.forms.fields.ChoiceField/MultipleChoiceField/TypedChoiceField`; no new dependency

**Storage**: none, no migration expected (descriptions are not part of the `choices` value Django records; to be confirmed by `makemigrations --check` in task T015)

**Testing**: unit tests on the choice sets, rendering tests of the forms, `FIELD_CHOICES` tests

**Project Type**: NetBox plugin

**Performance Goals**: none

**Constraints**: `FIELD_CHOICES` extend/replace behaviour unchanged; options without description render normally

**Scale/Scope**: 3 choice sets (`StatusChoices`, `InvoiceStatusChoices`, `BillingMethodChoices`), 6 form locations, translations, docs

## Constitution Check

| Principle | Assessment |
|-----------|------------|
| I. NetBox-native | Pass: uses the platform's descriptions. |
| II. Tested behaviour | Pass. Tests first: description of each choice in both languages, rendered `data-description`, extend and replace through `FIELD_CHOICES`, values/colors unchanged. |
| III. Lint-clean | Pass. |
| IV. Data safety | Pass, no data change. |
| V. Backward-compatible interfaces | Pass: REST, GraphQL, CSV unchanged (descriptions are not serialized). |
| VI. Simplicity | Pass. |
| VII. Documented change | Pass: `docs/`, `CHANGELOG.md` Enhancements, `locale/fr`. |

No Complexity Tracking entry.

## Project Structure

```text
specs/007-choice-descriptions/
├── plan.md  research.md  data-model.md  quickstart.md
└── contracts/choices.md

netbox_contract/
├── models.py          # three ChoiceSets use Choice(...)
├── forms.py           # explicit ChoiceField/MultipleChoiceField for the six locations
├── locale/fr/LC_MESSAGES/django.po(.mo)
└── tests/test_choice_descriptions.py   # new
docs/ (invoice and contract pages), CHANGELOG.md
```
