from netbox.filtersets import NetBoxModelFilterSet
from .models import Contract,Invoice,ServiceProvider

class ContractFilterSet(NetBoxModelFilterSet):

    class Meta:
        model = Contract
        fields = ('id', 'external_partie', 'internal_partie', 'status','circuit')

class InvoiceFilterSet(NetBoxModelFilterSet):

    class Meta:
        model = Invoice
        fields = ('id', 'contracts')

class ServiceProviderFilterSet(NetBoxModelFilterSet):

    class Meta:
        model = ServiceProvider
        fields = ('id','name')
