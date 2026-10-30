# Contract: choices and forms

- Stored values, labels, colours: identical to the previous release.
- REST / GraphQL / CSV representations: identical (descriptions are not serialized).
- HTML: each option of the fields listed in `research.md` R2 carries `data-description="<translated text>"`; options without a description carry none.
- `FIELD_CHOICES` (`netbox_contract.<ChoiceSetName>`): extend or replace as before; an entry may be a dict `{'value':..., 'label':..., 'color':..., 'description':...}`.
