from datetime import date, timedelta
from django.conf import settings
from core.choices import JobIntervalChoices
from netbox.jobs import JobRunner, system_job
from .models import Contract, StatusChoices


plugin_settings = settings.PLUGINS_CONFIG['netbox_contract']


@system_job(interval=JobIntervalChoices.INTERVAL_WEEKLY)
class ContractEndNotificationJob(JobRunner):
    class Meta:
        name = "Contract end notification Job"

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
