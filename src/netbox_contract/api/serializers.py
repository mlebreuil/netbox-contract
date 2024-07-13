from django.contrib.auth.models import ContentType
from drf_yasg.utils import swagger_serializer_method
from netbox.api.fields import ContentTypeField
from netbox.api.serializers import NetBoxModelSerializer, WritableNestedSerializer
from netbox.constants import NESTED_SERIALIZER_PREFIX
from rest_framework import serializers
from tenancy.api.nested_serializers import NestedTenantSerializer
from utilities.api import get_serializer_for_model

from ..models import (
    AccountingDimension,
    Contract,
    ContractAssignment,
    Invoice,
    InvoiceLine,
    ServiceProvider,
)


class NestedServiceProviderSerializer(WritableNestedSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_contract-api:serviceprovider-detail'
    )

    class Meta:
        model = ServiceProvider
        fields = ('id', 'url', 'display', 'name')


class NestedContractSerializer(WritableNestedSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_contract-api:contract-detail'
    )

    class Meta:
        model = Contract
        fields = ('id', 'url', 'display', 'name')


class NestedInvoiceSerializer(WritableNestedSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_contract-api:invoice-detail'
    )

    class Meta:
        model = Invoice
        fields = ('id', 'url', 'display', 'number')
        brief_fields = ('id', 'url', 'display', 'number')


class NestedContractAssignmentSerializer(WritableNestedSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_contract-api:ContractAssignment-detail'
    )

    class Meta:
        model = ContractAssignment
        fields = ('id', 'url', 'display', 'contract', 'content_object')
        brief_fields = ('id', 'url', 'display', 'contract', 'content_object')


class NestedInvoicelineSerializer(WritableNestedSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_contract-api:InvoiceLine-detail'
    )

    class Meta:
        model = InvoiceLine
        fields = ('id', 'url', 'display', 'invoice', 'amount')
        brief_fields = ('id', 'url', 'display', 'invoice', 'amount')


class NestedAccountingDimensionSerializer(WritableNestedSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_contract-api:AccountingDimension-detail'
    )

    class Meta:
        model = AccountingDimension
        fields = ('id', 'url', 'display', 'name', 'value')
        brief_fields = ('id', 'url', 'display', 'name', 'value')


class ContractSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_contract-api:contract-detail'
    )
    yrc = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    parent = NestedContractSerializer(many=False, required=False)
    tenant = NestedTenantSerializer(many=False, required=False)
    external_partie_object_type = ContentTypeField(queryset=ContentType.objects.all())
    external_partie_object = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Contract
        fields = (
            'id',
            'url',
            'display',
            'name',
            'external_partie_object_type',
            'external_partie_object_id',
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
            'external_partie_object',
            'status',
        )

    @swagger_serializer_method(serializer_or_field=serializers.JSONField)
    def get_external_partie_object(self, instance):
        serializer = get_serializer_for_model(
            instance.external_partie_object_type.model_class(),
            prefix=NESTED_SERIALIZER_PREFIX,
        )
        context = {'request': self.context['request']}
        return serializer(instance.external_partie_object, context=context).data


class InvoiceSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_contract-api:invoice-detail'
    )
    contracts = NestedContractSerializer(many=True, required=False)

    class Meta:
        model = Invoice
        fields = (
            'id',
            'url',
            'display',
            'number',
            'date',
            'contracts',
            'period_start',
            'period_end',
            'currency',
            'accounting_dimensions',
            'amount',
            'comments',
            'tags',
            'custom_fields',
            'created',
            'last_updated',
        )
        brief_fields = ('id', 'url', 'display', 'number', 'contracts')


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
        serializer = get_serializer_for_model(
            instance.content_type.model_class(), prefix=NESTED_SERIALIZER_PREFIX
        )
        context = {'request': self.context['request']}
        return serializer(instance.content_object, context=context).data


class InvoiceLineSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_contract-api:invoiceline-detail'
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
            'comments',
            'tags',
            'custom_fields',
            'created',
            'last_updated',
        )
        brief_fields = ('invoice', 'amount', 'url', 'display', 'name')


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
        brief_fields = ('name', 'value', 'url', 'display')
