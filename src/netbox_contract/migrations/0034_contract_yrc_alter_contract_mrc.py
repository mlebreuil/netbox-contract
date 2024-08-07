# Generated by Django 5.0.6 on 2024-08-01 15:43

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('netbox_contract', '0033_remove_contract_invoice_template'),
    ]

    operations = [
        migrations.AddField(
            model_name='contract',
            name='yrc',
            field=models.DecimalField(
                blank=True, decimal_places=2, max_digits=10, null=True
            ),
        ),
        migrations.AlterField(
            model_name='contract',
            name='mrc',
            field=models.DecimalField(
                blank=True, decimal_places=2, max_digits=10, null=True
            ),
        ),
    ]
