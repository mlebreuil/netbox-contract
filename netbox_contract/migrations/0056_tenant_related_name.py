"""The reverse name of Contract.tenant gets the app label as prefix: state-only change, no SQL (#329)."""

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('netbox_contract', '0055_contractassignment_unique'),
        ('tenancy', '0026_consolidate_unique_constraints'),  # the last one of NetBox 4.7.0
    ]

    operations = [
        migrations.AlterField(
            model_name='contract',
            name='tenant',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='netbox_contract_contracts',
                to='tenancy.tenant',
            ),
        ),
    ]
