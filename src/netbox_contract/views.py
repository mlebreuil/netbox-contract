from datetime import timedelta
from dateutil.relativedelta import relativedelta
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render
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

# Contract views

class ContractView(generic.ObjectView):
    queryset = models.Contract.objects.all()

    def get_extra_context(self, request, instance):
        invoice_table = tables.InvoiceListTable(instance.invoice.all())
        invoice_table.configure(request)
        circuit_table = tables.ContractCircuitListTable(instance.circuit.all())
        circuit_table.configure(request)

        return {
            'invoices_table': invoice_table,
            'circuit_table': circuit_table,
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
        if 'contract' in initial_data.keys():
            contract = models.Contract.objects.get(pk=initial_data['contract'])

            try:
                last_invoice = contract.invoice.latest('period_end')
                new_period_start = last_invoice.period_end + timedelta(days=1)
            except ObjectDoesNotExist:
                new_period_start = contract.start_date

            initial_data['period_start'] = new_period_start
            delta = relativedelta(months=contract.invoice_frequency)
            new_period_end = new_period_start + delta
            initial_data['period_end'] = new_period_end
            initial_data['amount'] = contract.mrc

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
