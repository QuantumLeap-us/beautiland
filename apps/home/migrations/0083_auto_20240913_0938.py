# Generated by Django 3.2.16 on 2024-09-13 04:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0082_auto_20240913_0936'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderitems',
            name='delivered_quantity',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='orderitems',
            name='delivery_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='discountvoucher',
            name='amount_trigger',
            field=models.CharField(choices=[('More than and equals to', 'More than and equals to'), ('Equals to', 'Equals to'), ('Less than and equals to', 'Less than and equals to'), ('More than', 'More than'), (None, '-------'), ('Less than', 'Less than')], max_length=128, null=True),
        ),
        migrations.AlterField(
            model_name='discountvoucher',
            name='quantity_trigger',
            field=models.CharField(choices=[('More than and equals to', 'More than and equals to'), ('Equals to', 'Equals to'), ('Less than and equals to', 'Less than and equals to'), ('More than', 'More than'), (None, '-------'), ('Less than', 'Less than')], max_length=128, null=True),
        ),
        migrations.AlterField(
            model_name='purchase',
            name='payment_method',
            field=models.CharField(choices=[('Bank Transfer/Cheque', 'Bank Transfer/Cheque'), ('COD', 'COD')], max_length=128, null=True),
        ),
        migrations.AlterField(
            model_name='purchase',
            name='status',
            field=models.CharField(choices=[('Pending', 'Pending'), ('Delivered', 'Delivered'), ('Partially Delivered', 'Partially Delivered')], default='Pending', max_length=128),
        ),
        migrations.AlterField(
            model_name='purchase',
            name='type',
            field=models.CharField(choices=[('Purchase', 'Purchase'), ('Quotation', 'Quotation')], max_length=128),
        ),
        migrations.AlterField(
            model_name='supplier',
            name='prefix',
            field=models.CharField(choices=[('+20', '+20 (Egypt)'), ('+1', '+1 (US)'), ('+81', '+81 (Japan)'), ('+966', '+966 (Saudi Arabia)'), ('+34', '+34 (Spain)'), ('+55', '+55 (Brazil)'), ('+61', '+61 (Australia)'), ('+49', '+49 (Germany)'), ('+44', '+44 (UK)'), ('+971', '+971 (UAE)'), ('+52', '+52 (Mexico)'), ('+39', '+39 (Italy)'), ('+7', '+7 (Russia)'), ('+86', '+86 (China)'), ('+65', '+65 (Singapore)'), ('+91', '+91 (India)'), ('+33', '+33 (France)'), ('+82', '+82 (South Korea)'), ('+64', '+64 (New Zealand)'), ('+1', '+1 (Canada)')], max_length=250),
        ),
        migrations.AlterField(
            model_name='voucher',
            name='discount_type',
            field=models.CharField(choices=[('Fixed Amount', 'Fixed Amount'), ('Rate(%)', 'Rate(%)'), (None, '-------')], max_length=128, null=True),
        ),
        migrations.AlterField(
            model_name='voucher',
            name='status',
            field=models.CharField(choices=[('Ready to start', 'Ready to start'), ('Ended', 'Ended'), ('Valid', 'Valid'), ('Cancelled', 'Cancelled'), ('Paused', 'Paused')], max_length=128),
        ),
        migrations.AlterField(
            model_name='voucher',
            name='voucher_type',
            field=models.CharField(choices=[('Product Combo', 'Product Combo'), ('Manual Discount', 'Manual Discount'), ('Free Gift', 'Free Gift'), ('Discount Voucher', 'Discount Voucher')], max_length=128),
        ),
    ]
