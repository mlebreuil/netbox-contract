from django import forms
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from extras.filters import TagFilter
from netbox.forms import (
    NetBoxModelBulkEditForm,
    NetBoxModelFilterSetForm,
    NetBoxModelForm,
    NetBoxModelImportForm,
)
from tenancy.models import Tenant
from utilities.forms.fields import (
    CommentField,
    ContentTypeChoiceField,
    CSVChoiceField,
    CSVContentTypeField,
    CSVModelChoiceField,
    DynamicModelChoiceField,
    DynamicModelMultipleChoiceField,
    JSONField,
    SlugField,
)
from utilities.forms.widgets import DatePicker, HTMXSelect

from .constants import SERVICE_PROVIDER_MODELS
from .models import (
    Contract,
    ContractAssignement,
    InternalEntityChoices,
    Invoice,
    ServiceProvider,
    StatusChoices,
)

plugin_settings = settings.PLUGINS_CONFIG['netbox_contract']
default_dimensions = plugin_settings.get('default_accounting_dimensions')


class Dimensions(JSONField):
    """
    Custom wrapper around Netbox's JSONField
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.widget.attrs['placeholder'] = str(default_dimensions)


class ContractForm(NetBoxModelForm):
    comments = CommentField()

    external_partie_object_type = ContentTypeChoiceField(
        queryset=ContentType.objects.all(),
        limit_choices_to=SERVICE_PROVIDER_MODELS,
        widget=HTMXSelect(),
    )
    external_partie_object = forms.ModelChoiceField(queryset=None)
    tenant = DynamicModelChoiceField(queryset=Tenant.objects.all())
    parent = DynamicModelChoiceField(queryset=Contract.objects.all(), required=False)
    accounting_dimensions = Dimensions()

    def __init__(self, *args, **kwargs):
        initial = kwargs.get('initial', None)
        super().__init__(*args, **kwargs)

        # Initialize the external party object gfk
        if initial and 'external_partie_object_type' in initial:
            external_partie_object_type = ContentType.objects.get_for_id(
                initial['external_partie_object_type']
            )
            external_partie_class = external_partie_object_type.model_class()
            self.fields[
                'external_partie_object'
            ].queryset = external_partie_class.objects.all()
            if (
                self.instance.external_partie_object_type
                and self.instance.external_partie_object_type.id
                == external_partie_object_type.id
            ):
                self.fields[
                    'external_partie_object'
                ].initial = self.instance.external_partie_object
            else:
                self.fields['external_partie_object'].initial = None
        elif self.instance.external_partie_object_type:
            external_partie_class = (
                self.instance.external_partie_object_type.model_class()
            )
            self.fields[
                'external_partie_object'
            ].queryset = external_partie_class.objects.all()
            self.fields[
                'external_partie_object'
            ].initial = self.instance.external_partie_object
        else:
            self.fields[
                'external_partie_object'
            ].queryset = ServiceProvider.objects.all()
            self.fields['external_partie_object'].initial = None

        # initialize accounting dimentsions widget
        # self.fields[
        #         'accounting_dimensions'
        #     ].widget.attrs['placeholder'] = '{"key": "value"}'

    class Meta:
        model = Contract
        fields = (
            'name',
            'external_partie_object_type',
            'external_partie_object',
            'external_reference',
            'internal_partie',
            'tenant',
            'status',
            'start_date',
            'end_date',
            'initial_term',
            'renewal_term',
            'currency',
            'accounting_dimensions',
            'mrc',
            'nrc',
            'invoice_frequency',
            'parent',
            'documents',
            'comments',
            'tags',
        )

        widgets = {
            'start_date': DatePicker(),
            'end_date': DatePicker(),
        }


class InvoiceForm(NetBoxModelForm):
    contracts = DynamicModelMultipleChoiceField(
        queryset=Contract.objects.all(), required=False
    )

    class Meta:
        model = Invoice
        fields = (
            'number',
            'date',
            'contracts',
            'period_start',
            'period_end',
            'currency',
            'accounting_dimensions',
            'amount',
            'documents',
            'comments',
            'tags',
        )
        widgets = {
            'date': DatePicker(),
            'period_start': DatePicker(),
            'period_end': DatePicker(),
        }


class ContractFilterSetForm(NetBoxModelFilterSetForm):
    model = Contract

    tenant = DynamicModelChoiceField(queryset=Tenant.objects.all(), required=False)
    external_reference = forms.CharField(required=False)
    internal_partie = forms.CharField(required=False)
    status = forms.ChoiceField(choices=StatusChoices, required=False)
    parent = DynamicModelChoiceField(queryset=Contract.objects.all(), required=False)


class InvoiceFilterSetForm(NetBoxModelFilterSetForm):
    model = Invoice
    contracts = DynamicModelMultipleChoiceField(
        queryset=Contract.objects.all(), required=False
    )


class ContractCSVForm(NetBoxModelImportForm):
    external_partie_object_type = CSVContentTypeField(
        queryset=ContentType.objects.all(),
        limit_choices_to=SERVICE_PROVIDER_MODELS,
        help_text='service provider object type in the form <app>.<model>',
    )
    external_partie_object_id = forms.CharField(
        help_text='service provider object name', label='external_partie_name'
    )
    tenant = CSVModelChoiceField(
        queryset=Tenant.objects.all(),
        to_field_name='name',
        help_text='Tenant name',
        required=False,
    )
    status = CSVChoiceField(choices=StatusChoices, help_text='Contract status')
    parent = CSVModelChoiceField(
        queryset=Contract.objects.all(),
        to_field_name='name',
        help_text='Contract name',
        required=False,
    )

    class Meta:
        model = Contract
        fields = [
            'name',
            'external_partie_object_type',
            'external_partie_object_id',
            'external_reference',
            'internal_partie',
            'tenant',
            'status',
            'start_date',
            'end_date',
            'initial_term',
            'renewal_term',
            'currency',
            'accounting_dimensions',
            'mrc',
            'nrc',
            'invoice_frequency',
            'documents',
            'comments',
            'parent',
        ]

    def clean_external_partie_object_id(self):
        name = self.cleaned_data.get('external_partie_object_id')
        external_partie_object_type = self.cleaned_data.get(
            'external_partie_object_type'
        )
        external_partie_object = external_partie_object_type.get_object_for_this_type(
            name=name
        )

        return external_partie_object.id


class ContractBulkEditForm(NetBoxModelBulkEditForm):
    name = forms.CharField(max_length=100, required=False)

    external_reference = forms.CharField(max_length=100, required=False)
    internal_partie = forms.ChoiceField(choices=InternalEntityChoices, required=False)
    comments = CommentField(required=False)
    parent = DynamicModelChoiceField(queryset=Contract.objects.all(), required=False)

    nullable_fields = ('comments',)
    model = Contract


class InvoiceCSVForm(NetBoxModelImportForm):
    contracts = CSVModelChoiceField(
        queryset=Contract.objects.all(),
        to_field_name='name',
        help_text='Related Contracts',
    )

    class Meta:
        model = Invoice
        fields = [
            'number',
            'date',
            'contracts',
            'period_start',
            'period_end',
            'currency',
            'accounting_dimensions',
            'amount',
            'documents',
            'comments',
            'tags',
        ]


class InvoiceBulkEditForm(NetBoxModelBulkEditForm):
    number = forms.CharField(max_length=100, required=True)
    contracts = DynamicModelMultipleChoiceField(
        queryset=Contract.objects.all(), required=False
    )
    model = Invoice


# service Provider forms


class ServiceProviderForm(NetBoxModelForm):
    slug = SlugField()
    comments = CommentField()

    class Meta:
        model = ServiceProvider
        fields = ('name', 'slug', 'portal_url', 'comments', 'tags')


class ServiceProviderFilterSetForm(NetBoxModelFilterSetForm):
    model = ServiceProvider
    tag = TagFilter()


class ServiceProviderCSVForm(NetBoxModelImportForm):
    slug = SlugField()
    comments = CommentField()

    class Meta:
        model = ServiceProvider
        fields = ['name', 'slug', 'portal_url', 'comments', 'tags']


class ServiceProviderBulkEditForm(NetBoxModelBulkEditForm):
    name = forms.CharField(max_length=100, required=True)
    comments = CommentField()
    nullable_fields = ('comments',)
    model = ServiceProvider


# ContractAssignement


class ContractAssignementForm(NetBoxModelForm):
    contract = DynamicModelChoiceField(queryset=Contract.objects.all())

    class Meta:
        model = ContractAssignement
        fields = ['content_type', 'object_id', 'contract', 'tags']
        widgets = {
            'content_type': forms.HiddenInput(),
            'object_id': forms.HiddenInput(),
        }


class ContractAssignementFilterSetForm(NetBoxModelFilterSetForm):
    model = ContractAssignement
    contract = DynamicModelChoiceField(queryset=Contract.objects.all())


class ContractAssignementImportForm(NetBoxModelImportForm):
    content_type = CSVContentTypeField(
        queryset=ContentType.objects.all(),
        help_text='Content Type in the form <app>.<model>',
    )
    contract = CSVModelChoiceField(
        queryset=Contract.objects.all(), help_text='Contract id'
    )

    class Meta:
        model = ContractAssignement
        fields = ['content_type', 'object_id', 'contract', 'tags']
