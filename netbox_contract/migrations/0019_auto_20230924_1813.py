# Generated by Django 4.2.5 on 2023-09-24 18:13

from django.db import migrations


def migrate_external_partie(apps, schema_editor):
    """
    Migrate contract Service providers to the new model
    """
    Contract = apps.get_model('netbox_contract', 'Contract')
    ContentType = apps.get_model('contenttypes', 'ContentType')
    ServiceProvider = apps.get_model('netbox_contract', 'ServiceProvider')
    ServiceProviderType = ContentType.objects.get(
        model=ServiceProvider._meta.model_name,
        app_label=ServiceProvider._meta.app_label,
    )

    for contract in Contract.objects.all():
        contract.external_partie_object_type = ServiceProviderType
        contract.external_partie_object_id = contract.external_partie.id
        contract.save()


def reverse_external_partie(apps, schema_editor):
    """
    Migrate contract Service providers to the new model
    """
    Contract = apps.get_model('netbox_contract', 'Contract')

    for contract in Contract.objects.all():
        contract.external_partie_object_type = None
        contract.external_partie_object_id = None
        contract.save()


class Migration(migrations.Migration):
    dependencies = [
        ('netbox_contract', '0018_contract_external_partie_object_id_and_more'),
    ]

    operations = [
    #    migrations.RunPython(migrate_external_partie, reverse_external_partie),
    ]
