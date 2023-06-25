from django import forms
from django.contrib.contenttypes.models import ContentType
import django_filters
from netbox.forms import NetBoxModelForm, NetBoxModelFilterSetForm, NetBoxModelBulkEditForm, NetBoxModelImportForm
from utilities.forms.fields import CommentField, CSVChoiceField, DynamicModelChoiceField, DynamicModelMultipleChoiceField, MultipleChoiceField, CSVModelChoiceField, SlugField, CSVContentTypeField
from utilities.forms.widgets import DatePicker
from extras.filters import TagFilter
from circuits.models import Circuit
from tenancy.models import Tenant
from .models import Contract, Invoice, ServiceProvider, StatusChoices, ContractAssignement

class ContractForm(NetBoxModelForm):
    comments = CommentField()

    external_partie=DynamicModelChoiceField(
        queryset=ServiceProvider.objects.all()
    )
    tenant=DynamicModelChoiceField(
        queryset=Tenant.objects.all()
    )
    parent=DynamicModelChoiceField(
        queryset=Contract.objects.all(),
        required=False
    )

    class Meta:
        model = Contract
        fields = ('name', 'external_partie', 'external_reference', 'internal_partie','tenant', 'status',
          'start_date', 'end_date','initial_term', 'renewal_term', 'currency','accounting_dimensions',
          'mrc', 'nrc','invoice_frequency','parent','documents', 'comments', 'tags')

        widgets = {
            'start_date': DatePicker(),
            'end_date': DatePicker(),
        }

class InvoiceForm(NetBoxModelForm):
    contracts=DynamicModelMultipleChoiceField(
        queryset=Contract.objects.all(),
        required=False
    )

    class Meta:
        model = Invoice
        fields = ('number', 'date', 'contracts','period_start', 'period_end',
          'currency','accounting_dimensions','amount', 'documents','comments','tags')
        widgets = {
            'date': DatePicker(),
            'period_start': DatePicker(),
            'period_end': DatePicker(),
        }

class ContractFilterSetForm(NetBoxModelFilterSetForm):
    model = Contract
    external_partie=DynamicModelChoiceField(
        queryset=ServiceProvider.objects.all(),
        required=False
    )
    tenant=DynamicModelChoiceField(
        queryset=Tenant.objects.all(),
        required=False
    )
    external_reference=forms.CharField(
        required=False
    )
    internal_partie= forms.CharField(
        required=False
    )
    status = MultipleChoiceField(
        choices=StatusChoices,
        required= False
    )
    circuit = DynamicModelMultipleChoiceField(
        queryset=Circuit.objects.all(),
        required=False
    )
    parent=DynamicModelChoiceField(
        queryset=Contract.objects.all(),
        required=False
    )

class InvoiceFilterSetForm(NetBoxModelFilterSetForm):
    model = Invoice
    contracts=DynamicModelMultipleChoiceField(
        queryset=Contract.objects.all(),
        required=False
    )

class ContractCSVForm(NetBoxModelImportForm):
    external_partie = CSVModelChoiceField(
        queryset=ServiceProvider.objects.all(),
        to_field_name='name',
        help_text='Service provider name'
    )
    tenant = CSVModelChoiceField(
        queryset=Tenant.objects.all(),
        to_field_name='name',
        help_text='Tenant name',
        required=False
    )
    status = CSVChoiceField(
        choices=StatusChoices,
        help_text='Contract status'
    )
    parent = CSVModelChoiceField(
        queryset=Contract.objects.all(),
        to_field_name='name',
        help_text='Contract name',
        required=False
    )

    class Meta:
        model = Contract
        fields = [
            'name', 'external_partie', 'internal_partie', 'external_reference','tenant', 'status',
            'start_date', 'end_date','initial_term', 'renewal_term', 'mrc', 'nrc',
            'invoice_frequency', 'documents', 'comments', 'parent'
        ]

class ContractBulkEditForm(NetBoxModelBulkEditForm):
    name = forms.CharField(
        max_length=100,
        required=True
    )
    external_partie = DynamicModelChoiceField(
        queryset=ServiceProvider.objects.all(),
        required=False
    )
    external_reference=forms.CharField(
        max_length=100,
        required=False
    )
    internal_partie = forms.CharField(
        max_length=30,
        required=True
    )
    comments = CommentField()
    circuit=DynamicModelChoiceField(
        queryset=Circuit.objects.all(),
        required=False
    )
    parent = DynamicModelChoiceField(
        queryset=Contract.objects.all(),
        required=False
    )

    nullable_fields = (
        'comments',
    )
    model = Contract

class InvoiceCSVForm(NetBoxModelImportForm):
    contracts = CSVModelChoiceField(
        queryset=Contract.objects.all(),
        to_field_name='name',
        help_text='Related Contracts'
    )

    class Meta:
        model = Invoice
        fields = [
            'number', 'date', 'contracts','period_start', 'period_end',
            'amount', 'tags'
        ]

class InvoiceBulkEditForm(NetBoxModelBulkEditForm):
    number = forms.CharField(
        max_length=100,
        required=True
    )
    contracts=DynamicModelMultipleChoiceField(
        queryset=Contract.objects.all(),
        required=False
    )
    model = Invoice

# service Provider forms

class ServiceProviderForm(NetBoxModelForm):
    slug = SlugField()
    comments = CommentField()

    class Meta:
        model = ServiceProvider
        fields = ('name', 'slug','portal_url',
            'comments', 'tags')

class ServiceProviderFilterSetForm(NetBoxModelFilterSetForm):
    model = ServiceProvider
    tag = TagFilter()

class ServiceProviderCSVForm(NetBoxModelImportForm):
    slug = SlugField()
    comments = CommentField()
    class Meta:
        model = ServiceProvider
        fields = [
            'name', 'slug','portal_url',
            'comments', 'tags'
        ]

class ServiceProviderBulkEditForm(NetBoxModelBulkEditForm):
    name = forms.CharField(
        max_length=100,
        required=True
    )
    comments = CommentField()
    nullable_fields = (
        'comments',
    )
    model = ServiceProvider

# ContractAssignement

class ContractAssignementForm(NetBoxModelForm):
    contract=DynamicModelChoiceField(
        queryset=Contract.objects.all()
    )

    class Meta:
        model = ContractAssignement
        fields = ['content_type', 'object_id', 'contract','tags']
        widgets = {
            'content_type': forms.HiddenInput(),
            'object_id': forms.HiddenInput(),
        }

class ContractAssignementFilterSetForm(NetBoxModelFilterSetForm):
    model = ContractAssignement
    contract=DynamicModelChoiceField(
        queryset=Contract.objects.all()
    )

class ContractAssignementImportForm(NetBoxModelImportForm):
    content_type = CSVContentTypeField(
        queryset=ContentType.objects.all(),
        help_text="Content Type in the form <app>.<model>"
    )
    contract = CSVModelChoiceField(
        queryset=Contract.objects.all(),
        help_text="Contract id"
    )
    class Meta:
        model = ContractAssignement
        fields = ['content_type', 'object_id', 'contract','tags']
