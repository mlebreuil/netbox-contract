"""Spec user story 2: conversion of existing costs and invoice templates (FR-013..FR-016, SC-002)."""

from datetime import date
from decimal import Decimal
from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from netbox_contract.conversion import convert_legacy_data
from netbox_contract.models import (
    AccountingDimension,
    BillingMethodChoices,
    Contract,
    ContractLine,
    Invoice,
    InvoiceLine,
    InvoiceStatusChoices,
    Unit,
)
from netbox_contract.tests.helpers import make_contract, make_invoice, make_line, monthly


def lines_of(contract):
    return list(ContractLine.objects.filter(contract=contract).select_related('unit').order_by('pk'))


class ConversionTestCase(TestCase):
    def test_monthly_cost(self):
        """Scenario 1."""
        contract = make_contract(mrc=Decimal(100))
        convert_legacy_data()
        (line,) = lines_of(contract)
        self.assertEqual(line.unit.billing_method, BillingMethodChoices.RECURRING)
        self.assertEqual(line.unit.months, 1)
        self.assertEqual(line.unit_price, Decimal(100))
        self.assertEqual(line.quantity, 1)
        self.assertFalse(line.invoiced_at_conversion)

    def test_yearly_cost(self):
        """Scenario 2."""
        contract = make_contract(yrc=Decimal(1200))
        convert_legacy_data()
        (line,) = lines_of(contract)
        self.assertEqual(line.unit.billing_method, BillingMethodChoices.RECURRING)
        self.assertEqual(line.unit.months, 12)
        self.assertEqual(line.unit_price, Decimal(1200))

    def test_one_time_cost(self):
        """Scenario 3."""
        contract = make_contract(nrc=Decimal(500))
        convert_legacy_data()
        (line,) = lines_of(contract)
        self.assertEqual(line.unit.billing_method, BillingMethodChoices.ONE_TIME)
        self.assertIsNone(line.unit.months)
        self.assertEqual(line.unit_price, Decimal(500))

    def test_recurring_and_one_time_costs(self):
        contract = make_contract(mrc=Decimal(100), nrc=Decimal(500))
        convert_legacy_data()
        methods = sorted(line.unit.billing_method for line in lines_of(contract))
        self.assertEqual(methods, [BillingMethodChoices.ONE_TIME, BillingMethodChoices.RECURRING])

    def test_no_costs_no_lines(self):
        """Scenario 6."""
        contract = make_contract()
        convert_legacy_data()
        self.assertEqual(lines_of(contract), [])

    def test_both_monthly_and_yearly_yearly_wins(self):
        contract = make_contract(mrc=Decimal(100), yrc=Decimal(1000))
        report = convert_legacy_data()
        (line,) = lines_of(contract)
        self.assertEqual(line.unit.months, 12)
        self.assertEqual(line.unit_price, Decimal(1000))
        self.assertTrue(any(contract.name in message for message in report.messages))

    def test_lines_take_contract_dates_and_currency(self):
        contract = make_contract(currency='eur', start_date=date(2024, 3, 1), end_date=None, mrc=Decimal(10))
        convert_legacy_data()
        (line,) = lines_of(contract)
        self.assertEqual(line.currency, 'eur')
        self.assertEqual(line.start_date, date(2024, 3, 1))
        self.assertIsNone(line.end_date)

    def test_contracts_stay_billable(self):
        contract = make_contract(mrc=Decimal(10))
        convert_legacy_data()
        contract.refresh_from_db()
        self.assertTrue(contract.billable)

    def test_existing_non_billable_choice_is_kept(self):
        contract = make_contract(mrc=Decimal(10), billable=False)
        convert_legacy_data()
        contract.refresh_from_db()
        self.assertFalse(contract.billable)

    def test_deprecated_fields_are_kept(self):
        contract = make_contract(mrc=Decimal(100), nrc=Decimal(50))
        convert_legacy_data()
        contract.refresh_from_db()
        self.assertEqual(contract.mrc, Decimal(100))
        self.assertEqual(contract.nrc, Decimal(50))


class TemplateConversionTestCase(TestCase):
    def setUp(self):
        self.contract = make_contract(mrc=Decimal(100), invoice_frequency=1)
        self.dimensions = [
            AccountingDimension.objects.create(name='account', value='A1'),
            AccountingDimension.objects.create(name='department', value='IT'),
            AccountingDimension.objects.create(name='account', value='A2'),
        ]
        self.template = Invoice.objects.create(
            number='_invoice_template_Contract', template=True, amount=Decimal(100), currency='usd'
        )
        self.template.contracts.add(self.contract)
        first = InvoiceLine.objects.create(invoice=self.template, amount=Decimal(60), currency='usd')
        first.accounting_dimensions.set(self.dimensions[:2])
        second = InvoiceLine.objects.create(invoice=self.template, amount=Decimal(40), currency='usd')
        second.accounting_dimensions.set(self.dimensions[2:])

    def test_template_lines_become_recurring_lines(self):
        """Scenario 4: dimensions copied, no separate mrc line."""
        convert_legacy_data()
        lines = lines_of(self.contract)
        self.assertEqual(len(lines), 2)
        self.assertEqual([line.unit_price for line in lines], [Decimal(60), Decimal(40)])
        for line in lines:
            self.assertEqual(line.unit.billing_method, BillingMethodChoices.RECURRING)
            self.assertEqual(line.unit.months, 1)
        self.assertEqual(
            sorted(d.pk for d in lines[0].accounting_dimensions.all()), sorted(d.pk for d in self.dimensions[:2])
        )
        self.assertEqual([d.pk for d in lines[1].accounting_dimensions.all()], [self.dimensions[2].pk])

    def test_template_and_its_lines_are_kept(self):
        """Scenario 5: template invoices are kept and unchanged."""
        convert_legacy_data()
        self.template.refresh_from_db()
        self.assertTrue(self.template.template)
        self.assertEqual(self.template.invoicelines.count(), 2)
        self.assertEqual(self.template.total_invoicelines_amount, Decimal(100))

    def test_template_frequency_gives_the_unit(self):
        self.contract.invoice_frequency = 3
        self.contract.mrc = Decimal(100 / 3).quantize(Decimal('0.01'))
        self.contract.save()
        convert_legacy_data()
        lines = lines_of(self.contract)
        self.assertEqual({line.unit.months for line in lines}, {3})

    def test_template_total_differing_from_recurring_cost_is_reported(self):
        self.contract.mrc = Decimal(120)
        self.contract.save()
        report = convert_legacy_data()
        lines = lines_of(self.contract)
        self.assertEqual(sum(line.unit_price for line in lines), Decimal(100))
        self.assertTrue(any(self.contract.name in message and '120' in message for message in report.messages))

    def test_template_without_lines_uses_the_recurring_cost(self):
        self.template.invoicelines.all().delete()
        convert_legacy_data()
        (line,) = lines_of(self.contract)
        self.assertEqual(line.unit_price, Decimal(100))


class ConversionSafetyTestCase(TestCase):
    def test_invoices_and_invoice_lines_unchanged(self):
        """Scenario 5."""
        contract = make_contract(mrc=Decimal(100), nrc=Decimal(500))
        invoice = make_invoice(contract, amount=100)
        InvoiceLine.objects.create(invoice=invoice, amount=Decimal(100), currency='usd')
        before = list(Invoice.objects.values()), list(InvoiceLine.objects.values())
        convert_legacy_data()
        self.assertEqual((list(Invoice.objects.values()), list(InvoiceLine.objects.values())), before)

    def test_running_twice_creates_no_duplicate(self):
        """FR-016."""
        make_contract(name='A', mrc=Decimal(100), nrc=Decimal(10))
        make_contract(name='B', yrc=Decimal(1000))
        first = convert_legacy_data()
        lines, units = ContractLine.objects.count(), Unit.objects.count()
        second = convert_legacy_data()
        self.assertEqual(ContractLine.objects.count(), lines)
        self.assertEqual(Unit.objects.count(), units)
        self.assertEqual(first.lines_created, 3)
        self.assertEqual(second.lines_created, 0)

    def test_units_are_found_by_name(self):
        existing = monthly()
        contract = make_contract(mrc=Decimal(100))
        convert_legacy_data()
        (line,) = lines_of(contract)
        self.assertEqual(line.unit, existing)

    def test_existing_unit_with_other_meaning_is_not_reused(self):
        Unit.objects.create(name='Monthly', billing_method=BillingMethodChoices.USAGE)
        contract = make_contract(mrc=Decimal(100))
        report = convert_legacy_data()
        (line,) = lines_of(contract)
        self.assertEqual(line.unit.billing_method, BillingMethodChoices.RECURRING)
        self.assertEqual(line.unit.months, 1)
        self.assertTrue(report.messages)
        convert_legacy_data()
        self.assertEqual(Unit.objects.filter(billing_method=BillingMethodChoices.RECURRING, months=1).count(), 1)

    def test_contracts_with_lines_are_skipped(self):
        contract = make_contract(mrc=Decimal(100))
        make_line(contract, monthly(), 80, description='Already there')
        report = convert_legacy_data()
        self.assertEqual([line.description for line in lines_of(contract)], ['Already there'])
        self.assertEqual(report.skipped, 1)

    def test_contract_with_invoices_is_converted(self):
        """The lock of FR-029 does not apply to the conversion, but applies to the converted lines."""
        contract = make_contract(mrc=Decimal(100))
        make_invoice(contract, amount=100)
        convert_legacy_data()
        (line,) = lines_of(contract)
        self.assertIsNotNone(line.lock_message())


class InvoicedAtConversionTestCase(TestCase):
    def test_flag_set_when_a_posted_invoice_exists(self):
        contract = make_contract(nrc=Decimal(500), mrc=Decimal(100))
        make_invoice(contract, amount=100, status=InvoiceStatusChoices.STATUS_POSTED)
        convert_legacy_data()
        by_method = {line.unit.billing_method: line for line in lines_of(contract)}
        self.assertTrue(by_method[BillingMethodChoices.ONE_TIME].invoiced_at_conversion)
        self.assertFalse(by_method[BillingMethodChoices.RECURRING].invoiced_at_conversion)

    def test_flag_not_set_without_posted_invoice(self):
        for status in (None, InvoiceStatusChoices.STATUS_DRAFT, InvoiceStatusChoices.STATUS_CANCELED):
            with self.subTest(status=status):
                contract = make_contract(name=f'Contract {status}', nrc=Decimal(500))
                if status:
                    make_invoice(contract, amount=100, status=status)
                convert_legacy_data()
                (line,) = lines_of(contract)
                self.assertFalse(line.invoiced_at_conversion)

    def test_template_does_not_count_as_posted_invoice(self):
        contract = make_contract(nrc=Decimal(500))
        make_invoice(contract, amount=0, template=True, period_start=None, period_end=None)
        convert_legacy_data()
        (line,) = lines_of(contract)
        self.assertFalse(line.invoiced_at_conversion)


class ConversionCommandTestCase(TestCase):
    def test_command_prints_the_report(self):
        make_contract(name='Legacy', mrc=Decimal(100), yrc=Decimal(1000))
        out = StringIO()
        call_command('convert_contract_lines', stdout=out)
        self.assertIn('Legacy', out.getvalue())
        self.assertEqual(ContractLine.objects.count(), 1)
        call_command('convert_contract_lines', stdout=StringIO())
        self.assertEqual(ContractLine.objects.count(), 1)


class HistoricalModelsTestCase(TestCase):
    """The data migration runs the conversion with the historical models of the migration state."""

    def test_conversion_with_historical_models(self):
        from django.db import connection
        from django.db.migrations.executor import MigrationExecutor

        contract = make_contract(mrc=Decimal(100), nrc=Decimal(5))
        executor = MigrationExecutor(connection)
        state = executor.loader.project_state(('netbox_contract', '0044_units_contract_lines_billable'))
        report = convert_legacy_data(state.apps)
        self.assertEqual(report.lines_created, 2)
        self.assertEqual(Contract.objects.get(pk=contract.pk).lines.count(), 2)
