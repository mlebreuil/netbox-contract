from decimal import Decimal

from django.db import migrations

CENT = Decimal('0.01')


def derive_invoice_line_amounts(apps, schema_editor):
    """
    Give every invoice line without unit price one, so that its amount is quantity x unit price (decision I14).
    The amount never changes: unit price = amount / quantity when that is exact, otherwise the line gets quantity
    1 and unit price = amount, and its former quantity is kept in its comments.
    """
    InvoiceLine = apps.get_model('netbox_contract', 'InvoiceLine')
    for line in InvoiceLine.objects.filter(unit_price__isnull=True).order_by('pk'):
        quantity, comments = line.quantity, line.comments
        if quantity and (line.amount / quantity).quantize(CENT) * quantity == line.amount:
            unit_price = (line.amount / quantity).quantize(CENT)
        else:
            if quantity not in (None, 0, 1):
                note = f'Quantity {quantity:f} before the 2.5.0 upgrade (the amount was not quantity x unit price).'
                comments = f'{comments}\n\n{note}' if comments else note
            quantity, unit_price = Decimal(1), line.amount
        InvoiceLine.objects.filter(pk=line.pk).update(quantity=quantity, unit_price=unit_price, comments=comments)


class Migration(migrations.Migration):

    dependencies = [
        ('netbox_contract', '0048_invoice_status_draft_default'),
    ]

    operations = [
        migrations.RunPython(derive_invoice_line_amounts, migrations.RunPython.noop),
    ]
