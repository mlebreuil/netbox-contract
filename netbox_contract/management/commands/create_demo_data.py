from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from netbox_contract.demo import create_demo_data, reset_demo_data


class Command(BaseCommand):
    help = (
        'Create demo data for development: named scenarios covering units, contract lines of each billing method, '
        'open-ended contracts, hierarchies, invoices in each status, amendments, legacy data, numeric edge cases and '
        'accounting dimensions. Everything is tagged "netbox-contract-demo". Safe to run more than once: a scenario '
        'that exists is skipped. Refuses to run unless DEVELOPER = True.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset', action='store_true',
            help='Delete the demo data (found by its tag), including Posted invoices, before creating it again.',
        )

    def handle(self, *args, **options):
        if not settings.DEVELOPER:
            raise CommandError('create_demo_data refuses to run unless DEVELOPER = True in the NetBox configuration.')
        if options['reset']:
            deleted = reset_demo_data()
            self.stdout.write('Deleted: ' + (', '.join(f'{n} {name}' for name, n in deleted.items()) or 'nothing'))
        report = create_demo_data()
        self.stdout.write(str(report))
