from django.db import migrations


def convert_legacy_costs(apps, schema_editor):
    from netbox_contract.conversion import convert_legacy_data

    report = convert_legacy_data(apps)
    if report.lines_created or report.messages:
        print(f'\nnetbox_contract: conversion of contract costs and invoice templates\n{report}')


class Migration(migrations.Migration):

    dependencies = [
        ('netbox_contract', '0044_units_contract_lines_billable'),
    ]

    operations = [
        migrations.RunPython(convert_legacy_costs, migrations.RunPython.noop),
    ]
