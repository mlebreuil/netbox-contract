from django import forms
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.utils.translation import gettext_lazy as _
from netbox.forms import (
    NetBoxModelBulkEditForm,
    NetBoxModelFilterSetForm,
    NetBoxModelForm,
    NetBoxModelImportForm,
)
from tenancy.forms import ContactModelFilterForm, TenancyFilterForm
from tenancy.models import Tenant
from utilities.forms import BOOLEAN_WITH_BLANK_CHOICES
from utilities.forms.fields import (
    ColorField,
    CommentField,
    ContentTypeChoiceField,
    CSVChoiceField,
    CSVContentTypeField,
    CSVModelChoiceField,
    CSVModelMultipleChoiceField,
    DynamicModelChoiceField,
    DynamicModelMultipleChoiceField,
    SlugField,
    TagFilterField,
)
from utilities.forms.widgets import DatePicker, HTMXSelect

from .constants import ASSIGNEMENT_MODELS, SERVICE_PROVIDER_MODELS
from .models import (
    AccountingDimension,
    AccountingDimensionStatusChoices,
    Contract,
    ContractAssignment,
    ContractType,
    CurrencyChoices,
    InternalEntityChoices,
    Invoice,
    InvoiceLine,
    ServiceProvider,
    StatusChoices,
    InvoiceStatusChoices,
)

plugin_settings = settings.PLUGINS_CONFIG['netbox_contract']


# Contract


class ContractForm(NetBoxModelForm):
    comments = CommentField(label=_('Comments'))

    external_party_object_type = ContentTypeChoiceField(
        queryset=ContentType.objects.all(),
        limit_choices_to=SERVICE_PROVIDER_MODELS,
        widget=HTMXSelect(),
        label=_('External party object type'),
    )
    external_party_object = forms.ModelChoiceField(queryset=None, label=_('External party object'))
    tenant = DynamicModelChoiceField(queryset=Tenant.objects.all(), required=False, selector=True, label=_('Tenant'))
    parent = DynamicModelChoiceField(
        queryset=Contract.objects.all(),
        required=False,
        selector=True,
        label=_('Parent'),
    )
    contract_type = DynamicModelChoiceField(
        queryset=ContractType.objects.all(), required=False, selector=True, label=_('Contract type')
    )

    def __init__(self, *args, **kwargs):
        initial = kwargs.get('initial', None)
        super().__init__(*args, **kwargs)

        # Initialize the external party object gfk
        if initial and 'external_party_object_type' in initial:
            external_party_object_type = ContentType.objects.get_for_id(initial['external_party_object_type'])
            external_party_class = external_party_object_type.model_class()
            self.fields['external_party_object'].queryset = external_party_class.objects.all()
            if (
                self.instance.external_party_object_type
                and self.instance.external_party_object_type.id == external_party_object_type.id
            ):
                self.fields['external_party_object'].initial = self.instance.external_party_object
            else:
                self.fields['external_party_object'].initial = None
        elif self.instance.external_party_object_type:
            external_party_class = self.instance.external_party_object_type.model_class()
            self.fields['external_party_object'].queryset = external_party_class.objects.all()
            self.fields['external_party_object'].initial = self.instance.external_party_object
        else:
            self.fields['external_party_object'].queryset = ServiceProvider.objects.all()
            self.fields['external_party_object'].initial = None

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
            'contract_type',
            'external_party_object_type',
            'external_party_object',
            'external_reference',
            'internal_party',
            'tenant',
            'status',
            'start_date',
            'end_date',
            'initial_term',
            'renewal_term',
            'notice_period',
            'currency',
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
            raise ValidationError('you should set monthly OR yearly recuring costs not both')


class ContractFilterForm(ContactModelFilterForm, TenancyFilterForm, NetBoxModelFilterSetForm):
    model = Contract

    contract_type = DynamicModelChoiceField(
        queryset=ContractType.objects.all(),
        required=False,
        selector=True,
        label=_('Contract type'),
    )
    external_reference = forms.CharField(required=False, label=_('External reference'))
    internal_party = forms.ChoiceField(choices=InternalEntityChoices, required=False, label=_('Internal party'))
    status = forms.ChoiceField(choices=StatusChoices, required=False, label=_('Status'))
    currency = forms.ChoiceField(choices=CurrencyChoices, required=False, label=_('Currency'))
    parent = DynamicModelChoiceField(
        queryset=Contract.objects.all(),
        required=False,
        selector=True,
        label=_('Parent'),
    )
    tag = TagFilterField(model)


class ContractCSVForm(NetBoxModelImportForm):
    external_party_object_type = CSVContentTypeField(
        queryset=ContentType.objects.all(),
        limit_choices_to=SERVICE_PROVIDER_MODELS,
        help_text='service provider object type in the form <app>.<model>',
    )
    external_party_object_id = forms.CharField(
        help_text='service provider object name', label=_('External party name')
    )
    tenant = CSVModelChoiceField(
        queryset=Tenant.objects.all(),
        to_field_name='name',
        help_text='Tenant name',
        required=False,
        label=_('Tenant'),
    )
    status = CSVChoiceField(choices=StatusChoices, help_text='Contract status', label=_('Status'))
    parent = CSVModelChoiceField(
        queryset=Contract.objects.all(),
        to_field_name='name',
        help_text='Contract name',
        required=False,
        label=_('Parent'),
    )
    contract_type = CSVModelChoiceField(
        queryset=ContractType.objects.all(),
        to_field_name='name',
        help_text='Contract type name',
        required=False,
        label=_('Contract type'),
    )

    class Meta:
        model = Contract
        fields = [
            'name',
            'contract_type',
            'external_party_object_type',
            'external_party_object_id',
            'external_reference',
            'internal_party',
            'tenant',
            'status',
            'start_date',
            'end_date',
            'initial_term',
            'renewal_term',
            'currency',
            'yrc',
            'mrc',
            'nrc',
            'invoice_frequency',
            'documents',
            'comments',
            'parent',
        ]

    def clean_external_party_object_id(self):
        name = self.cleaned_data.get('external_party_object_id')
        external_party_object_type = self.cleaned_data.get('external_party_object_type')
        external_party_object = external_party_object_type.get_object_for_this_type(name=name)

        return external_party_object.id


class ContractBulkEditForm(NetBoxModelBulkEditForm):
    name = forms.CharField(max_length=100, required=False, label=_('Name'))
    contract_type = DynamicModelChoiceField(
        queryset=ContractType.objects.all(),
        required=False,
        selector=True,
        label=_('Contract Type')
    )
    external_reference = forms.CharField(max_length=100, required=False, label=_('External reference'))
    internal_party = forms.ChoiceField(choices=InternalEntityChoices, required=False, label=_('Internal party'))
    tenant = DynamicModelChoiceField(queryset=Tenant.objects.all(), required=False, selector=True, label=_('Tenant'))
    comments = CommentField(required=False, label=_('Comments'))
    parent = DynamicModelChoiceField(
        queryset=Contract.objects.all(),
        required=False,
        selector=True,
        label=_('Parent'),
    )

    nullable_fields = ('comments',)
    model = Contract


# ContractType


class ContractTypeForm(NetBoxModelForm):
    color = ColorField(label=_('Color'))

    class Meta:
        model = ContractType
        fields = (
            'name',
            'description',
            'color',
            'tags',
        )


class ContractTypeCSVForm(NetBoxModelImportForm):
    name = forms.CharField(max_length=100, label=_('Name'))
    description = CommentField(label=_('Description'))
    color = ColorField(label=_('Color'))

    class Meta:
        model = ContractType
        fields = ['name', 'description', 'color']


class ContractTypeBulkEditForm(NetBoxModelBulkEditForm):
    description = CommentField(label=_('Description'))
    nullable_fields = ('comments',)
    color = ColorField(label=_('Color'), required=False,)
    model = ContractType


class ContractTypeFilterForm(NetBoxModelFilterSetForm):
    model = ContractType
    name = forms.CharField(required=False, label=_('Name'))
    description = CommentField(label=_('Description'))

# Invoice


class InvoiceForm(NetBoxModelForm):
    number = forms.CharField(
        max_length=100,
        help_text='Invoice template name will be overriden to _invoice_template_contract name',
        label=_('Number'),
    )
    contracts = DynamicModelMultipleChoiceField(
        queryset=Contract.objects.all(),
        required=False,
        selector=True,
        label=_('Contracts'),
    )

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
                        raise ValidationError('Only one invoice template allowed per contract')

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
                    invoice_template = Invoice.objects.get(template=True, contracts=contract)
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
                        if first and amount != invoice_template.total_invoicelines_amount:
                            line.amount = line.amount + amount - invoice_template.total_invoicelines_amount

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
            'status',
            'period_start',
            'period_end',
            'currency',
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
    number = forms.CharField(
        required=False,
        label=_('Number'),
    )
    template = forms.NullBooleanField(
        required=False,
        widget=forms.Select(choices=BOOLEAN_WITH_BLANK_CHOICES),
        label=_('Template'),
    )
    status = forms.ChoiceField(choices=InvoiceStatusChoices, required=False, label=_('Status'))
    currency = forms.ChoiceField(choices=CurrencyChoices, required=False, label=_('Currency'))
    contracts = DynamicModelMultipleChoiceField(
        queryset=Contract.objects.all(),
        required=False,
        selector=True,
        label=_('Contracts'),
    )
    accounting_dimensions = DynamicModelMultipleChoiceField(
        queryset=AccountingDimension.objects.all(),
        required=False,
        selector=True,
        label=_('Accounting Dimensions'),
    )

    tag = TagFilterField(model)


class InvoiceCSVForm(NetBoxModelImportForm):
    contracts = CSVModelMultipleChoiceField(
        queryset=Contract.objects.all(),
        to_field_name='name',
        help_text='Related Contracts',
        label=_('Contracts'),
    )
    status = CSVChoiceField(choices=InvoiceStatusChoices, help_text='Invoice status', label=_('Status'))

    class Meta:
        model = Invoice
        fields = [
            'number',
            'date',
            'contracts',
            'template',
            'status',
            'period_start',
            'period_end',
            'currency',
            'amount',
            'documents',
            'comments',
            'tags',
        ]


class InvoiceBulkEditForm(NetBoxModelBulkEditForm):
    number = forms.CharField(max_length=100, required=False, label=_('Number'))
    template = forms.BooleanField(
        required=False,
        label=_('Template'),
        help_text=_('Wether this invoice is a template or not'),
    )
    date = forms.DateField(
        required=False,
        label=_('Date'),
    )
    contracts = DynamicModelMultipleChoiceField(
        queryset=Contract.objects.all(),
        required=False,
        selector=True,
    )
    period_start = forms.DateField(
        required=False,
        label=_('Period start'),
    )
    period_end = forms.DateField(
        required=False,
        label=_('Period end'),
    )
    currency = forms.ChoiceField(
        choices=CurrencyChoices,
        required=False,
        label=_('Currency'),
    )
    amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        label=_('Amount'),
    )
    documents = forms.URLField(
        required=False,
        label=_('Documents'),
        help_text=_('URL to the contract documents'),
    )
    comments = CommentField(
        label=_('Comments'),
    )
    nullable_fields = ('comments',)

    model = Invoice


# service Provider forms


class ServiceProviderForm(NetBoxModelForm):
    slug = SlugField(label=_('Slug'))
    comments = CommentField(label=_('Comments'))

    class Meta:
        model = ServiceProvider
        fields = ('name', 'slug', 'portal_url', 'comments', 'tags')


class ServiceProviderFilterForm(ContactModelFilterForm, NetBoxModelFilterSetForm):
    model = ServiceProvider
    name = forms.CharField(required=False, label=_('Name'))
    tag = TagFilterField(model)


class ServiceProviderCSVForm(NetBoxModelImportForm):
    slug = SlugField(label=_('Slug'))
    comments = CommentField(label=_('Comments'))

    class Meta:
        model = ServiceProvider
        fields = ['name', 'slug', 'portal_url', 'comments', 'tags']


class ServiceProviderBulkEditForm(NetBoxModelBulkEditForm):
    name = forms.CharField(max_length=100, required=False, label=_('Name'))
    comments = CommentField(label=_('Comments'))
    nullable_fields = ('comments',)
    model = ServiceProvider


# ContractAssignment


class ContractAssignmentForm(NetBoxModelForm):

    content_type = ContentTypeChoiceField(
        queryset=ContentType.objects.all(),
        limit_choices_to=ASSIGNEMENT_MODELS,
        label=_('object type'),
    )

    contract = DynamicModelChoiceField(
        queryset=Contract.objects.all(),
        selector=True,
        label=_('Contract'))

    class Meta:
        model = ContractAssignment
        fields = ['content_type', 'object_id', 'contract', 'tags']
        # widgets = {
        #     'content_type': forms.HiddenInput(),
        #     'object_id': forms.HiddenInput(),
        # }


class ContractAssignmentFilterForm(NetBoxModelFilterSetForm):
    model = ContractAssignment
    contract = DynamicModelChoiceField(
        queryset=Contract.objects.all(),
        required=False,
        selector=True,
        label=_('Contract'),
    )


class ContractAssignmentImportForm(NetBoxModelImportForm):
    content_type = CSVContentTypeField(
        queryset=ContentType.objects.all(),
        limit_choices_to=ASSIGNEMENT_MODELS,
        help_text='Content Type in the form <app>.<model>',
        label=_('Content type'),
    )
    contract = CSVModelChoiceField(
        queryset=Contract.objects.all(),
        help_text='Contract id',
        label=_('Contract'),
    )

    class Meta:
        model = ContractAssignment
        fields = ['content_type', 'object_id', 'contract', 'tags']


class ContractAssignmentBulkEditForm(NetBoxModelBulkEditForm):
    contract = DynamicModelChoiceField(
        queryset=Contract.objects.all(),
        required=False,
        selector=True,
        label=_('Contract'),
    )
    model = ContractAssignment


# InvoiceLine


class InvoiceLineForm(NetBoxModelForm):
    invoice = DynamicModelChoiceField(
        queryset=Invoice.objects.all(),
        selector=True,
        label=_('Invoice'),
    )
    accounting_dimensions = DynamicModelMultipleChoiceField(
        queryset=AccountingDimension.objects.all(),
        required=False,
        selector=True,
        label=_('Accounting dimensions'),
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
        label=_('Invoice'),
    )
    accounting_dimensions = DynamicModelMultipleChoiceField(
        queryset=AccountingDimension.objects.all(),
        required=False,
        selector=True,
        label=_('Accounting dimensions'),
    )
    currency = forms.ChoiceField(
        choices=CurrencyChoices,
        required=False,
        label=_('Currency'),
    )
    tag = TagFilterField(model)


class InvoiceLineImportForm(NetBoxModelImportForm):
    invoice = CSVModelChoiceField(
        queryset=Invoice.objects.all(),
        to_field_name='number',
        help_text='Invoice number',
        label=_('Invoice'),
    )
    accounting_dimensions = CSVModelMultipleChoiceField(
        queryset=AccountingDimension.objects.all(),
        to_field_name='id',
        required=False,
        help_text='accounting dimension id',
        label=_('Accounting dimensions'),
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
        label=_('Accounting dimensions'),
    )
    comments = CommentField(label=_('Comments'))
    nullable_fields = ('comments',)
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

    name = forms.CharField(required=False, label=_('Name'))
    value = forms.CharField(required=False, label=_('Value'))
    status = forms.ChoiceField(
        choices=AccountingDimensionStatusChoices,
        required=False,
        label=_('Status'),
    )


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
    name = forms.CharField(max_length=20, required=False, label=_('Name'))
    value = forms.CharField(max_length=20, required=False, label=_('Value'))
    comments = CommentField(label=_('Comments'))
    nullable_fields = ('comments',)
    model = AccountingDimension
