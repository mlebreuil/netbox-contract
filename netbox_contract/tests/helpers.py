"""Factories shared by the test modules of the contract lines feature."""

from datetime import date
from decimal import Decimal

from circuits.models import Provider
from django.contrib.contenttypes.models import ContentType
from users.models import ObjectPermission
from utilities.permissions import resolve_permission_type

from netbox_contract.models import (
    BillingMethodChoices,
    Contract,
    ContractLine,
    Invoice,
    InvoiceLine,
    InvoiceStatusChoices,
    StatusChoices,
    Unit,
)

START = date(2025, 1, 1)
END = date(2025, 12, 31)


def make_provider():
    return Provider.objects.get_or_create(name='Provider A', slug='provider-a')[0]


def make_contract(name='Contract', currency='usd', start_date=START, end_date=END, **kwargs):
    provider = make_provider()
    kwargs.setdefault('invoice_frequency', 1)
    return Contract.objects.create(
        name=name,
        external_party_object_type=ContentType.objects.get_for_model(Provider),
        external_party_object_id=provider.pk,
        internal_party='default',
        status=StatusChoices.STATUS_ACTIVE,
        start_date=start_date,
        end_date=end_date,
        currency=currency,
        **kwargs,
    )


def make_unit(name, billing_method, months=None):
    return Unit.objects.get_or_create(name=name, defaults={'billing_method': billing_method, 'months': months})[0]


def monthly():
    return make_unit('Monthly', BillingMethodChoices.RECURRING, 1)


def yearly():
    return make_unit('Yearly', BillingMethodChoices.RECURRING, 12)


def one_time():
    return make_unit('One-time', BillingMethodChoices.ONE_TIME)


def usage():
    return make_unit('Usage', BillingMethodChoices.USAGE)


def make_line(contract, unit, unit_price, quantity=1, description='Line', **kwargs):
    kwargs.setdefault('currency', contract.currency)
    kwargs.setdefault('start_date', contract.start_date)
    kwargs.setdefault('end_date', contract.end_date)
    return ContractLine.objects.create(
        contract=contract,
        unit=unit,
        unit_price=Decimal(unit_price),
        quantity=Decimal(quantity),
        description=description,
        **kwargs,
    )


def make_invoice(contract=None, number='INV', status=InvoiceStatusChoices.STATUS_POSTED, amount=0,
                 period_start=date(2025, 1, 1), period_end=date(2025, 1, 31), currency=None, **kwargs):
    invoice = Invoice.objects.create(
        number=number,
        status=status,
        amount=Decimal(amount),
        period_start=period_start,
        period_end=period_end,
        currency=currency or (contract.currency if contract else 'usd'),
        **kwargs,
    )
    if contract is not None:
        invoice.contracts.add(contract)
    return invoice


def make_invoice_line(invoice, amount=None, contract_line=None, quantity=None, **kwargs):
    line = InvoiceLine(
        invoice=invoice,
        amount=None if amount is None else Decimal(amount),
        contract_line=contract_line,
        quantity=None if quantity is None else Decimal(quantity),
        currency=kwargs.pop('currency', invoice.currency),
        **kwargs,
    )
    line.save()
    return line


def add_constrained_permission(user, name, constraints):
    """Give the user a permission (<app>.<action>_<model>) limited by object constraints, as an ObjectPermission."""
    object_type, action = resolve_permission_type(name)
    permission = ObjectPermission.objects.create(
        name=f'{name} {constraints}'[:100], actions=[action], constraints=constraints
    )
    permission.users.add(user)
    permission.object_types.add(object_type)
    return permission


def invoiced_recurring_line(name='Invoiced contract'):
    """A monthly line on a contract with a Posted invoice: locked, and amendable."""
    contract = make_contract(name=name)
    line = make_line(contract, monthly(), 100, description='Monthly fee')
    make_invoice(contract, number=f'{name} JAN', amount=100)
    return line


def contract_page_with_lines(client, contract):
    """
    The contract page as a browser shows it: since #309 its contract lines table is loaded through HTMX from the
    contract line list, so the content of that table is appended to the page.
    """
    from django.urls import reverse

    page = client.get(contract.get_absolute_url())
    assert page.status_code == 200, page.status_code
    lines = client.get(
        f"{reverse('plugins:netbox_contract:contractline_list')}?embedded=True&contract_id={contract.pk}"
        '&exclude_columns=contract'
    )
    return page.content.decode() + (lines.content.decode() if lines.status_code == 200 else '')
