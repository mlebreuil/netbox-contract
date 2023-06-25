import django_tables2 as tables

from netbox.tables import NetBoxTable, columns
from circuits.models import Circuit
from .models import ContractAssignement, Contract, Invoice, ServiceProvider

class ContractAssignementListTable(NetBoxTable):
    content_type = columns.ContentTypeColumn(
        verbose_name='Object Type'
    )
    content_object = tables.Column(
        linkify=True,
        orderable=False
    )
    contract = tables.Column(
        linkify=True
    )
    actions = columns.ActionsColumn(
        actions=('edit', 'delete')
    )

    class Meta(NetBoxTable.Meta):
        model = ContractAssignement
        fields = ('pk', 'content_type', 'content_object', 'contract','contract__external_partie', 'actions')
        default_columns = ('pk', 'content_type', 'content_object', 'contract','contract__external_partie')

class ContractAssignementObjectTable(NetBoxTable):
    contract = tables.Column(
        linkify=True
    )
    actions = columns.ActionsColumn(
        actions=('edit', 'delete')
    )

    class Meta(NetBoxTable.Meta):
        model = ContractAssignement
        fields = ('pk','contract','contract__external_partie','contract__status','contract__start_date',
                  'contract__end_date','contract__mrc','contract__nrc', 'actions')
        default_columns = ('pk', 'contract','contract__external_partie','contract__status','contract__start_date',
                  'contract__end_date','contract__mrc','contract__nrc',)

class ContractAssignementContractTable(NetBoxTable):
    content_type = columns.ContentTypeColumn(
        verbose_name='Object Type'
    )
    content_object = tables.Column(
        linkify=True,
        verbose_name='Object',
        orderable=False
    )
    content_object__status = tables.Column(
        verbose_name='Status'
    )
    actions = columns.ActionsColumn(
        actions=('edit', 'delete')
    )

    class Meta(NetBoxTable.Meta):
        model = ContractAssignement
        fields = ('pk', 'content_type', 'content_object','content_object__status','actions')
        default_columns = ('pk', 'content_type', 'content_object','content_object__status')

class ContractListTable(NetBoxTable):

    name = tables.Column(
        linkify=True
    )
    external_partie = tables.Column(
        linkify=True
    )
    circuit = tables.ManyToManyColumn()
    parent = tables.Column(
        linkify=True
    )

    class Meta(NetBoxTable.Meta):
        model = Contract
        fields = ('pk', 'id', 'name', 'circuit', 'external_partie',
         'external_reference','internal_partie', 'status', 'mrc',
         'parent','comments', 'actions')
        default_columns = ('name', 'status', 'parent','circuit')

class ContractListBottomTable(NetBoxTable):
    name = tables.Column(
        linkify=True
    )
    class Meta(NetBoxTable.Meta):
        model = Contract
        fields = ('pk', 'id', 'name', 'all_circuits', 'external_partie',
          'external_reference','internal_partie', 'status', 'mrc',
          'comments', 'actions')
        default_columns = ('name', 'external_partie', 'status')

class InvoiceListTable(NetBoxTable):
    contracts = tables.ManyToManyColumn(
        linkify=True
    )
    number = tables.Column(
        linkify=True
    )

    class Meta(NetBoxTable.Meta):
        model = Invoice
        fields = ('pk', 'id', 'number', 'date', 'contracts', 'period_start',
          'period_end', 'amount', 'actions')
        default_columns = ('number', 'date', 'contracts', 'period_start', 'period_end', 'amount')


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

class ServiceProviderListTable(NetBoxTable):
    name = tables.Column(
        linkify=True
    )

    class Meta(NetBoxTable.Meta):
        model = ServiceProvider
        fields = ('pk', 'name', 'slug','portal_url')
        default_columns = ('name', 'portal_url')
