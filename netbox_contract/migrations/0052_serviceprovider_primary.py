"""Service providers become NetBox primary objects: they get a description and an owner (#309, research D9)."""

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('netbox_contract', '0051_contracttype_organizational'),
        ('users', '0015_owner'),
    ]

    operations = [
        migrations.AddField(
            model_name='serviceprovider',
            name='description',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name='serviceprovider',
            name='owner',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='users.owner'
            ),
        ),
    ]
