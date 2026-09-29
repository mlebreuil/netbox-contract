"""
Conversion of the deprecated contract costs and invoice templates into contract lines (research D8).

Used by the data migration 0045 (with the historical models of the migration) and by the
`convert_contract_lines` management command (with the current models). The conversion is
idempotent: a contract that already has contract lines is skipped and units are found by name.
Invoices, invoice lines and the deprecated fields are never changed; every judgement call is
written to the returned report.
"""

from dataclasses import dataclass, field
from decimal import Decimal

ONE_TIME = 'one_time'
RECURRING = 'recurring'
POSTED = 'posted'

UNIT_DEFINITIONS = {
    'one_time': ('One-time', ONE_TIME, None),
    1: ('Monthly', RECURRING, 1),
    12: ('Yearly', RECURRING, 12),
}


@dataclass
class ConversionReport:
    converted: int = 0
    skipped: int = 0
    lines_created: int = 0
    units_created: list = field(default_factory=list)
    messages: list = field(default_factory=list)

    def __str__(self):
        lines = [
            f'Contracts converted: {self.converted}',
            f'Contracts skipped (they already have contract lines): {self.skipped}',
            f'Contract lines created: {self.lines_created}',
        ]
        if self.units_created:
            lines.append(f'Units created: {", ".join(self.units_created)}')
        lines.extend(self.messages)
        return '\n'.join(lines)


class _Converter:
    def __init__(self, apps):
        if apps is None:
            from django.apps import apps
        self.Contract = apps.get_model('netbox_contract', 'Contract')
        self.ContractLine = apps.get_model('netbox_contract', 'ContractLine')
        self.Invoice = apps.get_model('netbox_contract', 'Invoice')
        self.InvoiceLine = apps.get_model('netbox_contract', 'InvoiceLine')
        self.Unit = apps.get_model('netbox_contract', 'Unit')
        self.report = ConversionReport()
        self._units = {}

    def unit(self, key):
        """Find or create a unit by name; a unit of that name with another meaning is not reused."""
        if key in self._units:
            return self._units[key]
        if key in UNIT_DEFINITIONS:
            name, billing_method, months = UNIT_DEFINITIONS[key]
        else:
            name, billing_method, months = f'Every {key} months', RECURRING, key

        unit = self.Unit.objects.filter(name=name).first()
        if unit is not None and (unit.billing_method, unit.months) != (billing_method, months):
            self.report.messages.append(
                f'The existing unit "{name}" is not a {billing_method} unit of {months or "no"} months; '
                f'the unit "{name} (converted)" is used instead.'
            )
            name = f'{name} (converted)'
            unit = self.Unit.objects.filter(name=name).first()
        if unit is None:
            unit = self.Unit.objects.create(name=name, billing_method=billing_method, months=months)
            self.report.units_created.append(name)
        self._units[key] = unit
        return unit

    def add_line(self, contract, unit, unit_price, description, dimensions=(), comments='', invoiced=False):
        line = self.ContractLine.objects.create(
            contract=contract,
            description=description,
            quantity=Decimal(1),
            unit_price=unit_price,
            unit=unit,
            currency=contract.currency,
            start_date=contract.start_date,
            end_date=contract.end_date,
            comments=comments,
            invoiced_at_conversion=invoiced,
        )
        if dimensions:
            line.accounting_dimensions.set(dimensions)
        self.report.lines_created += 1
        return line

    def convert(self):
        for contract in self.Contract.objects.order_by('pk'):
            if self.ContractLine.objects.filter(contract=contract).exists():
                self.report.skipped += 1
                continue
            if self.convert_contract(contract):
                self.report.converted += 1
        return self.report

    def convert_contract(self, contract):
        created = self.report.lines_created
        frequency = contract.invoice_frequency or 1
        if frequency < 1:
            self.report.messages.append(
                f'Contract "{contract.name}" (id {contract.pk}): invoice frequency {contract.invoice_frequency} '
                f'is not valid, 1 month is used for its invoice template lines.'
            )
            frequency = 1

        if contract.mrc and contract.yrc:
            self.report.messages.append(
                f'Contract "{contract.name}" (id {contract.pk}) has both a monthly ({contract.mrc}) and a yearly '
                f'({contract.yrc}) recurring cost; the yearly cost is used.'
            )
        if contract.yrc:
            recurring = ('yearly', contract.yrc, contract.yrc * frequency / 12)
        elif contract.mrc:
            recurring = ('monthly', contract.mrc, contract.mrc * frequency)
        else:
            recurring = None

        template = self.Invoice.objects.filter(template=True, contracts=contract).order_by('pk').first()
        template_lines = (
            list(self.InvoiceLine.objects.filter(invoice=template).order_by('pk')) if template else []
        )

        if template_lines:
            unit = self.unit(frequency)
            total = sum((line.amount for line in template_lines), Decimal(0))
            for line in template_lines:
                self.add_line(
                    contract,
                    unit,
                    line.amount,
                    'Migrated from invoice template',
                    dimensions=list(line.accounting_dimensions.all()),
                    comments=line.comments,
                )
            if recurring and recurring[2].quantize(Decimal('0.01')) != total:
                self.report.messages.append(
                    f'Contract "{contract.name}" (id {contract.pk}): the invoice template "{template.number}" '
                    f'totals {total} per {frequency} month(s) while the {recurring[0]} recurring cost '
                    f'({recurring[1]}) gives {recurring[2].quantize(Decimal("0.01"))}; the template lines were '
                    f'used and the difference was not added.'
                )
        elif recurring:
            kind, price, _ = recurring
            if kind == 'yearly':
                self.add_line(contract, self.unit(12), price, 'Yearly recurring cost')
            else:
                self.add_line(contract, self.unit(1), price, 'Monthly recurring cost')

        if contract.nrc:
            posted = (
                self.Invoice.objects.filter(contracts=contract, status=POSTED).exclude(template=True).exists()
            )
            self.add_line(contract, self.unit('one_time'), contract.nrc, 'One-time cost', invoiced=posted)

        return self.report.lines_created > created


def convert_legacy_data(apps=None):
    """
    Create the contract lines of every contract that has none, from its deprecated costs and its
    invoice template. Returns a ConversionReport. Pass the `apps` of a migration to use historical models.
    """
    return _Converter(apps).convert()
