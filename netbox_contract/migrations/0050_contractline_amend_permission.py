from django.db import migrations


class Migration(migrations.Migration):
    """Declare the "amend" permission action of contract lines (#309, research D6)."""

    dependencies = [
        ('netbox_contract', '0049_invoiceline_derived_amounts'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='contractline',
            options={
                'ordering': ('contract', 'start_date', 'description'),
                'permissions': [('amend', 'Amend the price or quantity of an invoiced contract line')],
                'verbose_name': 'contract line',
                'verbose_name_plural': 'contract lines',
            },
        ),
    ]
