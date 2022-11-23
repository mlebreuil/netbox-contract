from netbox.views import generic
from utilities.utils import count_related
from circuits.models import Circuit
from . import forms, models, tables, filtersets

# Contract views

class ContractView(generic.ObjectView):
    queryset = models.Contract.objects.all()

    def get_extra_context(self, request, instance):
        table = tables.InvoiceListTable(instance.invoice.all())
        table.configure(request)

        return {
            'invoices_table': table,
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
        count_circuits=count_related(Circuit, 'contract')
    )
    filterset = filtersets.ContractFilterSet
    table = tables.ContractListTable
    form = forms.ContractBulkEditForm

class ContractBulkDeleteView(generic.BulkDeleteView):
    queryset = models.Contract.objects.annotate(
        count_circuits=count_related(Circuit, 'contract')
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
