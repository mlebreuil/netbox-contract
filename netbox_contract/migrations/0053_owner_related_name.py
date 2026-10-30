"""NetBox 4.7 gives the owner field of its objects `related_name='+'`: state-only change, no SQL (#318)."""

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('netbox_contract', '0052_serviceprovider_primary'),
        ('users', '0015_owner'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contracttype',
            name='owner',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='users.owner'
            ),
        ),
        migrations.AlterField(
            model_name='serviceprovider',
            name='owner',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='users.owner'
            ),
        ),
    ]
