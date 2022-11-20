from django import forms
from netbox.forms import NetBoxModelForm, NetBoxModelFilterSetForm
from utilities.forms.fields import CommentField, DynamicModelChoiceField
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
