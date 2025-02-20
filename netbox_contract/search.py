from netbox.search import SearchIndex

from .models import AccountingDimension, Contract, ContractType, Invoice, InvoiceLine, ServiceProvider


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


indexes = [
    ServiceProviderIndex,
    ContractIndex,
    InvoiceIndex,
    InvoiceLineIndex,
    AccountingDimensionIndex,
    ContractTypeIndex,
]
