from datetime import timedelta, date
from dateutil.relativedelta import relativedelta
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import render, get_object_or_404
from netbox.views import generic
from netbox.views.generic.utils import get_prerequisite_model
from utilities.utils import count_related, normalize_querydict
from utilities.forms import restrict_form_fields
from circuits.models import Circuit
from . import forms, models, tables, filtersets

# ServiceProvider views

class ServiceProviderView(generic.ObjectView):
    queryset = models.ServiceProvider.objects.all()

class ServiceProviderListView(generic.ObjectListView):
    queryset = models.ServiceProvider.objects.all()
    table = tables.ServiceProviderListTable
    filterset = filtersets.ServiceProviderFilterSet
    filterset_form = forms.ServiceProviderFilterSetForm

class ServiceProviderEditView(generic.ObjectEditView):
    queryset = models.ServiceProvider.objects.all()
    form = forms.ServiceProviderForm

class ServiceProviderDeleteView(generic.ObjectDeleteView):
    queryset = models.ServiceProvider.objects.all()

class ServiceProviderBulkImportView(generic.BulkImportView):
    queryset = models.ServiceProvider.objects.all()
    model_form = forms.ServiceProviderCSVForm
    table = tables.ServiceProviderListTable

class ServiceProviderBulkEditView(generic.BulkEditView):
    queryset = models.ServiceProvider.objects.annotate()
    filterset = filtersets.ServiceProviderFilterSet
    table = tables.ServiceProviderListTable
    form = forms.ServiceProviderBulkEditForm

class ServiceProviderBulkDeleteView(generic.BulkDeleteView):
    queryset = models.ServiceProvider.objects.annotate()
    filterset = filtersets.ServiceProviderFilterSet
    table = tables.ServiceProviderListTable

# Contract assignement view

class ContractAssignementView(generic.ObjectView):
    queryset = models.ContractAssignement.objects.all()

class ContractAssignementListView(generic.ObjectListView):
    queryset = models.ContractAssignement.objects.all()
    table = tables.ContractAssignementListTable
    filterset = filtersets.ContractAssignementFilterSet
    filterset_form = forms.ContractAssignementFilterSetForm

class ContractAssignementEditView(generic.ObjectEditView):
    queryset = models.ContractAssignement.objects.all()
    form = forms.ContractAssignementForm

    def alter_object(self, instance, request, args, kwargs):
        if not instance.pk:
            # Assign the object based on URL kwargs
            content_type = get_object_or_404(ContentType, pk=request.GET.get('content_type'))
            instance.object = get_object_or_404(content_type.model_class(), pk=request.GET.get('object_id'))
        return instance

    def get_extra_addanother_params(self, request):
        return {
            'content_type': request.GET.get('content_type'),
            'object_id': request.GET.get('object_id'),
        }

class ContractAssignementDeleteView(generic.ObjectDeleteView):
    queryset = models.ContractAssignement.objects.all()

# Contract views

class ContractView(generic.ObjectView):
    queryset = models.Contract.objects.all()

    def get_extra_context(self, request, instance):
        invoices_table = tables.InvoiceListTable(instance.invoices.all())
        invoices_table.configure(request)
        circuit_table = tables.ContractCircuitListTable(instance.circuit.all())
        circuit_table.configure(request)
        assignements_table = tables.ContractAssignementListTable(instance.assignments.all())
        assignements_table.configure(request)

        return {
            'invoices_table': invoices_table,
            'circuit_table': circuit_table,
            'assignements_table': assignements_table,
        }

class ContractListView(generic.ObjectListView):
    queryset = models.Contract.objects.all()
    table = tables.ContractListTable
    filterset = filtersets.ContractFilterSet
    filterset_form = forms.ContractFilterSetForm

class ContractEditView(generic.ObjectEditView):
    queryset = models.Contract.objects.all()
    form = forms.ContractForm

class ContractDeleteView(generic.ObjectDeleteView):
    queryset = models.Contract.objects.all()

class ContractBulkImportView(generic.BulkImportView):
    queryset = models.Contract.objects.all()
    model_form = forms.ContractCSVForm
    table = tables.ContractListTable

class ContractBulkEditView(generic.BulkEditView):
    queryset = models.Contract.objects.annotate(
        count_circuits=count_related(Circuit, 'contracts')
    )
    filterset = filtersets.ContractFilterSet
    table = tables.ContractListTable
    form = forms.ContractBulkEditForm

class ContractBulkDeleteView(generic.BulkDeleteView):
    queryset = models.Contract.objects.annotate(
        count_circuits=count_related(Circuit, 'contracts')
    )
    filterset = filtersets.ContractFilterSet
    table = tables.ContractListTable

# Invoice views

class InvoiceView(generic.ObjectView):
    queryset = models.Invoice.objects.all()

    def get_extra_context(self, request, instance):
        contracts_table = tables.ContractListTable(instance.contracts.all())
        contracts_table.configure(request)

        return {
            'contracts_table': contracts_table,
        }

class InvoiceListView(generic.ObjectListView):
    queryset = models.Invoice.objects.all()
    table = tables.InvoiceListTable
    filterset = filtersets.InvoiceFilterSet
    filterset_form = forms.InvoiceFilterSetForm

class InvoiceEditView(generic.ObjectEditView):
    queryset = models.Invoice.objects.all()
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
            contract = models.Contract.objects.get(pk=initial_data['contracts'])

            try:
                last_invoice = contract.invoices.latest('period_end')
                new_period_start = last_invoice.period_end + timedelta(days=1)
            except ObjectDoesNotExist:
                if contract.start_date :
                    new_period_start = contract.start_date
                else:
                    new_period_start = None

            if new_period_start :
                initial_data['period_start'] = new_period_start
                delta = relativedelta(months=contract.invoice_frequency)
                new_period_end = new_period_start + delta - timedelta(days=1)
                initial_data['period_end'] = new_period_end

            initial_data['amount'] = contract.mrc * contract.invoice_frequency
            initial_data['currency'] = contract.currency
            if contract.accounting_dimensions :
                initial_data['accounting_dimensions'] = contract.accounting_dimensions

        form = self.form(instance=obj, initial=initial_data)
        restrict_form_fields(form, request.user)

        return render(request, self.template_name, {
            'model': model,
            'object': obj,
            'form': form,
            'return_url': self.get_return_url(request, obj),
            'prerequisite_model': get_prerequisite_model(self.queryset),
            **self.get_extra_context(request, obj),
        })

class InvoiceDeleteView(generic.ObjectDeleteView):
    queryset = models.Invoice.objects.all()

class InvoiceBulkImportView(generic.BulkImportView):
    queryset = models.Invoice.objects.all()
    model_form = forms.InvoiceCSVForm
    table = tables.InvoiceListTable

class InvoiceBulkEditView(generic.BulkEditView):
    queryset = models.Invoice.objects.all()
    filterset = filtersets.InvoiceFilterSet
    table = tables.InvoiceListTable
    form = forms.InvoiceBulkEditForm

class InvoiceBulkDeleteView(generic.BulkDeleteView):
    queryset = models.Invoice.objects.all()
    filterset = filtersets.InvoiceFilterSet
    table = tables.InvoiceListTable
