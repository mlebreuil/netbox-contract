import logging

from circuits.models import Provider
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
    OrganizationalModelBulkEditForm,
    OrganizationalModelFilterSetForm,
    OrganizationalModelForm,
    OrganizationalModelImportForm,
    PrimaryModelBulkEditForm,
    PrimaryModelFilterSetForm,
    PrimaryModelForm,
    PrimaryModelImportForm,
)
from tenancy.forms import ContactModelFilterForm, TenancyFilterForm
from tenancy.models import Tenant
from utilities.forms import BOOLEAN_WITH_BLANK_CHOICES, get_field_value
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
from utilities.forms.rendering import FieldSet
from utilities.forms.widgets import DatePicker, HTMXSelect
from utilities.templatetags.builtins.filters import bettertitle

from .constants import (
    ASSIGNEMENT_MODELS,
    DEPRECATED_CONTRACT_FIELDS,
    SERVICE_PROVIDER_MODELS,
    SERVICE_PROVIDER_TYPES,
)
from .models import (
    CONTRACT_LINE_LOCKED_FIELDS,
    AccountingDimension,
    AccountingDimensionStatusChoices,
    BillingMethodChoices,
    Contract,
    ContractAssignment,
    ContractLine,
    ContractType,
    CurrencyChoices,
    InternalEntityChoices,
    Invoice,
    InvoiceLine,
    InvoiceStatusChoices,
    ServiceProvider,
    StatusChoices,
    Unit,
)
from .services import invoicing
from .validators import check_invoice_contracts

plugin_settings = settings.PLUGINS_CONFIG['netbox_contract']

logger = logging.getLogger('netbox.plugins.netbox_contract')


def apply_field_settings(form, mandatory_setting, hidden_setting):
    """Apply the mandatory and hidden field settings, ignoring (with a warning) fields the form does not have."""
    for field in plugin_settings.get(mandatory_setting) or []:
        if field not in form.fields:
            logger.warning('%s: field "%s" is not in the form (deprecated or unknown), ignored', mandatory_setting,
                           field)
            continue
        form.fields[field].required = True
    for field in plugin_settings.get(hidden_setting) or []:
        if field not in form.fields:
            logger.warning('%s: field "%s" is not in the form (deprecated or unknown), ignored', hidden_setting, field)
            continue
        if not form.fields[field].required:
            form.fields[field].widget = forms.HiddenInput()
    prune_fieldsets(form)


def prune_fieldsets(form):
    """
    Keep in the form's sections only the fields it still shows: fields deleted (deprecated) or hidden by the settings
    are rendered once as hidden inputs, outside the sections; a section left without a field is dropped.
    """
    fieldsets = []
    for fieldset in form.fieldsets:
        items = [
            name for name in fieldset.items if name in form.fields and not form.fields[name].widget.is_hidden
        ]
        if items:
            fieldsets.append(FieldSet(*items, name=fieldset.name))
    form.fieldsets = tuple(fieldsets)


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
    internal_party = internal_party = forms.ChoiceField(
        choices=InternalEntityChoices,
        required=True,
        label=_('Internal party')
    )
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

    fieldsets = (
        FieldSet(
            'name', 'contract_type', 'status', 'external_reference', 'parent', 'documents', 'tags',
            name=_('Contract'),
        ),
        FieldSet('external_party_object_type', 'external_party_object', 'internal_party', name=_('Parties')),
        FieldSet('start_date', 'end_date', 'initial_term', 'renewal_term', 'notice_period', name=_('Dates and terms')),
        FieldSet('currency', 'invoice_frequency', 'billable', name=_('Billing')),
        FieldSet('tenant', name=_('Tenancy')),
        FieldSet('mrc', 'yrc', 'nrc', name=_('Deprecated')),
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

        # Deprecated cost fields are replaced by contract lines
        if plugin_settings.get('show_deprecated_fields'):
            for field in DEPRECATED_CONTRACT_FIELDS:
                self.fields[field].help_text = _('Deprecated: use contract lines instead.')
        else:
            for field in DEPRECATED_CONTRACT_FIELDS:
                del self.fields[field]

        # Initialise fields settings
        apply_field_settings(self, 'mandatory_contract_fields', 'hidden_contract_fields')

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
            'billable',
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

        if self.cleaned_data.get('mrc') and self.cleaned_data.get('yrc'):
            raise ValidationError('you should set monthly OR yearly recuring costs not both')


class ContractFilterForm(ContactModelFilterForm, TenancyFilterForm, NetBoxModelFilterSetForm):
    model = Contract
    fieldsets = (
        FieldSet('q', 'filter_id', 'tag'),
        FieldSet(
            'contract_type', 'status', 'external_reference', 'internal_party', 'parent', 'billable',
            name=_('Attributes'),
        ),
        FieldSet('service_provider_id', 'provider_id', name=_('Parties')),
        FieldSet('currency', name=_('Billing')),
        FieldSet('tenant_group_id', 'tenant_id', name=_('Tenant')),
        FieldSet('contact', 'contact_role', 'contact_group', name=_('Contacts')),
    )

    contract_type = DynamicModelChoiceField(
        queryset=ContractType.objects.all(),
        required=False,
        selector=True,
        label=_('Contract type'),
    )

    service_provider_id = DynamicModelChoiceField(
        queryset=ServiceProvider.objects.all(),
        required=False,
        selector=True,
        label=_('Service provider'),
        help_text=_('Filter by Service Provider'),
    )

    provider_id = DynamicModelChoiceField(
        queryset=Provider.objects.all(),
        required=False,
        selector=True,
        label=_('Circuit Provider'),
        help_text=_('Filter by Circuit Provider'),
    )

    external_reference = forms.CharField(required=False, label=_('External reference'))

    internal_party = forms.ChoiceField(
        choices=[('', '-----')] + list(InternalEntityChoices),
        required=False,
        label=_('Internal party')
    )

    status = forms.ChoiceField(choices=StatusChoices, required=False, label=_('Status'))

    currency = forms.ChoiceField(
        choices=[('', '-----')] + list(CurrencyChoices),
        required=False,
        label=_('Currency')
    )

    parent = DynamicModelChoiceField(
        queryset=Contract.objects.all(),
        required=False,
        selector=True,
        label=_('Parent'),
    )

    billable = forms.NullBooleanField(
        required=False,
        widget=forms.Select(choices=BOOLEAN_WITH_BLANK_CHOICES),
        label=_('Billable'),
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
            'billable',
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

    external_party_object_type = ContentTypeChoiceField(
        queryset=ContentType.objects.filter(model__in=SERVICE_PROVIDER_TYPES),
        widget=HTMXSelect(method='post', attrs={'hx-select': '#form_fields'}),
        required=False,
        label=_('External party type')
    )
    external_party_object = DynamicModelChoiceField(
        label=_('External party'),
        queryset=ServiceProvider.objects.none(),  # Initial queryset
        required=False,
        disabled=True,
        selector=True
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
    billable = forms.NullBooleanField(
        required=False,
        widget=forms.Select(choices=BOOLEAN_WITH_BLANK_CHOICES),
        label=_('Billable'),
    )

    nullable_fields = ('comments',)
    fieldsets = (
        FieldSet('name', 'contract_type', 'external_reference', 'parent', name=_('Contract')),
        FieldSet('external_party_object_type', 'external_party_object', 'internal_party', name=_('Parties')),
        FieldSet('billable', name=_('Billing')),
        FieldSet('tenant', name=_('Tenancy')),
    )

    model = Contract

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if external_party_object_type_id := get_field_value(self, 'external_party_object_type'):
            try:
                external_party_object_type = ContentType.objects.get(pk=external_party_object_type_id)
                model = external_party_object_type.model_class()
                self.fields['external_party_object'].queryset = model.objects.all()
                self.fields['external_party_object'].widget.attrs['selector'] = model._meta.label_lower
                self.fields['external_party_object'].disabled = False
                self.fields['external_party_object'].label = _(bettertitle(model._meta.verbose_name))
            except ObjectDoesNotExist:
                pass

# ContractType


class ContractTypeForm(OrganizationalModelForm):
    # Derived from the name when left empty (FR-018)
    slug = SlugField(label=_('Slug'), required=False)
    color = ColorField(label=_('Color'))

    fieldsets = (
        FieldSet('name', 'slug', 'description', 'color', 'tags', name=_('Contract type')),
    )

    class Meta:
        model = ContractType
        fields = ('name', 'slug', 'description', 'color', 'owner', 'comments', 'tags')


class ContractTypeCSVForm(OrganizationalModelImportForm):
    name = forms.CharField(max_length=100, label=_('Name'))
    slug = SlugField(label=_('Slug'), required=False)
    description = forms.CharField(max_length=200, required=False, label=_('Description'))
    color = ColorField(label=_('Color'))

    class Meta:
        model = ContractType
        fields = ['name', 'slug', 'description', 'color', 'owner', 'comments']


class ContractTypeBulkEditForm(OrganizationalModelBulkEditForm):
    description = forms.CharField(max_length=200, required=False, label=_('Description'))
    color = ColorField(label=_('Color'), required=False,)
    nullable_fields = ('description', 'comments')
    fieldsets = (
        FieldSet('description', 'color', name=_('Contract type')),
    )

    model = ContractType


class ContractTypeFilterForm(OrganizationalModelFilterSetForm):
    model = ContractType
    fieldsets = (
        FieldSet('q', 'filter_id'),
        FieldSet('name', 'slug', 'description', name=_('Attributes')),
        FieldSet('owner_group_id', 'owner_id', name=_('Ownership')),
    )
    name = forms.CharField(required=False, label=_('Name'))
    slug = forms.CharField(required=False, label=_('Slug'))
    description = forms.CharField(required=False, label=_('Description'))

# Invoice


class InvoiceForm(NetBoxModelForm):
    number = forms.CharField(
        max_length=100,
        label=_('Number'),
    )
    contracts = DynamicModelMultipleChoiceField(
        queryset=Contract.objects.all(),
        required=False,
        selector=True,
        label=_('Contracts'),
    )

    fieldsets = (
        FieldSet('number', 'date', 'contracts', 'status', 'documents', 'tags', name=_('Invoice')),
        FieldSet('period_start', 'period_end', 'currency', 'amount', name=_('Period and amount')),
        FieldSet('template', name=_('Deprecated')),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Invoice templates are deprecated: new ones are offered only when deprecated fields are shown
        if not plugin_settings.get('show_deprecated_fields'):
            del self.fields['template']
        else:
            self.fields['template'].help_text = _(
                'Deprecated: invoice lines are generated from the contract lines. The number of a template is '
                'replaced by _invoice_template_<contract name>.'
            )

        # Initialise fields settings
        apply_field_settings(self, 'mandatory_invoice_fields', 'hidden_invoice_fields')

        # A posted invoice keeps its amounts, period and contracts; its status can change (FR-031)
        if self.instance.pk and self.instance.locked_in_database():
            for field in (*Invoice.POSTED_LOCKED_FIELDS, 'contracts'):
                if field in self.fields:
                    self.fields[field].disabled = True

    def clean(self):
        super().clean()

        # contracts and currency (the relation is saved after the invoice, so it is checked here)
        is_new = not self.instance.pk
        errors = check_invoice_contracts(
            is_new,
            self.cleaned_data.get('contracts'),
            self.cleaned_data.get('currency'),
            previous_contract_ids=[] if is_new else list(self.instance.contracts.values_list('pk', flat=True)),
            previous_currency=None if is_new else Invoice.objects.get(pk=self.instance.pk).currency,
        )
        # a new invoice gets its lines from the contract lines (FR-021, FR-023)
        contracts = list(self.cleaned_data.get('contracts') or [])
        self.line_overrides = None
        if is_new and not self.cleaned_data.get('template') and len(contracts) == 1 and not errors:
            # quantities and unit prices typed in the preview of the lines (FR-032)
            self.line_overrides, errors = invoicing.parse_line_overrides(self.data)
            self.extra_lines, extra_errors = invoicing.parse_extra_lines(self.data)
            errors += extra_errors
            if not errors:
                errors = invoicing.check_new_invoice(
                    contracts[0],
                    self.cleaned_data.get('amount'),
                    self.cleaned_data.get('period_start'),
                    self.cleaned_data.get('period_end'),
                    self.line_overrides,
                    self.extra_lines,
                    check_line_dimensions=True,
                )
        if errors:
            raise ValidationError(errors)

        # template checks
        if self.cleaned_data.get('template'):
            # Check that there is only one invoice template per contract
            contracts = list(self.cleaned_data.get('contracts') or [])
            for contract in contracts:
                for invoice in contract.invoices.all():
                    if invoice.template and invoice.pk != self.instance.pk:
                        raise ValidationError('Only one invoice template allowed per contract')

            # Prefix the invoice name with _template
            if contracts:
                self.cleaned_data['number'] = '_invoice_template_' + contracts[-1].name

            # set the periode start and end date to null
            self.cleaned_data['period_start'] = None
            self.cleaned_data['period_end'] = None

    def save(self, *args, **kwargs):
        is_new = not bool(self.instance.pk)

        instance = super().save(*args, **kwargs)

        # Invoice lines are generated from the contract lines of a new invoice only; invoice templates are
        # no longer copied (they are kept for reference)
        if is_new and not instance.template:
            invoicing.generate_invoice_lines(
                instance, getattr(self, 'line_overrides', None), getattr(self, 'extra_lines', ())
            )

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


class InvoiceLineDimensionsForm(forms.Form):
    """Accounting dimensions of one row of the preview of a new invoice (FR-032)."""

    accounting_dimensions = DynamicModelMultipleChoiceField(
        queryset=AccountingDimension.objects.all(),
        required=False,
        label=_('Accounting dimensions'),
    )


class InvoiceFilterForm(NetBoxModelFilterSetForm):
    model = Invoice
    fieldsets = (
        FieldSet('q', 'filter_id', 'tag'),
        FieldSet('number', 'status', 'contracts', name=_('Attributes')),
        FieldSet('currency', 'accounting_dimensions', name=_('Billing')),
        FieldSet('template', name=_('Deprecated')),
    )
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

    def clean(self):
        super().clean()
        # Imported invoices follow the contract and currency rules; their lines are not generated
        is_new = not self.instance.pk
        if 'contracts' not in self.cleaned_data and not is_new:
            return
        errors = check_invoice_contracts(
            is_new,
            self.cleaned_data.get('contracts'),
            self.cleaned_data.get('currency', self.instance.currency),
            previous_contract_ids=[] if is_new else list(self.instance.contracts.values_list('pk', flat=True)),
            previous_currency=None if is_new else Invoice.objects.get(pk=self.instance.pk).currency,
        )
        if errors:
            raise ValidationError(errors)

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

    fieldsets = (
        FieldSet('number', 'date', 'contracts', 'documents', name=_('Invoice')),
        FieldSet('period_start', 'period_end', 'currency', 'amount', name=_('Period and amount')),
        FieldSet('template', name=_('Deprecated')),
    )

    model = Invoice

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Invoice templates are deprecated: the flag is offered only when deprecated fields are shown
        if not plugin_settings.get('show_deprecated_fields'):
            del self.fields['template']
        prune_fieldsets(self)


# service Provider forms


class ServiceProviderForm(PrimaryModelForm):
    slug = SlugField(label=_('Slug'))

    fieldsets = (
        FieldSet('name', 'slug', 'description', 'portal_url', 'tags', name=_('Service provider')),
    )

    class Meta:
        model = ServiceProvider
        fields = ('name', 'slug', 'description', 'portal_url', 'owner', 'comments', 'tags')


class ServiceProviderFilterForm(ContactModelFilterForm, PrimaryModelFilterSetForm):
    model = ServiceProvider
    fieldsets = (
        FieldSet('q', 'filter_id', 'tag'),
        FieldSet('name', 'description', name=_('Attributes')),
        FieldSet('owner_group_id', 'owner_id', name=_('Ownership')),
        FieldSet('contact', 'contact_role', 'contact_group', name=_('Contacts')),
    )
    name = forms.CharField(required=False, label=_('Name'))
    description = forms.CharField(required=False, label=_('Description'))
    tag = TagFilterField(model)


class ServiceProviderCSVForm(PrimaryModelImportForm):
    slug = SlugField(label=_('Slug'))

    class Meta:
        model = ServiceProvider
        fields = ['name', 'slug', 'description', 'portal_url', 'owner', 'comments', 'tags']


class ServiceProviderBulkEditForm(PrimaryModelBulkEditForm):
    name = forms.CharField(max_length=100, required=False, label=_('Name'))
    description = forms.CharField(max_length=200, required=False, label=_('Description'))
    nullable_fields = ('description', 'comments')
    fieldsets = (
        FieldSet('name', 'description', name=_('Service provider')),
    )

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

    fieldsets = (
        FieldSet('content_type', 'object_id', 'contract', 'tags', name=_('Assignment')),
    )

    class Meta:
        model = ContractAssignment
        fields = ['content_type', 'object_id', 'contract', 'tags']
        # widgets = {
        #     'content_type': forms.HiddenInput(),
        #     'object_id': forms.HiddenInput(),
        # }


class ContractAssignmentFilterForm(NetBoxModelFilterSetForm):
    model = ContractAssignment
    fieldsets = (
        FieldSet('q', 'filter_id'),
        FieldSet('contract', name=_('Attributes')),
    )
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
    fieldsets = (
        FieldSet('contract', name=_('Assignment')),
    )

    model = ContractAssignment


# InvoiceLine


class InvoiceLineForm(NetBoxModelForm):
    invoice = DynamicModelChoiceField(
        queryset=Invoice.objects.all(),
        selector=True,
        label=_('Invoice'),
    )
    contract_line = DynamicModelChoiceField(
        queryset=ContractLine.objects.all(),
        required=False,
        query_params={'invoice_id': '$invoice'},
        label=_('Contract line'),
        help_text=_('Lines of the invoice contract and of its non-billable descendants. When a contract line is '
                    'chosen, the unit and unit price default to its own.'),
    )
    unit = DynamicModelChoiceField(
        queryset=Unit.objects.all(),
        required=False,
        label=_('Unit'),
        help_text=_('Defaults to the unit of the contract line; fixed once the line is created'),
    )
    accounting_dimensions = DynamicModelMultipleChoiceField(
        queryset=AccountingDimension.objects.all(),
        required=False,
        selector=True,
        label=_('Accounting dimensions'),
    )

    # Fields fixed on a saved line that references a contract line (FR-024)
    CALCULATED_LINE_FIXED_FIELDS = ('invoice', 'contract_line', 'currency', 'amount')

    fieldsets = (
        FieldSet('invoice', 'contract_line', 'accounting_dimensions', 'tags', name=_('Invoice line')),
        FieldSet('unit', 'unit_price', 'quantity', 'currency', 'amount', name=_('Amount')),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['unit'].help_text = _('Defaults to the unit of the contract line')
        self.fields['unit_price'].help_text = _('Required; defaults to the unit price of the contract line')
        self.fields['quantity'].help_text = _(
            'Defaults to 1, or to the quantity of the contract line; usage-based lines are entered per invoice'
        )
        # The amount is always quantity x unit price (FR-024, decision I14)
        self.fields['amount'].disabled = True
        self.fields['amount'].help_text = _('Calculated from the quantity and the unit price when the line is saved')
        if not self.instance.pk:
            return

        # Lines of a posted invoice: only their accounting dimensions, comments and tags change (FR-031)
        if self.instance.invoice_locked():
            for field in InvoiceLine.POSTED_LOCKED_FIELDS:
                self.fields[field].disabled = True
            self.fields['amount'].help_text = _('The invoice is posted: set it back to draft to change this line')
            return

        # A calculated line keeps its invoice, contract line and currency; its unit, unit price and quantity change
        # A line generated from a contract line keeps its invoice, contract line and currency
        if self.instance.contract_line_id:
            for field in self.CALCULATED_LINE_FIXED_FIELDS:
                self.fields[field].disabled = True

    def clean(self):
        super().clean()

        # check for duplicate dimensions
        accounting_dimensions = self.cleaned_data.get('accounting_dimensions') or []
        dimensions_names = []
        for dimension in accounting_dimensions:
            if dimension.name in dimensions_names:
                raise ValidationError('duplicate accounting dimension')
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
            'contract_line',
            'unit',
            'unit_price',
            'quantity',
            'currency',
            'amount',
            'accounting_dimensions',
            'comments',
            'tags',
        ]


class InvoiceLineFilterForm(NetBoxModelFilterSetForm):
    model = InvoiceLine
    fieldsets = (
        FieldSet('q', 'filter_id', 'tag'),
        FieldSet('invoice', name=_('Attributes')),
        FieldSet('currency', 'accounting_dimensions', name=_('Billing')),
    )
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
    contract_line = CSVModelChoiceField(
        queryset=ContractLine.objects.all(),
        required=False,
        help_text='Contract line id; the unit and unit price default to its own',
        label=_('Contract line'),
    )
    unit = CSVModelChoiceField(
        queryset=Unit.objects.all(),
        to_field_name='name',
        required=False,
        help_text='Unit name',
        label=_('Unit'),
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
            'contract_line',
            'unit',
            'unit_price',
            'quantity',
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
    fieldsets = (
        FieldSet('invoice', 'accounting_dimensions', name=_('Invoice line')),
    )

    model = InvoiceLine


# Unit


class UnitForm(NetBoxModelForm):
    comments = CommentField(label=_('Comments'))

    fieldsets = (
        FieldSet('name', 'description', 'billing_method', 'months', 'tags', name=_('Unit')),
    )

    class Meta:
        model = Unit
        fields = ('name', 'description', 'billing_method', 'months', 'comments', 'tags')


class UnitFilterForm(NetBoxModelFilterSetForm):
    model = Unit
    fieldsets = (
        FieldSet('q', 'filter_id', 'tag'),
        FieldSet('name', 'billing_method', name=_('Attributes')),
    )
    name = forms.CharField(required=False, label=_('Name'))
    billing_method = forms.MultipleChoiceField(
        choices=BillingMethodChoices, required=False, label=_('Billing method')
    )
    tag = TagFilterField(model)


class UnitImportForm(NetBoxModelImportForm):
    billing_method = CSVChoiceField(
        choices=BillingMethodChoices, help_text='one_time, recurring or usage', label=_('Billing method')
    )

    class Meta:
        model = Unit
        fields = ('name', 'description', 'billing_method', 'months', 'comments', 'tags')


class UnitBulkEditForm(NetBoxModelBulkEditForm):
    description = forms.CharField(required=False, label=_('Description'))
    comments = CommentField(required=False, label=_('Comments'))
    nullable_fields = ('description', 'comments')
    fieldsets = (
        FieldSet('description', name=_('Unit')),
    )

    model = Unit


# ContractLine


def check_duplicate_dimensions(accounting_dimensions):
    names = [dimension.name for dimension in accounting_dimensions or ()]
    if len(names) != len(set(names)):
        raise ValidationError(_('duplicate accounting dimension'))


class ContractLineForm(NetBoxModelForm):
    contract = DynamicModelChoiceField(queryset=Contract.objects.all(), selector=True, label=_('Contract'))
    unit = DynamicModelChoiceField(queryset=Unit.objects.all(), selector=True, label=_('Unit'))
    accounting_dimensions = DynamicModelMultipleChoiceField(
        queryset=AccountingDimension.objects.all(),
        required=False,
        selector=True,
        label=_('Accounting dimensions'),
    )
    comments = CommentField(label=_('Comments'))

    fieldsets = (
        FieldSet('contract', 'description', 'accounting_dimensions', 'tags', name=_('Contract line')),
        FieldSet('quantity', 'unit_price', 'unit', 'currency', name=_('Price')),
        FieldSet('start_date', 'end_date', name=_('Dates')),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Once invoiced, only the internal fields of a line can change: the contract terms are shown disabled
        if self.instance.pk and self.instance.lock_message():
            for field in CONTRACT_LINE_LOCKED_FIELDS:
                if field in self.fields:
                    self.fields[field].disabled = True
        # Propose the currency of the contract given in the URL (?contract=<id>)
        contract_id = self.initial.get('contract')
        if contract_id and not self.initial.get('currency') and not self.instance.pk:
            contract = Contract.objects.filter(pk=contract_id).first()
            if contract:
                self.initial['currency'] = contract.currency

    def clean(self):
        super().clean()
        check_duplicate_dimensions(self.cleaned_data.get('accounting_dimensions'))

    class Meta:
        model = ContractLine
        fields = (
            'contract',
            'description',
            'quantity',
            'unit_price',
            'unit',
            'currency',
            'start_date',
            'end_date',
            'accounting_dimensions',
            'comments',
            'tags',
        )
        widgets = {
            'start_date': DatePicker(),
            'end_date': DatePicker(),
        }


class ContractLineAmendForm(forms.Form):
    """New unit price and/or quantity of a contract line from a date (FR-030)."""

    effective_date = forms.DateField(
        widget=DatePicker(), label=_('Applies from'), help_text=_('First day of the new terms')
    )
    unit_price = forms.DecimalField(max_digits=12, decimal_places=2, required=False, label=_('New unit price'))
    quantity = forms.DecimalField(max_digits=12, decimal_places=4, required=False, label=_('New quantity'))
    reason = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        label=_('Reason'),
        help_text=_('Recorded in the change log and on the new line'),
    )


class ContractLineFilterForm(NetBoxModelFilterSetForm):
    model = ContractLine
    fieldsets = (
        FieldSet('q', 'filter_id', 'tag'),
        FieldSet('contract_id', name=_('Attributes')),
        FieldSet('currency', 'unit_id', 'billing_method', 'accounting_dimensions', name=_('Billing')),
    )
    contract_id = DynamicModelMultipleChoiceField(
        queryset=Contract.objects.all(), required=False, selector=True, label=_('Contract')
    )
    unit_id = DynamicModelMultipleChoiceField(
        queryset=Unit.objects.all(), required=False, selector=True, label=_('Unit')
    )
    billing_method = forms.MultipleChoiceField(
        choices=BillingMethodChoices, required=False, label=_('Billing method')
    )
    currency = forms.MultipleChoiceField(choices=CurrencyChoices, required=False, label=_('Currency'))
    accounting_dimensions = DynamicModelMultipleChoiceField(
        queryset=AccountingDimension.objects.all(), required=False, selector=True, label=_('Accounting dimensions')
    )
    tag = TagFilterField(model)


class ContractLineImportForm(NetBoxModelImportForm):
    contract = CSVModelChoiceField(queryset=Contract.objects.all(), help_text='Contract id', label=_('Contract'))
    unit = CSVModelChoiceField(
        queryset=Unit.objects.all(), to_field_name='name', help_text='Unit name', label=_('Unit')
    )
    accounting_dimensions = CSVModelMultipleChoiceField(
        queryset=AccountingDimension.objects.all(),
        to_field_name='id',
        required=False,
        help_text='accounting dimension id',
        label=_('Accounting dimensions'),
    )

    class Meta:
        model = ContractLine
        fields = (
            'contract',
            'description',
            'quantity',
            'unit_price',
            'unit',
            'currency',
            'start_date',
            'end_date',
            'accounting_dimensions',
            'comments',
            'tags',
        )


class ContractLineBulkEditForm(NetBoxModelBulkEditForm):
    description = forms.CharField(max_length=200, required=False, label=_('Description'))
    quantity = forms.DecimalField(max_digits=12, decimal_places=4, required=False, label=_('Quantity'))
    unit_price = forms.DecimalField(max_digits=12, decimal_places=2, required=False, label=_('Unit price'))
    unit = DynamicModelChoiceField(queryset=Unit.objects.all(), required=False, selector=True, label=_('Unit'))
    start_date = forms.DateField(required=False, widget=DatePicker(), label=_('Start date'))
    end_date = forms.DateField(required=False, widget=DatePicker(), label=_('End date'))
    comments = CommentField(required=False, label=_('Comments'))
    nullable_fields = ('comments',)
    fieldsets = (
        FieldSet('description', name=_('Contract line')),
        FieldSet('quantity', 'unit_price', 'unit', name=_('Price')),
        FieldSet('start_date', 'end_date', name=_('Dates')),
    )

    model = ContractLine


# AccountingDimension


class AccountingDimensionForm(NetBoxModelForm):
    fieldsets = (
        FieldSet('name', 'value', 'status', 'tags', name=_('Accounting dimension')),
    )

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
    fieldsets = (
        FieldSet('q', 'filter_id'),
        FieldSet('name', 'value', 'status', name=_('Attributes')),
    )

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
    fieldsets = (
        FieldSet('name', 'value', name=_('Accounting dimension')),
    )

    model = AccountingDimension
