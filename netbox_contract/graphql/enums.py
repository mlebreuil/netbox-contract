import strawberry

from ..models import AccountingDimensionStatusChoices, BillingMethodChoices, InvoiceStatusChoices, StatusChoices

__all__ = (
    'AccountingDimensionStatusEnum',
    'BillingMethodEnum',
    'ContractStatusEnum',
    'InvoiceStatusEnum',
)


AccountingDimensionStatusEnum = strawberry.enum(
    AccountingDimensionStatusChoices.as_enum('AccountingDimensionStatusEnum', prefix='status')
)
BillingMethodEnum = strawberry.enum(BillingMethodChoices.as_enum('BillingMethodEnum', prefix='billing_method'))
ContractStatusEnum = strawberry.enum(StatusChoices.as_enum('ContractStatusEnum', prefix='status'))
InvoiceStatusEnum = strawberry.enum(InvoiceStatusChoices.as_enum('InvoiceStatusEnum', prefix='status'))
