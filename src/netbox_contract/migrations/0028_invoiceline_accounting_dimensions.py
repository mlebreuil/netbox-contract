# Generated by Django 5.0.6 on 2024-06-30 20:19

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('netbox_contract', '0027_invoiceline'),
    ]

    operations = [
        migrations.AddField(
            model_name='invoiceline',
            name='accounting_dimensions',
            field=models.JSONField(null=True),
        ),
    ]
