import django_tables2 as tables

from netbox.tables import NetBoxTable
from circuits.models import Circuit
from .models import Contract, Invoice

class ContractListTable(NetBoxTable):

    name = tables.Column(
        linkify=True
    )
    circuit = tables.ManyToManyColumn()

    class Meta(NetBoxTable.Meta):
        model = Contract
        fields = ('pk', 'id', 'name', 'circuit', 'external_partie', 'internal_partie', 'comments', 'actions')
        default_columns = ('name', 'circuit')

class ContractListBottomTable(NetBoxTable):
    name = tables.Column(
        linkify=True
    )
    class Meta(NetBoxTable.Meta):
        model = Contract
        fields = ('pk', 'id', 'name', 'all_circuits', 'external_partie', 'internal_partie', 'comments', 'actions')
        default_columns = ('name', 'external_partie')

class InvoiceListTable(NetBoxTable):
    contract = tables.Column(
        linkify=True
    )
    number = tables.Column(
        linkify=True
    )

    class Meta(NetBoxTable.Meta):
        model = Invoice
        fields = ('pk', 'id', 'number', 'contract', 'actions')
        default_columns = ('number', 'contract')


class ContractCircuitListTable(NetBoxTable):
    cid = tables.Column(
        linkify=True
    )
    provider = tables.Column(
        linkify=True
    )

    class Meta(NetBoxTable.Meta):
        model = Circuit
        fields = ('pk', 'id', 'cid', 'provider', 'type','status')
        default_columns = ('cid', 'provider','status')