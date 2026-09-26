from django.contrib.auth.models import ContentType
from drf_yasg.utils import swagger_serializer_method
from netbox.api.fields import ContentTypeField, SerializedPKRelatedField
from netbox.api.serializers import NetBoxModelSerializer, WritableNestedSerializer
from rest_framework import serializers
from tenancy.api.serializers_.tenants import TenantSerializer
from utilities.api import get_serializer_for_model

from ..models import (
    AccountingDimension,
    Contract,
    ContractAssignment,
    ContractLine,
    ContractType,
    CurrencyChoices,
    Invoice,
    InvoiceLine,
    ServiceProvider,
    Unit,
)
from ..services import invoicing
from ..validators import check_invoice_contracts


class NestedContractSerializer(WritableNestedSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_contract-api:contract-detail'
    )
    yrc = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    tenant = TenantSerializer(nested=True, required=False, allow_null=True)
    external_party_object_type = ContentTypeField(queryset=ContentType.objects.all())
    external_party_object = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Contract
        fields = fields = (
            'id',
            'url',
            'display',
            'name',
            'contract_type',
            'external_party_object_type',
            'external_party_object_id',
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
            'mrc',
            'yrc',
            'nrc',
            'invoice_frequency',
            'comments',
            'documents',
        )

    @swagger_serializer_method(serializer_or_field=serializers.JSONField)
    def get_external_party_object(self, instance):
        serializer = get_serializer_for_model(
            instance.external_party_object_type.model_class()
        )
        context = {'request': self.context['request']}
        return serializer(
            instance.external_party_object, nested=True, context=context
        ).data


class NestedInvoiceSerializer(WritableNestedSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_contract-api:invoice-detail'
    )

    class Meta:
        model = Invoice
        fields = ('id', 'url', 'display', 'number')
        brief_fields = ('id', 'url', 'display', 'number')


class NestedAccountingDimensionSerializer(WritableNestedSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_contract-api:accountingdimension-detail'
    )

    class Meta:
        model = AccountingDimension
        fields = ('id', 'url', 'display', 'name', 'value')
        brief_fields = ('id', 'url', 'display', 'name', 'value')


class ContractTypeSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='plugins-api:netbox_contract-api:contracttype-detail')

    class Meta:
        model = ContractType
        fields = (
            'id',
            'url',
            'display',
            'name',
            'description',
            'color',
            'tags',
            'custom_fields',
            'created',
            'last_updated',
        )
        brief_fields = ('id', 'name', 'description', 'url', 'display')


DEPRECATED_COST_HELP = 'Deprecated: replaced by contract lines. Kept for compatibility.'


class ContractSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_contract-api:contract-detail'
    )
    contract_type = ContractTypeSerializer(nested=True, required=False, allow_null=True)
    yrc = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True, help_text=DEPRECATED_COST_HELP)
    total_contract_value = serializers.DecimalField(
        max_digits=16, decimal_places=2, read_only=True, allow_null=True,
        help_text='Total value of the contract lines; null when not available (open-ended recurring line)',
    )
    yearly_contract_value = serializers.DecimalField(
        max_digits=16, decimal_places=2, read_only=True, help_text='Twelve-month value of the recurring lines'
    )
    yearly_billable_value = serializers.DecimalField(
        max_digits=16, decimal_places=2, read_only=True,
        help_text='Yearly value invoiced under this contract, including its non-billable descendants',
    )
    parent = NestedContractSerializer(many=False, required=False)
    tenant = TenantSerializer(nested=True, required=False, allow_null=True)
    external_party_object_type = ContentTypeField(queryset=ContentType.objects.all())
    external_party_object = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Contract
        fields = (
            'id',
            'url',
            'display',
            'name',
            'contract_type',
            'external_party_object_type',
            'external_party_object_id',
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
            'mrc',
            'yrc',
            'nrc',
            'invoice_frequency',
            'billable',
            'total_contract_value',
            'yearly_contract_value',
            'yearly_billable_value',
            'comments',
            'documents',
            'parent',
            'tags',
            'custom_fields',
            'created',
            'last_updated',
        )
        extra_kwargs = {
            'mrc': {'help_text': DEPRECATED_COST_HELP},
            'nrc': {'help_text': DEPRECATED_COST_HELP},
        }
        brief_fields = (
            'id',
            'url',
            'display',
            'name',
            'contract_type',
            'external_party_object_type',
            'external_party_object_id',
            'external_party_object',
            'external_reference',
            'internal_party',
            'tenant',
            'status',
            'start_date',
            'end_date',
            'initial_term',
            'renewal_term',
            'currency',
            'mrc',
            'yrc',
            'nrc',
            'invoice_frequency',
            'billable',
            'comments',
            'parent',
        )

    @swagger_serializer_method(serializer_or_field=serializers.JSONField)
    def get_external_party_object(self, instance):
        serializer = get_serializer_for_model(
            instance.external_party_object_type.model_class()
        )
        context = {'request': self.context['request']}
        return serializer(
            instance.external_party_object, nested=True, context=context
        ).data


class InvoiceSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_contract-api:invoice-detail'
    )
    contracts = SerializedPKRelatedField(
        queryset=Contract.objects.all(),
        serializer=ContractSerializer,
        required=False,
        many=True,
    )

    class Meta:
        model = Invoice
        fields = (
            'id',
            'url',
            'display',
            'number',
            'date',
            'template',
            'status',
            'contracts',
            'period_start',
            'period_end',
            'currency',
            'amount',
            'comments',
            'documents',
            'tags',
            'custom_fields',
            'created',
            'last_updated',
        )
        extra_kwargs = {
            'template': {'help_text': 'Deprecated: invoice lines are generated from the contract lines.'},
        }
        brief_fields = (
            'id',
            'url',
            'display',
            'number',
            'date',
            'template',
            'contracts',
            'period_start',
            'period_end',
            'currency',
            'amount',
            'comments',
        )

    def validate(self, data):
        is_new = self.instance is None
        previous_contract_ids = [] if is_new else list(self.instance.contracts.values_list('pk', flat=True))
        previous_currency = None if is_new else Invoice.objects.get(pk=self.instance.pk).currency

        data = super().validate(data)

        # contracts and currency (the relation is saved after the invoice, so it is checked here)
        if 'contracts' in data:
            contracts = data['contracts']
        else:
            contracts = [] if is_new else list(Contract.objects.filter(pk__in=previous_contract_ids))
        currency = data.get('currency', previous_currency or Invoice._meta.get_field('currency').default)
        errors = check_invoice_contracts(
            is_new, contracts, currency, previous_contract_ids=previous_contract_ids,
            previous_currency=previous_currency,
        )
        if errors:
            raise serializers.ValidationError({'contracts': errors})

        # a new invoice gets its lines from the contract lines (FR-021, FR-023)
        if is_new and not data.get('template') and len(contracts) == 1:
            errors = invoicing.check_new_invoice(
                contracts[0], data.get('amount'), data.get('period_start'), data.get('period_end')
            )
            if errors:
                raise serializers.ValidationError({'non_field_errors': errors})

        # template checks
        if data.get('template'):
            # Check that there is only one invoice template per contract
            for contract in contracts:
                for invoice in contract.invoices.all():
                    if invoice.template and invoice != self.instance:
                        raise serializers.ValidationError(
                            'Only one invoice template allowed per contract'
                        )

            # Prefix the invoice name with _template
            if contracts:
                data['number'] = '_invoice_template_' + contracts[-1].name

            # set the periode start and end date to null
            data['period_start'] = None
            data['period_end'] = None
        return data

    def create(self, validated_data):
        instance = super().create(validated_data)

        # Invoice lines are generated from the contract lines; invoice templates are no longer copied
        if not instance.template:
            invoicing.generate_invoice_lines(instance)

        return instance


class ServiceProviderSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_contract-api:serviceprovider-detail'
    )

    class Meta:
        model = ServiceProvider
        fields = (
            'id',
            'url',
            'display',
            'name',
            'slug',
            'portal_url',
            'comments',
            'tags',
            'custom_fields',
            'created',
            'last_updated',
        )
        brief_fields = ('id', 'url', 'display', 'name', 'slug')


class ContractAssignmentSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_contract-api:contractassignment-detail'
    )
    content_type = ContentTypeField(queryset=ContentType.objects.all())
    content_object = serializers.SerializerMethodField(read_only=True)
    contract = NestedContractSerializer()

    class Meta:
        model = ContractAssignment
        fields = (
            'id',
            'url',
            'display',
            'content_type',
            'object_id',
            'content_object',
            'contract',
            'tags',
            'custom_fields',
            'created',
            'last_updated',
        )
        brief_fields = ('id', 'url', 'display', 'content_object', 'contract', 'tags', 'custom_fields')

    @swagger_serializer_method(serializer_or_field=serializers.JSONField)
    def get_content_object(self, instance):
        serializer = get_serializer_for_model(instance.content_type.model_class())
        context = {'request': self.context['request']}
        return serializer(instance.content_object, nested=True, context=context).data


class UnitSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='plugins-api:netbox_contract-api:unit-detail')

    class Meta:
        model = Unit
        fields = (
            'id',
            'url',
            'display',
            'name',
            'description',
            'billing_method',
            'months',
            'comments',
            'tags',
            'custom_fields',
            'created',
            'last_updated',
        )
        brief_fields = ('id', 'url', 'display', 'name', 'description', 'billing_method', 'months')


class NestedContractLineSerializer(WritableNestedSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='plugins-api:netbox_contract-api:contractline-detail')

    class Meta:
        model = ContractLine
        fields = ('id', 'url', 'display', 'description', 'quantity', 'unit_price', 'start_date', 'end_date')


class ContractLineAmendmentSerializer(serializers.Serializer):
    """Input of the amend action (FR-030)."""

    effective_date = serializers.DateField(help_text='First day of the new terms')
    unit_price = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, allow_null=True)
    quantity = serializers.DecimalField(max_digits=12, decimal_places=4, required=False, allow_null=True)
    reason = serializers.CharField(help_text='Recorded in the change log and on the new line')


class ContractLineSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='plugins-api:netbox_contract-api:contractline-detail')
    contract = NestedContractSerializer()
    unit = UnitSerializer(nested=True)
    currency = serializers.ChoiceField(
        choices=CurrencyChoices,
        required=False,
        allow_blank=True,
        help_text="Defaults to the contract's currency",
    )
    accounting_dimensions = SerializedPKRelatedField(
        queryset=AccountingDimension.objects.all(),
        serializer=NestedAccountingDimensionSerializer,
        required=False,
        many=True,
    )
    total_value = serializers.DecimalField(
        max_digits=14, decimal_places=2, read_only=True, allow_null=True,
        help_text='Null when not available (recurring line without end date on an open-ended contract)',
    )
    yearly_value = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    replaces = NestedContractLineSerializer(read_only=True, help_text='The line replaced by an amendment')

    class Meta:
        model = ContractLine
        fields = (
            'id',
            'url',
            'display',
            'contract',
            'description',
            'quantity',
            'unit_price',
            'unit',
            'currency',
            'start_date',
            'end_date',
            'accounting_dimensions',
            'total_value',
            'yearly_value',
            'replaces',
            'invoiced_at_conversion',
            'comments',
            'tags',
            'custom_fields',
            'created',
            'last_updated',
        )
        brief_fields = ('id', 'url', 'display', 'contract', 'description', 'quantity', 'unit', 'unit_price',
                        'currency')

    def validate(self, data):
        data = super().validate(data)
        names = [dimension.name for dimension in data.get('accounting_dimensions') or ()]
        if len(names) != len(set(names)):
            raise serializers.ValidationError('duplicate accounting dimension')
        return data


class InvoiceLineSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_contract-api:invoiceline-detail'
    )
    invoice = NestedInvoiceSerializer(many=False, required=False)
    contract_line = ContractLineSerializer(nested=True, required=False, allow_null=True)
    unit = UnitSerializer(nested=True, read_only=True, help_text='Unit of the contract line')
    unit_price = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True, allow_null=True, help_text='Unit price of the contract line'
    )
    amount = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False,
        help_text='Calculated (and ignored if sent) when the line references a contract line; required otherwise',
    )
    accounting_dimensions = SerializedPKRelatedField(
        queryset=AccountingDimension.objects.all(),
        serializer=NestedAccountingDimensionSerializer,
        required=False,
        many=True,
    )

    class Meta:
        model = InvoiceLine
        fields = (
            'id',
            'url',
            'display',
            'invoice',
            'contract_line',
            'quantity',
            'unit',
            'unit_price',
            'amount',
            'currency',
            'accounting_dimensions',
            'comments',
            'tags',
            'custom_fields',
            'created',
            'last_updated',
        )
        brief_fields = (
            'invoice',
            'accounting_dimensions',
            'amount',
            'url',
            'display',
            'name',
        )

    def validate(self, data):
        data = super().validate(data)
        # check for duplicate dimensions
        accounting_dimensions = data.get('accounting_dimensions') or []
        dimensions_names = []
        for dimension in accounting_dimensions:
            if dimension.name in dimensions_names:
                raise serializers.ValidationError('duplicate accounting dimension')
            dimensions_names.append(dimension.name)
        return data


class AccountingDimensionSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_contract-api:accountingdimension-detail'
    )

    class Meta:
        model = AccountingDimension
        fields = (
            'id',
            'url',
            'display',
            'name',
            'value',
            'status',
            'comments',
            'tags',
            'custom_fields',
            'created',
            'last_updated',
        )
        brief_fields = ('id', 'name', 'value', 'url', 'display')
