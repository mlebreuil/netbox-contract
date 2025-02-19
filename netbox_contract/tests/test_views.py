from datetime import date
from decimal import Decimal

from circuits.models import Provider
from django.contrib.contenttypes.models import ContentType
from tenancy.models import Tenant
from utilities.testing import ViewTestCases

from netbox_contract.models import (
    Contract,
    ServiceProvider,
    StatusChoices,
)
from netbox_contract.tests.custom import ModelViewTestCase


class ContractTestCase(ModelViewTestCase, ViewTestCases.PrimaryObjectViewTestCase):
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
            external_partie_object_id=Provider.objects.get(slug='provider-a').id,
            internal_partie='default',
            status=StatusChoices.STATUS_ACTIVE,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            currency='usd',
            yrc=Decimal(1000),
            invoice_frequency=1
        )

        contract2 = Contract.objects.create(
            name='Contract2',
            external_partie_object_type=ContentType.objects.get_for_model(Provider),
            external_partie_object_id=Provider.objects.get(slug='provider-a').id,
            internal_partie='default',
            status=StatusChoices.STATUS_ACTIVE,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            currency='usd',
            yrc=Decimal(1000),
            invoice_frequency=1
        )

        contract3 = Contract.objects.create(
            name='Contract3',
            external_partie_object_type=ContentType.objects.get_for_model(Provider),
            external_partie_object_id=Provider.objects.get(slug='provider-a').id,
            internal_partie='default',
            status=StatusChoices.STATUS_ACTIVE,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            currency='usd',
            yrc=Decimal(1000),
            invoice_frequency=1
        )

        cls.form_data = {
            'name': 'Contract X',
            'external_partie_object_type': ContentType.objects.get_for_model(Provider).pk,
            'external_partie_object': Provider.objects.get(slug='provider-a').id,
            'external_reference': 'External Reference 1',
            'internal_partie': 'default',
            'tenant': Tenant.objects.get(name='Tenant 1').id,
            'status': StatusChoices.STATUS_ACTIVE,
            'start_date': date(2025, 1, 1),
            'end_date': date(2025, 12, 31),
            'initial_term': 12,
            'renewal_term': 12,
            'notice_period': 90,
            'currency': 'usd',
            'yrc': Decimal(1000),
            'nrc': Decimal(1000),
            'invoice_frequency': 1,
        }

        cls.csv_data = (
            'name,external_partie_object_type,external_partie_object_id,internal_partie,'
            'tenant,status,start_date,end_date,currency,mrc,nrc,invoice_frequency',
            'Contract 4,netbox_contract.serviceprovider,Service Provider A,entity1,'
            'Tenant 1,active,2025-01-01,2025-12-31,usd,100,1000,1',
            'Contract 5,netbox_contract.serviceprovider,Service Provider A,entity1,'
            'Tenant 1,active,2025-01-01,2025-12-31,usd,100,1000,1',
            'Contract 6,netbox_contract.serviceprovider,Service Provider A,entity1,'
            'Tenant 1,active,2025-01-01,2025-12-31,usd,100,1000,1'
        )

        cls.csv_update_data = (
            'id,name,comments',
            f'{contract1.pk},Contract 1,First contract',
            f'{contract2.pk},Contract 2,Second contract',
            f'{contract3.pk},Contract 3,Third contract',
        )

        cls.bulk_edit_data = {
            'comments': 'New comment',
        }
