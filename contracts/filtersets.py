from netbox.filtersets import NetBoxModelFilterSet
from .models import Contract,Invoice

class ContractFilterSet(NetBoxModelFilterSet):

    class Meta:
        model = Contract
        fields = ('id', 'external_partie', 'internal_partie', 'circuit')

class InvoiceFilterSet(NetBoxModelFilterSet):

    class Meta:
        model = Invoice
        fields = ('id', 'contract',)
