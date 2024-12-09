from django import forms
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from netbox.forms import (
    NetBoxModelBulkEditForm,
    NetBoxModelFilterSetForm,
    NetBoxModelForm,
    NetBoxModelImportForm,
)
from tenancy.models import Tenant
from utilities.forms import BOOLEAN_WITH_BLANK_CHOICES
from utilities.forms.fields import (
    CommentField,
    ContentTypeChoiceField,
    CSVChoiceField,
    CSVContentTypeField,
    CSVModelChoiceField,
    CSVModelMultipleChoiceField,
    DynamicModelChoiceField,
    DynamicModelMultipleChoiceField,
    JSONField,
    SlugField,
    TagFilterField,
)
from utilities.forms.widgets import DatePicker, HTMXSelect

from .constants import SERVICE_PROVIDER_MODELS
from .models import (
    AccountingDimension,
    AccountingDimensionStatusChoices,
    Contract,
    ContractAssignment,
    CurrencyChoices,
    InternalEntityChoices,
    Invoice,
    InvoiceLine,
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


# Contract


class ContractForm(NetBoxModelForm):
    comments = CommentField()

    external_partie_object_type = ContentTypeChoiceField(
        queryset=ContentType.objects.all(),
        limit_choices_to=SERVICE_PROVIDER_MODELS,
        widget=HTMXSelect(),
    )
    external_partie_object = forms.ModelChoiceField(queryset=None)
    tenant = DynamicModelChoiceField(
        queryset=Tenant.objects.all(), required=False, selector=True
    )
    parent = DynamicModelChoiceField(
        queryset=Contract.objects.all(), required=False, selector=True
    )
    accounting_dimensions = Dimensions(required=False)

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

        # Initialise fields settings
        mandatory_fields = plugin_settings.get('mandatory_contract_fields')
        for field in mandatory_fields:
            self.fields[field].required = True
        hidden_fields = plugin_settings.get('hidden_contract_fields')
        for field in hidden_fields:
            if not self.fields[field].required:
                self.fields[field].widget = forms.HiddenInput()

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
            'yrc',
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

    def clean(self):
        super().clean()

        if self.cleaned_data['mrc'] and self.cleaned_data['yrc']:
            raise ValidationError(
                'you should set monthly OR yearly recuring costs not both'
            )


class ContractFilterForm(NetBoxModelFilterSetForm):
    model = Contract

    tenant = DynamicModelChoiceField(
        queryset=Tenant.objects.all(), required=False, selector=True
    )
    external_reference = forms.CharField(required=False)
    internal_partie = forms.ChoiceField(choices=InternalEntityChoices, required=False)
    status = forms.ChoiceField(choices=StatusChoices, required=False)
    currency = forms.ChoiceField(choices=CurrencyChoices, required=False)
    parent = DynamicModelChoiceField(
        queryset=Contract.objects.all(), required=False, selector=True
    )
    tag = TagFilterField(model)


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
            'yrc',
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
    tenant = DynamicModelChoiceField(
        queryset=Tenant.objects.all(),
        required=False,
        selector=True,
    )
    accounting_dimensions = Dimensions(required=False)
    comments = CommentField(required=False)
    parent = DynamicModelChoiceField(
        queryset=Contract.objects.all(),
        required=False,
        selector=True,
    )

    nullable_fields = (
        'accounting_dimensions',
        'comments',
    )
    model = Contract


# Invoice


class InvoiceForm(NetBoxModelForm):
    number = forms.CharField(
        max_length=100,
        help_text='Invoice template name will be overriden to _invoice_template_contract name',
    )
    contracts = DynamicModelMultipleChoiceField(
        queryset=Contract.objects.all(), required=False, selector=True
    )
    accounting_dimensions = Dimensions(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Initialise fields settings
        mandatory_fields = plugin_settings.get('mandatory_invoice_fields')
        for field in mandatory_fields:
            self.fields[field].required = True
        hidden_fields = plugin_settings.get('hidden_invoice_fields')
        for field in hidden_fields:
            if not self.fields[field].required:
                self.fields[field].widget = forms.HiddenInput()

    def clean(self):
        super().clean()

        # template checks
        if self.cleaned_data['template']:
            # Check that there is only one invoice template per contract
            contracts = self.cleaned_data['contracts']
            for contract in contracts:
                for invoice in contract.invoices.all():
                    if invoice.template and invoice.pk != self.instance.pk:
                        raise ValidationError(
                            'Only one invoice template allowed per contract'
                        )

            # Prefix the invoice name with _template
            self.cleaned_data['number'] = '_invoice_template_' + contract.name

            # set the periode start and end date to null
            self.cleaned_data['period_start'] = None
            self.cleaned_data['period_end'] = None

    def save(self, *args, **kwargs):
        is_new = not bool(self.instance.pk)

        instance = super().save(*args, **kwargs)

        if is_new and not self.cleaned_data['template']:
            contracts = self.cleaned_data['contracts']

            for contract in contracts:
                try:
                    template_exists = True
                    invoice_template = Invoice.objects.get(
                        template=True, contracts=contract
                    )
                except ObjectDoesNotExist:
                    template_exists = False

                if template_exists:
                    first = True
                    for line in invoice_template.invoicelines.all():
                        dimensions = line.accounting_dimensions.all()
                        line.pk = None
                        line.id = None
                        line._state.adding = True
                        line.invoice = self.instance

                        # adjust the first invoice line amount
                        amount = self.cleaned_data['amount']
                        if (
                            first
                            and amount != invoice_template.total_invoicelines_amount
                        ):
                            line.amount = (
                                line.amount
                                + amount
                                - invoice_template.total_invoicelines_amount
                            )

                        line.save()

                        for dimension in dimensions:
                            line.accounting_dimensions.add(dimension)
                        first = False

        return instance

    class Meta:
        model = Invoice
        fields = (
            'number',
            'date',
            'contracts',
            'template',
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


class InvoiceFilterForm(NetBoxModelFilterSetForm):
    model = Invoice
    number = forms.CharField(required=False)
    template = forms.NullBooleanField(
        required=False, widget=forms.Select(choices=BOOLEAN_WITH_BLANK_CHOICES)
    )
    currency = forms.ChoiceField(choices=CurrencyChoices, required=False)
    contracts = DynamicModelMultipleChoiceField(
        queryset=Contract.objects.all(),
        required=False,
        selector=True,
    )
    tag = TagFilterField(model)


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
            'template',
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
    template = forms.BooleanField(required=False)
    date = forms.DateField(required=False)
    contracts = DynamicModelMultipleChoiceField(
        queryset=Contract.objects.all(),
        required=False,
        selector=True,
    )
    period_start = forms.DateField(required=False)
    period_end = forms.DateField(required=False)
    currency = forms.ChoiceField(choices=CurrencyChoices, required=False)
    accounting_dimensions = Dimensions(required=False)
    amount = forms.DecimalField(max_digits=10, decimal_places=2, required=False)
    documents = forms.URLField(required=False)
    comments = CommentField()
    nullable_fields = (
        'accounting_dimensions',
        'comments',
    )

    model = Invoice


# service Provider forms


class ServiceProviderForm(NetBoxModelForm):
    slug = SlugField()
    comments = CommentField()

    class Meta:
        model = ServiceProvider
        fields = ('name', 'slug', 'portal_url', 'comments', 'tags')


class ServiceProviderFilterForm(NetBoxModelFilterSetForm):
    model = ServiceProvider
    name = forms.CharField(required=False)
    tag = TagFilterField(model)


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


# ContractAssignment


class ContractAssignmentForm(NetBoxModelForm):
    contract = DynamicModelChoiceField(queryset=Contract.objects.all(), selector=True)

    class Meta:
        model = ContractAssignment
        fields = ['content_type', 'object_id', 'contract', 'tags']
        widgets = {
            'content_type': forms.HiddenInput(),
            'object_id': forms.HiddenInput(),
        }


class ContractAssignmentFilterForm(NetBoxModelFilterSetForm):
    model = ContractAssignment
    contract = DynamicModelChoiceField(
        queryset=Contract.objects.all(),
        selector=True,
    )


class ContractAssignmentImportForm(NetBoxModelImportForm):
    content_type = CSVContentTypeField(
        queryset=ContentType.objects.all(),
        help_text='Content Type in the form <app>.<model>',
    )
    contract = CSVModelChoiceField(
        queryset=Contract.objects.all(), help_text='Contract id'
    )

    class Meta:
        model = ContractAssignment
        fields = ['content_type', 'object_id', 'contract', 'tags']


# InvoiceLine


class InvoiceLineForm(NetBoxModelForm):
    invoice = DynamicModelChoiceField(queryset=Invoice.objects.all(), selector=True)
    accounting_dimensions = DynamicModelMultipleChoiceField(
        queryset=AccountingDimension.objects.all(), required=False, selector=True
    )

    def clean(self):
        super().clean()

        # check for duplicate dimensions
        accounting_dimensions = self.cleaned_data['accounting_dimensions']
        dimensions_names = []
        for dimension in accounting_dimensions:
            if dimension.name in dimensions_names:
                raise ValidationError('duplicate accounting dimension')
            else:
                dimensions_names.append(dimension.name)

        # Make sure mandatory dimensions are present
        mandatory_dimensions = plugin_settings.get('mandatory_dimensions')
        for dimension in mandatory_dimensions:
            if dimension not in dimensions_names:
                raise ValidationError(f'dimension {dimension} missing')

    class Meta:
        model = InvoiceLine
        fields = [
            'invoice',
            'currency',
            'amount',
            'accounting_dimensions',
            'comments',
            'tags',
        ]


class InvoiceLineFilterForm(NetBoxModelFilterSetForm):
    model = InvoiceLine
    invoice = DynamicModelChoiceField(
        queryset=Invoice.objects.all(),
        required=False,
        selector=True,
    )
    accounting_dimensions = DynamicModelMultipleChoiceField(
        queryset=AccountingDimension.objects.all(),
        required=False,
        selector=True,
    )
    currency = forms.ChoiceField(choices=CurrencyChoices, required=False)
    tag = TagFilterField(model)


class InvoiceLineImportForm(NetBoxModelImportForm):
    invoice = CSVModelChoiceField(
        queryset=Invoice.objects.all(),
        to_field_name='number',
        help_text='Invoice number',
    )
    accounting_dimensions = CSVModelMultipleChoiceField(
        queryset=AccountingDimension.objects.all(),
        to_field_name='id',
        help_text='accounting dimension id',
    )

    class Meta:
        model = InvoiceLine
        fields = [
            'invoice',
            'currency',
            'amount',
            'accounting_dimensions',
            'comments',
            'tags',
        ]


class InvoiceLineBulkEditForm(NetBoxModelBulkEditForm):
    invoice = DynamicModelChoiceField(queryset=Invoice.objects.all(), required=False)
    accounting_dimensions = DynamicModelMultipleChoiceField(
        queryset=AccountingDimension.objects.all(),
        required=False,
        selector=True,
    )
    model = InvoiceLine


# AccountingDimension


class AccountingDimensionForm(NetBoxModelForm):
    class Meta:
        model = AccountingDimension
        fields = [
            'name',
            'value',
            'status',
            'comments',
            'tags',
        ]


class AccountingDimensionFilterForm(NetBoxModelFilterSetForm):
    model = AccountingDimension

    name = forms.CharField(required=False)
    value = forms.CharField(required=False)
    status = forms.ChoiceField(choices=AccountingDimensionStatusChoices, required=False)


class AccountingDimensionImportForm(NetBoxModelImportForm):
    status = CSVChoiceField(choices=StatusChoices, help_text='Contract status')

    class Meta:
        model = AccountingDimension
        fields = [
            'name',
            'value',
            'status',
            'comments',
            'tags',
        ]


class AccountingDimensionBulkEditForm(NetBoxModelBulkEditForm):
    name = forms.CharField(max_length=20, required=False)
    value = forms.CharField(max_length=20, required=False)
    model = AccountingDimension
