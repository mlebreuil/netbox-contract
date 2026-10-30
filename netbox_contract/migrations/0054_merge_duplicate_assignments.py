"""Merge the contract assignments that assign the same contract to the same object twice (#318, spec 004).

Lossless: the oldest assignment of each group is kept and receives what the others carry (tags, journal entries,
bookmarks, subscriptions, image attachments, empty custom fields). Every merge, and every custom field whose
values differ, is reported. Running it again finds nothing to merge. The uniqueness rule itself is added by the
next migration, so that the data change and the schema change run in separate transactions.
"""

import logging

from django.db import migrations
from django.db.models import Count

logger = logging.getLogger('netbox_contract')


def _empty(value):
    return value in (None, '', [], {})


def _report(lines, line):
    lines.append(line)
    logger.warning(line)
    print(f'\n  {line}', end='')


def merge_duplicates(apps, schema_editor=None):
    """Merge duplicate (contract, object) assignments; return the report lines."""
    Assignment = apps.get_model('netbox_contract', 'ContractAssignment')
    groups = list(
        Assignment.objects.values('contract_id', 'content_type_id', 'object_id')
        .annotate(total=Count('pk'))
        .filter(total__gt=1)
        .order_by('contract_id', 'content_type_id', 'object_id')
    )
    lines = []
    if not groups:
        return lines

    ContentType = apps.get_model('contenttypes', 'ContentType')
    TaggedItem = apps.get_model('extras', 'TaggedItem')
    JournalEntry = apps.get_model('extras', 'JournalEntry')
    ImageAttachment = apps.get_model('extras', 'ImageAttachment')
    Bookmark = apps.get_model('extras', 'Bookmark')
    Subscription = apps.get_model('extras', 'Subscription')
    assignment_type = ContentType.objects.filter(app_label='netbox_contract', model='contractassignment').first()

    for group in groups:
        key = {name: group[name] for name in ('contract_id', 'content_type_id', 'object_id')}
        rows = list(Assignment.objects.filter(**key).order_by('pk'))
        kept, removed = rows[0], rows[1:]
        description = (
            f'contract assignments: contract #{key["contract_id"]}, object type #{key["content_type_id"]} '
            f'#{key["object_id"]}: kept #{kept.pk}, merged {", ".join(f"#{row.pk}" for row in removed)}'
        )
        moved = []
        custom_fields = dict(kept.custom_field_data or {})
        changed = False

        for row in removed:
            if assignment_type is not None:
                kept_tags = set(
                    TaggedItem.objects.filter(content_type=assignment_type, object_id=kept.pk).values_list(
                        'tag_id', flat=True
                    )
                )
                for item in TaggedItem.objects.filter(content_type=assignment_type, object_id=row.pk):
                    if item.tag_id in kept_tags:
                        item.delete()
                    else:
                        item.object_id = kept.pk
                        item.save()
                        kept_tags.add(item.tag_id)
                        moved.append(f'tag #{item.tag_id}')
                count = JournalEntry.objects.filter(
                    assigned_object_type=assignment_type, assigned_object_id=row.pk
                ).update(assigned_object_id=kept.pk)
                if count:
                    moved.append(f'{count} journal entries')
                count = ImageAttachment.objects.filter(object_type=assignment_type, object_id=row.pk).update(
                    object_id=kept.pk
                )
                if count:
                    moved.append(f'{count} image attachments')
                for model, label in ((Bookmark, 'bookmark'), (Subscription, 'subscription')):
                    for item in model.objects.filter(object_type=assignment_type, object_id=row.pk):
                        if model.objects.filter(
                            object_type=assignment_type, object_id=kept.pk, user_id=item.user_id
                        ).exists():
                            item.delete()
                        else:
                            item.object_id = kept.pk
                            item.save()
                            moved.append(f'{label} of user #{item.user_id}')

            for name, value in (row.custom_field_data or {}).items():
                current = custom_fields.get(name)
                if _empty(value) or value == current:
                    continue
                if _empty(current):
                    custom_fields[name] = value
                    changed = True
                    moved.append(f'custom field {name}')
                else:
                    _report(
                        lines,
                        f'{description}: custom field "{name}" differs, kept {current!r}, '
                        f'the value {value!r} of #{row.pk} is not kept',
                    )

        if changed:
            Assignment.objects.filter(pk=kept.pk).update(custom_field_data=custom_fields)
        Assignment.objects.filter(pk__in=[row.pk for row in removed]).delete()
        _report(lines, description + (f'; moved {", ".join(moved)}' if moved else ''))
    return lines


class Migration(migrations.Migration):

    dependencies = [
        ('netbox_contract', '0053_owner_related_name'),
        ('extras', '0119_notifications'),
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.RunPython(merge_duplicates, migrations.RunPython.noop),
    ]
