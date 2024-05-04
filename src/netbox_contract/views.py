from datetime import date, timedelta

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import F
from django.shortcuts import get_object_or_404, render
from netbox.views import generic
from netbox.views.generic.utils import get_prerequisite_model
from tenancy.views import ObjectContactsView
from utilities.forms import restrict_form_fields
from utilities.utils import normalize_querydict
from utilities.views import register_model_view

from . import filtersets, forms, tables
from .models import Contract, ContractAssignment, Invoice, ServiceProvider

plugin_settings = settings.PLUGINS_CONFIG['netbox_contract']

# ServiceProvider views


@register_model_view(ServiceProvider, 'contacts')
class ServiceProviderContactsView(ObjectContactsView):
    queryset = ServiceProvider.objects.all()


class ServiceProviderView(generic.ObjectView):
    queryset = ServiceProvider.objects.all()


class ServiceProviderListView(generic.ObjectListView):
    queryset = ServiceProvider.objects.all()
    table = tables.ServiceProviderListTable
    filterset = filtersets.ServiceProviderFilterSet
    filterset_form = forms.ServiceProviderFilterSetForm


class ServiceProviderEditView(generic.ObjectEditView):
    queryset = ServiceProvider.objects.all()
    form = forms.ServiceProviderForm


class ServiceProviderDeleteView(generic.ObjectDeleteView):
    queryset = ServiceProvider.objects.all()


class ServiceProviderBulkImportView(generic.BulkImportView):
    queryset = ServiceProvider.objects.all()
    model_form = forms.ServiceProviderCSVForm
    table = tables.ServiceProviderListTable


class ServiceProviderBulkEditView(generic.BulkEditView):
    queryset = ServiceProvider.objects.annotate()
    filterset = filtersets.ServiceProviderFilterSet
    table = tables.ServiceProviderListTable
    form = forms.ServiceProviderBulkEditForm


class ServiceProviderBulkDeleteView(generic.BulkDeleteView):
    queryset = ServiceProvider.objects.annotate()
    filterset = filtersets.ServiceProviderFilterSet
    table = tables.ServiceProviderListTable


# Contract assignment view


class ContractAssignmentView(generic.ObjectView):
    queryset = ContractAssignment.objects.all()


class ContractAssignmentListView(generic.ObjectListView):
    queryset = ContractAssignment.objects.all()
    table = tables.ContractAssignmentListTable
    filterset = filtersets.ContractAssignmentFilterSet
    filterset_form = forms.ContractAssignmentFilterSetForm
    actions = {
        'import': {'add'},
        'export': set(),
        'bulk_edit': {'change'},
        'bulk_delete': {'delete'},
    }


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


class ContractAssignmentDeleteView(generic.ObjectDeleteView):
    queryset = ContractAssignment.objects.all()


class ContractAssignmentBulkImportView(generic.BulkImportView):
    queryset = ContractAssignment.objects.all()
    model_form = forms.ContractAssignmentImportForm
    table = tables.ContractAssignmentListTable


# Contract views


@register_model_view(Contract)
class ContractView(generic.ObjectView):
    queryset = Contract.objects.annotate(yrc=F('mrc') * 12)

    def get_extra_context(self, request, instance):
        invoices_table = tables.InvoiceListTable(instance.invoices.all())
        invoices_table.configure(request)
        assignments_table = tables.ContractAssignmentContractTable(
            instance.assignments.all()
        )
        assignments_table.configure(request)
        childs_table = tables.ContractListBottomTable(instance.childs.all())
        childs_table.configure(request)

        hidden_fields = plugin_settings.get('hidden_contract_fields')

        return {
            'hidden_fields': hidden_fields,
            'invoices_table': invoices_table,
            'assignments_table': assignments_table,
            'childs_table': childs_table,
        }


class ContractListView(generic.ObjectListView):
    queryset = Contract.objects.annotate(yrc=F('mrc') * 12)
    table = tables.ContractListTable
    filterset = filtersets.ContractFilterSet
    filterset_form = forms.ContractFilterSetForm


class ContractEditView(generic.ObjectEditView):
    queryset = Contract.objects.all()
    form = forms.ContractForm

    def alter_object(self, obj, request, url_args, url_kwargs):
        """
        When this method is called after a Post,
        it is used here to set the external partie object id for exiting objects,
        In any case, this happens before the form is instanciated.

        Args:
            obj: The object being edited
            request: The current request
            url_args: URL path args
            url_kwargs: URL path kwargs
        """

        if request.method == 'POST':
            data = normalize_querydict(request.POST)
            obj.external_partie_object_id = data['external_partie_object']
            external_partie_object_type_id = data['external_partie_object_type']
            obj.external_partie_object_type = ContentType.objects.get(
                id=external_partie_object_type_id
            )
            external_partie_object_type = obj.external_partie_object_type
            obj.external_partie_object = (
                external_partie_object_type.get_object_for_this_type(
                    id=obj.external_partie_object_id
                )
            )

        return obj


class ContractDeleteView(generic.ObjectDeleteView):
    queryset = Contract.objects.all()


class ContractBulkImportView(generic.BulkImportView):
    queryset = Contract.objects.all()
    model_form = forms.ContractCSVForm
    table = tables.ContractListTable


class ContractBulkEditView(generic.BulkEditView):
    queryset = Contract.objects.all()
    filterset = filtersets.ContractFilterSet
    table = tables.ContractListTable
    form = forms.ContractBulkEditForm


class ContractBulkDeleteView(generic.BulkDeleteView):
    queryset = Contract.objects.all()
    filterset = filtersets.ContractFilterSet
    table = tables.ContractListTable


# Invoice views


@register_model_view(Invoice)
class InvoiceView(generic.ObjectView):
    queryset = Invoice.objects.all()

    def get_extra_context(self, request, instance):
        contracts_table = tables.ContractListTable(instance.contracts.all())
        contracts_table.configure(request)
        hidden_fields = plugin_settings.get('hidden_invoice_fields')

        return {
            'hidden_fields': hidden_fields,
            'contracts_table': contracts_table,
        }


class InvoiceListView(generic.ObjectListView):
    queryset = Invoice.objects.all()
    table = tables.InvoiceListTable
    filterset = filtersets.InvoiceFilterSet
    filterset_form = forms.InvoiceFilterSetForm


class InvoiceEditView(generic.ObjectEditView):
    queryset = Invoice.objects.all()
    form = forms.InvoiceForm

    def get(self, request, *args, **kwargs):
        """
        GET request handler
            Overrides the ObjectEditView function to include form initialization
            with data from the parent contract object

        Args:
            request: The current request
        """
        obj = self.get_object(**kwargs)
        obj = self.alter_object(obj, request, args, kwargs)
        model = self.queryset.model

        initial_data = normalize_querydict(request.GET)
        initial_data['date'] = date.today()
        if 'contracts' in initial_data.keys():
            contract = Contract.objects.get(pk=initial_data['contracts'])

            try:
                last_invoice = contract.invoices.latest('period_end')
                new_period_start = last_invoice.period_end + timedelta(days=1)
            except ObjectDoesNotExist:
                if contract.start_date:
                    new_period_start = contract.start_date
                else:
                    new_period_start = None

            if new_period_start:
                initial_data['period_start'] = new_period_start
                delta = relativedelta(months=contract.invoice_frequency)
                new_period_end = new_period_start + delta - timedelta(days=1)
                initial_data['period_end'] = new_period_end

            initial_data['amount'] = contract.mrc * contract.invoice_frequency
            initial_data['currency'] = contract.currency
            if contract.accounting_dimensions:
                initial_data['accounting_dimensions'] = contract.accounting_dimensions

        form = self.form(instance=obj, initial=initial_data)
        restrict_form_fields(form, request.user)

        return render(
            request,
            self.template_name,
            {
                'model': model,
                'object': obj,
                'form': form,
                'return_url': self.get_return_url(request, obj),
                'prerequisite_model': get_prerequisite_model(self.queryset),
                **self.get_extra_context(request, obj),
            },
        )


class InvoiceDeleteView(generic.ObjectDeleteView):
    queryset = Invoice.objects.all()


class InvoiceBulkImportView(generic.BulkImportView):
    queryset = Invoice.objects.all()
    model_form = forms.InvoiceCSVForm
    table = tables.InvoiceListTable


class InvoiceBulkEditView(generic.BulkEditView):
    queryset = Invoice.objects.all()
    filterset = filtersets.InvoiceFilterSet
    table = tables.InvoiceListTable
    form = forms.InvoiceBulkEditForm


class InvoiceBulkDeleteView(generic.BulkDeleteView):
    queryset = Invoice.objects.all()
    filterset = filtersets.InvoiceFilterSet
    table = tables.InvoiceListTable
