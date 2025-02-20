from datetime import date
from decimal import Decimal

from circuits.models import Provider
from django.contrib.contenttypes.models import ContentType
from tenancy.models import Tenant
from utilities.testing import ViewTestCases

from netbox_contract.models import (
    Contract,
    Invoice,
    InvoiceLine,
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
            "id,name,comments",
            f"{contract1.pk},Contract 1,First contract",
            f"{contract2.pk},Contract 2,Second contract",
            f"{contract3.pk},Contract 3,Third contract",
        )

        cls.bulk_edit_data = {
            'comments': 'New comment',
        }


class InvoiceTestCase(ModelViewTestCase, ViewTestCases.PrimaryObjectViewTestCase):
    model = Invoice

    @classmethod
    def setUpTestData(cls):

        # Create test provider
        Provider.objects.create(name='Provider A', slug='provider-a')

        # Create test Contract
        contract1 = Contract.objects.create(
            name='Contract1',
            external_partie_object_type=ContentType.objects.get_for_model(Provider),
            external_partie_object_id=Provider.objects.get(slug='provider-a').id,
            internal_partie='default',
            status=StatusChoices.STATUS_ACTIVE,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            currency='usd',
            mrc=Decimal(100),
            invoice_frequency=1
        )

        # Create test invoices
        invoices = Invoice.objects.bulk_create([
            Invoice(number='Invoice1', template=False, date=date(2025, 1, 25),
                    period_start=date(2025, 1, 1), period_end=date(2025, 1, 31),
                    currency='usd', amount=Decimal(100)),
            Invoice(number='Invoice2', template=False, date=date(2025, 2, 25),
                    period_start=date(2025, 2, 1), period_end=date(2025, 2, 28),
                    currency='usd', amount=Decimal(100)),
            Invoice(number='Invoice3', template=False, date=date(2025, 3, 25),
                    period_start=date(2025, 3, 1), period_end=date(2025, 3, 31),
                    currency='usd', amount=Decimal(100))
        ])

        # associate invoices to contract
        for invoice in invoices:
            invoice.save()
            invoice.contracts.add(contract1)

        cls.form_data = {
            'number': 'Invoice X',
            'contracts': [contract1.pk],
            'template': False,
            'date': date(2025, 1, 25),
            'period_start': date(2025, 1, 1),
            'period_end': date(2025, 1, 31),
            'currency': 'usd',
            'amount': Decimal(100),
        }

        cls.csv_data = (
            'number,contracts,currency,amount,date,template,period_start,period_end',
            'invoice4,Contract1,usd,100,2025-04-25,False,2025-04-01,2025-04-30',
            'invoice5,Contract1,usd,100,2025-05-25,False,2025-05-01,2025-05-31',
            'invoice6,Contract1,usd,100,2025-06-25,False,2025-06-01,2025-06-30',
        )

        cls.csv_update_data = (
            'id,number,comments',
            f'{invoices[0].pk},Invoice-1,First invoice',
            f'{invoices[1].pk},Invoice-2,Second invoice',
            f'{invoices[2].pk},Invoice-3,Third invoice',
        )

        cls.bulk_edit_data = {
            'comments': 'New comment',
        }


class InvoiceLineTestCase(ModelViewTestCase, ViewTestCases.PrimaryObjectViewTestCase):
    model = InvoiceLine

    @classmethod
    def setUpTestData(cls):

        # Create test Invoices
        invoices = Invoice.objects.bulk_create([
            Invoice(number='Invoice1', template=False, date=date(2025, 1, 25),
                    period_start=date(2025, 1, 1), period_end=date(2025, 1, 31),
                    currency='usd', amount=Decimal(100)),
            Invoice(number='Invoice2', template=False, date=date(2025, 2, 25),
                    period_start=date(2025, 2, 1), period_end=date(2025, 2, 28),
                    currency='usd', amount=Decimal(100)),
            Invoice(number='Invoice3', template=False, date=date(2025, 3, 25),
                    period_start=date(2025, 3, 1), period_end=date(2025, 3, 31),
                    currency='usd', amount=Decimal(100))
        ])

        for invoice in invoices:
            invoice.save()

        invoice_lines = InvoiceLine.objects.bulk_create([
            InvoiceLine(invoice=invoices[0], currency='usd', amount=Decimal(50)),
            InvoiceLine(invoice=invoices[0], currency='usd', amount=Decimal(50)),
        ])

        for invoice_line in invoice_lines:
            invoice_line.save()

        cls.form_data = {
            'invoice': invoices[1].pk,
            'currency': 'usd',
            'amount': Decimal(100),
        }

        cls.csv_data = (
            'invoice,currency,amount',
            'Invoice3,usd,50',
            'Invoice3,usd,50'
        )

        cls.csv_update_data = (
            'id,comments',
            f'{invoice_lines[0].pk},First line',
            f'{invoice_lines[1].pk},Second line',
        )

        cls.bulk_edit_data = {
            'comments': 'New comment',
        }
