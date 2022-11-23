from django import forms
from netbox.forms import NetBoxModelForm, NetBoxModelFilterSetForm, NetBoxModelBulkEditForm, NetBoxModelCSVForm
from utilities.forms.fields import CommentField, DynamicModelChoiceField
from utilities.forms import CSVModelChoiceField
from circuits.models import Circuit
from .models import Contract, Invoice

class ContractForm(NetBoxModelForm):
    comments = CommentField()
    circuit=DynamicModelChoiceField(
        queryset=Circuit.objects.all()
    )

    class Meta:
        model = Contract
        fields = ('name', 'external_partie', 'internal_partie', 'circuit', 'comments', 'tags')

class InvoiceForm(NetBoxModelForm):
    contract=DynamicModelChoiceField(
        queryset=Contract.objects.all()
    )

    class Meta:
        model = Invoice
        fields = ('number', 'contract', 'tags')

class ContractFilterSetForm(NetBoxModelFilterSetForm):
    model = Contract
    external_partie= forms.CharField(
        required=False
    )
    internal_partie= forms.CharField(
        required=False
    )
    circuit = DynamicModelChoiceField(
        queryset=Circuit.objects.all(),
        required=False
    )

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
            'name', 'external_partie', 'internal_partie', 'circuit', 'comments',
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
            'number', 'contract',
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
