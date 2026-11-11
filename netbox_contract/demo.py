"""
Demo data for development: named scenarios covering the contract lines feature.

Used by the `create_demo_data` management command. Every object created here carries the `netbox-contract-demo` tag,
which is what makes the command idempotent (a scenario whose contract already exists is skipped) and what
`reset_demo_data()` deletes. NetBox's own demo objects (devices, circuits, sites) are looked up by criteria, never by
id, and are only assigned to contracts, never changed.

The invoices are built with the services the screens use (`generate_invoice_lines`, `amend_contract_line`), so the
amounts are the ones a user would get.
"""

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from extras.models import Tag

from . import calculations
from .models import (
    AccountingDimension,
    AccountingDimensionStatusChoices,
    BillingMethodChoices,
    Contract,
    ContractAssignment,
    ContractLine,
    ContractType,
    InternalEntityChoices,
    Invoice,
    InvoiceLine,
    InvoiceStatusChoices,
    ServiceProvider,
    StatusChoices,
    Unit,
)
from .services.amendments import amend_contract_line
from .services.invoicing import generate_invoice_lines, lines_to_generate

TAG_NAME = 'netbox-contract demo'
TAG_SLUG = 'netbox-contract-demo'
TAG_COLOR = 'ff9800'

DRAFT = InvoiceStatusChoices.STATUS_DRAFT
POSTED = InvoiceStatusChoices.STATUS_POSTED
CANCELED = InvoiceStatusChoices.STATUS_CANCELED


@dataclass
class DemoReport:
    created: list = field(default_factory=list)
    skipped: list = field(default_factory=list)
    notes: list = field(default_factory=list)
    deleted: dict = field(default_factory=dict)

    def __str__(self):
        lines = []
        if self.deleted:
            lines.append('Deleted: ' + ', '.join(f'{count} {name}' for name, count in self.deleted.items()))
        lines.extend(f'Created: {name}' for name in self.created)
        lines.extend(f'Skipped (already there): {name}' for name in self.skipped)
        lines.extend(self.notes)
        return '\n'.join(lines)


class Demo:
    """The state shared by the scenarios: the tag, the shared objects and the report."""

    def __init__(self, report):
        self.report = report
        self.tag = Tag.objects.get_or_create(
            slug=TAG_SLUG, defaults={'name': TAG_NAME, 'color': TAG_COLOR}
        )[0]
        self.units = {}
        self.dimensions = {}
        self.contract_types = {}
        self.service_provider = None
        self.provider = None
        self.device = self.circuit = self.site = None

    def tagged(self, obj):
        obj.tags.add(self.tag)
        return obj

    # Shared objects

    def get_or_create(self, model, lookup, **defaults):
        obj = model.objects.filter(tags=self.tag, **lookup).first()
        if obj is None:
            obj = self.tagged(model.objects.create(**lookup, **defaults))
        return obj

    def unit(self, name, billing_method, months=None, description=''):
        return self.get_or_create(
            Unit, {'name': name}, billing_method=billing_method, months=months, description=description
        )

    def dimension(self, name, value):
        return self.get_or_create(
            AccountingDimension, {'name': name, 'value': value}, status=AccountingDimensionStatusChoices.STATUS_ACTIVE
        )

    def contract_type(self, name, color):
        return self.get_or_create(ContractType, {'name': name}, color=color)

    def external_party(self):
        """The circuit provider of NetBox's demo data, else the demo service provider."""
        return self.provider or self.service_provider

    # Records

    def contract(self, name, **kwargs):
        """A new demo contract, or None when it exists: its scenario is then skipped."""
        if Contract.objects.filter(name=name, tags=self.tag).exists():
            self.report.skipped.append(name)
            return None
        party = kwargs.pop('external_party', None) or self.external_party()
        values = {
            'internal_party': InternalEntityChoices.ENTITY,
            'status': StatusChoices.STATUS_ACTIVE,
            'start_date': date(2025, 1, 1),
            'end_date': date(2025, 12, 31),
            'currency': 'usd',
            'invoice_frequency': 1,
            'contract_type': self.contract_types.get('telecom'),
            'external_party_object_type': ContentType.objects.get_for_model(party),
            'external_party_object_id': party.pk,
        }
        values.update(kwargs)
        contract = self.tagged(Contract.objects.create(name=name, **values))
        self.report.created.append(name)
        return contract

    def line(self, contract, unit, unit_price, quantity=1, description='', dimensions=(), **kwargs):
        line = ContractLine.objects.create(
            contract=contract,
            unit=unit,
            unit_price=Decimal(unit_price),
            quantity=Decimal(quantity),
            description=description,
            currency=contract.currency,
            start_date=kwargs.pop('start_date', contract.start_date),
            end_date=kwargs.pop('end_date', contract.end_date),
            **kwargs,
        )
        self.tagged(line)
        if dimensions:
            line.accounting_dimensions.set(dimensions)
        return line

    def invoice(self, contract, number, period_start, period_end, status=POSTED, overrides=None):
        """
        An invoice for the period, with the lines the new-invoice screen generates, then moved to `status`
        (it is created as a Draft, as on the screen). `overrides` gives the quantity of usage-based lines
        and the quantity or unit price typed in the preview.
        """
        planned = lines_to_generate(contract, period_start, period_end, overrides)
        amount = calculations.round_amount(sum((line.amount for line in planned), Decimal(0)))
        invoice = Invoice.objects.create(
            number=number,
            status=DRAFT,
            date=period_end,
            period_start=period_start,
            period_end=period_end,
            currency=contract.currency,
            amount=amount,
        )
        self.tagged(invoice)
        invoice.contracts.add(contract)
        for line in generate_invoice_lines(invoice, overrides=overrides):
            self.tagged(line)
        if status != DRAFT:
            invoice.status = status
            invoice.save()
        return invoice


# Scenarios: each creates one contract and what hangs on it, and is skipped when the contract exists


def recurring_lines(demo):
    """Monthly and yearly recurring lines, with accounting dimensions; January and February posted, March draft."""
    contract = demo.contract(
        'Demo: recurring lines', external_reference='DEMO-REC', tenant=getattr(demo.circuit, 'tenant', None)
    )
    if contract is None:
        return None
    demo.line(contract, demo.units['monthly'], '1000', description='Internet access 1 Gbps',
              dimensions=[demo.dimensions['account-1'], demo.dimensions['cost-center-1']])
    demo.line(contract, demo.units['monthly'], '45.50', quantity=4, description='Static IP addresses',
              dimensions=[demo.dimensions['account-2']])
    demo.line(contract, demo.units['yearly'], '1200', description='Support plan')
    demo.invoice(contract, 'DEMO-REC-2025-01', date(2025, 1, 1), date(2025, 1, 31), POSTED)
    demo.invoice(contract, 'DEMO-REC-2025-02', date(2025, 2, 1), date(2025, 2, 28), POSTED)
    demo.invoice(contract, 'DEMO-REC-2025-03', date(2025, 3, 1), date(2025, 3, 31), DRAFT)
    return contract


def quarterly_billing(demo):
    """An invoice frequency of 3 months, a quarterly unit and a six-month unit."""
    contract = demo.contract('Demo: quarterly billing', invoice_frequency=3, currency='eur')
    if contract is None:
        return None
    demo.line(contract, demo.units['quarterly'], '750', description='Colocation, billed per quarter')
    demo.line(contract, demo.units['semiannual'], '2400', description='Hardware warranty')
    demo.invoice(contract, 'DEMO-QTR-2025-Q1', date(2025, 1, 1), date(2025, 3, 31), POSTED)
    demo.invoice(contract, 'DEMO-QTR-2025-Q2', date(2025, 4, 1), date(2025, 6, 30), DRAFT)
    return contract


def one_time_and_usage(demo):
    """One-time lines invoiced in two parts (the second invoice gets what remains) and a usage-based line."""
    contract = demo.contract('Demo: one-time and usage', external_reference='DEMO-OTU')
    if contract is None:
        return None
    install = demo.line(contract, demo.units['one-time'], '250', quantity=10, description='Router installation',
                        dimensions=[demo.dimensions['account-1']])
    demo.line(contract, demo.units['usage'], '0.08', description='Traffic (GB)')
    demo.invoice(contract, 'DEMO-OTU-2025-01', date(2025, 1, 1), date(2025, 1, 31), POSTED,
                 overrides={install.pk: {'quantity': Decimal(4)}})
    usage_line = contract.lines.get(unit=demo.units['usage'])
    demo.invoice(contract, 'DEMO-OTU-2025-02', date(2025, 2, 1), date(2025, 2, 28), POSTED,
                 overrides={usage_line.pk: {'quantity': Decimal('1250.5')}})
    demo.invoice(contract, 'DEMO-OTU-2025-03', date(2025, 3, 1), date(2025, 3, 31), DRAFT,
                 overrides={usage_line.pk: {'quantity': Decimal('980')}})
    return contract


def open_ended(demo):
    """A contract with no end date: its line has none either."""
    contract = demo.contract('Demo: open-ended', end_date=None, external_reference='DEMO-OPEN')
    if contract is None:
        return None
    demo.line(contract, demo.units['monthly'], '300', description='Managed firewall', end_date=None)
    demo.invoice(contract, 'DEMO-OPEN-2025-01', date(2025, 1, 1), date(2025, 1, 31), POSTED)
    demo.invoice(contract, 'DEMO-OPEN-2025-02', date(2025, 2, 1), date(2025, 2, 28), DRAFT)
    return contract


def hierarchy(demo):
    """
    A billable parent with a non-billable child (invoiced with the parent) and a billable child (invoiced on its own),
    which has its own non-billable child.
    """
    parent = demo.contract('Demo: hierarchy, parent', external_reference='DEMO-PARENT')
    if parent is None:
        return None
    demo.line(parent, demo.units['monthly'], '500', description='Framework fee')
    included = demo.contract('Demo: hierarchy, child (non-billable)', parent=parent, billable=False)
    demo.line(included, demo.units['monthly'], '120', description='Site A service')
    own = demo.contract('Demo: hierarchy, child (billable)', parent=parent)
    demo.line(own, demo.units['monthly'], '200', description='Site B service')
    grandchild = demo.contract('Demo: hierarchy, grandchild (non-billable)', parent=own, billable=False)
    demo.line(grandchild, demo.units['monthly'], '35', description='Site B backup line')
    demo.invoice(parent, 'DEMO-PARENT-2025-01', date(2025, 1, 1), date(2025, 1, 31), POSTED)
    demo.invoice(own, 'DEMO-CHILD-2025-01', date(2025, 1, 1), date(2025, 1, 31), POSTED)
    return parent


def amendments(demo):
    """A price amended from April and a quantity amended from July: each line is ended and a successor starts."""
    contract = demo.contract('Demo: amendments', external_reference='DEMO-AMEND')
    if contract is None:
        return None
    price = demo.line(contract, demo.units['monthly'], '800', description='Dedicated link')
    quantity = demo.line(contract, demo.units['monthly'], '60', quantity=5, description='Seats')
    for month, last_day in ((1, 31), (2, 28), (3, 31)):
        demo.invoice(
            contract, f'DEMO-AMEND-2025-{month:02d}', date(2025, month, 1), date(2025, month, last_day), POSTED
        )
    demo.tagged(amend_contract_line(
        price, date(2025, 4, 1), 'Price increase agreed with the provider', unit_price=Decimal(850)
    ))
    demo.invoice(contract, 'DEMO-AMEND-2025-04', date(2025, 4, 1), date(2025, 4, 30), POSTED)
    demo.tagged(amend_contract_line(quantity, date(2025, 7, 1), 'Two more seats', quantity=Decimal(7)))
    return contract


def canceled(demo):
    """A canceled contract, with a canceled invoice and a posted one."""
    contract = demo.contract(
        'Demo: canceled contract', status=StatusChoices.STATUS_CANCELED, end_date=date(2025, 6, 30)
    )
    if contract is None:
        return None
    demo.line(contract, demo.units['monthly'], '90', description='Legacy line', end_date=date(2025, 6, 30))
    demo.invoice(contract, 'DEMO-CANCEL-2025-01', date(2025, 1, 1), date(2025, 1, 31), CANCELED)
    demo.invoice(contract, 'DEMO-CANCEL-2025-02', date(2025, 2, 1), date(2025, 2, 28), POSTED)
    return contract


def numeric_edge_cases(demo):
    """Rounding, fractional quantities, proration over part-months and a leap year, and a large price."""
    contract = demo.contract(
        'Demo: numeric edge cases', currency='chf', start_date=date(2024, 1, 1), end_date=date(2025, 12, 31),
        external_reference='DEMO-NUM',
    )
    if contract is None:
        return None
    demo.line(contract, demo.units['monthly'], '33.33', quantity=3, description='Price that does not divide by 12')
    demo.line(contract, demo.units['monthly'], '0.01', description='One cent')
    demo.line(contract, demo.units['monthly'], '19.99', quantity='0.3333', description='Fractional quantity')
    demo.line(contract, demo.units['yearly'], '1234567.89', description='Large yearly price')
    demo.line(contract, demo.units['monthly'], '100', description='Starts mid-month',
              start_date=date(2025, 1, 15), end_date=date(2025, 3, 10))
    demo.line(contract, demo.units['one-time'], '0.005', quantity=1000, description='Half a cent times 1000')
    demo.invoice(contract, 'DEMO-NUM-2024-02', date(2024, 2, 1), date(2024, 2, 29), POSTED)
    demo.invoice(contract, 'DEMO-NUM-2025-01', date(2025, 1, 1), date(2025, 1, 31), POSTED)
    demo.invoice(contract, 'DEMO-NUM-2025-03', date(2025, 3, 1), date(2025, 3, 31), DRAFT)
    return contract


def legacy_data(demo):
    """
    Contracts as they were before contract lines: deprecated costs and an invoice template, and no contract line.
    `manage.py convert_contract_lines` converts them.
    """
    monthly_cost = demo.contract('Demo: legacy, monthly cost and template', mrc=Decimal(1000), nrc=Decimal(500),
                                 external_reference='DEMO-LEGACY-1')
    if monthly_cost is not None:
        _legacy_template(demo, monthly_cost, 'DEMO-LEGACY-TEMPLATE-1', Decimal(1000), 'account-1')
    yearly_cost = demo.contract('Demo: legacy, yearly cost', yrc=Decimal(1500), invoice_frequency=12,
                                external_reference='DEMO-LEGACY-2')
    if yearly_cost is not None:
        _legacy_template(demo, yearly_cost, 'DEMO-LEGACY-TEMPLATE-2', Decimal(1500), 'account-2')
    return monthly_cost or yearly_cost


def _legacy_template(demo, contract, number, amount, dimension):
    template = Invoice.objects.create(
        number=number, template=True, currency=contract.currency, amount=amount, comments='Invoice template'
    )
    demo.tagged(template)
    template.contracts.add(contract)
    line = InvoiceLine(invoice=template, currency=contract.currency, amount=amount)
    line.save()
    demo.tagged(line)
    line.accounting_dimensions.add(demo.dimensions[dimension], demo.dimensions['cost-center-1'])


def assignments(demo):
    """Assign the contracts to the NetBox demo objects found, when there are some."""
    targets = [
        ('Demo: recurring lines', demo.circuit),
        ('Demo: open-ended', demo.device),
        ('Demo: quarterly billing', demo.site),
    ]
    for name, target in targets:
        contract = Contract.objects.filter(name=name, tags=demo.tag).first()
        if contract is None or target is None:
            continue
        assignment, created = ContractAssignment.objects.get_or_create(
            contract=contract,
            content_type=ContentType.objects.get_for_model(target),
            object_id=target.pk,
        )
        if created:
            demo.tagged(assignment)
            demo.report.created.append(f'assignment of {contract.name} to {target}')


SCENARIOS = (
    recurring_lines,
    quarterly_billing,
    one_time_and_usage,
    open_ended,
    hierarchy,
    amendments,
    canceled,
    numeric_edge_cases,
    legacy_data,
)


def _find_netbox_objects(demo):
    """NetBox's demo objects, looked up by criteria: the first circuit with a tenant, device with a tenant, site."""
    from circuits.models import Circuit, Provider
    from dcim.models import Device, Site

    demo.circuit = Circuit.objects.filter(tenant__isnull=False).select_related('provider', 'tenant').order_by(
        'pk').first()
    demo.device = Device.objects.filter(tenant__isnull=False).order_by('pk').first()
    demo.site = Site.objects.order_by('pk').first()
    demo.provider = demo.circuit.provider if demo.circuit else Provider.objects.order_by('pk').first()
    if demo.circuit is None and demo.device is None and demo.site is None:
        demo.report.notes.append('No NetBox demo objects found: no contract is assigned to an object.')


def create_demo_data():
    """Create the demo scenarios that do not exist yet. Returns a DemoReport."""
    report = DemoReport()
    with transaction.atomic():
        demo = Demo(report)
        _find_netbox_objects(demo)
        demo.service_provider = demo.get_or_create(ServiceProvider, {'slug': 'demo-service-provider'},
                                                   name='Demo service provider')
        demo.contract_types['telecom'] = demo.contract_type('Demo telecom', 'blue')
        demo.units.update({
            'monthly': demo.unit('Demo monthly', BillingMethodChoices.RECURRING, 1, 'Price per month'),
            'quarterly': demo.unit('Demo quarterly', BillingMethodChoices.RECURRING, 3, 'Price per quarter'),
            'semiannual': demo.unit('Demo six months', BillingMethodChoices.RECURRING, 6, 'Price per six months'),
            'yearly': demo.unit('Demo yearly', BillingMethodChoices.RECURRING, 12, 'Price per year'),
            'one-time': demo.unit('Demo one-time', BillingMethodChoices.ONE_TIME, None, 'Billed once'),
            'usage': demo.unit('Demo usage', BillingMethodChoices.USAGE, None, 'Quantity entered on each invoice'),
        })
        demo.dimensions.update({
            'account-1': demo.dimension('account', 'demo-account-1'),
            'account-2': demo.dimension('account', 'demo-account-2'),
            'cost-center-1': demo.dimension('cost_center', 'demo-cost-center-1'),
        })
        for scenario in SCENARIOS:
            scenario(demo)
        assignments(demo)
    return report


def reset_demo_data():
    """
    Delete everything the demo created, found by its tag, and return the number of objects deleted per kind.
    Invoices are set back to Draft with a queryset update first: posted invoices are locked, which is the lock
    the demo is there to show, not an obstacle to cleaning up.
    """
    tag = Tag.objects.filter(slug=TAG_SLUG).first()
    deleted = {}
    if tag is None:
        return deleted
    with transaction.atomic():
        Invoice.objects.filter(tags=tag).update(status=DRAFT)
        for model in (
            ContractAssignment, InvoiceLine, Invoice, ContractLine, Contract, ServiceProvider, ContractType,
            AccountingDimension, Unit,
        ):
            queryset = model.objects.filter(tags=tag)
            count = queryset.count()
            if count:
                queryset.delete()
                deleted[model._meta.verbose_name_plural] = count
        tag.delete()
    return deleted
