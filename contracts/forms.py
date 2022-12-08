from django import forms
import django_filters
from netbox.forms import NetBoxModelForm, NetBoxModelFilterSetForm, NetBoxModelBulkEditForm, NetBoxModelCSVForm
from utilities.forms.fields import CommentField, DynamicModelChoiceField, DynamicModelMultipleChoiceField
from utilities.forms import CSVModelChoiceField, DatePicker,SlugField
from extras.filters import TagFilter
from circuits.models import Circuit
from .models import Contract, Invoice, ServiceProvider

class ContractForm(NetBoxModelForm):
    comments = CommentField()
    circuit=DynamicModelMultipleChoiceField(
        queryset=Circuit.objects.all()
    )
    external_partie=DynamicModelChoiceField(
        queryset=ServiceProvider.objects.all()
    )

    class Meta:
        model = Contract
        fields = ('name', 'external_partie', 'internal_partie', 'status',
          'start_date', 'initial_term', 'renewal_term', 'mrc', 'nrc', 'invoice_frequency',
          'circuit', 'comments', 'tags')

        widgets = {
            'start_date': DatePicker(),
        }

class InvoiceForm(NetBoxModelForm):
    contract=DynamicModelChoiceField(
        queryset=Contract.objects.all()
    )

    class Meta:
        model = Invoice
        fields = ('number', 'contract', 'period_start', 'period_end',
          'amount', 'tags')
        widgets = {
            'period_start': DatePicker(),
            'period_end': DatePicker(),
        }

class ContractFilterSetForm(NetBoxModelFilterSetForm):
    model = Contract
    external_partie=DynamicModelMultipleChoiceField(
        queryset=ServiceProvider.objects.all(),
        required=False
    )
    internal_partie= forms.CharField(
        required=False
    )
    status = django_filters.MultipleChoiceFilter(
        choices=(
            ('active', 'Active'),
            ('canceled', 'Canceled'),
        ),
        null_value=None
    )
    circuit = DynamicModelMultipleChoiceField(
        queryset=Circuit.objects.all(),
        required=False
    )
    tag = TagFilter()

class InvoiceFilterSetForm(NetBoxModelFilterSetForm):
    model = Invoice
    contract = DynamicModelChoiceField(
        queryset=Contract.objects.all(),
        required=False
    )

class ContractCSVForm(NetBoxModelCSVForm):
    circuit = CSVModelChoiceField(
        queryset=Circuit.objects.all(),
        to_field_name='name',
        help_text='Related Circuit'
    )

    class Meta:
        model = Contract
        fields = [
            'name', 'external_partie', 'internal_partie', 'status',
            'start_date', 'initial_term', 'renewal_term', 'mrc', 'nrc',
            'invoice_frequency', 'circuit'
        ]

class ContractBulkEditForm(NetBoxModelBulkEditForm):
    name = forms.CharField(
        max_length=100,
        required=True
    )
    external_partie = forms.CharField(
        max_length=30,
        required=True
    )
    internal_partie = forms.CharField(
        max_length=30,
        required=True
    )
    comments = CommentField()
    circuit=DynamicModelChoiceField(
        queryset=Circuit.objects.all()
    )

    nullable_fields = (
        'comments',
    )
    model = Contract

class InvoiceCSVForm(NetBoxModelCSVForm):
    contract = CSVModelChoiceField(
        queryset=Contract.objects.all(),
        to_field_name='name',
        help_text='Related Contract'
    )

    class Meta:
        model = Invoice
        fields = [
            'number', 'contract', 'period_start', 'period_end',
            'amount', 'tags'
        ]

class InvoiceBulkEditForm(NetBoxModelBulkEditForm):
    number = forms.CharField(
        max_length=100,
        required=True
    )

    contract=DynamicModelChoiceField(
        queryset=Contract.objects.all()
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

class ServiceProviderCSVForm(NetBoxModelCSVForm):
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
