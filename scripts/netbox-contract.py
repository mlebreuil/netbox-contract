from datetime import date
from decimal import *
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count
from extras.scripts import *
from netbox_contract.models import Contract, Invoice, InvoiceLine, AccountingDimension, StatusChoices

name = "Netbox-contracts custom scripts"

AMOUNT_PRECEDENCE = (
    ('invoice', 'Invoice'),
    ('dimensions', 'dimensions')
)

class update_expired_contract_status(Script):

    class Meta:
        name = "Update expired contracts status"
        description = "Update the status of contract with end date prior to today's date"
        commit_default = False

    def run(self, data, commit):

        username = self.request.user.username
        self.log_info(f"Running as user {username}")

        output = []

        expired_contracts = Contract.objects.filter(end_date__lte = date.today()).filter(status = StatusChoices.STATUS_ACTIVE )

        self.log_info(f"Processing Contracts")
        for contract in expired_contracts:
            output.append(f"{contract.name} to be updated")
            contract.status = StatusChoices.STATUS_CANCELED
            try:
                contract.save()
                self.log_info(f"{contract.name} updated")
            except Exception as e:
                self.log_failure(f"error processing {contract.name}: {e}")

        return '\n'.join(output)

class create_invoice_template(Script):

    class Meta:
        name = "Create invoice templates"
        description = "Convert the Accounting dimensions json field in Contracts to invoice template"
        commit_default = False

    def run(self, data, commit):

        username = self.request.user.username
        self.log_info(f"Running as user {username}")

        output = []

        self.log_info(f"Creating invoice templates from contract dimensions")

        # Create invoice templates for each active template
        for contract in Contract.objects.filter(status = StatusChoices.STATUS_ACTIVE ):
            self.log_info(f"Processing contract {contract.name}")

            # check if invoice template exist
            try:
                template_exists = True
                invoice_template = Invoice.objects.get(
                    template=True, contracts=contract
                )
            except ObjectDoesNotExist:
                template_exists = False

            if template_exists :
                self.log_info(f"Template already exists for {contract.name}")
                continue
            
            # if the invoice template does not exists create it
            if contract.accounting_dimensions:
                if contract.mrc is not None:
                    amount = contract.mrc * contract.invoice_frequency
                else:
                    amount = contract.yrc / 12 * contract.invoice_frequency
                invoice_template = Invoice(
                    template = True,
                    number = '_invoice_template_' + contract.name,
                    period_start = None,
                    period_end = None,
                    amount = amount,
                    accounting_dimensions = contract.accounting_dimensions
                )
                invoice_template.save()
                invoice_template.contracts.add(contract)
                self.log_info(f"Template {invoice_template.number} created for {contract.name}")

        return '\n'.join(output)

class create_invoice_lines(Script):

    class Meta:
        name = "Create invoice lines"
        description = "Convert the Accounting dimensions json field in invoices to invoice lines"
        commit_default = False

    ignore = StringVar(
        label="Ignore",
        description="Accounting dimensions to be ignored. List of string separated by comma.",
        required=False,
        regex=r"^\w+(,\w+)*$"
    )

    amount_precedence = ChoiceVar(
        label="Amount precedence",
        description="Select if the dimension amount or the invoice amount take precedence,",
        choices = AMOUNT_PRECEDENCE,
        required=False
    )

    line_amount_key = StringVar(
        label="Line amount key",
        description="Key name for line amount in the accounting dimension json with multiple lines",
        required=True,
    )

    def run(self, data, commit):

        username = self.request.user.username
        self.log_info(f"Running as user {username}")

        output = []

        line_amount_key = data['line_amount_key']

        exclude = [line_amount_key]
        if data['ignore']:
            exclude = exclude + data['ignore'].split(',')

        self.log_info(f"Creating invoice lines from invoices dimensions")
        self.log_info(f"Ignoring dimensions {exclude}")
        self.log_info(f"Line amount key {line_amount_key}")

        # import existing dimensions
        dimensions={}
        dims = AccountingDimension.objects.all()
        if dims.exists():
            for dim in dims:
                dimensions[dim.name +"_"+ dim.value] = dim

        # Get all invoices without invoice lines
        invoices = Invoice.objects.annotate(numberoflines=Count("invoicelines"))

        # Create invoice lines for each invoice
        for invoice in invoices:
            if invoice.numberoflines > 0:
                self.log_info(f"Invoice skipped {invoice.number}. Exiting lines")
                continue

            self.log_info(f"Processing Invoice {invoice.number}")
            
            total_invoice_lines_amount = 0
            single_line_invoice = False

            # Create invoice template lines
            # Check if several lines have to be created
            if type(invoice.accounting_dimensions) == list:
                # if the accounting dimensions is a list we assume that we have an "amount" 
                lines = invoice.accounting_dimensions
            else:
                lines = [invoice.accounting_dimensions]

            if len(lines) == 1:
                single_line_invoice = True

            for line in lines:
                if single_line_invoice and data['amount_precedence']=='invoice':
                    amount = invoice.amount
                else: 
                    if line_amount_key in line.keys():
                        if isinstance(line[line_amount_key], str):
                            try:
                                amount = Decimal(line[line_amount_key].replace(",",".").replace(" ",""))
                            except:
                                self.log_warning(f"Wrong number format {line[line_amount_key]}")
                                output.append(f"{invoice.number}: dimensions amount format to be updated")
                        else:
                            try:
                                amount = Decimal(line[line_amount_key])
                            except:
                                self.log_warning(f"Wrong number format {line[line_amount_key]}")
                                output.append(f"{invoice.number}: dimensions amount format to be updated")
                    else:
                        self.log_warning(f"Multiple lines or dimensions precedence and no amount for line")
                        continue

                invoice_line = InvoiceLine(
                    invoice = invoice,
                    currency = invoice.currency,
                    amount = amount,
                )
                invoice_line.save()
                self.log_info(f"Invoice line {invoice_line.id} created for {invoice.number}")
                total_invoice_lines_amount = total_invoice_lines_amount + amount

                # create and add dimensions
                for key, value in line.items():
                    if key not in exclude and value is not None:
                        if key +"_"+ str(value) not in dimensions.keys():
                            dimension = AccountingDimension(
                                name = key,
                                value = str(value)
                            )
                            dimension.save()
                            dimensions[key +"_"+ str(value)] = dimension
                        invoice_line.accounting_dimensions.add(dimensions[key +"_"+ str(value)])
                self.log_info(f"Accounting dimensions added to Invoice line {invoice_line.id}")


            if total_invoice_lines_amount != invoice.amount:
                self.log_warning(f"The total of invoice lines and invoice amount do not match.")
                output.append(f"{invoice.number}: Sum of invoice lines amount to be checked")

        return '\n'.join(output)
