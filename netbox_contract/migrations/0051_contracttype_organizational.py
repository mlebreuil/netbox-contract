"""
Contract types become NetBox organizational objects (#309, research D9 and D10): they get a slug, comments and an
owner, and their description is limited to 200 characters like on core objects.

Existing types get a unique slug derived from their name. A description longer than 200 characters is shortened at a
word boundary and its full text is moved to the comments, so that no text is lost; every slug made unique and every
description moved is reported. Running the data step again changes nothing.

Migrating back restores the moved descriptions from the comments before the new columns are dropped. Comments typed
after the upgrade are dropped with their column.
"""

import django.db.models.deletion
from django.db import migrations, models


def fill_slugs_and_shorten_descriptions(apps, schema_editor):
    from netbox_contract.text import plan_contract_type_changes

    ContractType = apps.get_model('netbox_contract', 'ContractType')
    rows = list(ContractType.objects.order_by('pk').values_list('pk', 'name', 'slug', 'description'))
    taken = {slug for _, _, slug, _ in rows if slug}
    changes, report = plan_contract_type_changes(rows, taken)
    for pk, change in changes.items():
        ContractType.objects.filter(pk=pk).update(**change)
    if report:
        print('\nnetbox_contract: contract types\n  ' + '\n  '.join(report))


def restore_descriptions(apps, schema_editor):
    from netbox_contract.text import restored_description

    ContractType = apps.get_model('netbox_contract', 'ContractType')
    for pk, description, comments in ContractType.objects.values_list('pk', 'description', 'comments'):
        full_text = restored_description(description, comments)
        if full_text is not None:
            ContractType.objects.filter(pk=pk).update(description=full_text)


class Migration(migrations.Migration):

    dependencies = [
        ('netbox_contract', '0050_contractline_amend_permission'),
        ('users', '0015_owner'),
    ]

    operations = [
        migrations.AddField(
            model_name='contracttype',
            name='slug',
            # No index yet: the unique constraint below creates it (adding both makes PostgreSQL's "_like" index twice)
            field=models.SlugField(blank=True, db_index=False, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='contracttype',
            name='comments',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='contracttype',
            name='owner',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='users.owner'
            ),
        ),
        migrations.RunPython(fill_slugs_and_shorten_descriptions, restore_descriptions),
        migrations.AlterField(
            model_name='contracttype',
            name='slug',
            field=models.SlugField(blank=True, max_length=100, unique=True),
        ),
        migrations.AlterField(
            model_name='contracttype',
            name='description',
            field=models.CharField(blank=True, max_length=200),
        ),
    ]
