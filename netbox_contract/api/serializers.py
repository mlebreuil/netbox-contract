from django.contrib.auth.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
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
    ContractType,
    Invoice,
    InvoiceLine,
    ServiceProvider,
)


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
            'currency',
            'mrc',
            'yrc',
            'nrc',
            'invoice_frequency',
            'comments',
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
            'tags',
            'custom_fields',
            'created',
            'last_updated',
        )
        brief_fields = ('id', 'name', 'description', 'url', 'display')


class ContractSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_contract-api:contract-detail'
    )
    contract_type = ContractTypeSerializer(nested=True, required=False, allow_null=True)
    yrc = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
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
            'currency',
            'mrc',
            'yrc',
            'nrc',
            'invoice_frequency',
            'comments',
            'parent',
            'tags',
            'custom_fields',
            'created',
            'last_updated',
        )
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
            'contracts',
            'period_start',
            'period_end',
            'currency',
            'amount',
            'comments',
            'tags',
            'custom_fields',
            'created',
            'last_updated',
        )
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
        data = super().validate(data)

        # template checks
        if data['template']:
            # Check that there is only one invoice template per contract
            contracts = data['contracts']
            for contract in contracts:
                for invoice in contract.invoices.all():
                    if invoice.template and invoice != self.instance:
                        raise serializers.ValidationError(
                            'Only one invoice template allowed per contract'
                        )

            # Prefix the invoice name with _template
            data['number'] = '_invoice_template_' + contract.name

            # set the periode start and end date to null
            data['period_start'] = None
            data['period_end'] = None
        return data

    def create(self, validated_data):
        instance = super().create(validated_data)

        if not instance.template:
            contracts = instance.contracts.all()

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
                        line.invoice = instance

                        # adjust the first invoice line amount
                        amount = validated_data['amount']
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
            'portal_url',
            'tags',
            'custom_fields',
            'created',
            'last_updated',
        )
        brief_fields = ('id', 'url', 'display', 'name')


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
            'created',
            'last_updated',
        )
        brief_fields = ('id', 'url', 'display', 'content_object', 'contract')

    @swagger_serializer_method(serializer_or_field=serializers.JSONField)
    def get_content_object(self, instance):
        serializer = get_serializer_for_model(instance.content_type.model_class())
        context = {'request': self.context['request']}
        return serializer(instance.content_object, nested=True, context=context).data


class InvoiceLineSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_contract-api:invoiceline-detail'
    )
    invoice = NestedInvoiceSerializer(many=False, required=False)
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
        super().validate(data)
        # check for duplicate dimensions
        accounting_dimensions = data['accounting_dimensions']
        dimensions_names = []
        for dimension in accounting_dimensions:
            if dimension.name in dimensions_names:
                raise serializers.ValidationError('duplicate accounting dimension')
            else:
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
            'comments',
            'tags',
            'custom_fields',
            'created',
            'last_updated',
        )
        brief_fields = ('id', 'name', 'value', 'url', 'display')
