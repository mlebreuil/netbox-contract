"""Spec 007: a description under the status and billing method options."""

import inspect
import textwrap

from django.test import SimpleTestCase, TestCase, override_settings
from django.utils import translation
from django.utils.translation import gettext_lazy as _
from utilities.choices import Choice, ChoiceSet
from utilities.forms.fields import ChoiceField

from netbox_contract import calculations, forms
from netbox_contract.models import BillingMethodChoices, InvoiceStatusChoices, StatusChoices

SETS = (StatusChoices, InvoiceStatusChoices, BillingMethodChoices)
PRISTINE = {}

# Values, labels and colours of the previous release
PREVIOUS = {
    StatusChoices: [('active', 'Active', 'green'), ('canceled', 'Canceled', 'red')],
    InvoiceStatusChoices: [
        ('draft', 'Draft', 'yellow'), ('posted', 'Posted', 'green'), ('canceled', 'Canceled', 'red'),
    ],
    BillingMethodChoices: [('one_time', 'One-time', 'blue'), ('recurring', 'Recurring', 'green'),
                           ('usage', 'Usage-based', 'orange')],
}
DESCRIPTIONS = {
    'draft': 'Being prepared: amounts and lines can still change',
    'posted': 'Final: amount, currency, period, contracts and the amounts of its lines are locked',
    'canceled': 'No longer valid; kept for the record',
    'active': 'In force',
    'one_time': 'Billed once, from quantity and unit price',
    'recurring': 'Billed every period, prorated to the invoice period',
    'usage': 'Billed from a quantity entered on each invoice',
}
CONTRACT_CANCELED = 'Ended or withdrawn; kept for the record'


def pristine(choice_set):
    """
    The choice set as the plugin defines it. A deployment (the CI configuration too) may replace the options of a
    set through FIELD_CHOICES, which hides the built-in ones, so the class is built again without any setting.
    """
    namespace = {'ChoiceSet': ChoiceSet, 'Choice': Choice, '_': _, 'calculations': calculations,
                 '__name__': 'netbox_contract.models'}
    with override_settings(FIELD_CHOICES={}):
        exec(textwrap.dedent(inspect.getsource(choice_set)), namespace)  # noqa: S102
    return namespace[choice_set.__name__]


def option_descriptions(form, name):
    widget = form.fields[name].widget
    return dict(getattr(widget, 'original_widget', widget).descriptions)


class ChoiceDataTestCase(SimpleTestCase):
    def sets(self):
        return [pristine(choice_set) for choice_set in SETS]

    def test_values_labels_and_colours_are_unchanged(self):
        for choice_set in self.sets():
            previous = PREVIOUS[next(c for c in PREVIOUS if c.__name__ == choice_set.__name__)]
            with self.subTest(choice_set.__name__):
                self.assertEqual([(c[0], str(c[1])) for c in choice_set], [(v, label) for v, label, _c in previous])
                self.assertEqual(choice_set.colors, {v: color for v, _l, color in previous})

    def test_every_choice_has_a_description(self):
        for choice_set in self.sets():
            for choice in choice_set:
                with self.subTest(choice_set.__name__, value=choice[0]):
                    self.assertTrue(str(choice.description))

    def test_wording(self):
        contract, invoice, billing = self.sets()
        for choice in invoice:
            self.assertEqual(str(choice.description), DESCRIPTIONS[choice.value])
        for choice in billing:
            self.assertEqual(str(choice.description), DESCRIPTIONS[choice.value])
        for choice in contract:
            expected = CONTRACT_CANCELED if choice.value == 'canceled' else DESCRIPTIONS[choice.value]
            self.assertEqual(str(choice.description), expected)

    def test_french_translations_differ_from_the_source(self):
        with translation.override('fr'):
            for choice_set in self.sets():
                for choice in choice_set:
                    with self.subTest(choice_set.__name__, value=choice[0]):
                        english = str(choice.description)
                        with translation.override('en'):
                            source = str(choice.description)
                        self.assertNotEqual(english, source)


class FormDescriptionTestCase(TestCase):
    def test_invoice_status(self):
        for form in (forms.InvoiceForm(), forms.InvoiceFilterForm()):
            with self.subTest(form=type(form).__name__):
                self.assertEqual(
                    option_descriptions(form, 'status'),
                    {v: DESCRIPTIONS[v] for v in ('draft', 'posted', 'canceled')},
                )

    def test_filter_form_renders_the_descriptions(self):
        html = forms.InvoiceFilterForm()['status'].as_widget()
        self.assertIn(f'data-description="{DESCRIPTIONS["posted"]}"', html)

    def test_billing_method(self):
        expected = {v: DESCRIPTIONS[v] for v in ('one_time', 'recurring', 'usage')}
        for form in (forms.UnitForm(), forms.UnitFilterForm(), forms.ContractLineFilterForm()):
            with self.subTest(form=type(form).__name__):
                self.assertEqual(option_descriptions(form, 'billing_method'), expected)

    def test_contract_status(self):
        # The test configuration replaces the contract statuses (FIELD_CHOICES), so the descriptions come from the
        # configured options; the built-in ones are checked in ChoiceDataTestCase.
        configured = {c.value: str(c.description) for c in StatusChoices if getattr(c, 'description', None)}
        for form in (forms.ContractForm(), forms.ContractFilterForm()):
            with self.subTest(form=type(form).__name__):
                self.assertEqual(option_descriptions(form, 'status'), configured)

    def test_contract_status_fields_are_description_aware(self):
        for form in (forms.ContractForm(), forms.ContractFilterForm()):
            field = form.fields['status']
            widget = getattr(field.widget, 'original_widget', field.widget)
            self.assertTrue(hasattr(widget, 'descriptions'))

    def test_option_without_description_renders(self):
        field = ChoiceField(choices=[('a', 'A'), ('b', 'B')])
        self.assertEqual(field.widget.descriptions, {})
        self.assertIn('<option value="b">', field.widget.render('x', 'a').replace('\n', ''))


class FieldChoicesTestCase(SimpleTestCase):
    def build(self, field_choices):
        with override_settings(FIELD_CHOICES=field_choices):
            return type('Probe', (ChoiceSet,), {
                'key': 'Invoice.status',
                '__module__': 'netbox_contract.probe',
                'CHOICES': list(InvoiceStatusChoices.CHOICES),
            })

    def test_extend_keeps_descriptions_and_accepts_entries_without(self):
        probe = self.build({'netbox_contract.Invoice.status+': [
            {'value': 'hold', 'label': 'On hold', 'color': 'orange', 'description': 'Waiting for approval'},
            ('plain', 'Plain'),
        ]})
        descriptions = dict(ChoiceField(choices=probe).widget.descriptions)
        self.assertEqual(descriptions['posted'], DESCRIPTIONS['posted'])
        self.assertEqual(descriptions['hold'], 'Waiting for approval')
        self.assertNotIn('plain', descriptions)

    def test_replace_shows_only_the_configured_options(self):
        probe = self.build({'netbox_contract.Invoice.status': [
            {'value': 'open', 'label': 'Open', 'description': 'Open for review'},
            {'value': 'shut', 'label': 'Shut'},
        ]})
        field = ChoiceField(choices=probe)
        self.assertEqual(dict(field.widget.descriptions), {'open': 'Open for review'})
        self.assertEqual([c[0] for c in field.choices], ['open', 'shut'])
