import logging
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from types import SimpleNamespace

from dateutil.relativedelta import relativedelta
from django import forms as django_forms
from django.apps import apps
from django.conf import settings
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db.models import Case, F, When
from django.db.models.functions import Round
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _
from extras.ui.panels import CustomFieldsPanel, TagsPanel
from netbox.object_actions import *
from netbox.ui import actions, layout
from netbox.ui.panels import CommentsPanel, ObjectsTablePanel
from netbox.views import generic
from netbox.views.generic.base import BaseObjectView
from utilities.querydict import normalize_querydict
from utilities.views import ViewTab, get_action_url, register_model_view

from . import calculations, filtersets, forms, panels, tables
from .constants import ASSIGNEMENT_TYPES
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
    contract_values,
    yearly_value_annotation,
)
from .object_actions import AmendContractLine
from .services import amendments, invoicing

plugin_settings = settings.PLUGINS_CONFIG['netbox_contract']

logger = logging.getLogger('netbox.plugins.netbox_contract')


# ContractType views


@register_model_view(ContractType)
class ContractTypeView(generic.ObjectView):
    queryset = ContractType.objects.all()
    template_name = 'generic/object.html'
    layout = layout.SimpleLayout(
        left_panels=[panels.ContractTypePanel(), CustomFieldsPanel()],
        right_panels=[TagsPanel(), CommentsPanel()],
    )


@register_model_view(ContractType, 'list', path='', detail=False)
class ContractTypeListView(generic.ObjectListView):
    queryset = ContractType.objects.all()
    table = tables.ContractTypeListTable
    filterset = filtersets.ContractTypeFilterSet
    filterset_form = forms.ContractTypeFilterForm


@register_model_view(ContractType, 'add', detail=False)
@register_model_view(ContractType, 'edit')
class ContractTypeEditView(generic.ObjectEditView):
    queryset = ContractType.objects.all()
    form = forms.ContractTypeForm


@register_model_view(ContractType, 'bulk_import', path='import', detail=False)
class ContractTypeBulkImportView(generic.BulkImportView):
    queryset = ContractType.objects.all()
    model_form = forms.ContractTypeCSVForm
    table = tables.ContractTypeListTable


@register_model_view(ContractType, 'bulk_edit', path='edit', detail=False)
class ContractTypeBulkEditView(generic.BulkEditView):
    queryset = ContractType.objects.annotate()
    filterset = filtersets.ContractTypeFilterSet
    table = tables.ContractTypeListTable
    form = forms.ContractTypeBulkEditForm


@register_model_view(ContractType, 'delete')
class ContractTypeDeleteView(generic.ObjectDeleteView):
    queryset = ContractType.objects.all()


@register_model_view(ContractType, 'bulk_delete', path='delete', detail=False)
class ContractTypeBulkDeleteView(generic.BulkDeleteView):
    queryset = ContractType.objects.annotate()
    filterset = filtersets.ContractTypeFilterSet
    table = tables.ContractTypeListTable


# ServiceProvider views

@register_model_view(ServiceProvider)
class ServiceProviderView(generic.ObjectView):
    queryset = ServiceProvider.objects.all()
    template_name = 'generic/object.html'
    layout = layout.SimpleLayout(
        left_panels=[panels.ServiceProviderPanel(), CustomFieldsPanel()],
        right_panels=[TagsPanel(), CommentsPanel()],
        bottom_panels=[
            ObjectsTablePanel(
                model='netbox_contract.contract',
                title=_('Contracts'),
                filters={'service_provider_id': lambda ctx: ctx['object'].pk},
            ),
        ],
    )


@register_model_view(ServiceProvider, 'list', path='', detail=False)
class ServiceProviderListView(generic.ObjectListView):
    queryset = ServiceProvider.objects.all()
    table = tables.ServiceProviderListTable
    filterset = filtersets.ServiceProviderFilterSet
    filterset_form = forms.ServiceProviderFilterForm


@register_model_view(ServiceProvider, 'add', detail=False)
@register_model_view(ServiceProvider, 'edit')
class ServiceProviderEditView(generic.ObjectEditView):
    queryset = ServiceProvider.objects.all()
    form = forms.ServiceProviderForm


@register_model_view(ServiceProvider, 'delete')
class ServiceProviderDeleteView(generic.ObjectDeleteView):
    queryset = ServiceProvider.objects.all()


@register_model_view(ServiceProvider, 'bulk_import', path='import', detail=False)
class ServiceProviderBulkImportView(generic.BulkImportView):
    queryset = ServiceProvider.objects.all()
    model_form = forms.ServiceProviderCSVForm
    table = tables.ServiceProviderListTable


@register_model_view(ServiceProvider, 'bulk_edit', path='edit', detail=False)
class ServiceProviderBulkEditView(generic.BulkEditView):
    queryset = ServiceProvider.objects.annotate()
    filterset = filtersets.ServiceProviderFilterSet
    table = tables.ServiceProviderListTable
    form = forms.ServiceProviderBulkEditForm


@register_model_view(ServiceProvider, 'bulk_delete', path='delete', detail=False)
class ServiceProviderBulkDeleteView(generic.BulkDeleteView):
    queryset = ServiceProvider.objects.annotate()
    filterset = filtersets.ServiceProviderFilterSet
    table = tables.ServiceProviderListTable


# Contract assignment view


@register_model_view(ContractAssignment)
class ContractAssignmentView(generic.ObjectView):
    queryset = ContractAssignment.objects.all()
    template_name = 'generic/object.html'
    layout = layout.SimpleLayout(
        left_panels=[panels.ContractAssignmentPanel(), CustomFieldsPanel()],
        right_panels=[TagsPanel()],
    )


@register_model_view(ContractAssignment, 'list', path='', detail=False)
class ContractAssignmentListView(generic.ObjectListView):
    queryset = ContractAssignment.objects.all()
    table = tables.ContractAssignmentListTable
    filterset = filtersets.ContractAssignmentFilterSet
    filterset_form = forms.ContractAssignmentFilterForm


@register_model_view(ContractAssignment, 'add', detail=False)
@register_model_view(ContractAssignment, 'edit')
class ContractAssignmentEditView(generic.ObjectEditView):
    queryset = ContractAssignment.objects.all()
    form = forms.ContractAssignmentForm

    def alter_object(self, instance, request, args, kwargs):
        if not instance.pk and kwargs:
            # Assign the object based on URL kwargs
            content_type = get_object_or_404(
                ContentType, pk=request.GET.get('content_type')
            )
            instance.object = get_object_or_404(
                content_type.model_class(), pk=request.GET.get('object_id')
            )
        return instance

    def get_extra_addanother_params(self, request):
        return {
            'content_type': request.GET.get('content_type'),
            'object_id': request.GET.get('object_id'),
        }


@register_model_view(ContractAssignment, 'delete')
class ContractAssignmentDeleteView(generic.ObjectDeleteView):
    queryset = ContractAssignment.objects.all()


@register_model_view(ContractAssignment, 'bulk_import', path='import', detail=False)
class ContractAssignmentBulkImportView(generic.BulkImportView):
    queryset = ContractAssignment.objects.all()
    model_form = forms.ContractAssignmentImportForm
    table = tables.ContractAssignmentListTable


@register_model_view(ContractAssignment, 'bulk_edit', path='edit', detail=False)
class ContractAssignmentBulkEditView(generic.BulkEditView):
    queryset = ContractAssignment.objects.annotate()
    filterset = filtersets.ContractAssignmentFilterSet
    table = tables.ContractAssignmentListTable
    form = forms.ContractAssignmentBulkEditForm


@register_model_view(ContractAssignment, 'bulk_delete', path='delete', detail=False)
class ContractAssignmentBulkDeleteView(generic.BulkDeleteView):
    queryset = ContractAssignment.objects.annotate()
    filterset = filtersets.ContractAssignmentFilterSet
    table = tables.ContractAssignmentListTable


class AddContractAssignment(AddObject):
    label = _('Add contract')

    @classmethod
    def get_url(cls, obj):
        # obj will be the parent object in the custom template (ObjectChildren hook)
        if hasattr(obj, 'pk') and hasattr(obj, '_meta') and obj.pk:
            parent = obj
            parent_ct = ContentType.objects.get_for_model(parent)
            base_url = get_action_url(ContractAssignment, action='add')
            return (
                f"{base_url}?content_type={parent_ct.pk}"
                f"&object_id={parent.pk}&return_url={parent.get_absolute_url()}"
            )

        # fallback for a class value (if called as model class)
        return get_action_url(ContractAssignment, action='add')


class BaseObjectContractAssignmentView(generic.ObjectChildrenView):
    child_model = ContractAssignment
    table = tables.ContractAssignmentObjectTable
    filterset = filtersets.ContractAssignmentFilterSet
    template_name = 'netbox_contract/object_contracts.html'
    actions = (AddContractAssignment, BulkEdit, BulkDelete)
    tab = ViewTab(
        label=_('Contracts'),
        visible=lambda obj: plugin_settings.get('contract_assignments_display', 'both') != 'inline',
        badge=lambda obj: ContractAssignment.objects.filter(
            content_type=ContentType.objects.get_for_model(obj), object_id=obj.id
        ).count(),
        permission='netbox_contract.view_contractassignment',
        weight=550,
        hide_if_empty=True,
    )

    def get_children(self, request, parent):
        object_type = ContentType.objects.get_for_model(parent)
        contract_assignments = ContractAssignment.objects.filter(
            content_type__pk=object_type.id, object_id=parent.id
        )
        return contract_assignments


# Dynamically register the view for all supported models
for model_string in ASSIGNEMENT_TYPES:
    app_label, model_name = model_string.split('.')
    try:
        model = apps.get_model(app_label, model_name)
    except LookupError:
        # A configured supported model may not (yet) be registered in the
        # app registry. This happens in particular with models that are
        # created dynamically by other plugins (e.g. netbox_custom_objects
        # custom object types), whose registration timing relative to our
        # own app loading is not guaranteed. Rather than letting this take
        # down the entire NetBox instance (including unrelated management
        # commands such as `migrate`), skip this entry and let the rest of
        # the plugin continue to load normally.
        logger.error(
            "netbox_contract: 'supported_models' entry '%s' does not "
            "resolve to a registered model; skipping the Contracts tab/"
            "view for it. Verify the app label and model name are "
            "correct, and that any plugin providing this model (e.g. "
            "netbox_custom_objects) has finished initializing before "
            "netbox_contract loads.",
            model_string,
        )
        continue

    class_name = f"{model_name.title()}ContractAssignmentView"
    attrs = {
        'queryset': model.objects.all(),
        'viewname': f'netbox_contract:{model_name}_contracts',
    }
    view_class = type(class_name, (BaseObjectContractAssignmentView,), attrs)

    register_model_view(model, 'contracts', path='contracts')(view_class)


# Contract views


@register_model_view(Contract)
class ContractView(generic.ObjectView):
    queryset = Contract.objects.annotate(
        calculated_rc=Round(
            Case(When(yrc__gt=0, then=F('yrc') / 12), default=F('mrc') * 12),
            precision=2,
        )
    )
    layout = layout.SimpleLayout(
        left_panels=[panels.ContractPanel(), panels.DeprecatedCostsPanel(), CustomFieldsPanel()],
        right_panels=[
            panels.ContractValuesPanel(),
            TagsPanel(),
            CommentsPanel(),
            panels.MessagePanel('netbox_contract/panels/contract_invoice_template.html'),
        ],
        bottom_panels=[
            panels.MessagePanel('netbox_contract/panels/lines_locked.html'),
            ObjectsTablePanel(
                model='netbox_contract.contractline',
                title=_('Contract lines'),
                filters={'contract_id': lambda ctx: ctx['object'].pk},
                exclude_columns=['contract'],
                actions=[
                    panels.AddContractLine(
                        'netbox_contract.contractline', label=_('Add a contract line'),
                        url_params={'contract': lambda ctx: ctx['object'].pk},
                    ),
                ],
            ),
            ObjectsTablePanel(
                model='netbox_contract.contractassignment',
                title=_('Assignments'),
                filters={'contract': lambda ctx: ctx['object'].pk},
                exclude_columns=['contract'],
            ),
            panels.ChildContractsPanel(
                model='netbox_contract.contract',
                title=_('Child contracts'),
                filters={'parent': lambda ctx: ctx['object'].pk},
                exclude_columns=['parent'],
            ),
            ObjectsTablePanel(
                model='netbox_contract.invoice',
                title=_('Invoices'),
                filters={'contracts': lambda ctx: ctx['object'].pk, 'template': 'False'},
                exclude_columns=['contracts'],
                actions=[
                    actions.AddObject(
                        'netbox_contract.invoice', label=_('Add an invoice'),
                        url_params={'contracts': lambda ctx: ctx['object'].pk},
                    ),
                ],
            ),
        ],
    )

    def get_extra_context(self, request, instance):
        values = contract_values([instance])[instance.pk]
        context = {
            # Computed once for the page in a fixed number of queries (FR-006), read by ContractValuesPanel
            'values': SimpleNamespace(
                billable=instance.billable, get_currency_display=instance.get_currency_display, **values
            ),
            'lines_locked': instance.invoices.exists(),
        }
        # Invoice templates are deprecated: looked up only when deprecated fields are shown
        if plugin_settings.get('show_deprecated_fields'):
            invoice_template = instance.invoices.filter(template=True).first()
            if invoice_template:
                invoicelines_table = tables.InvoiceLineListTable(invoice_template.invoicelines.all())
                invoicelines_table.columns.hide('invoice')
                invoicelines_table.columns.hide('currency')
                invoicelines_table.configure(request)
                invoicelines_table.columns.hide('actions')
                context.update(invoice_template=invoice_template, invoicelines_table=invoicelines_table)
        return context


@register_model_view(Contract, 'list', path='', detail=False)
class ContractListView(generic.ObjectListView):
    queryset = Contract.objects.annotate(yearly_value=yearly_value_annotation())
    table = tables.ContractListTable
    filterset = filtersets.ContractFilterSet
    filterset_form = forms.ContractFilterForm


@register_model_view(Contract, 'add', detail=False)
@register_model_view(Contract, 'edit')
class ContractEditView(generic.ObjectEditView):
    queryset = Contract.objects.all()
    form = forms.ContractForm

    def alter_object(self, obj, request, url_args, url_kwargs):
        """
        When this method is called after a Post,
        it is used here to set the external party object id for exiting objects,
        In any case, this happens before the form is instanciated.

        Args:
            obj: The object being edited
            request: The current request
            url_args: URL path args
            url_kwargs: URL path kwargs
        """

        if request.method == 'POST':
            data = normalize_querydict(request.POST)
            obj.external_party_object_id = data['external_party_object']
            external_party_object_type_id = data['external_party_object_type']
            obj.external_party_object_type = ContentType.objects.get(
                id=external_party_object_type_id
            )
            external_party_object_type = obj.external_party_object_type
            obj.external_party_object = (
                external_party_object_type.get_object_for_this_type(
                    id=obj.external_party_object_id
                )
            )

        return obj


@register_model_view(Contract, 'delete')
class ContractDeleteView(generic.ObjectDeleteView):
    queryset = Contract.objects.all()


@register_model_view(Contract, 'bulk_import', path='import', detail=False)
class ContractBulkImportView(generic.BulkImportView):
    queryset = Contract.objects.all()
    model_form = forms.ContractCSVForm
    table = tables.ContractListTable


@register_model_view(Contract, 'bulk_edit', path='edit', detail=False)
class ContractBulkEditView(generic.BulkEditView):
    queryset = Contract.objects.all()
    filterset = filtersets.ContractFilterSet
    table = tables.ContractListTable
    form = forms.ContractBulkEditForm


@register_model_view(Contract, 'bulk_delete', path='delete', detail=False)
class ContractBulkDeleteView(generic.BulkDeleteView):
    queryset = Contract.objects.all()
    filterset = filtersets.ContractFilterSet
    table = tables.ContractListTable


# Invoice views


@register_model_view(Invoice)
class InvoiceView(generic.ObjectView):
    queryset = Invoice.objects.all()
    layout = layout.SimpleLayout(
        left_panels=[
            panels.MessagePanel('netbox_contract/panels/invoice_template_notice.html'),
            panels.InvoicePanel(),
            CustomFieldsPanel(),
        ],
        right_panels=[TagsPanel(), CommentsPanel()],
        bottom_panels=[
            panels.MessagePanel('netbox_contract/panels/invoice_posted.html'),
            ObjectsTablePanel(
                model='netbox_contract.invoiceline',
                title=_('Invoice lines'),
                filters={'invoice': lambda ctx: ctx['object'].pk},
                exclude_columns=['invoice'],
                actions=[
                    panels.AddInvoiceLine(
                        'netbox_contract.invoiceline', label=_('Add a line'),
                        url_params={'invoice': lambda ctx: ctx['object'].pk},
                    ),
                ],
            ),
            ObjectsTablePanel(
                model='netbox_contract.contract',
                title=_('Contracts'),
                filters={'invoice_id': lambda ctx: ctx['object'].pk},
            ),
        ],
    )


@register_model_view(Invoice, 'list', path='', detail=False)
class InvoiceListView(generic.ObjectListView):
    queryset = Invoice.objects.all()
    table = tables.InvoiceListTable
    filterset = filtersets.InvoiceFilterSet
    filterset_form = forms.InvoiceFilterForm


def _parse_date(value):
    if value in (None, ''):
        return None
    if isinstance(value, date):
        return value
    try:
        return django_forms.DateField().to_python(value)
    except ValidationError:
        return None


def _format_number(value):
    return '' if value is None else f'{value.normalize():f}'


def build_lines_preview(data, user):
    """
    Lines a new invoice would get, from the contract, period, amount and the quantities and unit prices typed
    in the preview (FR-032). None for an invoice template.
    """
    if str(data.get('template', '')).lower() in ('on', 'true', '1'):
        return None
    preview = {
        'rows': [], 'extra_rows': [], 'units': Unit.objects.order_by('name'), 'total': None, 'message': None,
        'errors': [], 'amount_too_low': False, 'contract': None,
    }

    contract_ids = data.getlist('contracts') if hasattr(data, 'getlist') else data.get('contracts')
    if not isinstance(contract_ids, (list, tuple)):
        contract_ids = [contract_ids]
    contract_ids = [value for value in contract_ids if str(value).isdigit()]
    contracts = Contract.objects.restrict(user, 'view')
    contract = contracts.filter(pk=contract_ids[0]).first() if contract_ids else None
    if contract is None:
        preview['message'] = _('Choose a contract to see the lines generated for it.')
        return preview
    preview['contract'] = contract

    overrides, preview['errors'] = invoicing.parse_line_overrides(data)
    try:
        lines = invoicing.lines_to_generate(
            contract, _parse_date(data.get('period_start')), _parse_date(data.get('period_end')), overrides
        )
    except invoicing.InvoicingError as e:
        preview['message'] = e.message
        return preview

    for line in lines:
        prefix = f'line-{line.contract_line.pk}'
        preview['rows'].append({
            'line': line,
            'prefix': prefix,
            'dimensions_form': forms.InvoiceLineDimensionsForm(
                prefix=prefix, initial={'accounting_dimensions': [d.pk for d in line.accounting_dimensions]}
            ),
            'quantity_value': data.get(f'{prefix}-quantity', _format_number(line.quantity)),
            'unit_price_value': data.get(f'{prefix}-unit_price') or _format_number(line.unit_price),
        })
    # Lines added without contract line, with the buttons that add or remove one
    period_start, period_end = _parse_date(data.get('period_start')), _parse_date(data.get('period_end'))
    # incomplete rows simply have no amount yet; they are checked when the invoice is saved
    extra_lines, _errors = invoicing.parse_extra_lines(data)
    remove = str(data.get('remove_line', ''))
    extra_lines = [line for line in extra_lines if str(line.index) != remove]
    if data.get('add_line'):
        extra_lines.append(invoicing.ExtraLine(index=max((line.index for line in extra_lines), default=-1) + 1))
    added = invoicing.price_extra_lines(contract, period_start, period_end, extra_lines)
    for line in extra_lines:
        preview['extra_rows'].append({
            'index': line.index,
            'prefix': f'extra-{line.index}',
            'dimensions_form': forms.InvoiceLineDimensionsForm(
                prefix=f'extra-{line.index}',
                initial={'accounting_dimensions': [d.pk for d in line.accounting_dimensions]},
            ),
            'description': line.description,
            'unit_id': line.raw.get('unit', ''),
            'unit_price_value': line.raw.get('unit_price', ''),
            'quantity_value': line.raw.get('quantity', ''),
            'amount': line.amount,
        })

    preview['total'] = calculations.round_amount(sum((line.amount for line in [*lines, *added]), Decimal(0)))
    try:
        amount = Decimal(str(data.get('amount') or ''))
    except InvalidOperation:
        amount = None
    preview['amount_too_low'] = amount is not None and amount < preview['total']
    return preview


class InvoiceLinesPreviewView(BaseObjectView):
    """Refresh the preview of the lines of a new invoice when its form changes (FR-032)."""

    queryset = Invoice.objects.all()

    def get_required_permission(self):
        return 'netbox_contract.add_invoice'

    def post(self, request):
        return render(request, 'netbox_contract/inc/invoice_lines_preview.html', {
            'lines_preview': build_lines_preview(request.POST, request.user),
        })


def form_with_defaults(form_class, defaults):
    """
    The form class with extra initial values that the initial values passed by the view (the page address) override.
    Used to pre-fill a new object and still let core ObjectEditView.get() handle quick add and HTMX requests.
    """
    class FormWithDefaults(form_class):
        def __init__(self, *args, initial=None, **kwargs):
            super().__init__(*args, initial={**defaults, **(initial or {})}, **kwargs)

    return FormWithDefaults


@register_model_view(Invoice, 'add', detail=False)
@register_model_view(Invoice, 'edit')
class InvoiceEditView(generic.ObjectEditView):
    queryset = Invoice.objects.all()
    form = forms.InvoiceForm
    template_name = 'netbox_contract/invoice_edit.html'

    def get_extra_context(self, request, instance):
        if instance.pk:
            return {}
        if request.method == 'POST':
            return {'lines_preview': build_lines_preview(request.POST, request.user)}
        # New invoice: the preview uses the same values as the form, the address winning over the pre-fill
        data = {**getattr(self, 'prefill', {}), **normalize_querydict(request.GET)}
        return {'lines_preview': build_lines_preview(data, request.user)}

    def get(self, request, *args, **kwargs):
        """Pre-fill a new invoice from the contract given in the address, then render as core does."""
        if not kwargs:
            self.prefill = self.invoice_prefill(request)
            self.form = form_with_defaults(self.form, self.prefill)
        return super().get(request, *args, **kwargs)

    def invoice_prefill(self, request):
        """Values proposed for a new invoice; values given in the address are kept (they override these)."""
        prefill = {'date': date.today()}
        contract_id = request.GET.get('contracts')
        # Only a contract the user may view is used to pre-fill the invoice
        contract = (
            Contract.objects.restrict(request.user, 'view').filter(pk=contract_id).first()
            if str(contract_id).isdigit() else None
        )
        if contract is None:
            return prefill

        try:
            last_invoice = contract.invoices.exclude(template=True).filter(period_end__isnull=False).latest(
                'period_end'
            )
            new_period_start = last_invoice.period_end + timedelta(days=1)
        except ObjectDoesNotExist:
            new_period_start = contract.start_date or None

        new_period_end = None
        if new_period_start:
            prefill['period_start'] = new_period_start
            new_period_end = new_period_start + relativedelta(months=contract.invoice_frequency) - timedelta(days=1)
            prefill['period_end'] = new_period_end

        # Amount proposed from the contract lines (not from the deprecated cost fields)
        try:
            proposal = invoicing.propose_invoice(contract, new_period_start, new_period_end)
        except invoicing.InvoicingError as e:
            messages.error(request, e.message)
        else:
            if proposal.lines:
                prefill['amount'] = proposal.total

        prefill['currency'] = contract.currency
        return prefill


@register_model_view(Invoice, 'delete')
class InvoiceDeleteView(generic.ObjectDeleteView):
    queryset = Invoice.objects.all()


@register_model_view(Invoice, 'bulk_import', path='import', detail=False)
class InvoiceBulkImportView(generic.BulkImportView):
    queryset = Invoice.objects.all()
    model_form = forms.InvoiceCSVForm
    table = tables.InvoiceListTable


@register_model_view(Invoice, 'bulk_edit', path='edit', detail=False)
class InvoiceBulkEditView(generic.BulkEditView):
    queryset = Invoice.objects.all()
    filterset = filtersets.InvoiceFilterSet
    table = tables.InvoiceListTable
    form = forms.InvoiceBulkEditForm


@register_model_view(Invoice, 'bulk_delete', path='delete', detail=False)
class InvoiceBulkDeleteView(generic.BulkDeleteView):
    queryset = Invoice.objects.all()
    filterset = filtersets.InvoiceFilterSet
    table = tables.InvoiceListTable


# InvoiceLine


@register_model_view(InvoiceLine)
class InvoiceLineView(generic.ObjectView):
    queryset = InvoiceLine.objects.select_related('invoice', 'contract_line__contract', 'unit')
    layout = layout.SimpleLayout(
        left_panels=[panels.InvoiceLinePanel(), CustomFieldsPanel()],
        right_panels=[TagsPanel(), CommentsPanel()],
    )


@register_model_view(InvoiceLine, 'list', path='', detail=False)
class InvoiceLineListView(generic.ObjectListView):
    queryset = InvoiceLine.objects.select_related('invoice', 'contract_line', 'unit')
    table = tables.InvoiceLineListTable
    filterset = filtersets.InvoiceLineFilterSet
    filterset_form = forms.InvoiceLineFilterForm


@register_model_view(InvoiceLine, 'add', detail=False)
@register_model_view(InvoiceLine, 'edit')
class InvoiceLineEditView(generic.ObjectEditView):
    queryset = InvoiceLine.objects.all()
    form = forms.InvoiceLineForm

    def get(self, request, *args, **kwargs):
        """Pre-fill a new invoice line from the invoice given in the address, then render as core does."""
        if not kwargs:
            prefill = {}
            invoice_id = request.GET.get('invoice')
            # Only an invoice the user may view is used to pre-fill the line
            invoice = (
                Invoice.objects.restrict(request.user, 'view').filter(pk=invoice_id).first()
                if str(invoice_id).isdigit() else None
            )
            if invoice is not None:
                # propose the rest of the invoice amount as the unit price of one unit
                prefill = {
                    'unit_price': invoice.amount - invoice.total_invoicelines_amount,
                    'quantity': 1,
                    'currency': invoice.currency,
                }
            self.form = form_with_defaults(self.form, prefill)
        return super().get(request, *args, **kwargs)


@register_model_view(InvoiceLine, 'delete')
class InvoiceLineDeleteView(generic.ObjectDeleteView):
    queryset = InvoiceLine.objects.all()


@register_model_view(InvoiceLine, 'bulk_import', path='import', detail=False)
class InvoiceLineBulkImportView(generic.BulkImportView):
    queryset = InvoiceLine.objects.all()
    model_form = forms.InvoiceLineImportForm
    table = tables.InvoiceLineListTable


@register_model_view(InvoiceLine, 'bulk_edit', path='edit', detail=False)
class InvoiceLineBulkEditView(generic.BulkEditView):
    queryset = InvoiceLine.objects.annotate()
    filterset = filtersets.InvoiceLineFilterSet
    table = tables.InvoiceLineListTable
    form = forms.InvoiceLineBulkEditForm


@register_model_view(InvoiceLine, 'bulk_delete', path='delete', detail=False)
class InvoiceLineBulkDeleteView(generic.BulkDeleteView):
    queryset = InvoiceLine.objects.annotate()
    filterset = filtersets.InvoiceLineFilterSet
    table = tables.InvoiceLineListTable


# Unit


@register_model_view(Unit)
class UnitView(generic.ObjectView):
    queryset = Unit.objects.all()
    template_name = 'generic/object.html'
    layout = layout.SimpleLayout(
        left_panels=[panels.UnitPanel(), CustomFieldsPanel()],
        right_panels=[TagsPanel(), CommentsPanel()],
        bottom_panels=[
            ObjectsTablePanel(
                model='netbox_contract.contractline',
                title=_('Contract lines'),
                filters={'unit_id': lambda ctx: ctx['object'].pk},
                exclude_columns=['unit'],
            ),
        ],
    )


@register_model_view(Unit, 'list', path='', detail=False)
class UnitListView(generic.ObjectListView):
    queryset = Unit.objects.all()
    table = tables.UnitListTable
    filterset = filtersets.UnitFilterSet
    filterset_form = forms.UnitFilterForm


@register_model_view(Unit, 'add', detail=False)
@register_model_view(Unit, 'edit')
class UnitEditView(generic.ObjectEditView):
    queryset = Unit.objects.all()
    form = forms.UnitForm


@register_model_view(Unit, 'delete')
class UnitDeleteView(generic.ObjectDeleteView):
    queryset = Unit.objects.all()


@register_model_view(Unit, 'bulk_import', path='import', detail=False)
class UnitBulkImportView(generic.BulkImportView):
    queryset = Unit.objects.all()
    model_form = forms.UnitImportForm
    table = tables.UnitListTable


@register_model_view(Unit, 'bulk_edit', path='edit', detail=False)
class UnitBulkEditView(generic.BulkEditView):
    queryset = Unit.objects.all()
    filterset = filtersets.UnitFilterSet
    table = tables.UnitListTable
    form = forms.UnitBulkEditForm


@register_model_view(Unit, 'bulk_delete', path='delete', detail=False)
class UnitBulkDeleteView(generic.BulkDeleteView):
    queryset = Unit.objects.all()
    filterset = filtersets.UnitFilterSet
    table = tables.UnitListTable


# ContractLine


@register_model_view(ContractLine)
class ContractLineView(generic.ObjectView):
    queryset = ContractLine.objects.select_related('contract', 'unit', 'replaces')
    actions = (CloneObject, EditObject, DeleteObject, AmendContractLine)
    layout = layout.SimpleLayout(
        left_panels=[
            panels.MessagePanel('netbox_contract/panels/line_lock.html'),
            panels.ContractLinePanel(),
            CustomFieldsPanel(),
        ],
        right_panels=[TagsPanel(), CommentsPanel()],
    )

    def get_extra_context(self, request, instance):
        return {'lock_message': instance.lock_message()}


@register_model_view(ContractLine, 'amend', path='amend')
class ContractLineAmendView(BaseObjectView):
    """End a contract line and create the line that replaces it with a new unit price or quantity (FR-030)."""

    queryset = ContractLine.objects.select_related('contract', 'unit')
    template_name = 'netbox_contract/contractline_amend.html'

    additional_permissions = ['netbox_contract.view_contractline']

    def get_required_permission(self):
        # The "amend" action of object permissions (research D6); the queryset is restricted to it
        return 'netbox_contract.amend_contractline'

    def has_permission(self):
        if not super().has_permission():
            return False
        # Only lines the user may both view and amend, object constraints included
        self.queryset = self.queryset.restrict(self.request.user, 'view')
        return True

    def render_form(self, request, line, form):
        return render(request, self.template_name, {
            'object': line,
            'form': form,
            'last_invoiced_date': amendments.last_invoiced_date(line),
            'return_url': line.get_absolute_url(),
        })

    def get(self, request, pk):
        line = self.get_object(pk=pk)
        form = forms.ContractLineAmendForm(initial={'unit_price': line.unit_price, 'quantity': line.quantity})
        return self.render_form(request, line, form)

    def post(self, request, pk):
        line = self.get_object(pk=pk)
        form = forms.ContractLineAmendForm(request.POST)
        if form.is_valid():
            try:
                new = amendments.amend_contract_line(line, **form.cleaned_data)
            except amendments.AmendmentError as e:
                for field, message in e.errors.items():
                    form.add_error(None if field == '__all__' else field, message)
            else:
                messages.success(request, _('Contract line amended from {date}.').format(date=new.start_date))
                return redirect(new.get_absolute_url())
        return self.render_form(request, line, form)


@register_model_view(ContractLine, 'list', path='', detail=False)
class ContractLineListView(generic.ObjectListView):
    queryset = ContractLine.objects.with_lock_state().select_related('contract', 'unit').prefetch_related(
        'accounting_dimensions'
    )
    table = tables.ContractLineListTable
    filterset = filtersets.ContractLineFilterSet
    filterset_form = forms.ContractLineFilterForm


@register_model_view(ContractLine, 'add', detail=False)
@register_model_view(ContractLine, 'edit')
class ContractLineEditView(generic.ObjectEditView):
    """The add view accepts ?contract=<id> to pre-select the contract."""

    queryset = ContractLine.objects.all()
    form = forms.ContractLineForm
    template_name = 'netbox_contract/contractline_edit.html'

    def get_extra_context(self, request, instance):
        return {'lock_message': instance.lock_message() if instance.pk else None}


@register_model_view(ContractLine, 'delete')
class ContractLineDeleteView(generic.ObjectDeleteView):
    queryset = ContractLine.objects.all()


@register_model_view(ContractLine, 'bulk_import', path='import', detail=False)
class ContractLineBulkImportView(generic.BulkImportView):
    queryset = ContractLine.objects.all()
    model_form = forms.ContractLineImportForm
    table = tables.ContractLineListTable


@register_model_view(ContractLine, 'bulk_edit', path='edit', detail=False)
class ContractLineBulkEditView(generic.BulkEditView):
    queryset = ContractLine.objects.select_related('contract', 'unit')
    filterset = filtersets.ContractLineFilterSet
    table = tables.ContractLineListTable
    form = forms.ContractLineBulkEditForm


@register_model_view(ContractLine, 'bulk_delete', path='delete', detail=False)
class ContractLineBulkDeleteView(generic.BulkDeleteView):
    queryset = ContractLine.objects.select_related('contract', 'unit')
    filterset = filtersets.ContractLineFilterSet
    table = tables.ContractLineListTable


# Accounting dimension


@register_model_view(AccountingDimension)
class AccountingDimensionView(generic.ObjectView):
    queryset = AccountingDimension.objects.all()
    template_name = 'generic/object.html'
    layout = layout.SimpleLayout(
        left_panels=[panels.AccountingDimensionPanel(), CustomFieldsPanel()],
        right_panels=[TagsPanel(), CommentsPanel()],
    )


@register_model_view(AccountingDimension, 'list', path='', detail=False)
class AccountingDimensionListView(generic.ObjectListView):
    queryset = AccountingDimension.objects.all()
    table = tables.AccountingDimensionListTable
    filterset = filtersets.AccountingDimensionFilterSet
    filterset_form = forms.AccountingDimensionFilterForm


@register_model_view(AccountingDimension, 'add', detail=False)
@register_model_view(AccountingDimension, 'edit')
class AccountingDimensionEditView(generic.ObjectEditView):
    queryset = AccountingDimension.objects.all()
    form = forms.AccountingDimensionForm


@register_model_view(AccountingDimension, 'delete')
class AccountingDimensionDeleteView(generic.ObjectDeleteView):
    queryset = AccountingDimension.objects.all()


@register_model_view(AccountingDimension, 'bulk_import', path='import', detail=False)
class AccountingDimensionBulkImportView(generic.BulkImportView):
    queryset = AccountingDimension.objects.all()
    model_form = forms.AccountingDimensionImportForm
    table = tables.AccountingDimensionListTable


@register_model_view(AccountingDimension, 'bulk_edit', path='edit', detail=False)
class AccountingDimensionBulkEditView(generic.BulkEditView):
    queryset = AccountingDimension.objects.annotate()
    filterset = filtersets.AccountingDimensionFilterSet
    table = tables.AccountingDimensionListTable
    form = forms.AccountingDimensionBulkEditForm


@register_model_view(AccountingDimension, 'bulk_delete', path='delete', detail=False)
class AccountingDimensionBulkDeleteView(generic.BulkDeleteView):
    queryset = AccountingDimension.objects.annotate()
    filterset = filtersets.AccountingDimensionFilterSet
    table = tables.AccountingDimensionListTable
