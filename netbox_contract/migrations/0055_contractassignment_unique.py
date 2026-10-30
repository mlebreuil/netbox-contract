"""A contract is assigned to an object only once (#318, spec 004); duplicates were merged by 0054."""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('netbox_contract', '0054_merge_duplicate_assignments'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='contractassignment',
            constraint=models.UniqueConstraint(
                fields=('contract', 'content_type', 'object_id'), name='netbox_contract_unique_assignment'
            ),
        ),
    ]
