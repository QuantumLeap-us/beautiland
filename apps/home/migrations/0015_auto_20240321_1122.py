# Generated by Django 3.2.16 on 2024-03-21 11:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0014_auto_20240320_1648'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customer',
            name='area_code',
            field=models.CharField(choices=[('+81', '+81 (Japan)'), ('+33', '+33 (France)'), ('+64', '+64 (New Zealand)'), ('+52', '+52 (Mexico)'), ('+65', '+65 (Singapore)'), ('+39', '+39 (Italy)'), ('+966', '+966 (Saudi Arabia)'), ('+44', '+44 (UK)'), ('+82', '+82 (South Korea)'), ('+7', '+7 (Russia)'), ('+86', '+86 (China)'), ('+34', '+34 (Spain)'), ('+61', '+61 (Australia)'), ('+91', '+91 (India)'), ('+49', '+49 (Germany)'), ('+971', '+971 (UAE)'), ('+55', '+55 (Brazil)'), ('+20', '+20 (Egypt)'), ('+1', '+1 (Canada)'), ('+1', '+1 (US)')], max_length=128),
        ),
        migrations.AlterField(
            model_name='discountvoucher',
            name='amount_trigger',
            field=models.CharField(choices=[('Equals to', 'Equals to'), (None, '-------'), ('More than and equals to', 'More than and equals to'), ('Less than and equals to', 'Less than and equals to'), ('More than', 'More than'), ('Less than', 'Less than')], max_length=128, null=True),
        ),
        migrations.AlterField(
            model_name='discountvoucher',
            name='quantity_trigger',
            field=models.CharField(choices=[('Equals to', 'Equals to'), (None, '-------'), ('More than and equals to', 'More than and equals to'), ('Less than and equals to', 'Less than and equals to'), ('More than', 'More than'), ('Less than', 'Less than')], max_length=128, null=True),
        ),
        migrations.AlterField(
            model_name='order',
            name='payment_status',
            field=models.CharField(choices=[('Paid', 'paid'), ('Pending', 'Pending'), ('Failed', 'Failed')], default='Pending', max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='purchase',
            name='status',
            field=models.CharField(choices=[('Pending', 'Pending'), ('Partially Delivered', 'Partially Delivered'), ('Delivered', 'Delivered')], default='Pending', max_length=128),
        ),
        migrations.AlterField(
            model_name='purchase',
            name='type',
            field=models.CharField(choices=[('Purchase', 'Purchase'), ('Quotation', 'Quotation')], max_length=128),
        ),
        migrations.AlterField(
            model_name='voucher',
            name='status',
            field=models.CharField(choices=[('Ready to start', 'Ready to start'), ('Paused', 'Paused'), ('Valid', 'Valid'), ('Ended', 'Ended'), ('Cancelled', 'Cancelled')], max_length=128),
        ),
        migrations.AlterField(
            model_name='voucher',
            name='voucher_type',
            field=models.CharField(choices=[('Manual Discount', 'Manual Discount'), ('Discount Voucher', 'Discount Voucher'), ('Product Combo', 'Product Combo'), ('Free Gift', 'Free Gift')], max_length=128),
        ),
    ]
