# Generated by Django 3.2.16 on 2024-04-05 06:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0024_auto_20240405_0506'),
    ]

    operations = [
        migrations.AddField(
            model_name='supplier',
            name='status',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='customer',
            name='area_code',
            field=models.CharField(choices=[('+64', '+64 (New Zealand)'), ('+33', '+33 (France)'), ('+65', '+65 (Singapore)'), ('+20', '+20 (Egypt)'), ('+971', '+971 (UAE)'), ('+1', '+1 (US)'), ('+7', '+7 (Russia)'), ('+55', '+55 (Brazil)'), ('+82', '+82 (South Korea)'), ('+81', '+81 (Japan)'), ('+966', '+966 (Saudi Arabia)'), ('+86', '+86 (China)'), ('+61', '+61 (Australia)'), ('+91', '+91 (India)'), ('+49', '+49 (Germany)'), ('+1', '+1 (Canada)'), ('+39', '+39 (Italy)'), ('+44', '+44 (UK)'), ('+34', '+34 (Spain)'), ('+52', '+52 (Mexico)')], max_length=128),
        ),
        migrations.AlterField(
            model_name='discountvoucher',
            name='amount_trigger',
            field=models.CharField(choices=[('Less than and equals to', 'Less than and equals to'), ('Less than', 'Less than'), (None, '-------'), ('Equals to', 'Equals to'), ('More than', 'More than'), ('More than and equals to', 'More than and equals to')], max_length=128, null=True),
        ),
        migrations.AlterField(
            model_name='discountvoucher',
            name='quantity_trigger',
            field=models.CharField(choices=[('Less than and equals to', 'Less than and equals to'), ('Less than', 'Less than'), (None, '-------'), ('Equals to', 'Equals to'), ('More than', 'More than'), ('More than and equals to', 'More than and equals to')], max_length=128, null=True),
        ),
        migrations.AlterField(
            model_name='purchase',
            name='payment_method',
            field=models.CharField(choices=[('Bank Transfer/Cheque', 'Bank Transfer/Cheque'), ('COD', 'COD')], max_length=128, null=True),
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
            name='discount_type',
            field=models.CharField(choices=[('Rate(%)', 'Rate(%)'), (None, '-------'), ('Fixed Amount', 'Fixed Amount')], max_length=128, null=True),
        ),
        migrations.AlterField(
            model_name='voucher',
            name='status',
            field=models.CharField(choices=[('Ready to start', 'Ready to start'), ('Cancelled', 'Cancelled'), ('Ended', 'Ended'), ('Paused', 'Paused'), ('Valid', 'Valid')], max_length=128),
        ),
        migrations.AlterField(
            model_name='voucher',
            name='voucher_type',
            field=models.CharField(choices=[('Product Combo', 'Product Combo'), ('Free Gift', 'Free Gift'), ('Manual Discount', 'Manual Discount'), ('Discount Voucher', 'Discount Voucher')], max_length=128),
        ),
    ]
