from datetime import date, timedelta

from circuits.models import Circuit
from dateutil.relativedelta import relativedelta
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404, render
from netbox.views import generic
from netbox.views.generic.utils import get_prerequisite_model
from utilities.forms import restrict_form_fields
from utilities.utils import count_related, normalize_querydict

from . import filtersets, forms, tables
from .models import Contract, ContractAssignement, Invoice, ServiceProvider

# ServiceProvider views


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


# Contract assignement view


class ContractAssignementView(generic.ObjectView):
    queryset = ContractAssignement.objects.all()


class ContractAssignementListView(generic.ObjectListView):
    queryset = ContractAssignement.objects.all()
    table = tables.ContractAssignementListTable
    filterset = filtersets.ContractAssignementFilterSet
    filterset_form = forms.ContractAssignementFilterSetForm
    actions = [
        'import',
        'export',
    ]


class ContractAssignementEditView(generic.ObjectEditView):
    queryset = ContractAssignement.objects.all()
    form = forms.ContractAssignementForm

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


class ContractAssignementDeleteView(generic.ObjectDeleteView):
    queryset = ContractAssignement.objects.all()


class ContractAssignementBulkImportView(generic.BulkImportView):
    queryset = ContractAssignement.objects.all()
    model_form = forms.ContractAssignementImportForm
    table = tables.ContractAssignementListTable


# Contract views


class ContractView(generic.ObjectView):
    queryset = Contract.objects.all()

    def get_extra_context(self, request, instance):
        invoices_table = tables.InvoiceListTable(instance.invoices.all())
        invoices_table.configure(request)
        assignements_table = tables.ContractAssignementContractTable(
            instance.assignments.all()
        )
        assignements_table.configure(request)
        childs_table = tables.ContractListBottomTable(instance.childs.all())
        childs_table.configure(request)

        return {
            'invoices_table': invoices_table,
            'assignements_table': assignements_table,
            'childs_table': childs_table,
        }


class ContractListView(generic.ObjectListView):
    queryset = Contract.objects.all()
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
    queryset = Contract.objects.annotate(
        count_circuits=count_related(Circuit, 'contracts')
    )
    filterset = filtersets.ContractFilterSet
    table = tables.ContractListTable


# Invoice views


class InvoiceView(generic.ObjectView):
    queryset = Invoice.objects.all()

    def get_extra_context(self, request, instance):
        contracts_table = tables.ContractListTable(instance.contracts.all())
        contracts_table.configure(request)

        return {
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
