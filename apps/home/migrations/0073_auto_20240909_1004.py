# Generated by Django 3.2.16 on 2024-09-09 04:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0072_auto_20240906_1710'),
    ]

    operations = [
        migrations.AlterField(
            model_name='discountvoucher',
            name='amount_trigger',
            field=models.CharField(choices=[('Equals to', 'Equals to'), ('More than', 'More than'), ('Less than', 'Less than'), ('More than and equals to', 'More than and equals to'), (None, '-------'), ('Less than and equals to', 'Less than and equals to')], max_length=128, null=True),
        ),
        migrations.AlterField(
            model_name='discountvoucher',
            name='quantity_trigger',
            field=models.CharField(choices=[('Equals to', 'Equals to'), ('More than', 'More than'), ('Less than', 'Less than'), ('More than and equals to', 'More than and equals to'), (None, '-------'), ('Less than and equals to', 'Less than and equals to')], max_length=128, null=True),
        ),
        migrations.AlterField(
            model_name='order',
            name='order_type',
            field=models.CharField(choices=[('Sales Order', 'Sales Order'), ('Redlivery', 'Redlivery'), ('Redlivery - Broken', 'Redlivery - Broken'), ('Redelivery & Return', 'Redelivery & Return'), ('Return', 'Return')], default='Sales Order', max_length=100),
        ),
        migrations.AlterField(
            model_name='purchase',
            name='payment_method',
            field=models.CharField(choices=[('Bank Transfer/Cheque', 'Bank Transfer/Cheque'), ('COD', 'COD')], max_length=128, null=True),
        ),
        migrations.AlterField(
            model_name='purchase',
            name='status',
            field=models.CharField(choices=[('Delivered', 'Delivered'), ('Pending', 'Pending'), ('Partially Delivered', 'Partially Delivered')], default='Pending', max_length=128),
        ),
        migrations.AlterField(
            model_name='supplier',
            name='prefix',
            field=models.CharField(choices=[('+966', '+966 (Saudi Arabia)'), ('+971', '+971 (UAE)'), ('+52', '+52 (Mexico)'), ('+55', '+55 (Brazil)'), ('+44', '+44 (UK)'), ('+91', '+91 (India)'), ('+7', '+7 (Russia)'), ('+33', '+33 (France)'), ('+39', '+39 (Italy)'), ('+65', '+65 (Singapore)'), ('+82', '+82 (South Korea)'), ('+81', '+81 (Japan)'), ('+86', '+86 (China)'), ('+49', '+49 (Germany)'), ('+1', '+1 (US)'), ('+20', '+20 (Egypt)'), ('+1', '+1 (Canada)'), ('+61', '+61 (Australia)'), ('+64', '+64 (New Zealand)'), ('+34', '+34 (Spain)')], max_length=250),
        ),
        migrations.AlterField(
            model_name='voucher',
            name='discount_type',
            field=models.CharField(choices=[('Fixed Amount', 'Fixed Amount'), (None, '-------'), ('Rate(%)', 'Rate(%)')], max_length=128, null=True),
        ),
        migrations.AlterField(
            model_name='voucher',
            name='status',
            field=models.CharField(choices=[('Ended', 'Ended'), ('Ready to start', 'Ready to start'), ('Paused', 'Paused'), ('Valid', 'Valid'), ('Cancelled', 'Cancelled')], max_length=128),
        ),
        migrations.AlterField(
            model_name='voucher',
            name='voucher_type',
            field=models.CharField(choices=[('Manual Discount', 'Manual Discount'), ('Free Gift', 'Free Gift'), ('Discount Voucher', 'Discount Voucher'), ('Product Combo', 'Product Combo')], max_length=128),
        ),
    ]
