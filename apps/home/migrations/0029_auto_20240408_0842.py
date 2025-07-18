# Generated by Django 3.2.16 on 2024-04-08 08:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0028_auto_20240408_0513'),
    ]

    operations = [
        migrations.AddField(
            model_name='supplier',
            name='last_po_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='customer',
            name='area_code',
            field=models.CharField(choices=[('+7', '+7 (Russia)'), ('+64', '+64 (New Zealand)'), ('+20', '+20 (Egypt)'), ('+49', '+49 (Germany)'), ('+971', '+971 (UAE)'), ('+86', '+86 (China)'), ('+52', '+52 (Mexico)'), ('+82', '+82 (South Korea)'), ('+1', '+1 (US)'), ('+33', '+33 (France)'), ('+1', '+1 (Canada)'), ('+65', '+65 (Singapore)'), ('+34', '+34 (Spain)'), ('+91', '+91 (India)'), ('+81', '+81 (Japan)'), ('+39', '+39 (Italy)'), ('+61', '+61 (Australia)'), ('+966', '+966 (Saudi Arabia)'), ('+55', '+55 (Brazil)'), ('+44', '+44 (UK)')], max_length=128),
        ),
        migrations.AlterField(
            model_name='discountvoucher',
            name='amount_trigger',
            field=models.CharField(choices=[('More than', 'More than'), ('Less than and equals to', 'Less than and equals to'), (None, '-------'), ('More than and equals to', 'More than and equals to'), ('Equals to', 'Equals to'), ('Less than', 'Less than')], max_length=128, null=True),
        ),
        migrations.AlterField(
            model_name='discountvoucher',
            name='quantity_trigger',
            field=models.CharField(choices=[('More than', 'More than'), ('Less than and equals to', 'Less than and equals to'), (None, '-------'), ('More than and equals to', 'More than and equals to'), ('Equals to', 'Equals to'), ('Less than', 'Less than')], max_length=128, null=True),
        ),
        migrations.AlterField(
            model_name='purchase',
            name='payment_method',
            field=models.CharField(choices=[('COD', 'COD'), ('Bank Transfer/Cheque', 'Bank Transfer/Cheque')], max_length=128, null=True),
        ),
        migrations.AlterField(
            model_name='purchase',
            name='status',
            field=models.CharField(choices=[('Partially Delivered', 'Partially Delivered'), ('Delivered', 'Delivered'), ('Pending', 'Pending')], default='Pending', max_length=128),
        ),
        migrations.AlterField(
            model_name='supplier',
            name='prefix',
            field=models.CharField(choices=[('+7', '+7 (Russia)'), ('+64', '+64 (New Zealand)'), ('+20', '+20 (Egypt)'), ('+49', '+49 (Germany)'), ('+971', '+971 (UAE)'), ('+86', '+86 (China)'), ('+52', '+52 (Mexico)'), ('+82', '+82 (South Korea)'), ('+1', '+1 (US)'), ('+33', '+33 (France)'), ('+1', '+1 (Canada)'), ('+65', '+65 (Singapore)'), ('+34', '+34 (Spain)'), ('+91', '+91 (India)'), ('+81', '+81 (Japan)'), ('+39', '+39 (Italy)'), ('+61', '+61 (Australia)'), ('+966', '+966 (Saudi Arabia)'), ('+55', '+55 (Brazil)'), ('+44', '+44 (UK)')], max_length=250),
        ),
        migrations.AlterField(
            model_name='voucher',
            name='status',
            field=models.CharField(choices=[('Valid', 'Valid'), ('Cancelled', 'Cancelled'), ('Ended', 'Ended'), ('Paused', 'Paused'), ('Ready to start', 'Ready to start')], max_length=128),
        ),
        migrations.AlterField(
            model_name='voucher',
            name='voucher_type',
            field=models.CharField(choices=[('Discount Voucher', 'Discount Voucher'), ('Free Gift', 'Free Gift'), ('Product Combo', 'Product Combo'), ('Manual Discount', 'Manual Discount')], max_length=128),
        ),
    ]
