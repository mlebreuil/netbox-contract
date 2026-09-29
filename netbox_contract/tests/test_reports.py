"""Currency mismatch report (FR-012, SC-003, user story 4 scenario 7)."""

from django.test import TestCase

from netbox_contract.models import Contract, ContractLine, Invoice, InvoiceLine
from netbox_contract.reports import find_currency_mismatches
from netbox_contract.tests.helpers import make_contract, make_invoice, make_invoice_line, make_line, monthly


class CurrencyReportTestCase(TestCase):
    def test_clean_data_gives_nothing(self):
        parent = make_contract(name='Parent', currency='eur')
        child = make_contract(name='Child', currency='eur', parent=parent, billable=False)
        make_contract(name='Billable child', currency='chf', parent=parent)
        make_line(child, monthly(), 10)
        invoice = make_invoice(parent, amount=100)
        make_invoice_line(invoice, amount=10)
        make_invoice(None, number='No contract', amount=0, currency='usd')
        self.assertEqual(find_currency_mismatches(), [])

    def test_each_kind_of_mismatch_is_listed(self):
        parent = make_contract(name='Parent', currency='eur')
        child = make_contract(name='Child', currency='chf', parent=parent, billable=False)
        line = make_line(parent, monthly(), 10)
        ContractLine.objects.filter(pk=line.pk).update(currency='usd')
        invoice = make_invoice(parent, number='INV-1', amount=100, currency='chf')
        invoice_line = make_invoice_line(invoice, amount=10, currency='usd')

        mismatches = find_currency_mismatches()
        found = {(m.kind, m.object.pk, m.expected, m.found) for m in mismatches}
        self.assertEqual(
            found,
            {
                ('contract line', line.pk, 'eur', 'usd'),
                ('invoice', invoice.pk, 'eur', 'chf'),
                ('invoice line', invoice_line.pk, 'chf', 'usd'),
                ('non-billable child contract', child.pk, 'eur', 'chf'),
            },
        )
        for mismatch in mismatches:
            self.assertEqual(mismatch.url, mismatch.object.get_absolute_url())

    def test_report_alters_nothing(self):
        parent = make_contract(name='Parent', currency='eur')
        make_contract(name='Child', currency='chf', parent=parent, billable=False)
        invoice = make_invoice(parent, number='INV-1', amount=100, currency='chf')
        make_invoice_line(invoice, amount=10, currency='usd')
        snapshot = [
            list(model.objects.order_by('pk').values_list('pk', 'currency'))
            for model in (Contract, ContractLine, Invoice, InvoiceLine)
        ]
        find_currency_mismatches()
        self.assertEqual(
            [
                list(model.objects.order_by('pk').values_list('pk', 'currency'))
                for model in (Contract, ContractLine, Invoice, InvoiceLine)
            ],
            snapshot,
        )

    def test_multi_contract_invoice(self):
        eur = make_contract(name='EUR', currency='eur')
        chf = make_contract(name='CHF', currency='chf')
        invoice = make_invoice(eur, number='OLD', amount=0, currency='eur')
        invoice.contracts.add(chf)
        (mismatch,) = find_currency_mismatches()
        self.assertEqual((mismatch.kind, mismatch.expected, mismatch.found), ('invoice', 'chf', 'eur'))

    def test_script_lists_the_mismatches(self):
        import importlib.util
        from pathlib import Path

        path = Path(__file__).resolve().parents[2] / 'scripts' / 'netbox-contract.py'
        if not path.exists():
            self.skipTest('scripts/netbox-contract.py is only available in a source checkout')
        spec = importlib.util.spec_from_file_location('netbox_contract_scripts', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertFalse(hasattr(module, 'create_invoice_template'))
        self.assertFalse(hasattr(module, 'create_invoice_lines'))

        parent = make_contract(name='Parent', currency='eur')
        make_contract(name='Child', currency='chf', parent=parent, billable=False)
        script = module.report_currency_mismatches()
        script.messages = []
        script.log_warning = lambda message, obj=None: script.messages.append((message, obj))
        script.log_success = lambda message, obj=None: script.messages.append((message, obj))
        script.run({}, commit=False)
        self.assertEqual(len([m for m in script.messages if m[1] is not None]), 1)
        self.assertIn('CHF', script.messages[0][0].upper())
