from datetime import date, timedelta
from decimal import Decimal, InvalidOperation

from django.db.models import Count
from extras.scripts import ChoiceVar, IntegerVar, ObjectVar, Script, StringVar

from netbox_contract.models import (
    AccountingDimension,
    Contract,
    Invoice,
    InvoiceLine,
    StatusChoices,
)

name = 'Contracts related scripts'

AMOUNT_PRECEDENCE = (('invoice', 'Invoice'), ('dimensions', 'dimensions'))


class update_expired_contract_status(Script):
    class Meta:
        name = 'Update expired contracts status'
        description = (
            "Update the status of contract with end date prior to today's date"
        )
        commit_default = False

    def run(self, data, commit):
        username = self.request.user.username
        self.log_info(f'Running as user {username}')

        output = []

        expired_contracts = Contract.objects.filter(end_date__lte=date.today()).filter(
            status=StatusChoices.STATUS_ACTIVE
        )
        expired_contracts.update(status=StatusChoices.STATUS_CANCELED)

        return '\n'.join(output)


class create_invoice_template(Script):
    class Meta:
        name = 'Create invoice templates'
        description = 'Convert the Accounting dimensions json field in Contracts to invoice template'
        commit_default = False

    def run(self, data, commit):
        username = self.request.user.username
        self.log_info(f'Running as user {username}')

        output = []

        self.log_info('Creating invoice templates from contract dimensions')

        # Create invoice templates for each active template
        for contract in Contract.objects.filter(status=StatusChoices.STATUS_ACTIVE):
            self.log_info(f'Processing contract {contract.name}')

            # check if invoice template exist
            invoice_template = Invoice.objects.filter(
                template=True, contracts=contract
            ).first()

            if invoice_template:
                self.log_info(f'Template already exists for {contract.name}')
                continue

            # if the invoice template does not exists create it
            if contract.accounting_dimensions:
                if contract.mrc is not None:
                    amount = contract.mrc * contract.invoice_frequency
                else:
                    amount = contract.yrc / 12 * contract.invoice_frequency
                invoice_template = Invoice(
                    template=True,
                    number=f'_invoice_template_{contract.name}',
                    period_start=None,
                    period_end=None,
                    amount=amount,
                    accounting_dimensions=contract.accounting_dimensions,
                )
                invoice_template.save()
                invoice_template.contracts.add(contract)
                self.log_info(
                    f'Template {invoice_template.number} created for {contract.name}'
                )

        return '\n'.join(output)


class create_invoice_lines(Script):
    class Meta:
        name = 'Create invoice lines'
        description = (
            'Convert the Accounting dimensions json field in invoices to invoice lines'
        )
        commit_default = False

    ignore = StringVar(
        label='Ignore',
        description='Accounting dimensions to be ignored. List of string separated by comma.',
        required=False,
        regex=r'^\w+(,\w+)*$',
    )

    amount_precedence = ChoiceVar(
        label='Amount precedence',
        description='Select if the dimension amount or the invoice amount take precedence,',
        choices=AMOUNT_PRECEDENCE,
        required=False,
    )

    line_amount_key = StringVar(
        label='Line amount key',
        description='Key name for line amount in the accounting dimension json with multiple lines',
        required=True,
    )

    def run(self, data, commit):
        username = self.request.user.username
        self.log_info(f'Running as user {username}')

        output = []

        line_amount_key = data['line_amount_key']

        exclude = [line_amount_key]
        if data['ignore']:
            exclude.extend(data['ignore'].split(','))

        self.log_info('Creating invoice lines from invoices dimensions')
        self.log_info(f'Ignoring dimensions {exclude}')
        self.log_info(f'Line amount key {line_amount_key}')

        # import existing dimensions
        dimensions = {}
        dims = AccountingDimension.objects.all()
        if dims.exists():
            for dim in dims:
                dimensions[f'{dim.name}_{dim.value}'] = dim

        # Get all invoices without invoice lines
        invoices = Invoice.objects.annotate(numberoflines=Count('invoicelines'))

        # Create invoice lines for each invoice
        for invoice in invoices:
            if invoice.numberoflines > 0:
                self.log_info(f'Invoice skipped {invoice.number}. Exiting lines')
                continue

            self.log_info(f'Processing Invoice {invoice.number}')

            total_invoice_lines_amount = 0

            # Create invoice template lines
            # Check if several lines have to be created
            if isinstance(invoice.accounting_dimensions, list):
                # if the accounting dimensions is a list we assume that we have an "amount"
                lines = invoice.accounting_dimensions
            else:
                lines = [invoice.accounting_dimensions]

            single_line_invoice = len(lines) == 1

            for line in lines:
                if single_line_invoice and data['amount_precedence'] == 'invoice':
                    amount = invoice.amount
                else:
                    # Retrieving with get reduce the repetition of code
                    amount = line.get(line_amount_key)
                    # Checking first the case "not exist" allow us to remove one indent level
                    # NOTE: This works fine because None is not a valid value in this case.
                    if not amount:
                        self.log_warning(
                            'Multiple lines or dimensions precedence and no amount for line'
                        )
                        continue
                    # The try-except part is the same and can be extracted
                    if isinstance(amount, str):
                        amount = amount.replace(',', '.').replace(' ', '')
                    try:
                        amount = Decimal(line[line_amount_key])
                    except InvalidOperation:
                        self.log_warning(f'Wrong number format {line[line_amount_key]}')
                        output.append(
                            f'{invoice.number}: dimensions amount format to be updated'
                        )

                invoice_line = InvoiceLine(
                    invoice=invoice,
                    currency=invoice.currency,
                    amount=amount,
                )
                invoice_line.save()
                self.log_info(
                    f'Invoice line {invoice_line.id} created for {invoice.number}'
                )
                total_invoice_lines_amount = total_invoice_lines_amount + amount

                # create and add dimensions
                for key, value in line.items():
                    if key not in exclude and value is not None:
                        dimkey = f'{key}_{value}'
                        if dimkey not in dimensions.keys():
                            dimension = AccountingDimension(name=key, value=str(value))
                            dimension.save()
                            dimensions[dimkey] = dimension
                        invoice_line.accounting_dimensions.add(dimensions[dimkey])
                self.log_info(
                    f'Accounting dimensions added to Invoice line {invoice_line.id}'
                )

            if total_invoice_lines_amount != invoice.amount:
                self.log_warning(
                    'The total of invoice lines and invoice amount do not match.'
                )
                output.append(
                    f'{invoice.number}: Sum of invoice lines amount to be checked'
                )

        return '\n'.join(output)


class bulk_replace_accounting_dimension(Script):
    class Meta:
        name = 'Replace accounting dimension'
        description = 'Replace one accounting dimension by another one for all lines'
        commit_default = False

    current = ObjectVar(
        label='Current dimension',
        description='The accounting dimension to be replaced.',
        model=AccountingDimension,
    )

    new = ObjectVar(
        label='New accounting dimension',
        description='The new accounting dimension',
        model=AccountingDimension,
    )

    def run(self, data, commit):
        username = self.request.user.username
        self.log_info(f'Running as user {username}')

        output = []

        current_dimension = data['current']
        new_dimension = data['new']

        lines = InvoiceLine.objects.filter(accounting_dimensions=current_dimension)
        for line in lines:
            line.accounting_dimensions.remove(current_dimension)
            line.accounting_dimensions.add(new_dimension)
            self.log_info(f'invoice {line.invoice.number} updated')

        return '\n'.join(output)


class Check_contract_end(Script):
    class Meta:
        name = 'Check contract end'
        description = 'Check which contract will end '
        commit_default = False

    days_before_notice = IntegerVar(
        label='Days before notice',
        description='Report on contract with notice periode approaching',
    )

    def run(self, data, commit):
        username = self.request.user.username
        self.log_info(f'Running as user {username}')

        output = []

        days_before_notice = data['days_before_notice']

        contracts = Contract.objects.filter(status=StatusChoices.STATUS_ACTIVE)
        for contract in contracts:
            if contract.end_date is not None:
                if contract.notice_date <= date.today() + timedelta(
                    days=days_before_notice
                ):
                    self.log_info(
                        f'Contract {contract} end date: {contract.end_date} - notice : {contract.notice_period} days'
                    )
                    output.append(
                        f'{contract.name} - end date: {contract.end_date} - notice : {contract.notice_period} days'
                    )

        return '\n'.join(output)
