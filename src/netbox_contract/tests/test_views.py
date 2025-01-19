from datetime import date

from circuits.models import Provider
from dcim.models import Device
from django.contrib.contenttypes.models import ContentType
from tenancy.models import Tenant
from utilities.testing import ViewTestCases

from netbox_contract.models import (
    Contract,
    InternalEntityChoices,
    ServiceProvider,
    StatusChoices,
)


class ContractTestCase(ViewTestCases.PrimaryObjectViewTestCase):
    model = Contract

    @classmethod
    def setUpTestData(cls):

        # Create test circuits
        Provider.objects.create(name='Provider A', slug='provider-a')
        # create test tenant
        Tenant.objects.create(name='Tenant 1', slug='tenant-1')
        ServiceProvider.objects.create(name='Service Provider A', slug='service-provider-a')

        # Create three Contracts
        contract1 = Contract.objects.create(
            name='Contract1',
            external_partie_object_type=ContentType.objects.get_for_model(Provider),
            external_partie_object_id=Device.objects.get(slug='provider-a').id,
            internal_partie=InternalEntityChoices.ENTITY,
            status=StatusChoices.STATUS_ACTIVE,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            yrc=1000,
        )

        contract2 = Contract.objects.create(
            name='Contract2',
            external_partie_object_type=ContentType.objects.get_for_model(Provider),
            external_partie_object_id=Device.objects.get(slug='provider-a').id,
            internal_partie=InternalEntityChoices.ENTITY,
            status=StatusChoices.STATUS_ACTIVE,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            yrc=1000,
        )

        contract3 = Contract.objects.create(
            name='Contract3',
            external_partie_object_type=ContentType.objects.get_for_model(Provider),
            external_partie_object_id=Device.objects.get(slug='provider-a').id,
            internal_partie=InternalEntityChoices.ENTITY,
            status=StatusChoices.STATUS_ACTIVE,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            yrc=1000,
        )

        cls.form_data = {
            'name': 'Contract X',
            'external_partie_object_type': ContentType.objects.get_for_model(Provider),
            'external_partie_object_id': Device.objects.get(slug='provider-a').id,
            'external_reference': 'External Reference 1',
            'internal_partie': InternalEntityChoices.ENTITY,
            'tenant': Tenant.objects.get(name='Tenant 1').id,
            'status': StatusChoices.STATUS_ACTIVE,
            'start_date': date(2025, 1, 1),
            'end_date': date(2025, 12, 31),
            'initial_term': 12,
            'renewal_term': 12,
            'notice_period': 90,
            'currency': 'USD',
            'yrc': 1000,
            'nrc': 1000,
            'invoice_frequency': 1,
        }

        cls.csv_data = (
            'name,external_partie,internal_partie,tenant,status,start_date,end_date,mrc,nrc,invoice_frequency'
            'Contract 4,Service Provider A,Default entity,Tenant1,Active,2025-01-01,2025-12-31,100,1000,1',
            'Contract 5,Service Provider A,Default entity,Tenant1,Active,2025-01-01,2025-12-31,100,1000,1',
            'Contract 6,Service Provider A,Default entity,Tenant1,Active,2025-01-01,2025-12-31,100,1000,1',
        )

        cls.csv_update_data = (
            'id,name,comments',
            f'{contract1.pk},Contract 1,First contract',
            f'{contract2.pk},Contract 2,Second contract',
            f'{contract3.pk},Contract 3,Third contract',
        )

        cls.bulk_edit_data = {
            'description': 'New description',
        }
