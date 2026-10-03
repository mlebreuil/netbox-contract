"""Issue #309, user story 1: the amend permission action on contract lines (spec 003, research D4 and D6)."""

from datetime import date
from decimal import Decimal

from django.test import TestCase as DjangoTestCase
from django.urls import reverse
from netbox.registry import registry
from rest_framework import status
from users.constants import TOKEN_PREFIX
from users.forms.model_forms import ObjectPermissionForm
from users.models import Token
from utilities.testing import TestCase

from netbox_contract.models import ContractLine
from netbox_contract.tests.custom import APITestCase
from netbox_contract.tests.helpers import (
    add_constrained_permission,
    invoiced_recurring_line,
    make_contract,
    make_invoice,
    make_invoice_line,
    make_line,
    monthly,
    one_time,
)

AMEND_HELP = 'Amend the price or quantity of an invoiced contract line'


class LineAnnotationsTestCase(DjangoTestCase):
    """with_lock_state() computes, in the list query, what lock_message() and replaced_by tell line by line."""

    @classmethod
    def setUpTestData(cls):
        unlocked_contract = make_contract(name='Unlocked')
        cls.unlocked = make_line(unlocked_contract, monthly(), 10, description='Unlocked')

        invoiced_contract = make_contract(name='Invoiced')
        cls.locked_by_contract = make_line(invoiced_contract, monthly(), 20, description='Locked by contract')
        cls.replaced = make_line(invoiced_contract, monthly(), 30, description='Replaced', end_date=date(2025, 6, 30))
        cls.successor = make_line(
            invoiced_contract, monthly(), 35, description='Successor', start_date=date(2025, 7, 1),
            replaces=cls.replaced,
        )
        make_invoice(invoiced_contract, number='INV-1', amount=100)

        referenced_contract = make_contract(name='Referenced')
        cls.referenced = make_line(referenced_contract, monthly(), 40, description='Referenced')
        invoice = make_invoice(referenced_contract, number='INV-2', amount=40)
        make_invoice_line(invoice, contract_line=cls.referenced)

    def test_annotations_match_the_line_methods(self):
        lines = {line.pk: line for line in ContractLine.objects.with_lock_state()}
        for line in (self.unlocked, self.locked_by_contract, self.replaced, self.successor, self.referenced):
            with self.subTest(line=line.description):
                annotated = lines[line.pk]
                self.assertEqual(annotated.is_locked_line, bool(line.lock_message()))
                self.assertEqual(annotated.has_successor, line.replaced_by.exists())

    def test_expected_values(self):
        lines = {line.pk: line for line in ContractLine.objects.with_lock_state()}
        self.assertFalse(lines[self.unlocked.pk].is_locked_line)
        self.assertTrue(lines[self.locked_by_contract.pk].is_locked_line)
        self.assertTrue(lines[self.referenced.pk].is_locked_line)
        self.assertTrue(lines[self.replaced.pk].has_successor)
        self.assertFalse(lines[self.successor.pk].has_successor)

    def test_can_be_amended_uses_the_annotation(self):
        replaced = ContractLine.objects.with_lock_state().get(pk=self.replaced.pk)
        with self.assertNumQueries(1):  # the unit only, not replaced_by.exists()
            self.assertFalse(replaced.can_be_amended)


class PermissionRegistrationTestCase(DjangoTestCase):
    """US1-1: contract lines declare an "amend" action that object permissions offer."""

    def test_action_registered(self):
        actions = {action.name: action for action in registry['model_actions']['netbox_contract.contractline']}
        self.assertIn('amend', actions)
        self.assertEqual(str(actions['amend'].help_text), AMEND_HELP)

    def test_offered_by_the_object_permission_form(self):
        field = ObjectPermissionForm().fields['action_amend']
        self.assertEqual(str(field.help_text), AMEND_HELP)


class AmendUITestCase(TestCase):
    """US1-2 and US1-4 to US1-7: who sees the Amend button and may use the amend screen."""

    def setUp(self):
        super().setUp()
        self.line = invoiced_recurring_line()
        self.contract = self.line.contract
        self.amend_url = reverse('plugins:netbox_contract:contractline_amend', args=[self.line.pk])

    def pages(self, line, edit):
        pages = {
            'line': line.get_absolute_url(),
            'contract lines table': reverse('plugins:netbox_contract:contractline_list')
            + f'?contract_id={line.contract.pk}',
        }
        if edit:  # the edit page needs the change permission
            pages['line edit'] = reverse('plugins:netbox_contract:contractline_edit', args=[line.pk])
        return pages

    def assertButtonShown(self, shown, line=None, edit=False):
        line = line or self.line
        url = reverse('plugins:netbox_contract:contractline_amend', args=[line.pk])
        for page, page_url in self.pages(line, edit).items():
            with self.subTest(page=page, shown=shown):
                response = self.client.get(page_url)
                self.assertEqual(response.status_code, 200)
                (self.assertContains if shown else self.assertNotContains)(response, url)

    def test_view_and_amend_only(self):
        """US1-2: view + amend, without add or change, is enough to amend."""
        self.add_permissions(
            'netbox_contract.view_contract', 'netbox_contract.view_contractline',
            'netbox_contract.amend_contractline',
        )
        self.assertButtonShown(True)
        self.assertEqual(self.client.get(self.amend_url).status_code, 200)
        response = self.client.post(
            self.amend_url, {'effective_date': '2025-07-01', 'unit_price': '110', 'reason': 'Indexation'}
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(ContractLine.objects.filter(replaces=self.line, unit_price=Decimal('110')).exists())

    def test_add_and_change_without_amend(self):
        """US1-4: add + change no longer allow amending."""
        self.add_permissions(
            'netbox_contract.view_contract', 'netbox_contract.view_contractline',
            'netbox_contract.add_contractline', 'netbox_contract.change_contractline',
        )
        self.assertButtonShown(False, edit=True)
        self.assertEqual(self.client.get(self.amend_url).status_code, 403)

    def test_edit_page_with_change_and_amend(self):
        """FR-003: the locked-line message of the edit page offers Amend to a user allowed to amend the line."""
        self.add_permissions(
            'netbox_contract.view_contract', 'netbox_contract.view_contractline',
            'netbox_contract.change_contractline', 'netbox_contract.amend_contractline',
        )
        self.assertButtonShown(True, edit=True)

    def test_constrained_to_another_contract(self):
        """US1-5: an amend permission limited to the lines of another contract does not apply to this line."""
        other = invoiced_recurring_line(name='Other contract')
        self.add_permissions('netbox_contract.view_contract', 'netbox_contract.view_contractline')
        add_constrained_permission(self.user, 'netbox_contract.amend_contractline', {'contract': other.contract.pk})
        self.assertButtonShown(False)
        self.assertIn(self.client.get(self.amend_url).status_code, (403, 404))
        self.assertButtonShown(True, line=other)

    def test_lines_that_cannot_be_amended(self):
        """US1-6: one-time and already replaced lines show no button; a recurring line not invoiced yet does."""
        self.add_permissions(
            'netbox_contract.view_contract', 'netbox_contract.view_contractline',
            'netbox_contract.amend_contractline',
        )
        one_time_line = make_line(self.contract, one_time(), 50, description='Setup')
        not_invoiced = make_line(make_contract(name='Not invoiced'), monthly(), 10)
        replaced = invoiced_recurring_line(name='Replaced')
        make_line(replaced.contract, monthly(), 120, description='Successor', start_date=date(2025, 7, 1),
                  replaces=replaced)
        for line in (one_time_line, replaced):
            url = reverse('plugins:netbox_contract:contractline_amend', args=[line.pk])
            with self.subTest(line=line.description):
                self.assertNotContains(self.client.get(line.get_absolute_url()), url)
        self.assertContains(
            self.client.get(not_invoiced.get_absolute_url()),
            reverse('plugins:netbox_contract:contractline_amend', args=[not_invoiced.pk]),
        )

    def test_superuser(self):
        """US1-7."""
        self.user.is_superuser = True
        self.user.save()
        self.assertButtonShown(True, edit=True)

    def test_amend_without_view(self):
        """Edge case: the amend action without view permission does not open the amend screen."""
        self.add_permissions('netbox_contract.amend_contractline')
        self.assertIn(self.client.get(self.amend_url).status_code, (403, 404))

    def test_button_per_line_in_a_table(self):
        """Edge case: in a table mixing lines, the button is shown only on the amendable ones."""
        self.add_permissions(
            'netbox_contract.view_contract', 'netbox_contract.view_contractline',
            'netbox_contract.amend_contractline',
        )
        setup = make_line(self.contract, one_time(), 50, description='Setup')
        response = self.client.get(
            reverse('plugins:netbox_contract:contractline_list') + f'?contract_id={self.contract.pk}'
        )
        self.assertContains(response, self.amend_url)
        self.assertNotContains(response, reverse('plugins:netbox_contract:contractline_amend', args=[setup.pk]))


class AmendAPITestCase(APITestCase):
    """US1-3, US1-4 and the REST table of contracts/rest-api.md for POST contract-lines/{id}/amend/."""

    model = ContractLine

    def setUp(self):
        super().setUp()
        self.line = invoiced_recurring_line()
        self.url = reverse('plugins-api:netbox_contract-api:contractline-amend', args=[self.line.pk])
        self.data = {'effective_date': '2025-07-01', 'quantity': 3, 'reason': 'More seats'}

    def post(self, header=None):
        return self.client.post(self.url, self.data, format='json', **(header or self.header))

    def test_view_and_amend(self):
        self.add_permissions('netbox_contract.view_contractline', 'netbox_contract.amend_contractline')
        response = self.post()
        self.assertHttpStatus(response, status.HTTP_201_CREATED)
        self.assertEqual(response.data['replaces']['id'], self.line.pk)

    def test_add_and_change_without_amend(self):
        self.add_permissions(
            'netbox_contract.view_contractline', 'netbox_contract.add_contractline',
            'netbox_contract.change_contractline',
        )
        self.assertHttpStatus(self.post(), status.HTTP_403_FORBIDDEN)

    def test_amend_outside_the_view_constraints(self):
        other = invoiced_recurring_line(name='Other contract')
        add_constrained_permission(self.user, 'netbox_contract.view_contractline', {'contract': other.contract.pk})
        self.add_permissions('netbox_contract.amend_contractline')
        self.assertHttpStatus(self.post(), status.HTTP_404_NOT_FOUND)

    def test_read_only_token(self):
        self.add_permissions('netbox_contract.view_contractline', 'netbox_contract.amend_contractline')
        token = Token.objects.create(user=self.user, write_enabled=False)
        header = {'HTTP_AUTHORIZATION': f'Bearer {TOKEN_PREFIX}{token.key}.{token.token}'}
        self.assertHttpStatus(self.post(header), status.HTTP_403_FORBIDDEN)
