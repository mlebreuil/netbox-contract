from django import forms
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _
from netbox.forms import (
    NetBoxModelBulkEditForm,
    NetBoxModelFilterSetForm,
    NetBoxModelForm,
    NetBoxModelImportForm,
)
from circuits.models import Provider, ProviderAccount
from core.models import ObjectType
from utilities.forms import get_field_value
from utilities.forms.fields import (
    ColorField,
    CommentField,
    ContentTypeChoiceField,
    CSVContentTypeField,
    CSVModelChoiceField,
    DynamicModelChoiceField,
    TagFilterField,
    DynamicModelMultipleChoiceField,
)
from utilities.forms.widgets import DatePicker, HTMXSelect
from .models import (
    Contract,
    ContractAssignment,
    ContractType,
    Currency,
    LicenseAssignment,
    LicenseType,
    ServiceLevelAgreement,
    SoftwareLicense,
)
from dcim.models import Manufacturer, Region
plugin_settings = settings.PLUGINS_CONFIG['netbox_contracts']



# Contract
class ContractForm(NetBoxModelForm):
    parent = DynamicModelChoiceField(
        queryset=Contract.objects.all(),
        required=False,
        selector=True,
        label=_('Parent'),
    )
    contract_type = DynamicModelChoiceField(
        queryset=ContractType.objects.all(),
        required=True,
        selector=True, 
        quick_add=True,
        label=_('Contract Type')
    )
    provider = DynamicModelChoiceField(
        label=_('Provider'),
        queryset=Provider.objects.all(),
        selector=True,
        quick_add=True
    )
    provider_account = DynamicModelChoiceField(
        label=_('Provider account'),
        queryset=ProviderAccount.objects.all(),
        required=False,
        query_params={
            'provider_id': '$provider',
        }
    )
    comments = CommentField()


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    class Meta:
        model = Contract
        fields = (
            'name',
            'contract_type',
            'provider',
            'provider_account',
            'start_date',
            'end_date',
            'notice_period',
            'currency',
            'yrc',
            'nrc',
            'documents',
            'parent',
            'comments',
            'tags',
        )

        widgets = {
            'start_date': DatePicker(),
            'end_date': DatePicker(),
        }

class ContractFilterForm(NetBoxModelFilterSetForm):
    model = Contract
    contract_type = forms.ModelMultipleChoiceField(
        queryset=ContractType.objects.all(),
        required=False,
        label=_('Contract Type'),
        help_text=_('Filter by Contract Type'),
    )
    provider = DynamicModelChoiceField(
        queryset=Provider.objects.all(),
        required=False,
        selector=True,
        label=_('Provider'),
        help_text=_('Filter by Provider'),
    )
    provider_account = DynamicModelChoiceField(
        queryset=ProviderAccount.objects.all(),
        required=False,
        selector=True,
        label=_('Provider Account'),
        help_text=_('Filter by Provider Account'),
        query_params={
            'provider_id': '$provider',
        }
    )
    parent = DynamicModelChoiceField(
        queryset=Contract.objects.all(),
        required=False,
        selector=True,
        label=_('Parent'),
    )
    tag = TagFilterField(model)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class ContractCSVForm(NetBoxModelImportForm):
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
    provider = CSVModelChoiceField(
        queryset=Provider.objects.all(),
        to_field_name='name',
        help_text='NetBox name of the provider ',
        required=True,
        label=_('Provider'),
    )
    provider_account = CSVModelChoiceField(
        queryset=ProviderAccount.objects.all(),
        to_field_name='account',
        help_text='NetBox account name of the provider account ',
        required=False,
        label=_('Provider Account'),
    )
    currency = CSVModelChoiceField(
        queryset=Currency.objects.all(),
        to_field_name='currency_code',
        help_text='Currency code (e.g. USD)',
        required=False,
        label=_('Currency'),
    )

    class Meta:
        model = Contract
        fields = [
            'name',
            'contract_type',
            'provider',
            'provider_account',
            'start_date',
            'end_date',
            'notice_period',
            'currency',
            'yrc',
            'nrc',
            'documents',
            'parent',
            'comments',
            'tags',
        ]

class ContractBulkEditForm(NetBoxModelBulkEditForm):
    name = forms.CharField(max_length=100, required=False, label=_('Name'))
    contract_type = forms.ModelChoiceField(
        queryset=ContractType.objects.all(),
        required=False,
        label=_('Contract Type')
    )
    provider = DynamicModelChoiceField(
        queryset=Provider.objects.all(),
        required=False,
        selector=True,
        label=_('Provider'),
    )
    provider_account = DynamicModelChoiceField(
        queryset=ProviderAccount.objects.all(),
        required=False,
        selector=True,
        label=_('Provider Account'),
    )
    start_date = forms.DateField(required=False, label=_('Start Date'), widget=DatePicker())
    end_date = forms.DateField(required=False, label=_('End Date'), widget=DatePicker())
    notice_period = forms.IntegerField(required=False, label=_('Notice Period'))
    currency = DynamicModelChoiceField(
        queryset=Currency.objects.all(),
        required=False,
        selector=True,
        label=_('Currency'),
    )
    yrc = forms.DecimalField(required=False, label=_('Yearly Recurring Cost'))
    nrc = forms.DecimalField(required=False, label=_('Non-Recurring Cost'))
    documents = forms.URLField(required=False, label=_('Documents URL'))
    comments = CommentField(required=False, label=_('Comments'))
    parent = DynamicModelChoiceField(
        queryset=Contract.objects.all(),
        required=False,
        selector=True,
        label=_('Parent'),
    )
    nullable_fields = ('comments', 'documents', 'yrc', 'nrc', 'provider_account')
    model = Contract

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

# ContractType
class ContractTypeForm(NetBoxModelForm):
    color = ColorField(label=_('Color'))
    comments = CommentField(required=False)

    class Meta:
        model = ContractType
        fields = (
            'name',
            'description',
            'color',
            'comments',
            'tags',
        )

class ContractTypeCSVForm(NetBoxModelImportForm):
    name = forms.CharField(max_length=100, label=_('Name'))
    description = CommentField(label=_('Description'), required=False)
    color = ColorField(label=_('Color'), required=False)
    comments = CommentField(label=_('Comments'), required=False)

    class Meta:
        model = ContractType
        fields = ['name', 'description', 'color', 'comments', 'tags']

class ContractTypeBulkEditForm(NetBoxModelBulkEditForm):
    description = CommentField(label=_('Description'), required=False)
    color = ColorField(label=_('Color'), required=False)
    comments = CommentField(label=_('Comments'), required=False)
    nullable_fields = ('description', 'comments')
    model = ContractType

class ContractTypeFilterForm(NetBoxModelFilterSetForm):
    model = ContractType
    name = forms.CharField(required=False, label=_('Name'))
    description = CommentField(label=_('Description'))

# ContractAssignment
class ContractAssignmentForm(NetBoxModelForm):
    object_type = ContentTypeChoiceField(
        queryset=ContentType.objects.all(),
        widget=HTMXSelect(),
        label=_('Object Type'),
    )
    object = forms.ModelChoiceField(
        queryset=None,
        label=_('Object')
    )
    contract = DynamicModelChoiceField(
        queryset=Contract.objects.all(),
        required=True,
        selector=True,
        label=_('Contract'),
    )
    currency = DynamicModelChoiceField(
        queryset=Currency.objects.all(),
        required=False,
        selector=True,
        label=_('Currency'),
    )
    sla = DynamicModelChoiceField(
        queryset=ServiceLevelAgreement.objects.all(),
        required=False,
        selector=True,
        label=_('Service Level Agreement'),
    )
    provider = DynamicModelChoiceField(
        queryset=Provider.objects.all(),
        required=False,
        selector=True,
        label=_('Provider'),
    )
    provider_account = DynamicModelChoiceField(
        queryset=ProviderAccount.objects.all(),
        required=False,
        selector=True,
        label=_('Provider Account'),
        query_params={
            'provider_id': '$provider',
        }
    )
    fe = DynamicModelChoiceField(
        label=_('Field Engineer Provider'),
        queryset=Provider.objects.all(),
        required=False,
        help_text=_('Field Engineer provider responsible for this assignment'),
    )
    fe_account = DynamicModelChoiceField(
        label=_('Field Engineer Account'),
        queryset=ProviderAccount.objects.all(),
        required=False,
        help_text=_('Field Engineer account details'),
        query_params={
            'provider_id': '$fe',
        }
    )
    comments = CommentField(required=False)
    
    def __init__(self, *args, **kwargs):
        initial = kwargs.get('initial', None)
        super().__init__(*args, **kwargs)

        # Initialize the object gfk
        if initial and 'object_type' in initial:
            object_type = ContentType.objects.get_for_id(initial['object_type'])
            object_class = object_type.model_class()
            self.fields['object'].queryset = object_class.objects.all()
            if (
                self.instance.object_type
                and self.instance.object_type.id == object_type.id
            ):
                self.fields['object'].initial = self.instance.object
            else:
                self.fields['object'].initial = None
        elif self.instance.object_type:
            object_class = self.instance.object_type.model_class()
            self.fields['object'].queryset = object_class.objects.all()
            self.fields['object'].initial = self.instance.object
        else:
            self.fields['object'].queryset = Provider.objects.all()
            self.fields['object'].initial = None

    class Meta:
        model = ContractAssignment
        fields = [
            'contract',
            'object_type',
            'object',
            'end_date',
            'currency',
            'yrc',
            'nrc',
            'sla',
            'provider',
            'provider_account',
            'fe',
            'fe_account',
            'comments',
            'tags',
        ]

        widgets = {
            'end_date': DatePicker(),
        }

class ContractAssignmentFilterForm(NetBoxModelFilterSetForm):
    model = ContractAssignment
    region = DynamicModelMultipleChoiceField(
        queryset=Region.objects.all(),
        required=False,
        label='Region',
    )
    contract_type = forms.ModelMultipleChoiceField(
        queryset=ContractType.objects.all(),
        required=False,
        label=_('Contract Type'),
        help_text=_('Filter by Contract Type'),
    )
    contract = forms.ModelMultipleChoiceField(
        queryset=Contract.objects.all(),
        required=False,
        label=_('Contract'),
        help_text=_('Filter by Contract'),
    )
    provider = DynamicModelChoiceField(
        queryset=Provider.objects.all(),
        required=False,
        selector=True,
        label=_('Provider'),
        help_text=_('Filter by Provider'),
    )
    provider_account = DynamicModelChoiceField(
        queryset=ProviderAccount.objects.all(),
        required=False,
        selector=True,
        label=_('Provider Account'),
        help_text=_('Filter by Provider Account'),
        query_params={
            'provider_id': '$provider',
        }
    )
    fe = DynamicModelChoiceField(
        queryset=Provider.objects.all(),
        required=False,
        selector=True,
        label=_('Field Engineer Provider'),
        help_text=_('Filter by Field Engineer provider'),
    )
    fe_account = DynamicModelChoiceField(
        queryset=ProviderAccount.objects.all(),
        required=False,
        selector=True,
        label=_('Field Engineer Account'),
        help_text=_('Filter by Field Engineer account'),
        query_params={
            'provider_id': '$fe',
        }
    )

    # object_id = forms.CharField(
    #     help_text='ID of the object to be imported',
    #     label=_('Object ID')
    # )
    class Meta:
        model = ContractAssignment
        fields = ['contract','object_type','object_id', 'region']
        
class ContractAssignmentImportForm(NetBoxModelImportForm):
    object_type = CSVContentTypeField(
        queryset=ContentType.objects.all(),
        help_text='Content Type in the form <app>.<model>',
        label=_('Content type'),
    )
    contract = CSVModelChoiceField(
        queryset=Contract.objects.all(),
        help_text='ID of the contract to be imported',
        label=_('Contract'),
    )
    object_id = forms.CharField(
        required=True,
        help_text='ID of the object to be imported',
        label=_('Object ID')
    )
    currency = CSVModelChoiceField(
        queryset=Currency.objects.all(),
        to_field_name='currency_name',
        help_text='Currency name',
        required=False,
        label=_('Currency'),
    )
    sla = CSVModelChoiceField(
        queryset=ServiceLevelAgreement.objects.all(),
        to_field_name='name',
        help_text='Service level agreement name',
        required=False,
        label=_('SLA'),
    )
    provider = CSVModelChoiceField(
        queryset=Provider.objects.all(),
        to_field_name='name',
        help_text='NetBox name of the provider',
        required=False,
        label=_('Provider'),
    )
    provider_account = CSVModelChoiceField(
        queryset=ProviderAccount.objects.all(),
        to_field_name='account',
        help_text='NetBox account name of the provider account',
        required=False,
        label=_('Provider Account'),
    )
    fe = CSVModelChoiceField(
        queryset=Provider.objects.all(),
        to_field_name='name',
        help_text='NetBox name of the field engineer provider',
        required=False,
        label=_('Field Engineer Provider'),
    )
    fe_account = CSVModelChoiceField(
        queryset=ProviderAccount.objects.all(),
        to_field_name='account',
        help_text='NetBox account name of the field engineer account',
        required=False,
        label=_('Field Engineer Account'),
    )
    class Meta:
        model = ContractAssignment
        fields = [
            'contract',
            'object_type',
            'object_id',
            'end_date',
            'currency',
            'yrc',
            'nrc',
            'sla',
            'provider',
            'provider_account',
            'fe',
            'fe_account',
            'comments',
            'tags',
        ]

class ContractAssignmentBulkEditForm(NetBoxModelBulkEditForm):
    contract = DynamicModelChoiceField(
        queryset=Contract.objects.all(),
        required=False,
        selector=True,
        label=_('Contract'),
    )
    end_date = forms.DateField(required=False, label=_('End Date'), widget=DatePicker())
    currency = DynamicModelChoiceField(
        queryset=Currency.objects.all(),
        required=False,
        selector=True,
        label=_('Currency'),
    )
    yrc = forms.DecimalField(required=False, label=_('Yearly Recurring Cost'))
    nrc = forms.DecimalField(required=False, label=_('Non-Recurring Cost'))
    sla = DynamicModelChoiceField(
        queryset=ServiceLevelAgreement.objects.all(),
        required=False,
        selector=True,
        label=_('Service Level Agreement'),
    )
    provider = DynamicModelChoiceField(
        queryset=Provider.objects.all(),
        required=False,
        selector=True,
        label=_('Provider'),
    )
    provider_account = DynamicModelChoiceField(
        queryset=ProviderAccount.objects.all(),
        required=False,
        selector=True,
        label=_('Provider Account'),
    )
    fe = DynamicModelChoiceField(
        queryset=Provider.objects.all(),
        required=False,
        selector=True,
        label=_('Field Engineer Provider'),
    )
    fe_account = DynamicModelChoiceField(
        queryset=ProviderAccount.objects.all(),
        required=False,
        selector=True,
        label=_('Field Engineer Account'),
    )
    comments = CommentField(required=False, label=_('Comments'))
    nullable_fields = ('end_date', 'comments', 'yrc', 'nrc')
    model = ContractAssignment

# Service Level Agreement
class ServiceLevelAgreementForm(NetBoxModelForm):
    comments = CommentField(required=False)

    class Meta:
        model = ServiceLevelAgreement
        fields = ['name', 'description', 'comments', 'tags']

class ServiceLevelAgreementFilterForm(NetBoxModelFilterSetForm):
    model = ContractAssignment
    contract = DynamicModelChoiceField(
        queryset=ServiceLevelAgreement.objects.all(),
        required=False,
        selector=True,
        label=_('ServiceLevelAgreement'),
    )

class ServiceLevelAgreementImportForm(NetBoxModelImportForm):
    name = forms.CharField(required=False, label='SLA Name')
    description = forms.CharField(required=False, label='Description')
    comments = forms.CharField(required=False, label='Comments')

    class Meta:
        model = ServiceLevelAgreement
        fields = ['name', 'description', 'comments', 'tags']

class ServiceLevelAgreementBulkEditForm(NetBoxModelBulkEditForm):
    description = forms.CharField(required=False, label='Description')
    comments = CommentField(required=False, label='Comments')
    nullable_fields = ('description', 'comments')
    model = ServiceLevelAgreement

# Currency
class CurrencyForm(NetBoxModelForm):
    comments = CommentField(required=False)
    country = DynamicModelChoiceField(
        queryset=Region.objects.all(),
        required=False,
        selector=True,
        label=_('Country')
    )
    class Meta:
        model = Currency
        fields = ['currency_code', 'country', 'currency_name', 'currency_number', 'usd_rate', 'comments', 'tags']

class CurrencyFilterForm(NetBoxModelFilterSetForm):
    model = Currency
    country = DynamicModelMultipleChoiceField(
        queryset=Region.objects.all(),
        required=False,
        label='Country'
    )

    class Meta:
        model = Currency
        fields = ['currency_code', 'country', 'currency_name', 'currency_number', 'usd_rate']


class CurrencyBulkEditForm(NetBoxModelBulkEditForm):
    comments = CommentField(required=False, label=_('Comments'))
    nullable_fields = ('comments',)
    model = Currency

class CurrencyCSVForm(NetBoxModelImportForm):
    country = CSVModelChoiceField(
        queryset=Region.objects.all(),
        to_field_name='name',
        help_text='NetBox name of the Country ',
        required=True,
        label=_('Country'),
    )

    class Meta:
        model = Currency
        fields = ['currency_code', 'country', 'currency_name', 'currency_number', 'usd_rate', 'comments', 'tags']


#
# Software licensing
#
class LicenseTypeForm(NetBoxModelForm):
    class Meta:
        model = LicenseType
        fields = ('name', 'description', 'color', 'tags')


class LicenseTypeCSVForm(NetBoxModelImportForm):
    name = forms.CharField(max_length=100, label=_('Name'))
    description = forms.CharField(max_length=200, required=False, label=_('Description'))
    color = ColorField(label=_('Color'), required=False)

    class Meta:
        model = LicenseType
        fields = ('name', 'description', 'color', 'tags')


class SoftwareLicenseForm(NetBoxModelForm):
    manufacturer = DynamicModelChoiceField(
        queryset=Manufacturer.objects.all(),
        required=True,
        label=_('Manufacturer'),
    )
    local_currency = DynamicModelChoiceField(
        queryset=Currency.objects.all(),
        required=False,
        label=_('Local Currency'),
        context={'label': 'currency_code'},
    )
    license_type = DynamicModelChoiceField(
        queryset=LicenseType.objects.all(),
        required=False,
        label=_('License Type'),
    )

    class Meta:
        model = SoftwareLicense
        fields = (
            'manufacturer',
            'license_name',
            'friendly_name',
            'license_sku',
            'per_license_cost',
            'local_currency',
            'license_type',
            'tags',
        )


class SoftwareLicenseCSVForm(NetBoxModelImportForm):
    manufacturer = CSVModelChoiceField(
        queryset=Manufacturer.objects.all(),
        to_field_name='name',
        help_text='NetBox name of the manufacturer',
        label=_('Manufacturer'),
    )
    local_currency = CSVModelChoiceField(
        queryset=Currency.objects.all(),
        to_field_name='currency_code',
        help_text='Currency code (e.g. USD)',
        required=False,
        label=_('Local Currency'),
    )
    license_type = CSVModelChoiceField(
        queryset=LicenseType.objects.all(),
        to_field_name='name',
        help_text='License type name',
        required=False,
        label=_('License Type'),
    )

    class Meta:
        model = SoftwareLicense
        fields = (
            'manufacturer',
            'license_name',
            'friendly_name',
            'license_sku',
            'per_license_cost',
            'local_currency',
            'license_type',
            'tags',
        )


class LicenseAssignmentForm(NetBoxModelForm):
    software_license = DynamicModelChoiceField(
        queryset=SoftwareLicense.objects.all(),
        label=_('Software License'),
    )
    object_type = ContentTypeChoiceField(
        queryset=ObjectType.objects.public(),
        label=_('Object Type'),
        widget=HTMXSelect(),
    )
    object_id = forms.IntegerField(
        label=_('Object'),
        required=False,
        disabled=True,
        help_text=_('Select an object type first.'),
    )

    class Meta:
        model = LicenseAssignment
        fields = ('software_license', 'object_type', 'object_id', 'tags')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        object_type_id = get_field_value(self, 'object_type')
        model = None
        if object_type_id:
            try:
                model = ContentType.objects.get(pk=object_type_id).model_class()
            except (ContentType.DoesNotExist, ValueError):
                model = None

        # Once an object type is chosen, replace the placeholder with a lookup of that type's objects
        if model is not None:
            self.fields['object_id'] = DynamicModelChoiceField(
                queryset=model.objects.all(),
                label=_('Object'),
                selector=True,
            )
            if self.instance.pk and self.instance.object_type_id == int(object_type_id):
                self.fields['object_id'].initial = self.instance.assigned_object

    def clean(self):
        super().clean()

        # The object_id field yields a model instance; store its primary key on the instance instead.
        selected_object = self.cleaned_data.get('object_id')
        if selected_object is not None:
            self.cleaned_data['object_id'] = selected_object.pk

        return self.cleaned_data


class LicenseAssignmentCSVForm(NetBoxModelImportForm):
    software_license = CSVModelChoiceField(
        queryset=SoftwareLicense.objects.all(),
        to_field_name='license_name',
        help_text='Software license name',
        label=_('Software License'),
    )
    object_type = CSVContentTypeField(
        queryset=ObjectType.objects.public(),
        help_text='Content Type in the form <app>.<model>',
        label=_('Object type'),
    )
    object_id = forms.IntegerField(
        required=True,
        help_text='ID of the object to be assigned',
        label=_('Object ID'),
    )

    class Meta:
        model = LicenseAssignment
        fields = ('software_license', 'object_type', 'object_id', 'tags')
