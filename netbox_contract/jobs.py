from datetime import date, timedelta
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from core.choices import JobIntervalChoices
from netbox.jobs import JobRunner, system_job
from extras.models import EventRule
from extras.events import process_event_rules, serialize_for_event
from .models import Contract, StatusChoices


plugin_settings = settings.PLUGINS_CONFIG['netbox_contract']


@system_job(interval=JobIntervalChoices.INTERVAL_WEEKLY)
class ContractEventTrigger(JobRunner):
    class Meta:
        name = "Contract end event processing job"

    def run(self, *args, **kwargs):
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
