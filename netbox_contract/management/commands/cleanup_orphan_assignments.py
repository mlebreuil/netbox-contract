from django.core.management.base import BaseCommand
from django.db import transaction

from netbox_contract.models import ContractAssignment
from netbox_contract.orphans import find_orphan_assignments


class Command(BaseCommand):
    help = (
        'List the contract assignments whose object no longer exists and, with --apply, delete them. '
        'Nothing is deleted without --apply. Assignments whose object type is not installed are listed and kept.'
    )

    def add_arguments(self, parser):
        parser.add_argument('--apply', action='store_true', help='Delete the orphan assignments listed.')

    def handle(self, *args, **options):
        with transaction.atomic():
            report = find_orphan_assignments()
            totals = {}
            for assignment in report.orphans:
                label = str(assignment.content_type)
                totals[label] = totals.get(label, 0) + 1
            self.stdout.write(f'Orphan assignments: {len(report.orphans)}')
            for label, count in sorted(totals.items()):
                self.stdout.write(f'  {label}: {count}')
            for a in report.orphans:
                self.stdout.write(
                    f'  assignment {a.pk}: contract "{a.contract}", {a.content_type} (former id {a.object_id})'
                )
            if report.cannot_judge:
                self.stdout.write(f'Not judged (object type not installed), kept: {len(report.cannot_judge)}')
                for a in report.cannot_judge:
                    self.stdout.write(
                        f'  assignment {a.pk}: contract "{a.contract}", {a.content_type.app_label}.'
                        f'{a.content_type.model} (id {a.object_id})'
                    )
            if options['apply']:
                deleted = ContractAssignment.objects.filter(pk__in=[a.pk for a in report.orphans]).delete()[0]
                self.stdout.write(f'Deleted: {deleted}')
            elif report.orphans:
                self.stdout.write('Dry run: nothing deleted. Run again with --apply to delete them.')
