# Generated by Django 3.2.16 on 2024-06-03 08:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0055_auto_20240521_1419'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='delivery_id',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='discountvoucher',
            name='amount_trigger',
            field=models.CharField(choices=[('Equals to', 'Equals to'), ('More than and equals to', 'More than and equals to'), ('Less than and equals to', 'Less than and equals to'), (None, '-------'), ('Less than', 'Less than'), ('More than', 'More than')], max_length=128, null=True),
        ),
        migrations.AlterField(
            model_name='discountvoucher',
            name='quantity_trigger',
            field=models.CharField(choices=[('Equals to', 'Equals to'), ('More than and equals to', 'More than and equals to'), ('Less than and equals to', 'Less than and equals to'), (None, '-------'), ('Less than', 'Less than'), ('More than', 'More than')], max_length=128, null=True),
        ),
        migrations.AlterField(
            model_name='purchase',
            name='status',
            field=models.CharField(choices=[('Pending', 'Pending'), ('Delivered', 'Delivered'), ('Partially Delivered', 'Partially Delivered')], default='Pending', max_length=128),
        ),
        migrations.AlterField(
            model_name='purchase',
            name='type',
            field=models.CharField(choices=[('Quotation', 'Quotation'), ('Purchase', 'Purchase')], max_length=128),
        ),
        migrations.AlterField(
            model_name='supplier',
            name='prefix',
            field=models.CharField(choices=[('+44', '+44 (UK)'), ('+971', '+971 (UAE)'), ('+1', '+1 (Canada)'), ('+49', '+49 (Germany)'), ('+82', '+82 (South Korea)'), ('+64', '+64 (New Zealand)'), ('+55', '+55 (Brazil)'), ('+52', '+52 (Mexico)'), ('+86', '+86 (China)'), ('+61', '+61 (Australia)'), ('+966', '+966 (Saudi Arabia)'), ('+91', '+91 (India)'), ('+7', '+7 (Russia)'), ('+39', '+39 (Italy)'), ('+20', '+20 (Egypt)'), ('+1', '+1 (US)'), ('+65', '+65 (Singapore)'), ('+34', '+34 (Spain)'), ('+33', '+33 (France)'), ('+81', '+81 (Japan)')], max_length=250),
        ),
        migrations.AlterField(
            model_name='voucher',
            name='status',
            field=models.CharField(choices=[('Paused', 'Paused'), ('Valid', 'Valid'), ('Ended', 'Ended'), ('Cancelled', 'Cancelled'), ('Ready to start', 'Ready to start')], max_length=128),
        ),
        migrations.AlterField(
            model_name='voucher',
            name='voucher_type',
            field=models.CharField(choices=[('Manual Discount', 'Manual Discount'), ('Product Combo', 'Product Combo'), ('Free Gift', 'Free Gift'), ('Discount Voucher', 'Discount Voucher')], max_length=128),
        ),
    ]
