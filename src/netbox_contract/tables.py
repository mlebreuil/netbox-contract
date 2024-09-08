import django_tables2 as tables
from netbox.tables import NetBoxTable, columns

from .models import (
    AccountingDimension,
    Contract,
    ContractAssignment,
    Invoice,
    InvoiceLine,
    ServiceProvider,
)


class ContractAssignmentListTable(NetBoxTable):
    content_type = columns.ContentTypeColumn(verbose_name='Object Type')
    content_object = tables.Column(linkify=True, orderable=False)
    contract = tables.Column(linkify=True)
    actions = columns.ActionsColumn(actions=('edit', 'delete'))
    contract__external_partie_object = tables.Column(linkify=True)

    class Meta(NetBoxTable.Meta):
        model = ContractAssignment
        fields = (
            'pk',
            'content_type',
            'content_object',
            'contract',
            'contract__external_partie_object_type',
            'contract__external_partie_object',
            'actions',
        )
        default_columns = (
            'pk',
            'content_type',
            'content_object',
            'contract',
            'contract__external_partie_object_type',
            'contract__external_partie_object',
        )


class ContractAssignmentObjectTable(NetBoxTable):
    contract = tables.Column(linkify=True)
    actions = columns.ActionsColumn(actions=('edit', 'delete'))
    contract__external_partie_object = tables.Column(
        verbose_name='Partner', linkify=True
    )

    class Meta(NetBoxTable.Meta):
        model = ContractAssignment
        fields = (
            'pk',
            'contract',
            'contract__external_partie_object',
            'contract__status',
            'contract__start_date',
            'contract__end_date',
            'contract__mrc',
            'contract__nrc',
            'actions',
        )
        default_columns = (
            'pk',
            'contract',
            'contract__external_partie_object_type',
            'contract__external_partie_object',
            'contract__status',
            'contract__start_date',
            'contract__end_date',
            'contract__mrc',
            'contract__nrc',
        )


class ContractAssignmentContractTable(NetBoxTable):
    content_type = columns.ContentTypeColumn(verbose_name='Object Type')
    content_object = tables.Column(linkify=True, verbose_name='Object', orderable=False)
    content_object__status = tables.Column(verbose_name='Status')
    actions = columns.ActionsColumn(actions=('edit', 'delete'))

    class Meta(NetBoxTable.Meta):
        model = ContractAssignment
        fields = (
            'pk',
            'content_type',
            'content_object',
            'content_object__status',
            'actions',
        )
        default_columns = (
            'pk',
            'content_type',
            'content_object',
            'content_object__status',
        )


class ContractListTable(NetBoxTable):
    name = tables.Column(linkify=True)
    external_partie_object = tables.Column(verbose_name='External partie', linkify=True)
    parent = tables.Column(linkify=True)
    yrc = tables.Column(verbose_name='Yerly recuring costs')

    class Meta(NetBoxTable.Meta):
        model = Contract
        fields = (
            'pk',
            'id',
            'name',
            'external_partie_object_type',
            'external_partie_object',
            'external_reference',
            'internal_partie',
            'tenant',
            'status',
            'start_date',
            'end_date',
            'initial_term',
            'renewal_term',
            'currency',
            'accounting_dimensions',
            'mrc',
            'yrc',
            'nrc',
            'invoice_frequency',
            'documents',
            'comments',
            'parent',
            'actions',
        )
        default_columns = ('name', 'status', 'parent')


class ContractListBottomTable(NetBoxTable):
    name = tables.Column(linkify=True)
    external_partie_object = tables.Column(linkify=True)

    class Meta(NetBoxTable.Meta):
        model = Contract
        fields = (
            'pk',
            'id',
            'name',
            'external_partie_object_type',
            'external_partie_object',
            'external_reference',
            'internal_partie',
            'status',
            'mrc',
            'comments',
            'actions',
        )
        default_columns = (
            'name',
            'external_partie_object_type',
            'external_partie_object',
            'status',
        )


class InvoiceListTable(NetBoxTable):
    contracts = tables.ManyToManyColumn(linkify=True)
    number = tables.Column(linkify=True)

    class Meta(NetBoxTable.Meta):
        model = Invoice
        fields = (
            'pk',
            'id',
            'number',
            'date',
            'contracts',
            'period_start',
            'period_end',
            'currency',
            'accounting_dimensions',
            'amount',
            'documents',
            'comments',
            'actions',
        )
        default_columns = (
            'number',
            'date',
            'contracts',
            'period_start',
            'period_end',
            'amount',
        )


class ServiceProviderListTable(NetBoxTable):
    name = tables.Column(linkify=True)

    class Meta(NetBoxTable.Meta):
        model = ServiceProvider
        fields = ('pk', 'name', 'slug', 'portal_url')
        default_columns = ('name', 'portal_url')


class InvoiceLineListTable(NetBoxTable):
    invoice = tables.Column(linkify=True)
    accounting_dimensions = tables.ManyToManyColumn(
        linkify=True, filter=lambda qs: qs.order_by('name')
    )

    class Meta(NetBoxTable.Meta):
        model = InvoiceLine
        fields = (
            'pk',
            'invoice',
            'amount',
            'currency',
            'accounting_dimensions',
            'comments',
        )
        default_columns = (
            'pk',
            'invoice',
            'amount',
            'currency',
            'accounting_dimensions',
            'comments',
        )


class AccountingDimensionListTable(NetBoxTable):
    class Meta(NetBoxTable.Meta):
        model = AccountingDimension
        fields = (
            'pk',
            'name',
            'value',
            'comments',
        )
        default_columns = (
            'name',
            'value',
            'comments',
        )
