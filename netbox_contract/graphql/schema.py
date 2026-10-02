import strawberry
import strawberry_django

from .types import *


@strawberry.type(name='Query')
class NetBoxContractQuery:
    contract: ContractType = strawberry_django.field()
    contract_list: list[ContractType] = strawberry_django.field()

    contract_line: ContractLineType = strawberry_django.field()
    contract_line_list: list[ContractLineType] = strawberry_django.field()

    contract_type: ContractTypeType = strawberry_django.field()
    contract_type_list: list[ContractTypeType] = strawberry_django.field()

    contract_assignment: ContractAssignmentType = strawberry_django.field()
    contract_assignment_list: list[ContractAssignmentType] = strawberry_django.field()

    invoice: InvoiceType = strawberry_django.field()
    invoice_list: list[InvoiceType] = strawberry_django.field()

    invoice_line: InvoiceLineType = strawberry_django.field()
    invoice_line_list: list[InvoiceLineType] = strawberry_django.field()

    unit: UnitType = strawberry_django.field()
    unit_list: list[UnitType] = strawberry_django.field()

    accounting_dimension: AccountingDimensionType = strawberry_django.field()
    accounting_dimension_list: list[AccountingDimensionType] = strawberry_django.field()

    service_provider: ServiceProviderType = strawberry_django.field()
    service_provider_list: list[ServiceProviderType] = strawberry_django.field()


schema = [
    NetBoxContractQuery,
]
