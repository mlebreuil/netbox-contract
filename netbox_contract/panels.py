"""
Panels of the plugin's detail pages (research D1-D4, contracts/detail-pages.md). The pages are declared with NetBox's
`layout.SimpleLayout` in views.py; this module holds the attribute panels and the few panels and actions that core does
not provide: attributes hidden by plugin settings, deprecated fields, contract values and lock messages.
"""

from django.conf import settings
from django.utils.translation import gettext_lazy as _
from netbox.ui import actions, attrs, panels
from utilities.data import resolve_attr_path

__all__ = (
    'AccountingDimensionPanel',
    'AddContractLine',
    'AddInvoiceLine',
    'ChildContractsPanel',
    'ContractAssignmentPanel',
    'ContractLinePanel',
    'ContractPanel',
    'ContractTypePanel',
    'ContractValuesPanel',
    'DeprecatedCostsPanel',
    'InvoiceLinePanel',
    'InvoicePanel',
    'MessagePanel',
    'ServiceProviderPanel',
    'UnitPanel',
)


def plugin_setting(name):
    # Read at render time, so that a changed setting (or a test patching PLUGINS_CONFIG) applies at once
    return settings.PLUGINS_CONFIG['netbox_contract'].get(name)


#
# Attributes
#

class NotAvailableAttr(attrs.TextAttr):
    """A computed value that can be unknown (open-ended recurring line): "Not available" instead of a placeholder."""

    def get_value(self, obj):
        value = super().get_value(obj)
        return _('Not available') if value is None else value


class LinkAttr(attrs.ObjectAttribute):
    """An external address, rendered as a link."""

    template_name = 'netbox_contract/attrs/link.html'

    def __init__(self, *args, text=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.text = text

    def get_context(self, obj, attr, value, context):
        return {'text': self.text}


class AmountAttr(attrs.ObjectAttribute):
    """An amount followed by the currency of the object."""

    template_name = 'netbox_contract/attrs/amount.html'

    def __init__(self, *args, currency_accessor='object', note=None, none_text=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.currency_accessor = currency_accessor
        self.note = note
        self.none_text = none_text

    def render(self, obj, context):
        if self.none_text is not None and self.get_value(obj) is None:
            return self.none_text
        return super().render(obj, context)

    def get_context(self, obj, attr, value, context):
        source = obj if self.currency_accessor == 'object' else resolve_attr_path(obj, self.currency_accessor)
        return {
            'currency': source.get_currency_display() if source is not None else '',
            'note': self.note(obj) if callable(self.note) else self.note,
        }


#
# Panels
#

class SettingsAttributesPanel(panels.ObjectAttributesPanel):
    """
    An attributes panel that leaves out, at render time:
    - the attributes listed in the plugin setting named by `hidden_setting` (e.g. hidden_contract_fields);
    - the attributes of `optional_attrs` whose value is empty;
    - the names returned by hidden_attrs(obj), for rules that depend on the object.
    """

    hidden_setting = None
    optional_attrs = ()

    def hidden_attrs(self, obj):
        return set()

    def get_context(self, context):
        ctx = panels.ObjectPanel.get_context(self, context)
        obj = ctx['object']
        hidden = set(plugin_setting(self.hidden_setting) or []) if self.hidden_setting else set()
        hidden |= self.hidden_attrs(obj)
        hidden |= {name for name in self.optional_attrs if not resolve_attr_path(obj, name)}
        names = [
            name for name in self._attrs
            if name not in hidden
            and (not self.only or name in self.only)
            and (not self.exclude or name not in self.exclude)
        ]
        return {
            **ctx,
            'attrs': [
                {
                    'label': self._attrs[name].label or self._name_to_label(name),
                    'value': self._attrs[name].render(obj, {
                        'name': name,
                        'perms': ctx['perms'],
                        'preferences': context.get('preferences', {}),
                    }),
                } for name in names
            ],
        }


class DeprecatedPanelMixin:
    """Shown only when the show_deprecated_fields plugin setting is on."""

    def should_render(self, context):
        return bool(plugin_setting('show_deprecated_fields')) and super().should_render(context)


class MessagePanel(panels.TemplatePanel):
    """A message (lock, deprecation) whose template renders nothing when it does not apply."""


class ContractPanel(SettingsAttributesPanel):
    hidden_setting = 'hidden_contract_fields'
    optional_attrs = ('documents',)
    title = _('Contract')

    name = attrs.TextAttr('name', label=_('Name'))
    contract_type = attrs.RelatedObjectAttr('contract_type', linkify=True, colored=True, label=_('Contract type'))
    external_party_object = attrs.GenericForeignKeyAttr(
        'external_party_object', linkify=True, label=_('External party')
    )
    status = attrs.ChoiceAttr('status', label=_('Status'))
    external_reference = attrs.TextAttr('external_reference', label=_('External reference'))
    internal_party = attrs.ChoiceAttr('internal_party', label=_('Internal party'))
    tenant = attrs.RelatedObjectAttr('tenant', linkify=True, label=_('Tenant'))
    start_date = attrs.TextAttr('start_date', label=_('Start date'))
    end_date = attrs.TextAttr('end_date', label=_('End date'))
    initial_term = attrs.TextAttr('initial_term', format_string=_('{} month'), label=_('Initial term'))
    renewal_term = attrs.TextAttr('renewal_term', format_string=_('{} month'), label=_('Renewal term'))
    notice_period = attrs.TextAttr('notice_period', format_string=_('{} days'), label=_('Notice period'))
    currency = attrs.ChoiceAttr('currency', label=_('Currency'))
    invoice_frequency = attrs.TextAttr('invoice_frequency', label=_('Invoice frequency'))
    parent = attrs.RelatedObjectAttr('parent', linkify=True, label=_('Parent'))
    documents = LinkAttr('documents', text=_('Documents'), label=_('Documents'))


class DeprecatedCostsPanel(DeprecatedPanelMixin, SettingsAttributesPanel):
    title = _('Deprecated costs')

    mrc = attrs.TextAttr('mrc', label=_('Monthly recuring costs'))
    yrc = attrs.TextAttr('yrc', label=_('Yearly recuring costs'))
    calculated_rc = attrs.TextAttr('calculated_rc', label=_('Calculated corresponding Yearly or Monthly value'))
    nrc = attrs.TextAttr('nrc', label=_('Non recuring costs'))


class ContractValuesPanel(SettingsAttributesPanel):
    """The values of `contract_values()`, computed once by the view (FR-006) and passed as `values` in the context."""

    title = _('Values')
    accessor = 'values'

    billable = attrs.BooleanAttr('billable', label=_('Billable'))
    total_contract_value = AmountAttr(
        'total_contract_value', none_text=_('Not available'), label=_('Total contract value')
    )
    yearly_contract_value = AmountAttr('yearly_contract_value', label=_('Yearly value'))
    yearly_billable_value = AmountAttr('yearly_billable_value', label=_('Yearly billable value'))


class InvoicePanel(SettingsAttributesPanel):
    hidden_setting = 'hidden_invoice_fields'
    optional_attrs = ('documents',)
    title = _('Invoice')

    number = attrs.TextAttr('number', label=_('Number'))
    date = attrs.TextAttr('date', label=_('Date'))
    status = attrs.ChoiceAttr('status', label=_('Status'))
    period_start = attrs.TextAttr('period_start', label=_('Period start'))
    period_end = attrs.TextAttr('period_end', label=_('Period end'))
    currency = attrs.ChoiceAttr('currency', label=_('Currency'))
    amount = attrs.TextAttr('amount', label=_('Amount'))
    documents = LinkAttr('documents', text=_('Documents'), label=_('Documents'))
    total_invoicelines_amount = attrs.TextAttr('total_invoicelines_amount', label=_('Invoice lines total'))

    def hidden_attrs(self, obj):
        # A deprecated invoice template has no period
        return {'period_start', 'period_end'} if obj.template else set()


class ContractLinePanel(SettingsAttributesPanel):
    title = _('Contract line')

    contract = attrs.RelatedObjectAttr('contract', linkify=True, label=_('Contract'))
    description = attrs.TextAttr('description', label=_('Description'))
    quantity = attrs.TextAttr('quantity', label=_('Quantity'))
    unit = attrs.RelatedObjectAttr('unit', linkify=True, label=_('Unit'))
    billing_method = attrs.ChoiceAttr('unit.billing_method', label=_('Billing method'))
    unit_price = AmountAttr('unit_price', label=_('Unit price'))
    start_date = attrs.TextAttr('start_date', label=_('Start date'))
    end_date = attrs.TextAttr('end_date', label=_('End date'))
    accounting_dimensions = attrs.RelatedObjectListAttr(
        'accounting_dimensions', linkify=True, label=_('Accounting dimensions')
    )
    total_value = NotAvailableAttr('total_value', label=_('Total value'))
    yearly_value = attrs.TextAttr('yearly_value', label=_('Yearly value'))
    replaces = attrs.TemplatedAttr(
        'replaces', template_name='netbox_contract/attrs/replaces.html', label=_('Replaces')
    )
    replaced_by = attrs.TemplatedAttr(
        'replaced_by', template_name='netbox_contract/attrs/replaced_by.html', label=_('Replaced by')
    )
    invoiced_at_conversion = attrs.BooleanAttr('invoiced_at_conversion', label=_('Invoiced at conversion'))


class InvoiceLinePanel(SettingsAttributesPanel):
    title = _('Invoice line')

    invoice = attrs.RelatedObjectAttr('invoice', linkify=True, label=_('Invoice'))
    contract_line = attrs.RelatedObjectAttr(
        'contract_line', linkify=True, grouped_by='contract', label=_('Contract line')
    )
    quantity = attrs.TextAttr('quantity', label=_('Quantity'))
    unit = attrs.RelatedObjectAttr('unit', linkify=True, label=_('Unit'))
    unit_price = attrs.TextAttr('unit_price', label=_('Unit price'))
    amount = AmountAttr(
        'amount', label=_('Amount'), note=lambda line: _('calculated') if line.unit_price is not None else None
    )
    currency = attrs.ChoiceAttr('currency', label=_('Currency'))
    accounting_dimensions = attrs.RelatedObjectListAttr(
        'accounting_dimensions', linkify=True, label=_('Accounting dimensions')
    )


class UnitPanel(SettingsAttributesPanel):
    title = _('Unit')

    name = attrs.TextAttr('name', label=_('Name'))
    description = attrs.TextAttr('description', label=_('Description'))
    billing_method = attrs.ChoiceAttr('billing_method', label=_('Billing method'))
    months = attrs.TextAttr('months', label=_('Months covered by one unit price'))


class AccountingDimensionPanel(SettingsAttributesPanel):
    title = _('Accounting dimension')

    name = attrs.TextAttr('name', label=_('Name'))
    value = attrs.TextAttr('value', label=_('Value'))
    status = attrs.ChoiceAttr('status', label=_('Status'))


class ContractTypePanel(SettingsAttributesPanel):
    title = _('Contract type')

    name = attrs.TextAttr('name', label=_('Name'))
    slug = attrs.TextAttr('slug', label=_('Slug'))
    description = attrs.TextAttr('description', label=_('Description'))
    color = attrs.ColorAttr('color')


class ServiceProviderPanel(SettingsAttributesPanel):
    title = _('Service provider')

    name = attrs.TextAttr('name', label=_('Name'))
    slug = attrs.TextAttr('slug', label=_('Slug'))
    description = attrs.TextAttr('description', label=_('Description'))
    portal_url = LinkAttr('portal_url', label=_('Portal URL'))


class ContractAssignmentPanel(SettingsAttributesPanel):
    title = _('Contract assignment')

    contract = attrs.RelatedObjectAttr('contract', linkify=True, label=_('Contract'))
    content_object = attrs.GenericForeignKeyAttr('content_object', linkify=True, label=_('Object'))


class ChildContractsPanel(panels.ObjectsTablePanel):
    """Child contracts, shown only when the contract has some (as before)."""

    def should_render(self, context):
        obj = context.get('object')
        return super().should_render(context) and obj is not None and obj.childs.exists()


#
# Panel actions
#

class AddContractLine(actions.AddObject):
    """Add a line to the contract, unless its lines are locked because it has invoices."""

    def render(self, context):
        obj = context.get('object')
        if obj is not None and obj.invoices.exists():
            return ''
        return super().render(context)


class AddInvoiceLine(actions.AddObject):
    """Add a line to the invoice, unless the invoice is posted (locked)."""

    def render(self, context):
        obj = context.get('object')
        if obj is not None and obj.is_locked:
            return ''
        return super().render(context)
