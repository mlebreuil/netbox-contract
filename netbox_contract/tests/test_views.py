from datetime import date
from decimal import Decimal

from circuits.models import Circuit, CircuitType, Provider, ProviderAccount
from dcim.models import Device, DeviceRole, DeviceType, Manufacturer, Site
from django.contrib.contenttypes.models import ContentType
from netbox.choices import ColorChoices
from tenancy.models import Tenant
from utilities.testing import ViewTestCases

from netbox_contract.models import (
    AccountingDimension,
    Contract,
    ContractAssignment,
    ContractType,
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

        # Create test provider
        Provider.objects.create(name='Provider A', slug='provider-a')
        # create test tenant
        Tenant.objects.create(name='Tenant 1', slug='tenant-1')
        ServiceProvider.objects.create(name='Service Provider A', slug='service-provider-a')
        # Create test contract-ype
        ContractType.objects.create(
            name='Contract Type A',
            description='Description for type A',
            color=ColorChoices.COLOR_BLUE
        )

        # Create three Contracts
        contract1 = Contract.objects.create(
            name='Contract1',
            contract_type=ContractType.objects.get(name='Contract Type A'),
            external_party_object_type=ContentType.objects.get_for_model(Provider),
            external_party_object_id=Provider.objects.get(slug='provider-a').id,
            internal_party='default',
            status=StatusChoices.STATUS_ACTIVE,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            currency='usd',
            yrc=Decimal(1000),
            invoice_frequency=1
        )

        contract2 = Contract.objects.create(
            name='Contract2',
            external_party_object_type=ContentType.objects.get_for_model(Provider),
            external_party_object_id=Provider.objects.get(slug='provider-a').id,
            internal_party='default',
            status=StatusChoices.STATUS_ACTIVE,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            currency='usd',
            yrc=Decimal(1000),
            invoice_frequency=1
        )

        contract3 = Contract.objects.create(
            name='Contract3',
            external_party_object_type=ContentType.objects.get_for_model(Provider),
            external_party_object_id=Provider.objects.get(slug='provider-a').id,
            internal_party='default',
            status=StatusChoices.STATUS_ACTIVE,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            currency='usd',
            yrc=Decimal(1000),
            invoice_frequency=1
        )

        cls.form_data = {
            'name': 'Contract X',
            'contract_type': ContractType.objects.get(name='Contract Type A').pk,
            'external_party_object_type': ContentType.objects.get_for_model(Provider).pk,
            'external_party_object': Provider.objects.get(slug='provider-a').id,
            'external_reference': 'External Reference 1',
            'internal_party': 'default',
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
            'name,contract_type,external_party_object_type,external_party_object_id,internal_party,'
            'tenant,status,start_date,end_date,currency,mrc,nrc,invoice_frequency',
            'Contract 4,Contract Type A,netbox_contract.serviceprovider,Service Provider A,entity1,'
            'Tenant 1,active,2025-01-01,2025-12-31,usd,100,1000,1',
            'Contract 5,Contract Type A,netbox_contract.serviceprovider,Service Provider A,entity1,'
            'Tenant 1,active,2025-01-01,2025-12-31,usd,100,1000,1',
            'Contract 6,Contract Type A,netbox_contract.serviceprovider,Service Provider A,entity1,'
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
            external_party_object_type=ContentType.objects.get_for_model(Provider),
            external_party_object_id=Provider.objects.get(slug='provider-a').id,
            internal_party='default',
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


class AccountingDimensionTestCase(ModelViewTestCase, ViewTestCases.PrimaryObjectViewTestCase):
    model = AccountingDimension

    @classmethod
    def setUpTestData(cls):

        # Create test dimensions
        dimensions = AccountingDimension.objects.bulk_create([
            AccountingDimension(name='account', value='account1', status=StatusChoices.STATUS_ACTIVE),
            AccountingDimension(name='account', value='account2', status=StatusChoices.STATUS_ACTIVE),
        ])

        for dimension in dimensions:
            dimension.save()

        cls.form_data = {
            'name': 'cc',
            'value': 'cc1',
            'status': StatusChoices.STATUS_ACTIVE,
        }

        cls.csv_data = (
            'name,value,status',
            'cc,cc2,active',
            'account,account3,active'
        )

        cls.csv_update_data = (
            'id,comments',
            f'{dimensions[0].pk},First account',
            f'{dimensions[1].pk},Second account',
        )

        cls.bulk_edit_data = {
            'comments': 'New comment',
        }


class ServiceProviderTestCase(ModelViewTestCase, ViewTestCases.PrimaryObjectViewTestCase):
    model = ServiceProvider

    @classmethod
    def setUpTestData(cls):

        # Create test providers
        providers = ServiceProvider.objects.bulk_create([
            ServiceProvider(name='Provider 1', slug='provider-1'),
            ServiceProvider(name='Provider 2', slug='provider-2'),
        ])

        for provider in providers:
            provider.save()

        cls.form_data = {
            'name': 'Provider 3',
            'slug': 'provider-3',
        }

        cls.csv_data = (
            'name,slug',
            'Provider 4,provider-4',
            'Provider 5,provider-5'
        )

        cls.csv_update_data = (
            'id,comments',
            f'{providers[0].pk},First provider',
            f'{providers[1].pk},Second provider',
        )

        cls.bulk_edit_data = {
            'comments': 'New comment',
        }


class ContractTypeTestCase(ModelViewTestCase, ViewTestCases.PrimaryObjectViewTestCase):
    model = ContractType

    @classmethod
    def setUpTestData(cls):
        # Create test contract types
        contract_types = ContractType.objects.bulk_create([
            ContractType(name='Contract Type 1', description='Description for type 1', color=ColorChoices.COLOR_BLUE),
            ContractType(name='Contract Type 2', description='Description for type 2', color=ColorChoices.COLOR_RED),
        ])

        for contract_type in contract_types:
            contract_type.save()

        cls.form_data = {
            'name': 'Contract Type 3',
            'description': 'Description for type 3',
            'color': ColorChoices.COLOR_GREEN,
        }

        cls.csv_data = (
            'name,description,color',
            'Contract Type 4,Description for type 4,' + str(ColorChoices.COLOR_YELLOW),
            'Contract Type 5,Description for type 5,' + str(ColorChoices.COLOR_ORANGE)
        )

        cls.csv_update_data = (
            'id,description',
            f'{contract_types[0].pk},Updated description for type 1',
            f'{contract_types[1].pk},Updated description for type 2',
        )

        cls.bulk_edit_data = {
            'description': 'Updated bulk description',
        }


class ContractAssignmentTestCase(ModelViewTestCase, ViewTestCases.PrimaryObjectViewTestCase):
    model = ContractAssignment

    @classmethod
    def setUpTestData(cls):

        # Create a test device
        site = Site.objects.create(name='Site 1', slug='site-1')
        manufacturer = Manufacturer.objects.create(name='Manufacturer 1', slug='manufacturer-1')
        devicetype = DeviceType.objects.create(model='Device Type 1', slug='device-type-1', manufacturer=manufacturer)
        role = DeviceRole.objects.create(name='Device Role 1', slug='device-role-1')
        device1 = Device.objects.create(
                name='Device 1',
                site=site,
                device_type=devicetype,
                role=role
            )
        device2 = Device.objects.create(
                name='Device 2',
                site=site,
                device_type=devicetype,
                role=role
            )
        device3 = Device.objects.create(
                name='Device 3',
                site=site,
                device_type=devicetype,
                role=role
            )
        device4 = Device.objects.create(
                name='Device 4',
                site=site,
                device_type=devicetype,
                role=role
            )
        # Create a test service provider
        service_provider = ServiceProvider.objects.create(name='Service Provider 1', slug='service-provider-1')
        service_provider.save()

        # Create a test Contract
        contract1 = Contract.objects.create(
            name='Contract1',
            external_party_object_type=ContentType.objects.get_for_model(ServiceProvider),
            external_party_object_id=ServiceProvider.objects.get(slug='service-provider-1').id,
            internal_party='default',
            status=StatusChoices.STATUS_ACTIVE,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            currency='usd',
            yrc=Decimal(1000),
            invoice_frequency=1
        )

        # Create a test circuit
        provider = Provider.objects.create(name='Provider A', slug='provider-a')
        provider.save()
        provider_account = ProviderAccount.objects.create(name='Provider Account 1', provider=provider, account='1234')
        circuit_type = CircuitType.objects.create(name='Circuit Type 1', slug='circuit-type-1')
        circuit1 = Circuit.objects.create(
                cid='Circuit 1', provider=provider, provider_account=provider_account, type=circuit_type
            )
        circuit2 = Circuit.objects.create(
                cid='Circuit 2', provider=provider, provider_account=provider_account, type=circuit_type
            )
        circuit3 = Circuit.objects.create(
                cid='Circuit 3', provider=provider, provider_account=provider_account, type=circuit_type
            )

        contract2 = Contract.objects.create(
            name='Contract2',
            external_party_object_type=ContentType.objects.get_for_model(Provider),
            external_party_object_id=Provider.objects.get(slug='provider-a').id,
            internal_party='default',
            status=StatusChoices.STATUS_ACTIVE,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            currency='usd',
            yrc=Decimal(1000),
            invoice_frequency=1
        )

        # Create test assignements
        assignements = ContractAssignment.objects.bulk_create([
            ContractAssignment(
                content_type=ContentType.objects.get_for_model(Device),
                content_object=device1,
                contract=contract1
            ),
            ContractAssignment(
                content_type=ContentType.objects.get_for_model(Circuit),
                content_object=circuit1,
                contract=contract2
            )
        ])

        for assignement in assignements:
            assignement.save()

        cls.form_data = {
            'content_type': ContentType.objects.get_for_model(Device).pk,
            'object_id': device2.pk,
            'contract': contract1.pk
        }

        cls.csv_data = (
            'content_type,object_id,contract',
            f'circuits.circuit,{circuit3.pk},{contract2.pk}',
            f'circuits.circuit,{device3.pk},{contract1.pk}',
        )

        cls.csv_update_data = (
            'id,object_id',
            f'{assignements[0].pk},{device4.pk}',
            f'{assignements[1].pk},{circuit2.pk}',
        )

        # contract for bulk edition
        contract3 = Contract.objects.create(
            name='Contract3',
            external_party_object_type=ContentType.objects.get_for_model(ServiceProvider),
            external_party_object_id=ServiceProvider.objects.get(slug='service-provider-1').id,
            internal_party='default',
            status=StatusChoices.STATUS_ACTIVE,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            currency='usd',
            yrc=Decimal(1100),
            invoice_frequency=1
        )

        contract3.save()

        cls.bulk_edit_data = {
            'contract': contract3.pk,
        }
