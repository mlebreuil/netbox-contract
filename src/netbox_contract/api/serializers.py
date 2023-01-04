from rest_framework import serializers

from circuits.api.nested_serializers import NestedCircuitSerializer
from netbox.api.serializers import NetBoxModelSerializer, WritableNestedSerializer
from ..models import Contract, Invoice, ServiceProvider

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

class ContractSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_contract-api:contract-detail'
    )
    circuit= NestedCircuitSerializer(many=True)
    external_partie = NestedServiceProviderSerializer(many=False)

    class Meta:
        model = Contract
        fields = (
            'id', 'url','display', 'name', 'external_partie','internal_partie','circuit','comments',
            'tags', 'custom_fields', 'created', 'last_updated',
        )

class InvoiceSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_contract-api:invoice-detail'
    )
    contract=NestedContracSerializer()

    class Meta:
        model = Invoice
        fields = (
            'id', 'url', 'display', 'number', 'contract', 'tags', 'custom_fields', 'created',
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
