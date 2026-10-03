from django.core.management.base import BaseCommand
from django.db import transaction

from netbox_contract.conversion import convert_legacy_data


class Command(BaseCommand):
    help = (
        'Create contract lines from the deprecated costs and invoice templates of the contracts that have no '
        'contract lines yet, and print the conversion report. Safe to run more than once.'
    )

    def handle(self, *args, **options):
        with transaction.atomic():
            report = convert_legacy_data()
        self.stdout.write(str(report))
