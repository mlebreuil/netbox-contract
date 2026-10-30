"""Assignments whose object no longer exists (spec 006, research R8)."""

from dataclasses import dataclass, field

from django.contrib.contenttypes.models import ContentType

from .models import ContractAssignment


@dataclass
class OrphanReport:
    orphans: list = field(default_factory=list)  # assignments whose object is gone
    cannot_judge: list = field(default_factory=list)  # assignments whose object type is not installed


def find_orphan_assignments():
    """Compare every assignment with the object it points to; never changes anything."""
    report = OrphanReport()
    for content_type in ContentType.objects.filter(contractassignment__isnull=False).distinct():
        assignments = ContractAssignment.objects.filter(content_type=content_type).select_related('contract')
        model = content_type.model_class()
        if model is None:
            report.cannot_judge.extend(assignments.order_by('pk'))
            continue
        ids = [a.object_id for a in assignments]
        existing = set(model._base_manager.filter(pk__in=ids).values_list('pk', flat=True))
        report.orphans.extend(a for a in assignments.order_by('pk') if a.object_id not in existing)
    report.orphans.sort(key=lambda a: a.pk)
    return report
