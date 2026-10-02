import django_tables2 as tables
from django.conf import settings
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from netbox.tables import NetBoxTable, columns
from tenancy.tables import ContactsColumnMixin

from .models import (
    AccountingDimension,
    Contract,
    ContractAssignment,
    ContractLine,
    ContractType,
    Invoice,
    InvoiceLine,
    ServiceProvider,
    Unit,
)
from .object_actions import can_amend

plugin_settings = settings.PLUGINS_CONFIG['netbox_contract']


class DeprecatedColumnsMixin:
    """Leave out the columns of deprecated contract fields unless the show_deprecated_fields setting is true."""

    deprecated_columns = ()

    def __init__(self, *args, **kwargs):
        if not plugin_settings.get('show_deprecated_fields'):
            kwargs['exclude'] = (*(kwargs.get('exclude') or ()), *self.deprecated_columns)
        super().__init__(*args, **kwargs)


class ContractTypeListTable(NetBoxTable):
    name = tables.Column(linkify=True)
    color = columns.ColorColumn()
    actions = columns.ActionsColumn(actions=('edit', 'delete'))

    class Meta(NetBoxTable.Meta):
        model = ContractType
        fields = ('pk', 'id', 'name', 'description', 'color', 'actions')
        default_columns = ('name', 'description', 'color')


class ContractAssignmentListTable(NetBoxTable):
    id = tables.Column(linkify=True)
    content_type = columns.ContentTypeColumn(verbose_name='Object Type')
    content_object = tables.Column(linkify=True, orderable=False)
    contract = tables.Column(linkify=True)
    actions = columns.ActionsColumn(actions=('edit', 'delete'))
    contract__external_party_object = tables.Column(linkify=True)
    tags = columns.TagColumn(url_name='plugins:netbox_contract:contractassignment_list')
    contract__contract_type = columns.ColoredLabelColumn(verbose_name='Contract type')

    class Meta(NetBoxTable.Meta):
        model = ContractAssignment
        fields = (
            'id',
            'content_type',
            'content_object',
            'contract',
            'contract__contract_type',
            'contract__external_party_object_type',
            'contract__external_party_object',
            'actions',
        )
        default_columns = (
            'id',
            'content_type',
            'content_object',
            'contract',
            'contract__contract_type',
            'contract__external_party_object_type',
            'contract__external_party_object',
        )


class ContractAssignmentObjectTable(DeprecatedColumnsMixin, NetBoxTable):
    deprecated_columns = ('contract__mrc', 'contract__nrc')
    contract = tables.Column(linkify=True)
    actions = columns.ActionsColumn(actions=('edit', 'delete'))
    contract__external_party_object = tables.Column(
        verbose_name='Partner', linkify=True
    )
    contract__status = columns.ChoiceFieldColumn(
        verbose_name=('Status'),
    )
    contract__contract_type = columns.ColoredLabelColumn(verbose_name='Contract type')
    contract_type = tables.Column(linkify=True, verbose_name='Contract type')

    class Meta(NetBoxTable.Meta):
        model = ContractAssignment
        fields = (
            'pk',
            'contract',
            'contract__external_party_object',
            'contract__status',
            'contract__contract_type',
            'contract__start_date',
            'contract__end_date',
            'contract__mrc',
            'contract__nrc',
            'actions',
        )
        default_columns = (
            'pk',
            'contract',
            'contract__external_party_object_type',
            'contract__external_party_object',
            'contract__status',
            'contract__contract_type',
            'contract__start_date',
            'contract__end_date',
            'contract__mrc',
            'contract__nrc',
        )


class ContractListTable(DeprecatedColumnsMixin, ContactsColumnMixin, NetBoxTable):
    deprecated_columns = ('mrc', 'yrc', 'nrc')
    name = tables.Column(linkify=True)
    external_party_object = tables.Column(verbose_name='External party', linkify=True)
    parent = tables.Column(linkify=True)
    yrc = tables.Column(verbose_name='Yearly recurring cost (deprecated)')
    mrc = tables.Column(verbose_name='Monthly recurring cost (deprecated)')
    nrc = tables.Column(verbose_name='Non-recurring cost (deprecated)')
    status = columns.ChoiceFieldColumn(
        verbose_name=('Status'),
    )
    tags = columns.TagColumn(url_name='plugins:netbox_contract:contract_list')
    contract_type = tables.Column(linkify=True, verbose_name='Contract type')
    billable = columns.BooleanColumn(verbose_name='Billable')
    yearly_value = tables.Column(verbose_name='Yearly value')

    class Meta(NetBoxTable.Meta):
        model = Contract
        fields = (
            'pk',
            'id',
            'name',
            'contract_type',
            'external_party_object_type',
            'external_party_object',
            'external_reference',
            'internal_party',
            'tenant',
            'status',
            'start_date',
            'end_date',
            'initial_term',
            'renewal_term',
            'currency',
            'mrc',
            'yrc',
            'nrc',
            'invoice_frequency',
            'billable',
            'yearly_value',
            'documents',
            'comments',
            'parent',
            'actions',
        )
        default_columns = ('name', 'status', 'contract_type', 'parent', 'billable', 'yearly_value')


class InvoiceListTable(NetBoxTable):
    contracts = tables.ManyToManyColumn(linkify=True)
    number = tables.Column(linkify=True)
    status = columns.ChoiceFieldColumn(
        verbose_name=('Status'),
    )
    tags = columns.TagColumn(url_name='plugins:netbox_contract:invoiceline_list')

    class Meta(NetBoxTable.Meta):
        model = Invoice
        fields = (
            'pk',
            'id',
            'number',
            'date',
            'status',
            'contracts',
            'period_start',
            'period_end',
            'currency',
            'amount',
            'documents',
            'comments',
            'actions',
        )
        default_columns = (
            'number',
            'date',
            'status',
            'contracts',
            'period_start',
            'period_end',
            'amount',
        )


class ServiceProviderListTable(NetBoxTable):
    name = tables.Column(linkify=True)
    tags = columns.TagColumn(url_name='plugins:netbox_contract:serviceprovider_list')

    class Meta(NetBoxTable.Meta):
        model = ServiceProvider
        fields = ('pk', 'name', 'slug', 'portal_url')
        default_columns = ('name', 'portal_url')


class InvoiceLineListTable(NetBoxTable):
    invoice = tables.Column(linkify=True)
    contract_line = tables.Column(linkify=True)
    unit = tables.Column(linkify=True, verbose_name='Unit')
    accounting_dimensions = tables.ManyToManyColumn(linkify_item=True, filter=lambda qs: qs.order_by('name'))
    tags = columns.TagColumn(url_name='plugins:netbox_contract:invoiceline_list')

    class Meta(NetBoxTable.Meta):
        model = InvoiceLine
        fields = (
            'pk',
            'id',
            'invoice',
            'contract_line',
            'quantity',
            'unit',
            'unit_price',
            'amount',
            'currency',
            'accounting_dimensions',
            'comments',
        )
        default_columns = (
            'pk',
            'id',
            'invoice',
            'contract_line',
            'quantity',
            'unit',
            'unit_price',
            'amount',
            'currency',
            'accounting_dimensions',
            'comments',
        )


class AccountingDimensionListTable(NetBoxTable):
    name = tables.Column(linkify=True)
    status = columns.ChoiceFieldColumn(
        verbose_name=('Status'),
    )
    tags = columns.TagColumn(url_name='plugins:netbox_contract:accountingdimension_list')

    class Meta(NetBoxTable.Meta):
        model = AccountingDimension
        fields = (
            'pk',
            'name',
            'value',
            'comments',
            'status',
        )
        default_columns = (
            'name',
            'value',
            'comments',
            'status',
        )


class UnitListTable(NetBoxTable):
    name = tables.Column(linkify=True)
    billing_method = columns.ChoiceFieldColumn(verbose_name='Billing method')
    tags = columns.TagColumn(url_name='plugins:netbox_contract:unit_list')

    class Meta(NetBoxTable.Meta):
        model = Unit
        fields = ('pk', 'id', 'name', 'description', 'billing_method', 'months', 'comments', 'tags', 'actions')
        default_columns = ('name', 'billing_method', 'months', 'description')


AMEND_BUTTON = (
    '<a href="{url}" class="btn btn-sm btn-primary" title="{title}">'
    '<i class="mdi mdi-cash-sync" aria-hidden="true"></i> {label}</a> '
)


class ContractLineActionsColumn(columns.ActionsColumn):
    """
    Actions of a contract line, decided line by line (research D4): no Delete on a locked line, and an Amend button
    when the line can be amended and the user may amend it. Reads the with_lock_state() annotations when present.
    """

    def render(self, record, table, **kwargs):
        locked = record.is_locked_line if hasattr(record, 'is_locked_line') else bool(record.lock_message())
        all_actions = self.actions
        if locked:
            self.actions = {name: item for name, item in all_actions.items() if name != 'delete'}
        try:
            html = super().render(record, table, **kwargs)
        finally:
            self.actions = all_actions

        request = getattr(table, 'context', {}).get('request')
        user = getattr(request, 'user', None)
        if user is not None and record.pk and can_amend(record, user):
            url = reverse('plugins:netbox_contract:contractline_amend', args=[record.pk])
            html = format_html(
                AMEND_BUTTON, url=url, title=_('Amend price or quantity'), label=_('Amend')
            ) + html
        return mark_safe(html)


class ContractLineListTable(NetBoxTable):
    contract = tables.Column(linkify=True)
    description = tables.Column(linkify=True)
    unit = tables.Column(linkify=True)
    unit__billing_method = columns.ChoiceFieldColumn(verbose_name='Billing method')
    accounting_dimensions = tables.ManyToManyColumn(linkify_item=True, filter=lambda qs: qs.order_by('name'))
    total_value = tables.Column(verbose_name='Total value', orderable=False)
    yearly_value = tables.Column(verbose_name='Yearly value', orderable=False)
    invoiced_at_conversion = columns.BooleanColumn(verbose_name='Invoiced at conversion')
    tags = columns.TagColumn(url_name='plugins:netbox_contract:contractline_list')
    actions = ContractLineActionsColumn()

    class Meta(NetBoxTable.Meta):
        model = ContractLine
        fields = (
            'pk',
            'id',
            'contract',
            'description',
            'quantity',
            'unit',
            'unit__billing_method',
            'unit_price',
            'currency',
            'start_date',
            'end_date',
            'accounting_dimensions',
            'total_value',
            'yearly_value',
            'invoiced_at_conversion',
            'comments',
            'tags',
            'actions',
        )
        default_columns = (
            'contract',
            'description',
            'quantity',
            'unit',
            'unit_price',
            'currency',
            'start_date',
            'end_date',
            'accounting_dimensions',
        )
