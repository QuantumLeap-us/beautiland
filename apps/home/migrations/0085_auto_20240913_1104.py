# Generated by Django 3.2.16 on 2024-09-13 05:34

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0084_auto_20240913_1039'),
    ]

    operations = [
        migrations.AddField(
            model_name='deliverorderitems',
            name='deliver_order',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='home.deliverorder'),
        ),
        migrations.AlterField(
            model_name='discountvoucher',
            name='amount_trigger',
            field=models.CharField(choices=[('Equals to', 'Equals to'), ('Less than and equals to', 'Less than and equals to'), ('More than and equals to', 'More than and equals to'), ('Less than', 'Less than'), (None, '-------'), ('More than', 'More than')], max_length=128, null=True),
        ),
        migrations.AlterField(
            model_name='discountvoucher',
            name='quantity_trigger',
            field=models.CharField(choices=[('Equals to', 'Equals to'), ('Less than and equals to', 'Less than and equals to'), ('More than and equals to', 'More than and equals to'), ('Less than', 'Less than'), (None, '-------'), ('More than', 'More than')], max_length=128, null=True),
        ),
        migrations.AlterField(
            model_name='purchase',
            name='payment_method',
            field=models.CharField(choices=[('COD', 'COD'), ('Bank Transfer/Cheque', 'Bank Transfer/Cheque')], max_length=128, null=True),
        ),
        migrations.AlterField(
            model_name='purchase',
            name='status',
            field=models.CharField(choices=[('Delivered', 'Delivered'), ('Pending', 'Pending'), ('Partially Delivered', 'Partially Delivered')], default='Pending', max_length=128),
        ),
        migrations.AlterField(
            model_name='purchase',
            name='type',
            field=models.CharField(choices=[('Purchase', 'Purchase'), ('Quotation', 'Quotation')], max_length=128),
        ),
        migrations.AlterField(
            model_name='supplier',
            name='prefix',
            field=models.CharField(choices=[('+86', '+86 (China)'), ('+1', '+1 (Canada)'), ('+49', '+49 (Germany)'), ('+971', '+971 (UAE)'), ('+81', '+81 (Japan)'), ('+39', '+39 (Italy)'), ('+65', '+65 (Singapore)'), ('+52', '+52 (Mexico)'), ('+44', '+44 (UK)'), ('+1', '+1 (US)'), ('+34', '+34 (Spain)'), ('+55', '+55 (Brazil)'), ('+61', '+61 (Australia)'), ('+91', '+91 (India)'), ('+33', '+33 (France)'), ('+7', '+7 (Russia)'), ('+966', '+966 (Saudi Arabia)'), ('+20', '+20 (Egypt)'), ('+82', '+82 (South Korea)'), ('+64', '+64 (New Zealand)')], max_length=250),
        ),
        migrations.AlterField(
            model_name='voucher',
            name='discount_type',
            field=models.CharField(choices=[(None, '-------'), ('Rate(%)', 'Rate(%)'), ('Fixed Amount', 'Fixed Amount')], max_length=128, null=True),
        ),
        migrations.AlterField(
            model_name='voucher',
            name='status',
            field=models.CharField(choices=[('Valid', 'Valid'), ('Ready to start', 'Ready to start'), ('Ended', 'Ended'), ('Cancelled', 'Cancelled'), ('Paused', 'Paused')], max_length=128),
        ),
        migrations.AlterField(
            model_name='voucher',
            name='voucher_type',
            field=models.CharField(choices=[('Discount Voucher', 'Discount Voucher'), ('Manual Discount', 'Manual Discount'), ('Product Combo', 'Product Combo'), ('Free Gift', 'Free Gift')], max_length=128),
        ),
    ]
