from netbox.search import SearchIndex

from .models import (
    AccountingDimension,
    Contract,
    ContractLine,
    ContractType,
    Invoice,
    InvoiceLine,
    ServiceProvider,
    Unit,
)


class ServiceProviderIndex(SearchIndex):
    model = ServiceProvider
    fields = (
        ('name', 100),
        ('comments', 5000),
    )


class ContractIndex(SearchIndex):
    model = Contract
    fields = (
        ('name', 100),
        ('comments', 5000),
    )


class InvoiceIndex(SearchIndex):
    model = Invoice
    fields = (
        ('number', 100),
        ('comments', 5000),
    )


class InvoiceLineIndex(SearchIndex):
    model = InvoiceLine
    fields = (
        ('invoice', 100),
        ('comments', 5000),
    )


class AccountingDimensionIndex(SearchIndex):
    model = AccountingDimension
    fields = (
        ('name', 20),
        ('value', 20),
    )


class ContractTypeIndex(SearchIndex):
    model = ContractType
    fields = (
        ('name', 20),
        ('description', 20),
    )


class UnitIndex(SearchIndex):
    model = Unit
    fields = (
        ('name', 100),
        ('description', 500),
        ('comments', 5000),
    )


class ContractLineIndex(SearchIndex):
    model = ContractLine
    fields = (
        ('description', 100),
        ('comments', 5000),
    )
    display_attrs = ('contract', 'unit', 'unit_price', 'currency')


indexes = [
    ServiceProviderIndex,
    ContractIndex,
    InvoiceIndex,
    InvoiceLineIndex,
    AccountingDimensionIndex,
    ContractTypeIndex,
    UnitIndex,
    ContractLineIndex,
]
