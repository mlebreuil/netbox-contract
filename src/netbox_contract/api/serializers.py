from drf_yasg.utils import swagger_serializer_method
from rest_framework import serializers
from django.contrib.auth.models import ContentType
from circuits.api.nested_serializers import NestedCircuitSerializer
from netbox.api.serializers import NetBoxModelSerializer, WritableNestedSerializer
from netbox.api.fields import ContentTypeField
from netbox.constants import NESTED_SERIALIZER_PREFIX
from utilities.api import get_serializer_for_model
from ..models import Contract, Invoice, ServiceProvider, ContractAssignement

class NestedServiceProviderSerializer(WritableNestedSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_contract-api:serviceprovider-detail'
    )

    class Meta:
        model = ServiceProvider
        fields = ('id', 'url', 'display', 'name')

class NestedContracSerializer(WritableNestedSerializer):
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

class NestedContractAssignementSerializer(WritableNestedSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_contract-api:ContractAssignement-detail'
    )

    class Meta:
        model = ContractAssignement
        fields = ('id', 'url', 'display','contract','content_object')

class ContractSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_contract-api:contract-detail'
    )
    circuit= NestedCircuitSerializer(many=True, required=False)
    external_partie = NestedServiceProviderSerializer(many=False)

    class Meta:
        model = Contract
        fields = (
            'id', 'url','display', 'name', 'status', 'external_partie','internal_partie','circuit','comments',
            'tags', 'custom_fields', 'created', 'last_updated',
        )

class InvoiceSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_contract-api:invoice-detail'
    )
    contracts = NestedContracSerializer(many=True, required=False)

    class Meta:
        model = Invoice
        fields = (
            'id', 'url', 'display', 'number', 'date', 'contracts', 'tags', 'custom_fields', 'created',
            'last_updated',
        )

class ServiceProviderSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_contract-api:serviceprovider-detail'
    )

    class Meta:
        model = ServiceProvider
        fields = (
            'id', 'url', 'display', 'name', 'portal_url', 'tags', 'custom_fields', 'created',
            'last_updated',
        )

class ContractAssignementSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='plugins-api:netbox_contract-api:contractassignement-detail')
    content_type = ContentTypeField(
        queryset=ContentType.objects.all()
    )
    content_object = serializers.SerializerMethodField(read_only=True)
    contract = NestedContracSerializer()

    class Meta:
        model = ContractAssignement
        fields = [
            'id', 'url', 'display', 'content_type', 'object_id', 'content_object', 'contract', 'created',
            'last_updated',
        ]

    @swagger_serializer_method(serializer_or_field=serializers.JSONField)
    def get_content_object(self, instance):
        serializer = get_serializer_for_model(instance.content_type.model_class(), prefix=NESTED_SERIALIZER_PREFIX)
        context = {'request': self.context['request']}
        return serializer(instance.content_object, context=context).data
