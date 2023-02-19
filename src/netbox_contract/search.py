from netbox.search import SearchIndex, register_search
from .models import ServiceProvider, Contract, Invoice

@register_search
class ServiceProviderIndex(SearchIndex):
    model = ServiceProvider
    fields = (
        ('name', 100),
        ('comments', 5000),
    )

@register_search
class ContractIndex(SearchIndex):
    model = Contract
    fields = (
        ('name', 100),
        ('comments', 5000),
    )

@register_search
class InvoiceIndex(SearchIndex):
    model = Invoice
    fields = (
        ('number', 100),
        ('comments', 5000),
    )
