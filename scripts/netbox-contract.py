from datetime import date, timedelta
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from extras.scripts import IntegerVar, ObjectVar, Script
from extras.models import EventRule
from extras.events import process_event_rules, serialize_for_event
from netbox_contract.models import (
    AccountingDimension,
    Contract,
    InvoiceLine,
    StatusChoices,
)


plugin_settings = settings.PLUGINS_CONFIG['netbox_contract']

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


class ContractEventTrigger(Script):
    class Meta:
        name = "Contract end event processing script"
        commit_default = False

    def run(self, data, commit):
        contracts = Contract.objects.filter(status=StatusChoices.STATUS_ACTIVE)
        days_before_notice_notification = plugin_settings.get('days_before_notice_notification')

        for contract in contracts:
            if contract.end_date is not None:
                if contract.notice_date <= date.today() + timedelta(
                    days=days_before_notice_notification
                ):
                    # set 'notice_warning'
                    contract.notice_warning = True
                    contract.save()

                    # process event rules
                    event_rules = EventRule.objects.filter(
                        event_types__contains=['contract_notice'],
                        enabled=True,
                        object_types=ContentType.objects.get_for_model(contract),
                    )

                    data = serialize_for_event(contract)

                    username = None
                    process_event_rules(
                        event_rules=event_rules,
                        object_type=ContentType.objects.get_for_model(contract),
                        event_type='contract_notice',
                        data=data,
                        username=username
                    )
